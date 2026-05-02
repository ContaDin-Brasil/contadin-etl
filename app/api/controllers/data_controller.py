"""Controllers de Data (ETL)"""

from fastapi import UploadFile

from app.api.schemas.data_schema import DataProcessResponse
from app.api.services.data_service import process_spreadsheet


def handle_process_spreadsheet(
    file: UploadFile, usuario_id: int | None = None
) -> DataProcessResponse:
    """Handler do POST - recebe planilha, estrutura com IA e retorna dados limpos."""
    return process_spreadsheet(file, usuario_id)
