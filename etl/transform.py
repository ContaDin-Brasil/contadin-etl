"""
Normaliza e mapeia colunas da planilha para o schema do banco.
"""
import pandas as pd


RECORRENCIA_MAP = {
    "": None,
    "Diário": "DIARIO",
    "Semanal": "SEMANAL",
    "Mensal": "MENSAL",
    "Anual": "ANUAL",
}


def _limpar_string(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().replace("nan", "")


def transformar_instituicoes(df: pd.DataFrame, usuario_id: int) -> pd.DataFrame:
    """Retorna DataFrame com colunas: nome, tipo, fk_usuario."""
    df = df.dropna(how="all")
    if df.empty:
        return pd.DataFrame(columns=["nome", "tipo", "fk_usuario"])
    out = pd.DataFrame()
    out["nome"] = _limpar_string(df["Nome"])
    out["tipo"] = _limpar_string(df["Tipo"])
    out["fk_usuario"] = usuario_id
    out = out[out["nome"] != ""].drop_duplicates(subset=["nome"], keep="first")
    return out.reset_index(drop=True)


def transformar_categorias(df: pd.DataFrame, usuario_id: int) -> pd.DataFrame:
    """Retorna DataFrame com colunas: nome, tipo, fk_usuario."""
    df = df.dropna(how="all")
    if df.empty:
        return pd.DataFrame(columns=["nome", "tipo", "fk_usuario"])
    out = pd.DataFrame()
    out["nome"] = _limpar_string(df["Nome"])
    out["tipo"] = _limpar_string(df["Tipo"])
    out["fk_usuario"] = usuario_id
    out = out[out["nome"] != ""].drop_duplicates(subset=["nome"], keep="first")
    return out.reset_index(drop=True)


def transformar_transacoes(
    df: pd.DataFrame,
    map_instituicao: dict[str, int],
    map_categoria: dict[str, int],
    usuario_id: int,
) -> pd.DataFrame:
    """
    Retorna DataFrame com colunas do banco: valor, tipo, descricao, data_transacao,
    parcelado, recorrencia, fim_transacao, fk_instituicao, fk_categoria, fk_usuario.
    """
    df = df.dropna(how="all")
    if df.empty:
        return pd.DataFrame(
            columns=[
                "valor", "tipo", "descricao", "data_transacao", "parcelado",
                "recorrencia", "fim_transacao", "fk_instituicao", "fk_categoria", "fk_usuario",
            ]
        )
    out = pd.DataFrame()
    out["data_transacao"] = pd.to_datetime(df["Data"], errors="coerce")
    out["tipo"] = _limpar_string(df["Tipo"]).str.upper()
    out["valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    out["descricao"] = _limpar_string(df["Descricao"])
    out["parcelado"] = _limpar_string(df["Parcelado"]).str.upper().eq("SIM")
    rec = _limpar_string(df["Recorrencia"])
    out["recorrencia"] = rec.map(lambda x: RECORRENCIA_MAP.get(x, x) if x else None)
    out["fim_transacao"] = pd.to_datetime(df["Fim da recorrencia"], errors="coerce").dt.date
    out["fim_transacao"] = out["fim_transacao"].replace({pd.NaT: None})
    nome_inst = _limpar_string(df["Instituicao"])
    nome_cat = _limpar_string(df["Categoria"])
    out["fk_instituicao"] = nome_inst.map(map_instituicao)
    out["fk_categoria"] = nome_cat.map(map_categoria)
    out["fk_usuario"] = usuario_id
    # Remove linhas sem data, valor ou FK essenciais
    out = out.dropna(subset=["data_transacao", "valor", "fk_instituicao"])
    return out.reset_index(drop=True)
