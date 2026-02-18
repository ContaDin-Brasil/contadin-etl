================================================================================
  PLANILHA DE TRANSAÇÕES – Instruções
================================================================================

Se você está usando o arquivo no MICROSOFT EXCEL:
  • As listas de Instituição e Categoria já devem aparecer ao clicar na setinha
    das células das colunas E e F na aba Transacoes.
  • Preencha primeiro as abas Instituicoes e Categorias; os nomes que você
    colocar na coluna "Nome" (coluna A) de cada aba aparecerão nas listas.

Se você está usando no GOOGLE PLANILHAS e a lista está VAZIA:
  O Google Planilhas não usa direito as validações entre abas vindas do Excel.
  Faça o seguinte para a lista de INSTITUIÇÃO aparecer:

  1. Abra a aba "Transacoes".
  2. Selecione a coluna E (Instituicao) – clique no cabeçalho "E".
  3. Menu: Dados → Validação de dados.
  4. Em "Critérios", escolha "Lista de intervalo".
  5. No campo do intervalo, digite exatamente:
       Instituicoes!A2:A
  6. Clique em "Salvar".

  Para a lista de CATEGORIA:

  1. Na aba "Transacoes", selecione a coluna F (Categoria).
  2. Menu: Dados → Validação de dados.
  3. Critérios: "Lista de intervalo".
  4. Intervalo:
       Categorias!A2:A
  5. Salvar.

Depois disso, ao clicar numa célula da coluna Instituicao ou Categoria, deve
aparecer a lista com os nomes que você cadastrou nas abas Instituicoes e
Categorias (coluna "Nome").

================================================================================
