"""Configuração das variáveis de ambiente"""

import os

from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Gemini — suporta múltiplos valores separados por vírgula
# Ex: GEMINI_API_KEY="key1,key2,key3"
# Ex: GEMINI_MODEL="gemini-2.5-pro,gemini-2.5-flash,gemini-1.5-flash"
_raw_keys = os.getenv("GEMINI_API_KEY", "")
_raw_models = os.getenv("GEMINI_MODEL", "")

GEMINI_API_KEYS: list[str] = [k.strip() for k in _raw_keys.split(",") if k.strip()]
GEMINI_MODELS: list[str] = [m.strip() for m in _raw_models.split(",") if m.strip()]

# Retrocompatibilidade — acesso direto à primeira key/modelo
GEMINI_API_KEY: str | None = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else None
GEMINI_MODEL: str | None = GEMINI_MODELS[0] if GEMINI_MODELS else None

# User
USUARIO_ID_PADRAO = int(os.getenv("USUARIO_ID", "1"))
