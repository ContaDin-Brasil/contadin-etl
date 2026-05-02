"""Configuração das variáveis de ambiente"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# User
USUARIO_ID_PADRAO = int(os.getenv("USUARIO_ID", "1"))
