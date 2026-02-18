#!/usr/bin/env python3
"""
Insere o primeiro usuário na tabela usuario e mostra o ID para usar em USUARIO_ID / .env.
Requer variável DATABASE_URL (ou .env). Ajuste as colunas abaixo se sua tabela for diferente.
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text

# Ajuste estes valores e os nomes das colunas conforme a tabela usuario no seu banco
NOME = os.getenv("USUARIO_NOME", "Usuario Inicial")
EMAIL = os.getenv("USUARIO_EMAIL", "admin@example.com")
SENHA = os.getenv("USUARIO_SENHA", "altere_me_123")  # troque no app ou use hash depois


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Defina DATABASE_URL no ambiente ou no .env", file=sys.stderr)
        sys.exit(1)
    engine = create_engine(url)
    with engine.connect() as conn:
        # Cria a tabela usuario se não existir (SQL Server)
        conn.execute(text("""
            IF OBJECT_ID('usuario', 'U') IS NULL
            CREATE TABLE usuario (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nome NVARCHAR(255),
                email NVARCHAR(255),
                senha NVARCHAR(255)
            )
        """))
        conn.commit()
        # Ajuste as colunas (nome, email, senha) se sua tabela tiver outros nomes
        conn.execute(
            text(
                "INSERT INTO usuario (nome, email, senha) VALUES (:nome, :email, :senha)"
            ),
            {"nome": NOME, "email": EMAIL, "senha": SENHA},
        )
        conn.commit()
        r = conn.execute(text("SELECT SCOPE_IDENTITY() AS id"))
        row = r.fetchone()
        id_ = int(row[0]) if row and row[0] else None
        if id_ is None:
            r2 = conn.execute(
                text("SELECT id FROM usuario WHERE email = :email"),
                {"email": EMAIL},
            )
            row2 = r2.fetchone()
            id_ = row2[0] if row2 else None
    if id_ is not None:
        print(f"Usuário criado com id = {id_}")
        print(f"Defina no .env: USUARIO_ID={id_}")
    else:
        print("Usuário inserido; não foi possível obter o id. Verifique a tabela usuario.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)