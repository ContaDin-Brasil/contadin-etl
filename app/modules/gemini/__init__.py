"""Módulo de integração com Gemini — funções de alto nível.

Mantém as mesmas assinaturas públicas para não quebrar os serviços existentes.
Toda a resiliência (fallback de keys/modelos, retry, thinking_config adaptation)
é delegada ao GeminiResilientClient em app.modules.gemini.client.
"""

from google.genai import types

from app.modules.gemini.client import GeminiResilientClient, RetryConfig, get_client

__all__ = [
    "generate",
    "generate_with_image",
    "generate_with_audio",
    "get_client",
    "GeminiResilientClient",
    "RetryConfig",
]

_DEFAULT_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
)

_JSON_CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    response_mime_type="application/json",
)


def generate(prompt: str) -> str:
    """Envia um prompt de texto ao Gemini e retorna a resposta completa."""
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]
    return get_client().call(contents, _DEFAULT_CONFIG)


def generate_with_image(prompt: str, image_bytes: bytes, mime_type: str) -> str:
    """Envia um prompt com imagem ao Gemini e retorna a resposta completa."""
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        )
    ]
    return get_client().call(contents, _JSON_CONFIG)


def generate_with_audio(prompt: str, audio_bytes: bytes, mime_type: str) -> str:
    """Envia um prompt com áudio ao Gemini e retorna a resposta completa."""
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        )
    ]
    return get_client().call(contents, _JSON_CONFIG)


if __name__ == "__main__":
    print(generate("Olá, mundo!"))
