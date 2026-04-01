"""Routers do domínio generate"""

from fastapi import APIRouter

from app.api.domain.generate.schemas import GenerateRequest, GenerateResponse
from app.api.domain.generate.controllers import handle_ola_mundo, handle_custom_prompt

router = APIRouter(prefix="/generate", tags=["generate"])


@router.get("/ola-mundo", response_model=GenerateResponse)
def get_ola_mundo():
    """Envia o prompt pré-definido (ola_mundo.md) ao Gemini."""
    return handle_ola_mundo()


@router.post("/", response_model=GenerateResponse)
def post_generate(request: GenerateRequest):
    """Envia um prompt customizado ao Gemini."""
    return handle_custom_prompt(request)
