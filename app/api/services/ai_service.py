"""Services de IA"""

from pathlib import Path

from fastapi import UploadFile

from app.modules.gemini import generate, generate_with_image
from app.modules.etl.transform import parse_ai_response
from app.utils.match import match_scan_response
from app.api.schemas.ai_schema import ScanResponse
from app.api.schemas.data_schema import InstitutionData, TransactionData

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "modules" / "gemini" / "prompts"


def generate_hello_world() -> str:
    """Lê o prompt ola_mundo.md e envia ao Gemini."""
    prompt_path = PROMPTS_DIR / "ola_mundo.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    return generate(prompt)


def generate_custom(prompt: str) -> str:
    """Envia um prompt customizado ao Gemini."""
    return generate(prompt)


def scan_image(file: UploadFile, usuario_id: int | None = None) -> ScanResponse:
    """Envia imagem ao Gemini para extrair dados de transação e instituição."""
    image_bytes = file.file.read()
    mime_type = file.content_type or "image/jpeg"

    prompt = (PROMPTS_DIR / "scan_image.md").read_text(encoding="utf-8")

    ai_response = generate_with_image(prompt, image_bytes, mime_type)
    structured = parse_ai_response(ai_response)

    if usuario_id is not None:
        structured = match_scan_response(structured, usuario_id)

    return ScanResponse(
        transacao=TransactionData(**structured.get("transacao", {})),
        instituicao=InstitutionData(**structured.get("instituicao", {})),
    )
