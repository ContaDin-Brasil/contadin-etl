"""Parseia e valida a resposta da IA em dados estruturados."""

import json
import re

from app.core.exceptions import AIResponseError


def parse_ai_response(raw_response: str) -> dict:
    """Extrai o JSON da resposta da IA, removendo wrappers de markdown se houver."""
    if not raw_response or not raw_response.strip():
        raise AIResponseError(
            "A IA retornou uma resposta vazia.",
            detail=None,
        )

    text = raw_response.strip()

    md_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if md_match:
        text = md_match.group(1).strip()

    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIResponseError(
            "A resposta da IA não é um JSON válido.",
            detail=str(exc),
        ) from exc
