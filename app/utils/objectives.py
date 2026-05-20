"""Consultas e métricas de objetivos (padrão igual a match.py)."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import text

from app.core.database import get_engine

TipoObjetivo = Literal["LIMITE_GASTO", "AUMENTO_RECEITA"]

StatusObjetivo = Literal[
    "EM_ANDAMENTO",
    "PERTO_DO_LIMITE",
    "ACIMA_DO_COMBINADO",
    "META_BATIDA",
    "PERIODO_NAO_INICIADO",
    "PERIODO_ENCERRADO",
]

INSIGHT_PADRAO_OK = (
    "Você está controlando bem este objetivo. Continue acompanhando seus gastos."
)
ACAO_PADRAO_OK = (
    "Continue organizando suas finanças — seus objetivos estão sob controle."
)


@dataclass(frozen=True)
class ObjetivoRow:
    id: UUID
    nome: str
    tipo_objetivo: TipoObjetivo
    valor: float
    data_inicio: date
    data_fim: date
    fk_categoria: UUID
    nome_categoria: str


@dataclass(frozen=True)
class ObjetivoEnriquecido:
    objetivo_id: UUID
    nome: str
    tipo_objetivo: TipoObjetivo
    nome_categoria: str
    data_inicio: date
    data_fim: date
    valor: float
    valor_realizado: float
    percentual: float | None
    status: str
    concluido: bool
    dias_restantes: int | None
    gap: float | None
    padrao_semana: dict[str, float] | None = None


def _as_float(value: Decimal | float | int) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _calcular_metricas(
    *,
    tipo_objetivo: TipoObjetivo,
    valor: float,
    valor_realizado: float,
    data_inicio: date,
    data_fim: date,
    hoje: date,
) -> tuple[float | None, float | None, int | None, bool, StatusObjetivo]:
    concluido = data_fim < hoje

    if data_inicio > hoje:
        return None, None, (data_fim - hoje).days, False, "PERIODO_NAO_INICIADO"

    percentual: float | None = None
    if valor > 0:
        percentual = round((valor_realizado / valor) * 100, 1)

    gap = (
        round(valor - valor_realizado, 2)
        if tipo_objetivo == "AUMENTO_RECEITA"
        else round(valor_realizado - valor, 2)
    )
    dias_restantes = max((data_fim - hoje).days, 0) if not concluido else 0

    if concluido:
        return percentual, gap, dias_restantes, True, "PERIODO_ENCERRADO"

    if tipo_objetivo == "LIMITE_GASTO":
        if valor_realizado > valor:
            status: StatusObjetivo = "ACIMA_DO_COMBINADO"
        elif percentual is not None and percentual >= 80:
            status = "PERTO_DO_LIMITE"
        else:
            status = "EM_ANDAMENTO"
    elif valor_realizado >= valor:
        status = "META_BATIDA"
    else:
        status = "EM_ANDAMENTO"

    return percentual, gap, dias_restantes, concluido, status


def listavel_na_ui(data_inicio: date, data_fim: date, hoje: date | None = None) -> bool:
    hoje = hoje or date.today()
    return data_inicio <= hoje and data_fim >= hoje


def _periodo_efetivo(
    obj: ObjetivoRow,
    hoje: date,
    data_inicio_filtro: date | None,
    data_fim_filtro: date | None,
) -> tuple[date, date]:
    inicio = obj.data_inicio
    fim = min(obj.data_fim, hoje)
    if data_inicio_filtro is not None:
        inicio = max(inicio, data_inicio_filtro)
    if data_fim_filtro is not None:
        fim = min(fim, data_fim_filtro, obj.data_fim)
    return inicio, fim


def buscar_objetivos(
    fk_usuario: UUID,
    *,
    tipo_objetivo: TipoObjetivo | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[ObjetivoRow]:
    sql = """
        SELECT
            o.id,
            o.nome,
            o.tipo_objetivo,
            o.valor,
            o.data_inicio,
            o.data_fim,
            o.fk_categoria,
            c.nome AS nome_categoria
        FROM objetivo o
        JOIN categoria c ON c.id = o.fk_categoria
        WHERE o.fk_usuario = :fk_usuario
    """
    params: dict[str, Any] = {"fk_usuario": str(fk_usuario)}

    if tipo_objetivo is not None:
        sql += " AND o.tipo_objetivo = :tipo_objetivo"
        params["tipo_objetivo"] = tipo_objetivo
    if data_inicio is not None:
        sql += " AND o.data_fim >= :data_inicio"
        params["data_inicio"] = data_inicio
    if data_fim is not None:
        sql += " AND o.data_inicio <= :data_fim"
        params["data_fim"] = data_fim

    sql += " ORDER BY o.data_fim ASC, o.nome ASC"

    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    result: list[ObjetivoRow] = []
    for row in rows:
        result.append(
            ObjetivoRow(
                id=UUID(str(row[0])),
                nome=row[1],
                tipo_objetivo=row[2],
                valor=_as_float(row[3]),
                data_inicio=row[4] if isinstance(row[4], date) else row[4].date(),
                data_fim=row[5] if isinstance(row[5], date) else row[5].date(),
                fk_categoria=UUID(str(row[6])),
                nome_categoria=row[7],
            )
        )
    return result


def buscar_realizado_por_objetivo(
    fk_usuario: UUID,
    objetivos: list[ObjetivoRow],
    *,
    hoje: date,
    data_inicio_filtro: date | None = None,
    data_fim_filtro: date | None = None,
) -> dict[UUID, float]:
    if not objetivos:
        return {}

    ids = [str(o.id) for o in objetivos]
    sql = """
        SELECT
            o.id,
            COALESCE(SUM(t.valor), 0) AS total
        FROM objetivo o
        LEFT JOIN transacao t ON t.fk_categoria = o.fk_categoria
            AND t.tipo::text = CASE
                WHEN o.tipo_objetivo = 'LIMITE_GASTO' THEN 'GASTO'
                ELSE 'RECEITA'
            END
            AND t.data_transacao::date >= GREATEST(
                o.data_inicio,
                COALESCE(:data_inicio_filtro, o.data_inicio)
            )
            AND t.data_transacao::date <= LEAST(
                o.data_fim,
                COALESCE(:data_fim_filtro, o.data_fim),
                :hoje
            )
        LEFT JOIN instituicao i ON i.id = t.fk_instituicao
            AND i.fk_usuario = :fk_usuario
        WHERE o.fk_usuario = :fk_usuario
          AND o.id = ANY(CAST(:objetivo_ids AS uuid[]))
        GROUP BY o.id
    """
    params: dict[str, Any] = {
        "fk_usuario": str(fk_usuario),
        "hoje": hoje,
        "data_inicio_filtro": data_inicio_filtro,
        "data_fim_filtro": data_fim_filtro,
        "objetivo_ids": ids,
    }

    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    realizado = {UUID(str(r[0])): _as_float(r[1]) for r in rows}
    for obj in objetivos:
        realizado.setdefault(obj.id, 0.0)
    return realizado


def buscar_padrao_semana(
    fk_usuario: UUID,
    objetivo_ids: list[UUID],
    *,
    periodo_inicio: date,
    periodo_fim: date,
) -> dict[UUID, dict[str, float]]:
    if not objetivo_ids:
        return {}

    sql = """
        SELECT
            o.id,
            CASE WHEN EXTRACT(ISODOW FROM t.data_transacao) IN (6, 7)
                THEN 'fim_de_semana' ELSE 'dias_uteis' END AS periodo,
            SUM(t.valor) AS total
        FROM objetivo o
        JOIN transacao t ON t.fk_categoria = o.fk_categoria
            AND t.tipo = 'GASTO'
            AND t.data_transacao::date >= :periodo_inicio
            AND t.data_transacao::date <= :periodo_fim
        JOIN instituicao i ON i.id = t.fk_instituicao
            AND i.fk_usuario = :fk_usuario
        WHERE o.fk_usuario = :fk_usuario
          AND o.tipo_objetivo = 'LIMITE_GASTO'
          AND o.id = ANY(CAST(:objetivo_ids AS uuid[]))
        GROUP BY o.id, periodo
    """
    params = {
        "fk_usuario": str(fk_usuario),
        "periodo_inicio": periodo_inicio,
        "periodo_fim": periodo_fim,
        "objetivo_ids": [str(i) for i in objetivo_ids],
    }

    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    out: dict[UUID, dict[str, float]] = {}
    for oid, periodo, total in rows:
        uid = UUID(str(oid))
        out.setdefault(uid, {})
        out[uid][str(periodo)] = _as_float(total)
    return out


def buscar_top_gastos_globais(
    fk_usuario: UUID,
    *,
    dias: int = 90,
    limite: int = 8,
) -> list[dict[str, Any]]:
    hoje = date.today()
    inicio = hoje - timedelta(days=dias)
    sql = """
        SELECT c.nome, SUM(t.valor) AS total, COUNT(*) AS qtd
        FROM transacao t
        JOIN instituicao i ON i.id = t.fk_instituicao AND i.fk_usuario = :fk_usuario
        JOIN categoria c ON c.id = t.fk_categoria
        WHERE t.tipo = 'GASTO'
          AND t.data_transacao::date >= :inicio
          AND t.data_transacao::date <= :fim
        GROUP BY c.id, c.nome
        ORDER BY total DESC
        LIMIT :limite
    """
    params = {
        "fk_usuario": str(fk_usuario),
        "inicio": inicio,
        "fim": hoje,
        "limite": limite,
    }
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()

    return [
        {"categoria": r[0], "total": round(_as_float(r[1]), 2), "qtd": int(r[2])}
        for r in rows
    ]


def enriquecer_objetivos(
    fk_usuario: UUID,
    objetivos: list[ObjetivoRow],
    *,
    hoje: date | None = None,
    data_inicio_filtro: date | None = None,
    data_fim_filtro: date | None = None,
    incluir_padrao_semana: bool = False,
) -> list[ObjetivoEnriquecido]:
    hoje = hoje or date.today()
    if not objetivos:
        return []

    periodos = [
        _periodo_efetivo(o, hoje, data_inicio_filtro, data_fim_filtro)
        for o in objetivos
    ]
    periodo_inicio = min(p[0] for p in periodos)
    periodo_fim = max(p[1] for p in periodos)

    realizado_map = buscar_realizado_por_objetivo(
        fk_usuario,
        objetivos,
        hoje=hoje,
        data_inicio_filtro=data_inicio_filtro,
        data_fim_filtro=data_fim_filtro,
    )

    padrao_map: dict[UUID, dict[str, float]] = {}
    if incluir_padrao_semana:
        ids_gasto = [o.id for o in objetivos if o.tipo_objetivo == "LIMITE_GASTO"]
        padrao_map = buscar_padrao_semana(
            fk_usuario,
            ids_gasto,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
        )

    enriquecidos: list[ObjetivoEnriquecido] = []
    for obj in objetivos:
        realizado = realizado_map.get(obj.id, 0.0)
        percentual, gap, dias_restantes, concluido, status = _calcular_metricas(
            tipo_objetivo=obj.tipo_objetivo,
            valor=obj.valor,
            valor_realizado=realizado,
            data_inicio=obj.data_inicio,
            data_fim=obj.data_fim,
            hoje=hoje,
        )
        enriquecidos.append(
            ObjetivoEnriquecido(
                objetivo_id=obj.id,
                nome=obj.nome,
                tipo_objetivo=obj.tipo_objetivo,
                nome_categoria=obj.nome_categoria,
                data_inicio=obj.data_inicio,
                data_fim=obj.data_fim,
                valor=obj.valor,
                valor_realizado=realizado,
                percentual=percentual,
                status=status,
                concluido=concluido,
                dias_restantes=dias_restantes,
                gap=gap,
                padrao_semana=padrao_map.get(obj.id),
            )
        )
    return enriquecidos


def objetivo_para_prompt(item: ObjetivoEnriquecido) -> dict[str, Any]:
    row: dict[str, Any] = {
        "objetivo_id": str(item.objetivo_id),
        "nome": item.nome,
        "tipo_objetivo": item.tipo_objetivo,
        "nome_categoria": item.nome_categoria,
        "data_inicio": item.data_inicio.isoformat(),
        "data_fim": item.data_fim.isoformat(),
        "valor": item.valor,
        "valor_realizado": round(item.valor_realizado, 2),
        "percentual": item.percentual,
        "status": item.status,
        "concluido": item.concluido,
        "dias_restantes": item.dias_restantes,
        "gap": item.gap,
    }
    if item.padrao_semana:
        row["padrao_semana"] = item.padrao_semana
    return row
