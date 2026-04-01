"""Services do domínio generate"""

from pathlib import Path

from app.modules.gemini import generate


PROMPTS_DIR = Path(__file__).resolve().parents[4] / "modules" / "gemini" / "prompts"


def generate_ola_mundo() -> str:
    """Lê o prompt ola_mundo.md e envia ao Gemini."""
    prompt_path = PROMPTS_DIR / "ola_mundo.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    return generate(prompt)


def generate_custom(prompt: str) -> str:
    """Envia um prompt customizado ao Gemini."""
    return generate(prompt)
