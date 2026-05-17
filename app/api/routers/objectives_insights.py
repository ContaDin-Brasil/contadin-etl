"""Rotas de insights e ação recomendada para objetivos."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.controllers.objectives_insights_controller import (
    handle_acao_recomendada,
    handle_insights_objetivos,
)
from app.api.schemas.objectives_insights_schema import (
    AcaoRecomendadaResponse,
    InsightItem,
    TipoObjetivo,
)

router = APIRouter(prefix="/objetivos/kpis", tags=["objetivos", "kpis"])


@router.get("/acao-recomendada", response_model=AcaoRecomendadaResponse)
def get_acao_recomendada(
    fk_usuario: UUID = Query(..., description="UUID do usuário"),
    data_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    data_fim: str | None = Query(None, description="YYYY-MM-DD"),
    tipo_objetivo: TipoObjetivo | None = Query(None),
):
    """Uma ação recomendada: visão geral ou focada no período/tipo informado."""
    return handle_acao_recomendada(
        fk_usuario,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tipo_objetivo=tipo_objetivo,
    )


@router.get("/insights", response_model=list[InsightItem])
def get_insights_objetivos(
    fk_usuario: UUID = Query(..., description="UUID do usuário"),
):
    """Um insight por objetivo ativo na listagem do usuário."""
    return handle_insights_objetivos(fk_usuario)
