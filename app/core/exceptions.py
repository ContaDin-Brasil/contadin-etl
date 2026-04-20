"""Exceções de domínio da aplicação."""


class ETLError(Exception):
    """Base para todos os erros do pipeline ETL."""

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class ExtractionError(ETLError):
    """Falha ao ler ou converter o arquivo enviado."""


class AIResponseError(ETLError):
    """A IA retornou uma resposta que não pôde ser interpretada como JSON."""


class AIServiceError(ETLError):
    """Falha na comunicação com o serviço de IA (timeout, quota, etc.)."""


class MatchError(ETLError):
    """Falha ao consultar entidades existentes no banco durante o matching."""
