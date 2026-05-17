"""Gera insights e ação recomendada a partir de objetivos e transações no banco."""

import json
import logging
from datetime import date
from pathlib import Path
from uuid import UUID

from app.api.schemas.objectives_insights_schema import (
    AcaoRecomendadaResponse,
    InsightItem,
    TipoObjetivo,
)
from app.core.exceptions import AIResponseError
from app.modules.etl.transform import parse_ai_response
from app.modules.gemini import generate
from app.utils.objectives import (
    ACAO_PADRAO_OK,
    INSIGHT_PADRAO_OK,
    ObjetivoEnriquecido,
    ObjetivoRow,
    buscar_objetivos,
    buscar_top_gastos_globais,
    enriquecer_objetivos,
    listavel_na_ui,
    objetivo_para_prompt,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "modules" / "gemini" / "prompts"


def _parse_data(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _modo_filtrado(
    data_inicio: date | None,
    data_fim: date | None,
    tipo_objetivo: TipoObjetivo | None,
) -> bool:
    return data_inicio is not None or data_fim is not None or tipo_objetivo is not None


def _insight_for_objetivo(rows: object, objetivo_id: UUID) -> str:
    if not isinstance(rows, list):
        return ""
    tid = str(objetivo_id)
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = (
            row.get("objetivo_id")
            if row.get("objetivo_id") is not None
            else row.get("objetivoId")
        )
        if rid is not None and str(rid) == tid:
            ins = row.get("insight")
            if isinstance(ins, str):
                return ins.strip()
            if ins is not None:
                return str(ins).strip()
            return ""
    return ""


def _normalizar_insight(texto: str, item: ObjetivoEnriquecido) -> str:
    if texto:
        return texto
    if (
        item.status in ("EM_ANDAMENTO", "META_BATIDA")
        and item.tipo_objetivo == "AUMENTO_RECEITA"
    ):
        return INSIGHT_PADRAO_OK
    if item.status in ("EM_ANDAMENTO", "PERIODO_NAO_INICIADO"):
        return INSIGHT_PADRAO_OK
    if item.status == "META_BATIDA":
        return "Parabéns, você atingiu o valor combinado para este objetivo."
    return INSIGHT_PADRAO_OK


def _carregar_objetivos_ui(
    fk_usuario: UUID,
    *,
    tipo_objetivo: TipoObjetivo | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
) -> list[ObjetivoRow]:
    try:
        rows = buscar_objetivos(
            fk_usuario,
            tipo_objetivo=tipo_objetivo,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    except Exception as exc:  # noqa: BLE001 — banco indisponível / tabela ausente
        logger.warning("Objetivos: falha ao buscar no banco (%s)", exc)
        return []

    hoje = date.today()
    return [o for o in rows if listavel_na_ui(o.data_inicio, o.data_fim, hoje)]


def _montar_contexto_acao(
    fk_usuario: UUID,
    *,
    data_inicio: date | None,
    data_fim: date | None,
    tipo_objetivo: TipoObjetivo | None,
) -> dict:
    filtrado = _modo_filtrado(data_inicio, data_fim, tipo_objetivo)
    rows = _carregar_objetivos_ui(
        fk_usuario,
        tipo_objetivo=tipo_objetivo if filtrado else None,
        data_inicio=data_inicio if filtrado else None,
        data_fim=data_fim if filtrado else None,
    )

    enriquecidos = enriquecer_objetivos(
        fk_usuario,
        rows,
        data_inicio_filtro=data_inicio if filtrado else None,
        data_fim_filtro=data_fim if filtrado else None,
        incluir_padrao_semana=not filtrado,
    )

    payload: dict = {
        "fk_usuario": str(fk_usuario),
        "modo": "filtrado" if filtrado else "geral",
        "data_inicio": data_inicio.isoformat() if data_inicio else None,
        "data_fim": data_fim.isoformat() if data_fim else None,
        "tipo_objetivo": tipo_objetivo,
        "objetivos": [objetivo_para_prompt(o) for o in enriquecidos],
    }

    if not filtrado:
        try:
            payload["gastos_globais_top"] = buscar_top_gastos_globais(fk_usuario)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Top gastos globais: falha (%s)", exc)
            payload["gastos_globais_top"] = []

    return payload


def gerar_insights_objetivos(fk_usuario: UUID) -> list[InsightItem]:
    rows = _carregar_objetivos_ui(fk_usuario)
    if not rows:
        return []

    enriquecidos = enriquecer_objetivos(
        fk_usuario,
        rows,
        incluir_padrao_semana=True,
    )

    template = (PROMPTS_DIR / "insights_objectives.md").read_text(encoding="utf-8")
    payload = {
        "fk_usuario": str(fk_usuario),
        "objetivos": [objetivo_para_prompt(o) for o in enriquecidos],
    }
    prompt = f"{template}\n{json.dumps(payload, ensure_ascii=False)}"

    try:
        raw = generate(prompt)
        data = parse_ai_response(raw)
        itens_raw = data.get("itens", []) if isinstance(data, dict) else []
        return [
            InsightItem(
                objetivo_id=o.objetivo_id,
                insight=_normalizar_insight(
                    _insight_for_objetivo(itens_raw, o.objetivo_id),
                    o,
                ),
            )
            for o in enriquecidos
        ]
    except (AIResponseError, OSError, ValueError, TypeError) as exc:
        logger.warning("Insights objetivos: fallback (%s)", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Insights objetivos: erro inesperado (%s)", exc)

    return [
        InsightItem(objetivo_id=o.objetivo_id, insight=INSIGHT_PADRAO_OK)
        for o in enriquecidos
    ]


def gerar_acao_recomendada(
    fk_usuario: UUID,
    *,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    tipo_objetivo: TipoObjetivo | None = None,
) -> AcaoRecomendadaResponse:
    d_inicio = _parse_data(data_inicio)
    d_fim = _parse_data(data_fim)

    payload = _montar_contexto_acao(
        fk_usuario,
        data_inicio=d_inicio,
        data_fim=d_fim,
        tipo_objetivo=tipo_objetivo,
    )

    if not payload.get("objetivos") and not payload.get("gastos_globais_top"):
        return AcaoRecomendadaResponse(acao_recomendada=ACAO_PADRAO_OK)

    template = (PROMPTS_DIR / "acao_recomendada.md").read_text(encoding="utf-8")
    prompt = f"{template}\n{json.dumps(payload, ensure_ascii=False)}"

    try:
        raw = generate(prompt)
        data = parse_ai_response(raw)
        texto = data.get("acao_recomendada")
        if texto is None:
            texto = data.get("acaoRecomendada")
        if not isinstance(texto, str):
            texto = str(texto) if texto is not None else ""

        oid_raw = data.get("objetivo_id")
        if oid_raw is None:
            oid_raw = data.get("objetivoId")
        objetivo_uuid: UUID | None = None
        if oid_raw not in (None, "", "null"):
            try:
                objetivo_uuid = UUID(str(oid_raw))
            except ValueError:
                objetivo_uuid = None

        texto = texto.strip()
        if not texto:
            texto = ACAO_PADRAO_OK

        return AcaoRecomendadaResponse(
            acao_recomendada=texto,
            objetivo_id=objetivo_uuid,
        )
    except (AIResponseError, OSError, ValueError, TypeError) as exc:
        logger.warning("Ação recomendada: fallback (%s)", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ação recomendada: erro inesperado (%s)", exc)

    return AcaoRecomendadaResponse(acao_recomendada=ACAO_PADRAO_OK)
