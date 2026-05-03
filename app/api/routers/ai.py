"""Routers de IA"""

from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile

from app.api.schemas.ai_schema import AIRequest, AIResponse, ScanResponse
from app.api.controllers.ai_controller import (
    handle_hello_world,
    handle_custom_prompt,
    handle_scan_image,
    handle_scan_audio,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/hello-world", response_model=AIResponse)
def get_hello_world():
    """Envia o prompt pré-definido (ola_mundo.md) ao Gemini."""
    return handle_hello_world()


@router.post("/query", response_model=AIResponse)
def post_query(request: AIRequest):
    """Envia um prompt customizado ao Gemini."""
    return handle_custom_prompt(request)


@router.post("/scan", response_model=ScanResponse)
def post_scan(
    file: UploadFile = File(...),
    usuario_id: UUID | None = Query(
        None, description="ID do usuário para matching de entidades existentes"
    ),
):
    """Recebe imagem de documento financeiro e extrai dados de transação e instituição."""
    return handle_scan_image(file, usuario_id)


@router.post("/audio", response_model=ScanResponse)
def post_audio(
    file: UploadFile = File(...),
    usuario_id: UUID | None = Query(
        None, description="ID do usuário para matching de entidades existentes"
    ),
):
    """Recebe áudio com descrição de transação e extrai dados de transação e instituição."""
    return handle_scan_audio(file, usuario_id)
