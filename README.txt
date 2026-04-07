================================================================================
  ContaDIN ETL - API de processamento financeiro com IA
================================================================================

API construída com FastAPI que utiliza o Google Gemini para estruturar dados
financeiros a partir de planilhas e imagens de documentos (boletos, recibos,
notas fiscais, etc.).

================================================================================
  ARQUITETURA
================================================================================

app/
├── main.py                         # Entry point da aplicação FastAPI
├── config/
│   └── __init__.py                 # Variáveis de ambiente (.env)
│
├── api/
│   ├── routers/
│   │   ├── __init__.py             # Exporta todos os routers
│   │   ├── ai.py                   # Rotas de IA (/ai)
│   │   └── data.py                 # Rotas de dados/ETL (/data)
│   ├── controllers/
│   │   ├── ai_controller.py        # Handlers de IA
│   │   └── data_controller.py      # Handlers de dados
│   ├── services/
│   │   ├── ai_service.py           # Lógica de negócio de IA
│   │   └── data_service.py         # Orquestra o pipeline ETL
│   └── schemas/
│       ├── ai_schema.py            # Modelos de request/response de IA
│       └── data_schema.py          # Modelos de entidades financeiras
│
└── modules/
    ├── gemini/
    │   ├── __init__.py             # Cliente Gemini (text + image)
    │   └── prompts/
    │       ├── ola_mundo.md        # Prompt de teste
    │       ├── parse_spreadsheet.md # Prompt para estruturar planilhas
    │       └── scan_image.md       # Prompt para extrair dados de imagens
    └── etl/
        ├── __init__.py
        ├── extract.py              # Lê planilhas (xlsx/csv) para texto
        └── transform.py            # Parseia JSON da resposta do Gemini

Fluxo: Router -> Controller -> Service -> Module

================================================================================
  ENDPOINTS
================================================================================

  IA (/ai)
  --------
  GET  /ai/hello-world    Envia prompt pré-definido ao Gemini (teste)
  POST /ai/query           Envia prompt customizado ao Gemini
                           Body: { "prompt": "..." }
  POST /ai/scan            Recebe imagem de documento financeiro e extrai
                           dados de transação e instituição
                           Body: multipart/form-data (file)

  Data (/data)
  ------------
  POST /data/process       Recebe planilha financeira (xlsx/csv), estrutura
                           com IA e retorna JSON com entidades extraídas
                           Body: multipart/form-data (file)

================================================================================
  CONFIGURAÇÃO
================================================================================

Variáveis de ambiente (.env):

  DATABASE_URL        URL de conexão com o banco de dados
  GEMINI_API_KEY      Chave da API do Google Gemini
  GEMINI_MODEL        Modelo do Gemini (ex: gemini-2.5-flash-preview-04-17)
  USUARIO_ID_PADRAO   ID padrão do usuário

================================================================================
  COMO RODAR
================================================================================

  1. Criar ambiente virtual e instalar dependências:

     uv venv
     uv pip install -r requirements.txt

  2. Configurar variáveis de ambiente:

     cp .env.example .env
     # editar .env com suas credenciais

  3. Iniciar o servidor:

     uvicorn app.main:app --reload

  4. Acessar documentação interativa:

     http://localhost:8000/docs

================================================================================
