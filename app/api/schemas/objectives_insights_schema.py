"""Schemas para insights e ação recomendada de objetivos."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TipoObjetivo = Literal["LIMITE_GASTO", "AUMENTO_RECEITA"]


class AcaoRecomendadaResponse(BaseModel):
    acao_recomendada: str = ""
    objetivo_id: UUID | None = None


class InsightItem(BaseModel):
    objetivo_id: UUID
    insight: str = ""
