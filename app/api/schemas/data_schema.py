"""Schemas de Data (ETL)"""

from pydantic import BaseModel


class InstitutionData(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    icone: str | None = None
    cor: str | None = None
    id_existente: int | None = None


class CategoryData(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    icone: str | None = None
    cor: str | None = None
    id_existente: int | None = None


class TransactionData(BaseModel):
    valor: float | None = None
    tipo: str | None = None
    descricao: str | None = None
    data_transacao: str | None = None
    parcelado: bool | None = None
    recorrencia: str | None = None
    fim_transacao: str | None = None
    instituicao: str | None = None
    categoria: str | None = None
    fk_instituicao: int | None = None
    fk_categoria: int | None = None


class SpendingGoalData(BaseModel):
    nome: str | None = None
    valor: float | None = None
    data_fim_meta: str | None = None
    categoria: str | None = None
    fk_categoria: int | None = None
    fk_usuario: int | None = None


class DataProcessResponse(BaseModel):
    instituicoes: list[InstitutionData]
    categorias: list[CategoryData]
    transacoes: list[TransactionData]
    metas_gasto: list[SpendingGoalData]
