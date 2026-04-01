"""
Carga no SQL Server via SQLAlchemy. Insere instituições, categorias e transações.
"""
import pandas as pd
from sqlalchemy import create_engine, text


def carregar_instituicoes(engine, df: pd.DataFrame, usuario_id: int) -> dict[str, int]:
    """Insere instituições e retorna mapa nome -> id."""
    if df.empty:
        return {}
    df[["nome", "tipo", "fk_usuario"]].to_sql(
        "instituicao",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )
    with engine.connect() as conn:
        r = conn.execute(
            text("SELECT [Id], [Nome] FROM instituicao WHERE fk_usuario = :uid"),
            {"uid": usuario_id},
        )
        rows = r.fetchall()
    return {row[1]: row[0] for row in rows}


def carregar_categorias(engine, df: pd.DataFrame, usuario_id: int) -> dict[str, int]:
    """Insere categorias e retorna mapa nome -> id."""
    if df.empty:
        return {}
    df[["nome", "tipo", "fk_usuario"]].to_sql(
        "categoria",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )
    with engine.connect() as conn:
        r = conn.execute(
            text("SELECT [Id], [Nome] FROM categoria WHERE fk_usuario = :uid"),
            {"uid": usuario_id},
        )
        rows = r.fetchall()
    return {row[1]: row[0] for row in rows}


def carregar_transacoes(engine, df: pd.DataFrame) -> None:
    """Insere transações."""
    if df.empty:
        return
    cols = [
        "valor", "tipo", "descricao", "data_transacao", "parcelado",
        "recorrencia", "fim_transacao", "fk_instituicao", "fk_categoria", "fk_usuario",
    ]
    df[cols].to_sql(
        "transacao",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )
