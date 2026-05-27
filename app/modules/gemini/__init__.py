"""Módulo de integração com Gemini"""

import logging

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.core.exceptions import AIServiceError
from app.modules.gemini.model_fallback import is_quota_error, models_to_try

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
)

_JSON_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    response_mime_type="application/json",
)


def _stream_to_text(
    client: genai.Client,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
) -> str:
    """Executa generate_content_stream e concatena o texto da resposta."""
    models = list(models_to_try())
    last_exc: Exception | None = None

    for index, model in enumerate(models):
        try:
            result = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    result += chunk.text
            if index > 0:
                logger.info("Gemini respondeu com modelo alternativo: %s", model)
            return result
        except Exception as exc:
            last_exc = exc
            has_next = index < len(models) - 1
            if is_quota_error(exc) and has_next:
                next_model = models[index + 1]
                logger.warning(
                    "Cota/limite no modelo %s (%s). Tentando %s.",
                    model,
                    exc,
                    next_model,
                )
                continue
            raise AIServiceError(
                "Não foi possível consultar o serviço de IA.",
                detail=str(exc),
            ) from exc

    raise AIServiceError(
        "Não foi possível consultar o serviço de IA.",
        detail=str(last_exc),
    ) from last_exc


def generate(prompt: str) -> str:
    """Envia um prompt ao Gemini e retorna a resposta completa."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]
    return _stream_to_text(client, contents, _DEFAULT_CONFIG)


def generate_with_image(prompt: str, image_bytes: bytes, mime_type: str) -> str:
    """Envia um prompt com imagem ao Gemini e retorna a resposta completa."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    return _stream_to_text(client, contents, _JSON_CONFIG)


def generate_with_audio(prompt: str, audio_bytes: bytes, mime_type: str) -> str:
    """Envia um prompt com áudio ao Gemini e retorna a resposta completa."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    return _stream_to_text(client, contents, _JSON_CONFIG)


if __name__ == "__main__":
    print(generate("Olá, mundo!"))
