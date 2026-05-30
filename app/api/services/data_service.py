"""Services de Data (ETL)"""

from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import AIServiceError, ExtractionError, MatchError
from app.modules.gemini import generate
from app.modules.etl.extract import extract_spreadsheet
from app.modules.etl.transform import parse_ai_response
from app.utils.match import match_data_response
from app.api.schemas.data_schema import (
    DataProcessResponse,
    InstitutionData,
    CategoryData,
    TransactionData,
    ObjetivoData,
)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "modules" / "gemini" / "prompts"


def _parse_spreadsheet_response(ai_response: str) -> dict:
    """Parseia a resposta da planilha e rejeita conteúdo não financeiro."""
    structured = parse_ai_response(ai_response)
    if structured.get("erro"):
        raise ExtractionError(
            structured.get("mensagem")
            or "Não foi possível estruturar dados financeiros da planilha enviada.",
            detail=structured.get("erro"),
        )
    return structured


def process_spreadsheet(
    file: UploadFile, usuario_id: int | None = None
) -> DataProcessResponse:
    """Pipeline completo: extract -> AI structuring -> transform -> match -> response."""

    try:
        raw_data = extract_spreadsheet(file)
    except Exception as exc:
        raise ExtractionError(
            "Não foi possível ler o arquivo enviado. Verifique se é um .xlsx, .xls ou .csv válido.",
            detail=str(exc),
        ) from exc

    try:
        prompt_template = (PROMPTS_DIR / "parse_spreadsheet.md").read_text(
            encoding="utf-8"
        )
        prompt = f"{prompt_template}\n\n{raw_data}"
        ai_response = generate(prompt)
    except Exception as exc:
        raise AIServiceError(
            "Falha ao se comunicar com o serviço de IA. Tente novamente em instantes.",
            detail=str(exc),
        ) from exc

    # AIResponseError é levado direto — já tem mensagem clara
    structured = _parse_spreadsheet_response(ai_response)

    if usuario_id is not None:
        try:
            structured = match_data_response(structured, usuario_id)
        except Exception as exc:
            raise MatchError(
                "Erro ao buscar entidades existentes no banco de dados.",
                detail=str(exc),
            ) from exc

    objetivos_raw = structured.get("objetivos") or structured.get("metas_gasto", [])
    objetivos_normalizados = []
    for item in objetivos_raw:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        if row.get("data_fim") is None and row.get("data_fim_meta") is not None:
            row["data_fim"] = row.pop("data_fim_meta")
        objetivos_normalizados.append(row)

    return DataProcessResponse(
        instituicoes=[InstitutionData(**i) for i in structured.get("instituicoes", [])],
        categorias=[CategoryData(**c) for c in structured.get("categorias", [])],
        transacoes=[TransactionData(**t) for t in structured.get("transacoes", [])],
        objetivos=[ObjetivoData(**o) for o in objetivos_normalizados],
    )
