"""Módulo de integração com Gemini"""

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.core.exceptions import AIServiceError

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
    try:
        result = ""
        for chunk in client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                result += chunk.text
        return result
    except Exception as exc:
        raise AIServiceError(
            "Não foi possível consultar o serviço de IA.",
            detail=str(exc),
        ) from exc


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
