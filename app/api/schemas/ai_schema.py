"""Schemas de IA"""

from pydantic import BaseModel

from app.api.schemas.data_schema import InstitutionData, TransactionData


class AIRequest(BaseModel):
    prompt: str


class AIResponse(BaseModel):
    response: str


class ScanResponse(BaseModel):
    transacao: TransactionData
    instituicao: InstitutionData
