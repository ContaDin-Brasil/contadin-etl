"""Conexão com o banco de dados via SQLAlchemy"""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import DATABASE_URL


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Retorna o engine do SQLAlchemy, criando na primeira chamada."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não configurada no .env")
    return create_engine(DATABASE_URL)
