"""Routers de Data (ETL)"""

from fastapi import APIRouter, File, Query, UploadFile

from app.api.schemas.data_schema import DataProcessResponse
from app.api.controllers.data_controller import handle_process_spreadsheet

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/process", response_model=DataProcessResponse)
def post_process(
    file: UploadFile = File(...),
    usuario_id: int | None = Query(
        None, description="ID do usuário para matching de entidades existentes"
    ),
):
    """Recebe uma planilha financeira, estrutura com IA e retorna dados limpos."""
    return handle_process_spreadsheet(file, usuario_id)
