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
    SpendingGoalData,
)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "modules" / "gemini" / "prompts"


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
        prompt_template = (PROMPTS_DIR / "parse_spreadsheet.md").read_text(encoding="utf-8")
        prompt = f"{prompt_template}\n\n{raw_data}"
        ai_response = generate(prompt)
    except Exception as exc:
        raise AIServiceError(
            "Falha ao se comunicar com o serviço de IA. Tente novamente em instantes.",
            detail=str(exc),
        ) from exc

    # AIResponseError é levado direto — já tem mensagem clara
    structured = parse_ai_response(ai_response)

    if usuario_id is not None:
        try:
            structured = match_data_response(structured, usuario_id)
        except Exception as exc:
            raise MatchError(
                "Erro ao buscar entidades existentes no banco de dados.",
                detail=str(exc),
            ) from exc

    return DataProcessResponse(
        instituicoes=[InstitutionData(**i) for i in structured.get("instituicoes", [])],
        categorias=[CategoryData(**c) for c in structured.get("categorias", [])],
        transacoes=[TransactionData(**t) for t in structured.get("transacoes", [])],
        metas_gasto=[SpendingGoalData(**s) for s in structured.get("metas_gasto", [])],
    )
