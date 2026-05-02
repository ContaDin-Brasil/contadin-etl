"""Schemas de Data (ETL)"""

from typing import Literal

from pydantic import BaseModel

TipoMovimento = Literal["GASTO", "RECEITA"]
TipoRecorrencia = Literal["DIARIO", "SEMANAL", "MENSAL", "ANUAL"]


class InstitutionData(BaseModel):
    """Instituição"""
    id: int | None = None
    nome: str | None = None
    tipo: str | None = None
    icone: str | None = None
    cor: str | None = None
    fk_usuario: int | None = None


class CategoryData(BaseModel):
    """Categoria"""
    id: int | None = None
    nome: str | None = None
    tipo: TipoMovimento | None = None
    icone: str | None = None
    cor: str | None = None
    fk_usuario: int | None = None


class TransactionData(BaseModel):
    """Transação"""
    valor: float | None = None
    tipo: TipoMovimento | None = None
    descricao: str | None = None
    data_transacao: str | None = None
    parcelado: bool | None = None
    recorrencia: TipoRecorrencia | None = None
    fim_transacao: str | None = None
    instituicao: str | None = None
    categoria: str | None = None
    fk_instituicao: int | None = None
    fk_categoria: int | None = None


class SpendingGoalData(BaseModel):
    """Meta de Gasto"""
    nome: str | None = None
    valor: float | None = None
    data_fim_meta: str | None = None
    categoria: str | None = None
    fk_categoria: int | None = None
    fk_usuario: int | None = None


class DataProcessResponse(BaseModel):
    """Resposta do Processamento de Dados"""
    instituicoes: list[InstitutionData]
    categorias: list[CategoryData]
    transacoes: list[TransactionData]
    metas_gasto: list[SpendingGoalData]
