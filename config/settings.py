"""
Configuração do ETL: conexão com SQL Server e ID do usuário padrão.
"""
import os

# Connection string: use DATABASE_URL ou monte com SERVER, DATABASE, USER, PASSWORD
# Exemplo: mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mssql+pyodbc://user:password@localhost/ContaDin?driver=ODBC+Driver+18+for+SQL+Server",
)

# ID do usuário para fk_usuario (planilha não tem usuário)
USUARIO_ID_PADRAO = int(os.getenv("USUARIO_ID", "1"))
