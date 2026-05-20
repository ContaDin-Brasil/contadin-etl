"""Handlers de insights e KPIs de objetivos."""

from uuid import UUID

from app.api.schemas.objectives_insights_schema import (
    AcaoRecomendadaResponse,
    InsightItem,
    TipoObjetivo,
)
from app.api.services.objectives_insights_service import (
    gerar_acao_recomendada,
    gerar_insights_objetivos,
)


def handle_acao_recomendada(
    fk_usuario: UUID,
    *,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    tipo_objetivo: TipoObjetivo | None = None,
) -> AcaoRecomendadaResponse:
    return gerar_acao_recomendada(
        fk_usuario,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo_objetivo=tipo_objetivo,
    )


def handle_insights_objetivos(fk_usuario: UUID) -> list[InsightItem]:
    return gerar_insights_objetivos(fk_usuario)
