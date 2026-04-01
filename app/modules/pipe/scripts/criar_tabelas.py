#!/usr/bin/env python3
"""
Cria as tabelas do CoitaDin no SQL Server: usuario, instituicao, categoria, transacao.
Requer DATABASE_URL no ambiente ou no .env.
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import create_engine, text


def criar_tabelas(engine) -> None:
    with engine.connect() as conn:
        # 1. usuario (precisa existir antes das FKs)
        conn.execute(text("""
            IF OBJECT_ID('usuario', 'U') IS NULL
            CREATE TABLE usuario (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nome NVARCHAR(255) NOT NULL,
                sobrenome NVARCHAR(255) NOT NULL,
                email NVARCHAR(255),
                senha NVARCHAR(255) NOT NULL,
                tel NVARCHAR(50),
                ativo BIT NOT NULL DEFAULT 1
            )
        """))
        conn.commit()

        # 2. instituicao
        conn.execute(text("""
            IF OBJECT_ID('instituicao', 'U') IS NULL
            CREATE TABLE instituicao (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nome NVARCHAR(255) NOT NULL,
                tipo NVARCHAR(100) NOT NULL,
                icone NVARCHAR(255),
                cor NVARCHAR(50),
                fk_usuario INT NOT NULL,
                CONSTRAINT FK_instituicao_usuario FOREIGN KEY (fk_usuario) REFERENCES usuario(id)
            )
        """))
        conn.commit()

        # 3. categoria
        conn.execute(text("""
            IF OBJECT_ID('categoria', 'U') IS NULL
            CREATE TABLE categoria (
                id INT IDENTITY(1,1) PRIMARY KEY,
                nome NVARCHAR(255) NOT NULL,
                tipo NVARCHAR(20) NOT NULL CHECK (tipo IN ('GASTO', 'RECEITA', 'GLOBAL')),
                fk_usuario INT NOT NULL,
                CONSTRAINT FK_categoria_usuario FOREIGN KEY (fk_usuario) REFERENCES usuario(id)
            )
        """))
        conn.commit()

        # 4. transacao
        conn.execute(text("""
            IF OBJECT_ID('transacao', 'U') IS NULL
            CREATE TABLE transacao (
                id INT IDENTITY(1,1) PRIMARY KEY,
                valor FLOAT NOT NULL,
                tipo NVARCHAR(20) NOT NULL CHECK (tipo IN ('GASTO', 'RECEITA')),
                descricao NVARCHAR(500),
                data_transacao DATETIME,
                parcelado BIT NOT NULL,
                recorrencia NVARCHAR(20) CHECK (recorrencia IN ('DIARIO', 'SEMANAL', 'MENSAL', 'ANUAL')),
                fim_transacao DATE,
                fk_instituicao INT NOT NULL,
                fk_categoria INT,
                fk_usuario INT NOT NULL,
                CONSTRAINT FK_transacao_instituicao FOREIGN KEY (fk_instituicao) REFERENCES instituicao(id),
                CONSTRAINT FK_transacao_categoria FOREIGN KEY (fk_categoria) REFERENCES categoria(id),
                CONSTRAINT FK_transacao_usuario FOREIGN KEY (fk_usuario) REFERENCES usuario(id)
            )
        """))
        conn.commit()

    print("Tabelas criadas ou já existentes: usuario, instituicao, categoria, transacao.")


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("Defina DATABASE_URL no ambiente ou no .env", file=sys.stderr)
        sys.exit(1)
    engine = create_engine(url)
    try:
        criar_tabelas(engine)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
