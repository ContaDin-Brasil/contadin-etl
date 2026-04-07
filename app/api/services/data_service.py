"""Services de Data (ETL)"""

from pathlib import Path

from fastapi import UploadFile

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
    raw_data = extract_spreadsheet(file)

    prompt_template = (PROMPTS_DIR / "parse_spreadsheet.md").read_text(encoding="utf-8")
    prompt = f"{prompt_template}\n\n{raw_data}"

    ai_response = generate(prompt)
    structured = parse_ai_response(ai_response)

    if usuario_id is not None:
        structured = match_data_response(structured, usuario_id)

    return DataProcessResponse(
        instituicoes=[
            InstitutionData(**i) for i in structured.get("instituicoes", [])
        ],
        categorias=[
            CategoryData(**c) for c in structured.get("categorias", [])
        ],
        transacoes=[
            TransactionData(**t) for t in structured.get("transacoes", [])
        ],
        metas_gasto=[
            SpendingGoalData(**s) for s in structured.get("metas_gasto", [])
        ],
    )
