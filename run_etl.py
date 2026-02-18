#!/usr/bin/env python3
"""
Orquestra o ETL: planilha Excel -> transformação -> SQL Server.
Uso: python run_etl.py [caminho_planilha.xlsx]
"""
import sys
from sqlalchemy import create_engine

from config.settings import DATABASE_URL, USUARIO_ID_PADRAO
from etl.extract import extrair
from etl.transform import transformar_instituicoes, transformar_categorias, transformar_transacoes
from etl.load import carregar_instituicoes, carregar_categorias, carregar_transacoes


def main() -> None:
    planilha = sys.argv[1] if len(sys.argv) > 1 else "planilha_transacoes.xlsx"
    print(f"Planilha: {planilha}")

    df_inst, df_cat, df_trans = extrair(planilha)
    print("Extraído: Instituicoes, Categorias, Transacoes")

    df_inst = transformar_instituicoes(df_inst, USUARIO_ID_PADRAO)
    df_cat = transformar_categorias(df_cat, USUARIO_ID_PADRAO)
    print(f"Transformado: {len(df_inst)} instituições, {len(df_cat)} categorias")

    engine = create_engine(DATABASE_URL)
    map_inst = carregar_instituicoes(engine, df_inst, USUARIO_ID_PADRAO)
    map_cat = carregar_categorias(engine, df_cat, USUARIO_ID_PADRAO)
    print("Instituições e categorias carregadas.")

    df_trans = transformar_transacoes(df_trans, map_inst, map_cat, USUARIO_ID_PADRAO)
    print(f"Transformado: {len(df_trans)} transações")
    carregar_transacoes(engine, df_trans)
    print("Transações carregadas. ETL concluído.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
