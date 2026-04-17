"""ContaDIN - API"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routers import ai_router, data_router
from app.core.exceptions import AIResponseError, AIServiceError, ETLError, ExtractionError, MatchError

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(ai_router)
app.include_router(data_router)


@app.exception_handler(ExtractionError)
async def extraction_error_handler(_: Request, exc: ExtractionError) -> JSONResponse:
    logger.warning("ExtractionError: %s | detalhe: %s", exc.message, exc.detail)
    return JSONResponse(
        status_code=422,
        content={"error": "extraction_error", "message": exc.message},
    )


@app.exception_handler(AIResponseError)
async def ai_response_error_handler(_: Request, exc: AIResponseError) -> JSONResponse:
    logger.warning("AIResponseError: %s | detalhe: %s", exc.message, exc.detail)
    return JSONResponse(
        status_code=422,
        content={"error": "ai_response_error", "message": exc.message},
    )


@app.exception_handler(AIServiceError)
async def ai_service_error_handler(_: Request, exc: AIServiceError) -> JSONResponse:
    logger.error("AIServiceError: %s | detalhe: %s", exc.message, exc.detail)
    return JSONResponse(
        status_code=503,
        content={"error": "ai_service_error", "message": exc.message},
    )


@app.exception_handler(MatchError)
async def match_error_handler(_: Request, exc: MatchError) -> JSONResponse:
    logger.error("MatchError: %s | detalhe: %s", exc.message, exc.detail)
    return JSONResponse(
        status_code=502,
        content={"error": "match_error", "message": exc.message},
    )


@app.exception_handler(ETLError)
async def etl_error_handler(_: Request, exc: ETLError) -> JSONResponse:
    """Captura qualquer ETLError não tratado pelos handlers específicos acima."""
    logger.error("ETLError inesperado: %s | detalhe: %s", exc.message, exc.detail)
    return JSONResponse(
        status_code=500,
        content={"error": "etl_error", "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """Último recurso — evita que qualquer exceção vire um 500 sem corpo."""
    logger.exception("Erro inesperado não tratado: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Ocorreu um erro interno inesperado. Tente novamente.",
        },
    )
