"""Matching de entidades existentes no banco de dados."""

import logging
from unicodedata import normalize, category

from sqlalchemy import text

from app.core.database import get_engine

logger = logging.getLogger(__name__)


def _normalizar(texto: str) -> str:
    """Remove acentos e converte pra lowercase pra comparação."""
    texto = normalize("NFD", texto.lower().strip())
    return "".join(c for c in texto if category(c) != "Mn")


def _buscar_instituicoes(usuario_id: int) -> dict[str, int]:
    """Retorna mapa nome_normalizado -> id das instituições do usuário."""
    with get_engine().connect() as conn:
        rows = conn.execute(
            text("SELECT id, nome FROM instituicao WHERE fk_usuario = :uid"),
            {"uid": usuario_id},
        ).fetchall()
    return {_normalizar(row[1]): row[0] for row in rows}


def _buscar_categorias(usuario_id: int) -> dict[str, int]:
    """Retorna mapa nome_normalizado -> id das categorias do usuário e globais."""
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, nome FROM categoria
                WHERE fk_usuario = :uid OR fk_usuario IS NULL
            """
            ),
            {"uid": usuario_id},
        ).fetchall()
    # Categorias do usuário ficam por último no dict, sobrescrevendo globais de mesmo nome
    return {_normalizar(row[1]): row[0] for row in rows}


def _match_ou_avisa(mapa: dict[str, int], nome: str, contexto: str) -> int | None:
    """Busca o ID no mapa e loga um aviso se não encontrar."""
    resultado = mapa.get(_normalizar(nome))
    if resultado is None:
        logger.warning("Match não encontrado — %s: '%s'", contexto, nome)
    return resultado


def match_data_response(data: dict, usuario_id: int) -> dict:
    """
    Recebe o dict estruturado (saída do Gemini já parseada) e enriquece
    com IDs de entidades existentes no banco para o usuário.
    """
    map_inst = _buscar_instituicoes(usuario_id)
    map_cat = _buscar_categorias(usuario_id)

    for inst in data.get("instituicoes", []):
        nome = inst.get("nome")
        if nome:
            inst["id_existente"] = _match_ou_avisa(map_inst, nome, "instituicao")

    for cat in data.get("categorias", []):
        nome = cat.get("nome")
        if nome:
            cat["id_existente"] = _match_ou_avisa(map_cat, nome, "categoria")

    for trans in data.get("transacoes", []):
        nome_inst = trans.get("instituicao")
        nome_cat = trans.get("categoria")
        if nome_inst:
            trans["fk_instituicao"] = _match_ou_avisa(
                map_inst, nome_inst, "transacao.instituicao"
            )
        if nome_cat:
            trans["fk_categoria"] = _match_ou_avisa(
                map_cat, nome_cat, "transacao.categoria"
            )

    for meta in data.get("metas_gasto", []):
        meta["fk_usuario"] = usuario_id
        nome_cat = meta.get("categoria")
        if nome_cat:
            meta["fk_categoria"] = _match_ou_avisa(
                map_cat, nome_cat, "meta_gasto.categoria"
            )

    return data


def match_scan_response(data: dict, usuario_id: int) -> dict:
    """
    Recebe o dict do scan de imagem (transacao + instituicao) e enriquece
    com IDs de entidades existentes no banco para o usuário.
    """
    map_inst = _buscar_instituicoes(usuario_id)
    map_cat = _buscar_categorias(usuario_id)

    inst = data.get("instituicao", {})
    nome_inst = inst.get("nome")
    if nome_inst:
        inst["id_existente"] = _match_ou_avisa(map_inst, nome_inst, "scan.instituicao")

    trans = data.get("transacao", {})
    nome_inst_trans = trans.get("instituicao")
    nome_cat = trans.get("categoria")
    if nome_inst_trans:
        trans["fk_instituicao"] = _match_ou_avisa(
            map_inst, nome_inst_trans, "scan.transacao.instituicao"
        )
    if nome_cat:
        trans["fk_categoria"] = _match_ou_avisa(
            map_cat, nome_cat, "scan.transacao.categoria"
        )

    return data
