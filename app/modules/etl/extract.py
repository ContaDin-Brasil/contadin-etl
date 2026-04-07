"""Extrai dados brutos de planilhas enviadas via upload."""

import io

import pandas as pd
from fastapi import UploadFile


def extract_spreadsheet(file: UploadFile) -> str:
    """Lê uma planilha (xlsx/xls/csv) e retorna seu conteúdo como texto CSV."""
    contents = file.file.read()
    filename = file.filename or ""

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
        return df.to_csv(index=False)

    sheets = pd.read_excel(io.BytesIO(contents), sheet_name=None)
    parts = []
    for sheet_name, df in sheets.items():
        parts.append(f"=== Aba: {sheet_name} ===")
        parts.append(df.to_csv(index=False))

    return "\n\n".join(parts)
