"""Controllers do domínio generate"""

from app.api.domain.generate.schemas import GenerateRequest, GenerateResponse
from app.api.domain.generate.services import generate_ola_mundo, generate_custom


def handle_ola_mundo() -> GenerateResponse:
    """Handler do GET - envia o prompt ola_mundo.md ao Gemini."""
    result = generate_ola_mundo()
    return GenerateResponse(response=result)


def handle_custom_prompt(request: GenerateRequest) -> GenerateResponse:
    """Handler do POST - envia um prompt customizado ao Gemini."""
    result = generate_custom(request.prompt)
    return GenerateResponse(response=result)
