# ContaDIN ETL

API construída com **FastAPI** que utiliza o **Google Gemini** para estruturar dados financeiros a partir de planilhas e imagens de documentos (boletos, recibos, notas fiscais, etc.).

---

## Arquitetura

```
app/
├── main.py                          # Entry point da aplicação FastAPI
├── config/
│   └── __init__.py                  # Variáveis de ambiente (.env)
│
├── api/
│   ├── routers/
│   │   ├── __init__.py              # Exporta todos os routers
│   │   ├── ai.py                    # Rotas de IA (/ai)
│   │   └── data.py                  # Rotas de dados/ETL (/data)
│   ├── controllers/
│   │   ├── ai_controller.py         # Handlers de IA
│   │   └── data_controller.py       # Handlers de dados
│   ├── services/
│   │   ├── ai_service.py            # Lógica de negócio de IA
│   │   └── data_service.py          # Orquestra o pipeline ETL
│   └── schemas/
│       ├── ai_schema.py             # Modelos de request/response de IA
│       └── data_schema.py           # Modelos de entidades financeiras
│
└── modules/
    ├── gemini/
    │   ├── __init__.py              # Cliente Gemini (text + image)
    │   └── prompts/
    │       ├── ola_mundo.md         # Prompt de teste
    │       ├── parse_spreadsheet.md # Prompt para estruturar planilhas
    │       └── scan_image.md        # Prompt para extrair dados de imagens
    └── etl/
        ├── __init__.py
        ├── extract.py               # Lê planilhas (xlsx/csv) para texto
        └── transform.py             # Parseia JSON da resposta do Gemini
```

**Fluxo:** Router → Controller → Service → Module

---

## Endpoints

### IA (`/ai`)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/ai/hello-world` | Envia prompt pré-definido ao Gemini (teste de conectividade) |
| `POST` | `/ai/query` | Envia prompt customizado ao Gemini — body: `{ "prompt": "..." }` |
| `POST` | `/ai/scan` | Recebe imagem de documento financeiro e extrai dados de transação e instituição — body: `multipart/form-data (file)` |
| `POST` | `/ai/audio` | Recebe áudio e transcreve os dados de transação — body: `multipart/form-data (file)` |

### Dados (`/data`)

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/data/process` | Recebe planilha financeira (xlsx/csv), estrutura com IA e retorna JSON com as entidades extraídas — body: `multipart/form-data (file)` |

---

## Configuração

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | URL de conexão com o banco de dados |
| `GEMINI_API_KEY` | Chave da API do Google Gemini |
| `GEMINI_MODEL` | Modelo do Gemini (ex: `gemini-2.5-flash-preview-04-17`) |
| `USUARIO_ID_PADRAO` | ID padrão do usuário |

---

## Como rodar

**Pré-requisito:** Python 3.12 ou 3.13 instalado.

**1. Criar e ativar o ambiente virtual**

```bash
python -m venv .venv
```

- Windows: `.venv\Scripts\activate`
- macOS / Linux: `source .venv/bin/activate`

**2. Instalar as dependências**

```bash
pip install -r requirements.txt
```

**3. Configurar variáveis de ambiente**

```bash
cp .env.example .env
# Editar .env com suas credenciais
```

**4. Iniciar o servidor**

```bash
python -m uvicorn app.main:app --reload
```

**5. Acessar a documentação interativa**

```
http://localhost:8000/docs
```

---

> **Atenção — acesso via dispositivo físico ou emulador mobile**
>
> O comando padrão (passo 4) sobe o servidor apenas em `localhost`, o que impede que dispositivos físicos e emuladores consigam alcançá-lo pela rede local.
>
> Se o frontend mobile não registrar nenhum log ao chamar a API de IA (câmera, galeria ou áudio), substitua o comando do passo 4 por:
>
> ```bash
> uvicorn app.main:app --reload --host 0.0.0.0
> ```
>
> Isso faz o servidor escutar em todas as interfaces de rede, tornando-o acessível pelo IP da máquina (ex.: `http://192.168.X.X:8000`).