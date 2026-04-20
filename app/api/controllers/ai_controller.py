"""Controllers de IA"""

from fastapi import UploadFile

from app.api.schemas.ai_schema import AIRequest, AIResponse, ScanResponse
from app.api.services.ai_service import (
    generate_hello_world,
    generate_custom,
    scan_image,
)


def handle_hello_world() -> AIResponse:
    """Handler do GET - envia o prompt ola_mundo.md ao Gemini."""
    result = generate_hello_world()
    return AIResponse(response=result)


def handle_custom_prompt(request: AIRequest) -> AIResponse:
    """Handler do POST - envia um prompt customizado ao Gemini."""
    result = generate_custom(request.prompt)
    return AIResponse(response=result)


def handle_scan_image(file: UploadFile, usuario_id: int | None = None) -> ScanResponse:
    """Handler do POST - extrai dados financeiros de uma imagem."""
    return scan_image(file, usuario_id)
