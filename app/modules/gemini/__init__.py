"""Módulo de integração com Gemini"""

from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_MODEL


def generate(prompt: str) -> str:
    """Envia um prompt ao Gemini e retorna a resposta completa."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            result += chunk.text

    return result


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
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            result += chunk.text

    return result


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
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
    )

    result = ""
    for chunk in client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            result += chunk.text

    return result


if __name__ == "__main__":
    print(generate("Olá, mundo!"))
