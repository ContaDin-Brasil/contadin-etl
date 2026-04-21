"""
Script de seed para popular o banco PostgreSQL com dados de teste.

Popula as tabelas:
  - usuario
  - token_recuperar_senha
  - instituicao  (10 bancos conhecidos + 5 vales: Flash, Alelo, Sodexo, Ticket, VR)
  - categoria
  - transacao    (120 registros)
  - meta_gasto
"""

import os
import random
import sys
import uuid
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ── Configuração ─────────────────────────────────────────────────────────────────

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Dados de seed ─────────────────────────────────────────────────────────────────

USUARIO = {
    "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
    "nome": "João",
    "sobrenome": "Silva",
    "email": "joao.silva@email.com",
    "senha": "$2b$12$examplehashedpassword123456",
    "tel": "11999990001",
    "ativo": True,
}

INSTITUICOES = [
    # 10 bancos conhecidos
    {"nome": "Nubank", "tipo": "banco", "icone": "nubank.svg", "cor": "#820AD1"},
    {"nome": "Itaú", "tipo": "banco", "icone": "itau.svg", "cor": "#FF6600"},
    {"nome": "Bradesco", "tipo": "banco", "icone": "bradesco.svg", "cor": "#CC092F"},
    {"nome": "Santander", "tipo": "banco", "icone": "santander.svg", "cor": "#EC0000"},
    {"nome": "Caixa", "tipo": "banco", "icone": "caixa.svg", "cor": "#0070AF"},
    {"nome": "Banco do Brasil", "tipo": "banco", "icone": "bb.svg", "cor": "#FFDD00"},
    {"nome": "BTG Pactual", "tipo": "banco", "icone": "btg.svg", "cor": "#1F3C88"},
    {"nome": "Inter", "tipo": "banco", "icone": "inter.svg", "cor": "#FF6B00"},
    {"nome": "C6 Bank", "tipo": "banco", "icone": "c6.svg", "cor": "#242424"},
    {"nome": "XP", "tipo": "banco", "icone": "xp.svg", "cor": "#000000"},
    # 5 vales / benefícios
    {"nome": "Flash", "tipo": "vale", "icone": "flash.svg", "cor": "#FF4F00"},
    {"nome": "Alelo", "tipo": "vale", "icone": "alelo.svg", "cor": "#ED1C24"},
    {"nome": "Sodexo", "tipo": "vale", "icone": "sodexo.svg", "cor": "#E00034"},
    {"nome": "Ticket", "tipo": "vale", "icone": "ticket.svg", "cor": "#F7941D"},
    {"nome": "VR", "tipo": "vale", "icone": "vr.svg", "cor": "#FF0000"},
]

CATEGORIAS = [
    # GASTO  (índices 0-9)
    {"nome": "Alimentação", "icone": "food.svg", "cor": "#FF6B6B", "tipo": "GASTO"},
    {"nome": "Transporte", "icone": "car.svg", "cor": "#4ECDC4", "tipo": "GASTO"},
    {"nome": "Moradia", "icone": "home.svg", "cor": "#45B7D1", "tipo": "GASTO"},
    {"nome": "Saúde", "icone": "health.svg", "cor": "#96CEB4", "tipo": "GASTO"},
    {"nome": "Educação", "icone": "book.svg", "cor": "#FFEAA7", "tipo": "GASTO"},
    {"nome": "Lazer", "icone": "game.svg", "cor": "#DDA0DD", "tipo": "GASTO"},
    {"nome": "Vestuário", "icone": "shirt.svg", "cor": "#F0E68C", "tipo": "GASTO"},
    {"nome": "Tecnologia", "icone": "laptop.svg", "cor": "#87CEEB", "tipo": "GASTO"},
    {"nome": "Streaming", "icone": "play.svg", "cor": "#E50914", "tipo": "GASTO"},
    {"nome": "Supermercado", "icone": "cart.svg", "cor": "#90EE90", "tipo": "GASTO"},
    # RECEITA (índices 10-15)
    {"nome": "Salário", "icone": "money.svg", "cor": "#2ECC71", "tipo": "RECEITA"},
    {"nome": "Freelance", "icone": "code.svg", "cor": "#3498DB", "tipo": "RECEITA"},
    {
        "nome": "Investimentos",
        "icone": "chart.svg",
        "cor": "#F39C12",
        "tipo": "RECEITA",
    },
    {"nome": "Reembolso", "icone": "refresh.svg", "cor": "#1ABC9C", "tipo": "RECEITA"},
    {
        "nome": "Vale Refeição",
        "icone": "food2.svg",
        "cor": "#E67E22",
        "tipo": "RECEITA",
    },
    {
        "nome": "Vale Transporte",
        "icone": "bus.svg",
        "cor": "#9B59B6",
        "tipo": "RECEITA",
    },
]

# (descricao, valor_min, valor_max, tipo, categoria_idx, recorrencia, parcelado)
TRANSACOES_TEMPLATE = [
    ("Almoço no restaurante", 25, 80, "GASTO", 0, None, False),
    ("iFood", 30, 120, "GASTO", 0, None, False),
    ("Padaria", 8, 30, "GASTO", 0, None, False),
    ("Supermercado mensal", 300, 700, "GASTO", 9, "MENSAL", False),
    ("Uber", 15, 60, "GASTO", 1, None, False),
    ("Gasolina", 150, 350, "GASTO", 1, None, False),
    ("Ônibus", 5, 20, "GASTO", 1, None, False),
    ("Aluguel", 1200, 2500, "GASTO", 2, "MENSAL", False),
    ("Condomínio", 250, 600, "GASTO", 2, "MENSAL", False),
    ("Conta de luz", 80, 250, "GASTO", 2, "MENSAL", False),
    ("Conta de água", 40, 120, "GASTO", 2, "MENSAL", False),
    ("Plano de saúde", 200, 500, "GASTO", 3, "MENSAL", False),
    ("Farmácia", 20, 150, "GASTO", 3, None, False),
    ("Consulta médica", 150, 400, "GASTO", 3, None, False),
    ("Curso online", 100, 500, "GASTO", 4, None, True),
    ("Livro", 30, 120, "GASTO", 4, None, False),
    ("Cinema", 30, 80, "GASTO", 5, None, False),
    ("Show/Evento", 80, 300, "GASTO", 5, None, False),
    ("Academia", 80, 200, "GASTO", 5, "MENSAL", False),
    ("Roupas", 80, 400, "GASTO", 6, None, True),
    ("Tênis", 150, 600, "GASTO", 6, None, True),
    ("Celular novo", 800, 3000, "GASTO", 7, None, True),
    ("Notebook", 2500, 7000, "GASTO", 7, None, True),
    ("Acessórios tech", 100, 500, "GASTO", 7, None, False),
    ("Netflix", 45, 55, "GASTO", 8, "MENSAL", False),
    ("Spotify", 20, 25, "GASTO", 8, "MENSAL", False),
    ("Amazon Prime", 19, 25, "GASTO", 8, "MENSAL", False),
    ("Salário", 3500, 8000, "RECEITA", 10, "MENSAL", False),
    ("Freelance desenvolvimento", 500, 3000, "RECEITA", 11, None, False),
    ("Dividendos", 100, 800, "RECEITA", 12, None, False),
    ("Reembolso empresa", 50, 500, "RECEITA", 13, None, False),
    ("Vale refeição Flash", 500, 800, "RECEITA", 14, "MENSAL", False),
    ("Vale refeição Alelo", 500, 800, "RECEITA", 14, "MENSAL", False),
    ("Vale transporte", 200, 400, "RECEITA", 15, "MENSAL", False),
]

META_GASTOS = [
    {"nome": "Controle Alimentação", "valor": 600.0, "cat_idx": 0},
    {"nome": "Limite Transporte", "valor": 400.0, "cat_idx": 1},
    {"nome": "Lazer Mensal", "valor": 300.0, "cat_idx": 5},
    {"nome": "Vestuário Trimestral", "valor": 800.0, "cat_idx": 6},
    {"nome": "Tecnologia Anual", "valor": 3000.0, "cat_idx": 7},
]

TOKENS_RECUPERACAO = [
    {"token": "tok_a1b2c3d4e5f6789012345678901234ab", "utilizado": False, "dias": 1},
    {"token": "tok_b2c3d4e5f678901234567890abcdef12", "utilizado": True, "dias": -5},
]


# ── Helpers ───────────────────────────────────────────────────────────────────────


def rand_date(start_days_ago: int = 365, end_days_ago: int = 0) -> datetime:
    delta = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=delta)


def rand_valor(vmin: float, vmax: float) -> float:
    return round(random.uniform(vmin, vmax), 2)


# ── DDL ───────────────────────────────────────────────────────────────────────────


def create_tables(conn: psycopg2.extensions.connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        DO $$ BEGIN
            CREATE TYPE tipo_transacao    AS ENUM ('GASTO', 'RECEITA');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        DO $$ BEGIN
            CREATE TYPE recorrencia_tipo  AS ENUM ('DIARIO', 'SEMANAL', 'MENSAL', 'ANUAL');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;

        CREATE TABLE IF NOT EXISTS usuario (
            id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome      VARCHAR NOT NULL,
            sobrenome VARCHAR,
            email     VARCHAR NOT NULL,
            senha     VARCHAR NOT NULL,
            tel       VARCHAR,
            ativo     BOOLEAN NOT NULL
        );

        CREATE TABLE IF NOT EXISTS token_recuperar_senha (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token           VARCHAR NOT NULL UNIQUE,
            utilizado       BOOLEAN,
            data_expiracao  TIMESTAMP NOT NULL,
            fk_usuario      UUID NOT NULL REFERENCES usuario(id)
        );

        CREATE TABLE IF NOT EXISTS instituicao (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome       VARCHAR NOT NULL,
            tipo       VARCHAR NOT NULL,
            icone      VARCHAR,
            cor        VARCHAR,
            fk_usuario UUID NOT NULL REFERENCES usuario(id)
        );

        CREATE TABLE IF NOT EXISTS categoria (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome       VARCHAR NOT NULL,
            icone      VARCHAR,
            cor        VARCHAR,
            tipo       tipo_transacao NOT NULL,
            fk_usuario UUID REFERENCES usuario(id)
        );

        CREATE TABLE IF NOT EXISTS transacao (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            valor           DOUBLE PRECISION NOT NULL,
            tipo            tipo_transacao NOT NULL,
            descricao       VARCHAR,
            data_transacao  TIMESTAMP,
            parcelado       BOOLEAN NOT NULL,
            recorrencia     recorrencia_tipo,
            fim_transacao   DATE,
            fk_instituicao  UUID NOT NULL REFERENCES instituicao(id),
            fk_categoria    UUID REFERENCES categoria(id)
        );

        CREATE TABLE IF NOT EXISTS meta_gasto (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome          VARCHAR NOT NULL,
            valor         DOUBLE PRECISION NOT NULL,
            data_fim_meta DATE,
            fk_usuario    UUID NOT NULL REFERENCES usuario(id),
            fk_categoria  UUID NOT NULL REFERENCES categoria(id)
        );
    """
    )
    conn.commit()
    cur.close()
    print("  OK — tabelas criadas/verificadas")


# ── Inserções ─────────────────────────────────────────────────────────────────────


def seed(conn: psycopg2.extensions.connection) -> None:
    cur = conn.cursor()

    print("\n[1/6] Inserindo usuário...")
    cur.execute(
        """
        INSERT INTO usuario (id, nome, sobrenome, email, senha, tel, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """,
        (
            USUARIO["id"],
            USUARIO["nome"],
            USUARIO["sobrenome"],
            USUARIO["email"],
            USUARIO["senha"],
            USUARIO["tel"],
            USUARIO["ativo"],
        ),
    )
    conn.commit()
    usuario_uuid = USUARIO["id"]
    print(f"  OK — usuário id={usuario_uuid}")

    print("\n[2/6] Inserindo tokens de recuperação de senha...")
    for tok in TOKENS_RECUPERACAO:
        expiracao = datetime.now() + timedelta(days=tok["dias"])
        cur.execute(
            """
            INSERT INTO token_recuperar_senha (token, utilizado, data_expiracao, fk_usuario)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (token) DO NOTHING
        """,
            (tok["token"], tok["utilizado"], expiracao, usuario_uuid),
        )
    conn.commit()
    print(f"  OK — {len(TOKENS_RECUPERACAO)} tokens inseridos")

    print("\n[3/6] Inserindo instituições...")
    inst_ids = []
    for inst in INSTITUICOES:
        cur.execute(
            """
            INSERT INTO instituicao (nome, tipo, icone, cor, fk_usuario)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """,
            (inst["nome"], inst["tipo"], inst["icone"], inst["cor"], usuario_uuid),
        )
        inst_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"  OK — {len(inst_ids)} instituições (10 bancos + 5 vales)")

    print("\n[4/6] Inserindo categorias...")
    cat_ids = []
    for cat in CATEGORIAS:
        cur.execute(
            """
            INSERT INTO categoria (nome, icone, cor, tipo, fk_usuario)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """,
            (cat["nome"], cat["icone"], cat["cor"], cat["tipo"], usuario_uuid),
        )
        cat_ids.append(cur.fetchone()[0])
    conn.commit()
    print(f"  OK — {len(cat_ids)} categorias")

    banco_ids = inst_ids[:10]
    vale_ids = inst_ids[10:]

    print("\n[5/6] Inserindo transações (120 registros)...")
    transacoes = []

    while len(transacoes) < 120:
        descricao, vmin, vmax, tipo, cat_idx, recorrencia, parcelado = random.choice(
            TRANSACOES_TEMPLATE
        )
        valor = rand_valor(vmin, vmax)
        data_tx = rand_date(365, 0)
        cat_id = cat_ids[cat_idx]

        if tipo == "RECEITA" and cat_idx in (14, 15):
            inst_id = random.choice(vale_ids)
        elif tipo == "GASTO" and cat_idx == 0:
            inst_id = random.choice(vale_ids + banco_ids)
        else:
            inst_id = random.choice(banco_ids)

        fim_tx = None
        if recorrencia or parcelado:
            fim_tx = (data_tx + timedelta(days=random.randint(30, 365))).date()

        transacoes.append(
            (
                valor,
                tipo,
                descricao,
                data_tx,
                parcelado,
                recorrencia,
                fim_tx,
                inst_id,
                cat_id,
            )
        )

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO transacao
            (valor, tipo, descricao, data_transacao, parcelado, recorrencia,
             fim_transacao, fk_instituicao, fk_categoria)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
        transacoes,
    )
    conn.commit()
    print(f"  OK — {len(transacoes)} transações inseridas")

    print("\n[6/6] Inserindo metas de gasto...")
    for meta in META_GASTOS:
        fim_meta = (datetime.now() + timedelta(days=random.randint(30, 90))).date()
        cur.execute(
            """
            INSERT INTO meta_gasto (nome, valor, data_fim_meta, fk_usuario, fk_categoria)
            VALUES (%s, %s, %s, %s, %s)
        """,
            (meta["nome"], meta["valor"], fim_meta, usuario_uuid, cat_ids[meta["cat_idx"]]),
        )
    conn.commit()
    print(f"  OK — {len(META_GASTOS)} metas de gasto")

    cur.close()


# ── Entry point ───────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("  SEED — Banco de dados Contadin (PostgreSQL)")
    print("=" * 60)

    if not DATABASE_URL:
        print("ERRO: DATABASE_URL não encontrada no .env")
        sys.exit(1)

    print(f"\nConectando em: {DATABASE_URL.split('@')[-1]} ...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except psycopg2.OperationalError as e:
        print(f"ERRO ao conectar: {e}")
        sys.exit(1)

    print("Conexão estabelecida!\n")

    try:
        print("[0/6] Criando tabelas (se não existirem)...")
        create_tables(conn)
        seed(conn)
    except psycopg2.Error as e:
        print(f"\nERRO durante o seed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("  Seed concluído com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
