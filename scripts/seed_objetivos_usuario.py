"""
Insere ~15 objetivos de teste (cenários variados) para um usuário fixo.

Requisitos:
  - DATABASE_URL no .env (mesmo padrão do seed_database.py)
  - O `fk_usuario` deve existir em `usuario`
  - Categorias `GASTO` e `RECEITA` para esse usuário (ou globais); o script cria
    categorias mínimas no usuário se faltar algum tipo

Uso:
  python scripts/seed_objetivos_usuario.py
  python scripts/seed_objetivos_usuario.py --limpar   # remove objetivos deste usuário antes
  SEED_FK_USUARIO=... python scripts/seed_objetivos_usuario.py

DDL da tabela `objetivo` é idempotente (IF NOT EXISTS). Se o Flyway/Java já criou
a tabela com tipos diferentes, use --sem-ddl e ajuste o script às suas colunas.
"""

from __future__ import annotations

import argparse
import calendar
import os
import sys
import uuid
from datetime import date, timedelta
from typing import Any

import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Usuário padrão solicitado (sobrescreve com SEED_FK_USUARIO ou --usuario)
DEFAULT_FK_USUARIO = uuid.UUID("df5f4d59-d321-470a-bd0d-c370b355af12")


def _today() -> date:
    return date.today()


def ensure_objetivo_table(conn: Any, *, skip_ddl: bool) -> None:
    if skip_ddl:
        return
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS objetivo (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome            VARCHAR(255) NOT NULL,
            descricao       TEXT,
            valor           NUMERIC(19, 2) NOT NULL,
            tipo_objetivo   VARCHAR(32) NOT NULL
                CHECK (tipo_objetivo IN ('LIMITE_GASTO', 'AUMENTO_RECEITA')),
            prioridade      VARCHAR(32),
            data_inicio     DATE NOT NULL,
            data_fim        DATE NOT NULL,
            fk_usuario      UUID NOT NULL REFERENCES usuario(id),
            fk_categoria    UUID NOT NULL REFERENCES categoria(id),
            criado_em       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            atualizado_em   TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_objetivo_fk_usuario ON objetivo (fk_usuario);
        """
    )
    conn.commit()
    cur.close()


def fetch_categorias_por_tipo(
    cur: Any, fk_usuario: uuid.UUID
) -> dict[str, list[uuid.UUID]]:
    cur.execute(
        """
        SELECT id, tipo::text
        FROM categoria
        WHERE fk_usuario = %s OR fk_usuario IS NULL
        ORDER BY CASE WHEN fk_usuario = %s THEN 0 ELSE 1 END, nome
        """,
        (str(fk_usuario), str(fk_usuario)),
    )
    out: dict[str, list[uuid.UUID]] = {"GASTO": [], "RECEITA": []}
    for row in cur.fetchall():
        cid, tipo = row[0], row[1]
        if tipo in out:
            out[tipo].append(cid)
    return out


def ensure_categorias_minimas(
    conn: Any, cur: Any, fk_usuario: uuid.UUID
) -> dict[str, list[uuid.UUID]]:
    """Garante pelo menos 4 categorias GASTO e 4 RECEITA do usuário (para variar FK)."""
    extras = [
        ("Alimentação (seed obj)", "GASTO", "food.svg", "#FF6B6B"),
        ("Transporte (seed obj)", "GASTO", "car.svg", "#4ECDC4"),
        ("Lazer (seed obj)", "GASTO", "game.svg", "#DDA0DD"),
        ("Saúde (seed obj)", "GASTO", "health.svg", "#96CEB4"),
        ("Salário (seed obj)", "RECEITA", "money.svg", "#2ECC71"),
        ("Freelance (seed obj)", "RECEITA", "code.svg", "#3498DB"),
        ("Bônus (seed obj)", "RECEITA", "gift.svg", "#F39C12"),
        ("Investimentos (seed obj)", "RECEITA", "chart.svg", "#1ABC9C"),
    ]
    for nome, tipo, icone, cor in extras:
        cur.execute(
            """
            SELECT COUNT(*) FROM categoria
            WHERE fk_usuario = %s AND nome = %s
            """,
            (str(fk_usuario), nome),
        )
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO categoria (nome, icone, cor, tipo, fk_usuario)
                VALUES (%s, %s, %s, %s::tipo_transacao, %s)
                """,
                (nome, icone, cor, tipo, str(fk_usuario)),
            )
    conn.commit()
    return fetch_categorias_por_tipo(cur, fk_usuario)


def limpar_objetivos(cur: Any, fk_usuario: uuid.UUID) -> int:
    cur.execute("DELETE FROM objetivo WHERE fk_usuario = %s", (str(fk_usuario),))
    return cur.rowcount


def _colunas_objetivo(cur: Any) -> set[str]:
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'objetivo'
        """
    )
    return {r[0] for r in cur.fetchall()}


def _montar_insert_objetivo(cur: Any) -> tuple[str, list[str]]:
    """Monta INSERT só com colunas que existem (Hibernate costuma não dar DEFAULT em id)."""
    cols_db = _colunas_objetivo(cur)
    if not cols_db:
        raise RuntimeError(
            "Tabela `objetivo` não existe. Crie com o app/Flyway ou rode sem --sem-ddl."
        )

    ordem_base = [
        "id",
        "nome",
        "descricao",
        "valor",
        "tipo_objetivo",
        "prioridade",
        "data_inicio",
        "data_fim",
        "fk_usuario",
        "fk_categoria",
    ]
    colunas: list[str] = []
    placeholders: list[str] = []
    params_order: list[str] = []

    for nome in ordem_base:
        if nome in cols_db:
            colunas.append(nome)
            placeholders.append("%s")
            params_order.append(nome)

    if "concluido" in cols_db:
        colunas.append("concluido")
        placeholders.append("%s")
        params_order.append("concluido")

    for ts in ("criado_em", "atualizado_em"):
        if ts in cols_db:
            colunas.append(ts)
            placeholders.append("NOW()")

    sql = f"INSERT INTO objetivo ({', '.join(colunas)}) VALUES ({', '.join(placeholders)})"
    return sql, params_order


def build_rows(
    fk_usuario: uuid.UUID,
    gasto_ids: list[uuid.UUID],
    receita_ids: list[uuid.UUID],
) -> list[tuple[Any, ...]]:
    """15 cenários: nomes começam com [CEN xx] para filtro na UI/API."""
    t = _today()
    g = lambda i: str(gasto_ids[i % len(gasto_ids)])
    r = lambda i: str(receita_ids[i % len(receita_ids)])

    rows: list[tuple[Any, ...]] = []

    # --- LIMITE_GASTO (8 cenários) ---
    rows.append(
        (
            "[CEN 01] Gasto — período longo ativo, consumo baixo (~15%)",
            "Janela ampla; pouco gasto na categoria no período.",
            "LIMITE_GASTO",
            "ALTA",
            t - timedelta(days=10),
            t + timedelta(days=80),
            2000.00,
            g(0),
        )
    )
    rows.append(
        (
            "[CEN 02] Gasto — perto do limite (~90%)",
            "Meta apertada; narrativa de atenção ao teto.",
            "LIMITE_GASTO",
            "MEDIA",
            t - timedelta(days=20),
            t + timedelta(days=10),
            500.00,
            g(1),
        )
    )
    rows.append(
        (
            "[CEN 03] Gasto — estourou o combinado",
            "Valor meta baixo para simular ultrapassagem fácil nos relatórios.",
            "LIMITE_GASTO",
            "ALTA",
            t - timedelta(days=30),
            t + timedelta(days=5),
            100.00,
            g(2),
        )
    )
    rows.append(
        (
            "[CEN 04] Gasto — período só no futuro",
            "Ainda não começou; métricas devem refletir vigência futura.",
            "LIMITE_GASTO",
            "BAIXA",
            t + timedelta(days=7),
            t + timedelta(days=37),
            1500.00,
            g(3),
        )
    )
    rows.append(
        (
            "[CEN 05] Gasto — período encerrado (passado)",
            "Objetivo já findou; útil para teste de concluído / histórico.",
            "LIMITE_GASTO",
            "BAIXA",
            t - timedelta(days=120),
            t - timedelta(days=30),
            800.00,
            g(0),
        )
    )
    rows.append(
        (
            "[CEN 06] Gasto — janela de 7 dias (urgente)",
            "Poucos dias para fechar o período.",
            "LIMITE_GASTO",
            "ALTA",
            t - timedelta(days=2),
            t + timedelta(days=5),
            400.00,
            g(1),
        )
    )
    rows.append(
        (
            "[CEN 07] Gasto — prioridade ALTA + descrição curta",
            "Combina prioridade e texto mínimo.",
            "LIMITE_GASTO",
            "ALTA",
            t - timedelta(days=5),
            t + timedelta(days=25),
            600.00,
            g(2),
        )
    )
    rows.append(
        (
            "[CEN 08] Gasto — prioridade BAIXA + sem descrição",
            None,
            "LIMITE_GASTO",
            "BAIXA",
            t - timedelta(days=1),
            t + timedelta(days=60),
            3000.00,
            g(3),
        )
    )

    # --- AUMENTO_RECEITA (7 cenários) ---
    rows.append(
        (
            "[CEN 09] Receita — bem abaixo da meta",
            "Receita alvo alto; difícil bater no curto prazo.",
            "AUMENTO_RECEITA",
            "MEDIA",
            t - timedelta(days=5),
            t + timedelta(days=25),
            10000.00,
            r(0),
        )
    )
    rows.append(
        (
            "[CEN 10] Receita — quase na meta (~85%)",
            "Próximo do objetivo.",
            "AUMENTO_RECEITA",
            "ALTA",
            t - timedelta(days=15),
            t + timedelta(days=15),
            5000.00,
            r(1),
        )
    )
    rows.append(
        (
            "[CEN 11] Receita — superou a meta",
            "Meta modesta para permitir ultrapassagem nos agregados.",
            "AUMENTO_RECEITA",
            "MEDIA",
            t - timedelta(days=10),
            t + timedelta(days=20),
            800.00,
            r(2),
        )
    )
    rows.append(
        (
            "[CEN 12] Receita — janela anual",
            "Objetivo de longo prazo.",
            "AUMENTO_RECEITA",
            "BAIXA",
            t - timedelta(days=30),
            t + timedelta(days=335),
            120000.00,
            r(3),
        )
    )
    year, month = t.year, t.month
    last_dom = calendar.monthrange(year, month)[1]
    inicio_mes = date(year, month, 1)
    fim_mes = date(year, month, last_dom)
    rows.append(
        (
            "[CEN 13] Receita — só mês corrente",
            "Início no 1º dia do mês e fim no último dia do mês corrente.",
            "AUMENTO_RECEITA",
            "ALTA",
            inicio_mes,
            fim_mes,
            7000.00,
            r(0),
        )
    )
    rows.append(
        (
            "[CEN 14] Receita — descrição longa (texto)",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed non risus. Suspendisse lectus tortor, dignissim sit amet, "
            "adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam.",
            "AUMENTO_RECEITA",
            "MEDIA",
            t - timedelta(days=7),
            t + timedelta(days=23),
            4500.00,
            r(1),
        )
    )
    rows.append(
        (
            "[CEN 15] Receita — valor mínimo e borda de data",
            "Valor pequeno; datas no mesmo mês.",
            "AUMENTO_RECEITA",
            "BAIXA",
            t,
            t + timedelta(days=1),
            0.01,
            r(2),
        )
    )

    uid = str(fk_usuario)
    out: list[tuple[Any, ...]] = []
    for nome, desc, tipo, pri, di, df, valor, fk_cat in rows:
        oid = str(uuid.uuid4())
        out.append((oid, nome, desc, valor, tipo, pri, di, df, uid, fk_cat))
    return out


def insert_objetivos(conn: Any, cur: Any, fk_usuario: uuid.UUID) -> int:
    por_tipo = fetch_categorias_por_tipo(cur, fk_usuario)
    gasto_ids = por_tipo["GASTO"]
    receita_ids = por_tipo["RECEITA"]
    if not gasto_ids or not receita_ids:
        por_tipo = ensure_categorias_minimas(conn, cur, fk_usuario)
        gasto_ids = por_tipo["GASTO"]
        receita_ids = por_tipo["RECEITA"]
    if not gasto_ids or not receita_ids:
        raise RuntimeError(
            "Não há categorias GASTO e RECEITA após tentativa de criação. "
            "Verifique tipos no banco (enum tipo_transacao)."
        )

    batch = build_rows(fk_usuario, gasto_ids, receita_ids)
    sql, params_order = _montar_insert_objetivo(cur)
    if "concluido" in params_order:
        batch = [(*row, False) for row in batch]

    if batch and len(batch[0]) != len(params_order):
        raise RuntimeError(
            f"Incompatibilidade de colunas: INSERT espera {len(params_order)} valores por linha, "
            f"o seed montou {len(batch[0])}. Parâmetros: {params_order}"
        )

    cur.executemany(sql, batch)
    return len(batch)


def usuario_existe(cur: Any, fk_usuario: uuid.UUID) -> bool:
    cur.execute("SELECT 1 FROM usuario WHERE id = %s", (str(fk_usuario),))
    return cur.fetchone() is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de objetivos por cenário.")
    parser.add_argument(
        "--usuario",
        type=uuid.UUID,
        default=uuid.UUID(os.getenv("SEED_FK_USUARIO", str(DEFAULT_FK_USUARIO))),
        help="UUID do usuário (default: constante no script ou SEED_FK_USUARIO).",
    )
    parser.add_argument(
        "--limpar",
        action="store_true",
        help="Remove todos os objetivos deste usuário antes de inserir.",
    )
    parser.add_argument(
        "--sem-ddl",
        action="store_true",
        help="Não executa CREATE TABLE (use se o Flyway já criou `objetivo`).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        metavar="SEG",
        help="Timeout em segundos para abrir conexão TCP com o PostgreSQL (padrão: 15).",
    )
    args = parser.parse_args()
    fk_usuario: uuid.UUID = args.usuario

    if not DATABASE_URL:
        print("ERRO: DATABASE_URL não encontrada no .env", file=sys.stderr)
        sys.exit(1)

    alvo = (
        DATABASE_URL.split("@")[-1]
        if "@" in DATABASE_URL
        else "(URL sem @ — verifique o formato)"
    )
    print("=" * 60, flush=True)
    print("  SEED — Objetivos por cenário (PostgreSQL)", flush=True)
    print("=" * 60, flush=True)
    print(f"\n fk_usuario = {fk_usuario}", flush=True)
    print(f" Alvo (host/db): {alvo}", flush=True)
    print(
        f" Abrindo conexão (timeout {args.timeout}s)… "
        "Se travar aqui, o host não responde ou a rede bloqueia a porta.\n",
        flush=True,
    )

    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=args.timeout)
    except psycopg2.OperationalError as e:
        print(f"ERRO ao conectar: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        cur = conn.cursor()
        if not usuario_existe(cur, fk_usuario):
            print(
                f"ERRO: usuário {fk_usuario} não existe na tabela `usuario`. "
                "Crie o usuário antes ou passe --usuario com um id válido.",
                file=sys.stderr,
            )
            sys.exit(1)

        ensure_objetivo_table(conn, skip_ddl=args.sem_ddl)

        if args.limpar:
            n = limpar_objetivos(cur, fk_usuario)
            conn.commit()
            print(f"Removidos {n} objetivo(s) anteriores deste usuário.")

        n_ins = insert_objetivos(conn, cur, fk_usuario)
        conn.commit()
        print(f"Inseridos {n_ins} objetivos.")
    except psycopg2.Error as e:
        print(f"\nERRO: {e}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("  Concluído.")
    print("=" * 60)


if __name__ == "__main__":
    main()
