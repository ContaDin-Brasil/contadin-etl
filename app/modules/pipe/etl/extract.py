"""
Extrai dados da planilha Excel em DataFrames.
"""
import pandas as pd


def extrair(arquivo_xlsx: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Lê as abas Instituicoes, Categorias e Transacoes do Excel.
    Retorna (df_instituicoes, df_categorias, df_transacoes).
    """
    sheets = pd.read_excel(
        arquivo_xlsx,
        sheet_name=["Instituicoes", "Categorias", "Transacoes"],
    )
    return (
        sheets["Instituicoes"],
        sheets["Categorias"],
        sheets["Transacoes"],
    )
