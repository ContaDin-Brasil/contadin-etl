"""Cliente resiliente para a API do Google Gemini.

Estratégia de fallback (executada a cada chamada):
  Para cada modelo na lista configurada:
    Para cada API key disponível (não em cooldown):
      Tenta até `max_retries_per_combination` vezes:
        - Quota / rate-limit  → marca key em cooldown, tenta próxima key
        - Erro transitório    → exponential backoff e retry
        - thinking inválido   → remove thinking_config e repete (transparente)
        - Erro irrecuperável  → abandona o modelo, tenta o próximo
  Se todos os recursos esgotarem → lança AIServiceUnavailableException.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from threading import Lock

from google import genai
from google.genai import types

from app.core.exceptions import AIServiceUnavailableException

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Model Capabilities
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ModelCapabilities:
    """Capacidades declaradas de um modelo Gemini."""

    supports_thinking_config: bool = True


# Registry estático — fonte de verdade para modelos conhecidos.
# Modelos ausentes são assumidos como premium (thinking=True) e terão suas
# capabilities descobertas em runtime via auto-detecção por erro.
_CAPABILITY_REGISTRY: dict[str, ModelCapabilities] = {
    # ── Premium / Thinking ────────────────────────────────────────────────────
    "gemini-2.5-pro":         ModelCapabilities(supports_thinking_config=True),
    "gemini-2.5-flash":       ModelCapabilities(supports_thinking_config=True),
    "gemini-3-flash-preview": ModelCapabilities(supports_thinking_config=True),
    # ── Flash / Standard ─────────────────────────────────────────────────────
    "gemini-2.0-flash":       ModelCapabilities(supports_thinking_config=False),
    "gemini-2.0-flash-lite":  ModelCapabilities(supports_thinking_config=False),
    "gemini-1.5-pro":         ModelCapabilities(supports_thinking_config=False),
    "gemini-1.5-flash":       ModelCapabilities(supports_thinking_config=False),
    "gemini-1.0-pro":         ModelCapabilities(supports_thinking_config=False),
}


def _resolve_capabilities(model: str) -> ModelCapabilities:
    """Resolve capabilities por exact match, depois por substring match."""
    if model in _CAPABILITY_REGISTRY:
        return _CAPABILITY_REGISTRY[model]
    for name, caps in _CAPABILITY_REGISTRY.items():
        if name in model or model.startswith(name):
            return caps
    logger.debug(
        "Modelo '%s' não encontrado no registry — assumindo suporte a thinking_config",
        model,
    )
    return ModelCapabilities(supports_thinking_config=True)


# ──────────────────────────────────────────────────────────────────────────────
# Runtime Capability Cache  (thread-safe)
# ──────────────────────────────────────────────────────────────────────────────


class _CapabilityCache:
    """Cache em memória de capabilities descobertas via auto-detecção em runtime."""

    def __init__(self) -> None:
        self._data: dict[str, ModelCapabilities] = {}
        self._lock = Lock()

    def get(self, model: str) -> ModelCapabilities:
        with self._lock:
            if model not in self._data:
                self._data[model] = _resolve_capabilities(model)
            return self._data[model]

    def mark_thinking_unsupported(self, model: str) -> None:
        """Registra que este modelo não suporta thinking_config."""
        with self._lock:
            self._data[model] = ModelCapabilities(supports_thinking_config=False)
        logger.info(
            "Capability cache atualizado: '%s' não suporta thinking_config",
            model,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Key Pool  (thread-safe)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class _KeyEntry:
    api_key: str
    cooldown_until: float = field(default=0.0)  # timestamp monotônico


class _KeyPool:
    """Gerencia múltiplas API keys com cooldown por quota esgotada."""

    def __init__(self, api_keys: list[str], cooldown_seconds: int = 60) -> None:
        if not api_keys:
            raise ValueError("Nenhuma API key configurada para o GeminiResilientClient.")
        self._entries = [_KeyEntry(api_key=k) for k in api_keys]
        self._cooldown_seconds = cooldown_seconds
        self._lock = Lock()

    @property
    def total(self) -> int:
        return len(self._entries)

    def get_all_available(self) -> list[str]:
        """Retorna todas as keys não-cooldown no momento da chamada."""
        now = time.monotonic()
        with self._lock:
            return [e.api_key for e in self._entries if e.cooldown_until <= now]

    def mark_cooldown(self, api_key: str) -> None:
        """Marca uma key como indisponível pelo período de cooldown."""
        until = time.monotonic() + self._cooldown_seconds
        with self._lock:
            for entry in self._entries:
                if entry.api_key == api_key:
                    entry.cooldown_until = until
                    logger.warning(
                        "API key ...%s marcada em cooldown por %ds",
                        api_key[-6:],
                        self._cooldown_seconds,
                    )
                    return


# ──────────────────────────────────────────────────────────────────────────────
# Retry Configuration
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class RetryConfig:
    """Parâmetros de retry e cooldown do cliente resiliente."""

    max_retries_per_combination: int = 3
    """Tentativas por par (modelo, key) antes de desistir."""

    base_backoff_seconds: float = 1.0
    """Backoff inicial para erros transitórios (dobra a cada tentativa)."""

    max_backoff_seconds: float = 16.0
    """Teto do backoff exponencial."""

    key_cooldown_seconds: int = 60
    """Tempo (em segundos) que uma key fica indisponível após quota esgotada."""


# ──────────────────────────────────────────────────────────────────────────────
# Error Classification
# ──────────────────────────────────────────────────────────────────────────────


def _is_quota_error(exc: Exception) -> bool:
    """429, RESOURCE_EXHAUSTED, quota exceeded, rate limit."""
    msg = str(exc).lower()
    type_name = type(exc).__name__
    return any(
        [
            "429" in msg,
            "resource_exhausted" in msg,
            "quota exceeded" in msg,
            "rate limit" in msg,
            "ratelimitexceeded" in msg,
            "ResourceExhausted" in type_name,
            "TooManyRequests" in type_name,
        ]
    )


def _is_thinking_unsupported(exc: Exception) -> bool:
    """INVALID_ARGUMENT relacionado a thinking_config não suportado."""
    msg = str(exc).lower()
    type_name = type(exc).__name__
    is_invalid_arg = "invalid_argument" in msg or "InvalidArgument" in type_name
    is_thinking = any(
        kw in msg
        for kw in ("thinking", "thinking_level", "thinking level", "not supported for this model")
    )
    return is_invalid_arg and is_thinking


def _is_transient_error(exc: Exception) -> bool:
    """Timeouts e erros de rede que justificam retry."""
    msg = str(exc).lower()
    type_name = type(exc).__name__
    return any(
        [
            "timeout" in msg,
            "timed out" in msg,
            "connection" in msg,
            "DeadlineExceeded" in type_name,
            "ServiceUnavailable" in type_name,
            "Unavailable" in type_name,
        ]
    )


# ──────────────────────────────────────────────────────────────────────────────
# Config Adapter
# ──────────────────────────────────────────────────────────────────────────────


def _adapt_config(
    config: types.GenerateContentConfig,
    caps: ModelCapabilities,
) -> types.GenerateContentConfig:
    """Remove thinking_config se o modelo não suportar o parâmetro."""
    if caps.supports_thinking_config or config.thinking_config is None:
        return config

    logger.debug("Adaptando config: removendo thinking_config (modelo não suporta)")

    # GenerateContentConfig é um Pydantic model — serializa e reconstrói sem o campo
    try:
        raw: dict = config.model_dump(exclude_none=True)
    except AttributeError:
        raw = {k: v for k, v in vars(config).items() if v is not None}

    raw.pop("thinking_config", None)
    return types.GenerateContentConfig(**raw) if raw else types.GenerateContentConfig()


# ──────────────────────────────────────────────────────────────────────────────
# Resilient Client
# ──────────────────────────────────────────────────────────────────────────────


class GeminiResilientClient:
    """Cliente Gemini com fallback automático entre modelos e API keys.

    Uso básico::

        client = GeminiResilientClient(api_keys=[...], models=[...])
        text = client.call(contents, config)

    O cliente tenta todos os pares (modelo, key) na ordem configurada,
    aplicando backoff exponencial para erros transitórios e cooldown
    para keys com quota esgotada. Thinking_config é removido automaticamente
    para modelos que não o suportam, sem quebrar a chamada.
    """

    def __init__(
        self,
        api_keys: list[str],
        models: list[str],
        retry_config: RetryConfig | None = None,
    ) -> None:
        if not models:
            raise ValueError("Nenhum modelo configurado para o GeminiResilientClient.")

        self._models = models
        self._retry_config = retry_config or RetryConfig()
        self._key_pool = _KeyPool(
            api_keys,
            cooldown_seconds=self._retry_config.key_cooldown_seconds,
        )
        self._capability_cache = _CapabilityCache()

        logger.info(
            "GeminiResilientClient inicializado — %d modelo(s), %d key(s): %s",
            len(models),
            self._key_pool.total,
            models,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def call(
        self,
        contents: list[types.Content],
        config: types.GenerateContentConfig | None = None,
    ) -> str:
        """Executa uma chamada ao Gemini com fallback completo.

        Args:
            contents: Lista de mensagens/partes para o modelo.
            config:   Configuração de geração (thinking_config, temperatura etc.).
                      Pode incluir thinking_config mesmo para modelos flash —
                      o cliente removerá automaticamente se necessário.

        Returns:
            Texto completo gerado pelo modelo.

        Raises:
            AIServiceUnavailableException: Todos os modelos e keys falharam.
        """
        effective_config = config or types.GenerateContentConfig()
        rc = self._retry_config
        last_error: Exception | None = None
        all_keys_in_cooldown = False

        for model_index, model in enumerate(self._models):
            next_model = (
                self._models[model_index + 1] if model_index + 1 < len(self._models) else None
            )
            fallback_hint = f" → fallback para '{next_model}'" if next_model else " → sem mais fallbacks"

            available_keys = self._key_pool.get_all_available()

            if not available_keys:
                all_keys_in_cooldown = True
                logger.warning(
                    "Todas as keys em cooldown ao tentar modelo '%s'%s",
                    model,
                    fallback_hint,
                )
                continue

            model_failed_permanently = False
            quota_esgotada = False

            for key in available_keys:
                for attempt in range(rc.max_retries_per_combination):
                    try:
                        result = self._call_with_capability_adaptation(
                            model, key, contents, effective_config
                        )
                        prefix = "Fallback bem-sucedido" if model_index > 0 else "Chamada bem-sucedida"
                        logger.info(
                            "%s — modelo='%s' key=...%s",
                            prefix,
                            model,
                            key[-6:],
                        )
                        return result

                    except Exception as exc:
                        last_error = exc

                        if _is_quota_error(exc):
                            quota_esgotada = True
                            logger.warning(
                                "Cota esgotada — modelo='%s' key=...%s%s",
                                model,
                                key[-6:],
                                fallback_hint,
                            )
                            self._key_pool.mark_cooldown(key)
                            break  # tenta próxima key

                        elif _is_transient_error(exc):
                            backoff = min(
                                rc.base_backoff_seconds * (2**attempt),
                                rc.max_backoff_seconds,
                            )
                            logger.warning(
                                "Erro transitório (tentativa %d/%d) — aguardando %.1fs — %s",
                                attempt + 1,
                                rc.max_retries_per_combination,
                                backoff,
                                exc,
                            )
                            time.sleep(backoff)
                            # loop continua: retry na mesma (modelo, key)

                        else:
                            # INVALID_ARGUMENT não-thinking, model not found, etc.
                            logger.error(
                                "Erro irrecuperável — modelo='%s'%s — %s",
                                model,
                                fallback_hint,
                                exc,
                            )
                            model_failed_permanently = True
                            break  # abandona tentativas desta key

                if model_failed_permanently:
                    break  # abandona as demais keys deste modelo

            if model_failed_permanently:
                logger.warning(
                    "Modelo '%s' descartado por erro irrecuperável%s",
                    model,
                    fallback_hint,
                )

        detail = (
            f"Todas as API keys estão em cooldown (quota esgotada). "
            f"Aguarde {self._retry_config.key_cooldown_seconds}s e tente novamente."
            if all_keys_in_cooldown and last_error is None
            else str(last_error)
        )
        raise AIServiceUnavailableException(
            message=(
                "Serviço Gemini indisponível: todos os modelos e API keys falharam. "
                f"Modelos tentados: {self._models}."
            ),
            detail=detail,
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _call_with_capability_adaptation(
        self,
        model: str,
        api_key: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> str:
        """Executa a chamada adaptando o config às capabilities do modelo.

        Se o modelo retornar erro de thinking não suportado:
          1. Atualiza o cache de capabilities.
          2. Remove thinking_config e repete a chamada — de forma transparente.
        """
        caps = self._capability_cache.get(model)
        adapted = _adapt_config(config, caps)

        try:
            return self._stream(model, api_key, contents, adapted)
        except Exception as exc:
            if _is_thinking_unsupported(exc):
                logger.info(
                    "Auto-detecção: '%s' não suporta thinking_config — repetindo sem ele",
                    model,
                )
                self._capability_cache.mark_thinking_unsupported(model)
                adapted = _adapt_config(config, self._capability_cache.get(model))
                return self._stream(model, api_key, contents, adapted)
            raise

    def _stream(
        self,
        model: str,
        api_key: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> str:
        """Executa generate_content_stream e retorna o texto completo concatenado."""
        client = genai.Client(api_key=api_key)
        chunks: list[str] = []
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                chunks.append(chunk.text)
        return "".join(chunks)


# ──────────────────────────────────────────────────────────────────────────────
# Module-level Singleton  (thread-safe via double-checked locking)
# ──────────────────────────────────────────────────────────────────────────────

_client: GeminiResilientClient | None = None
_client_lock = Lock()


def get_client() -> GeminiResilientClient:
    """Retorna o singleton do GeminiResilientClient, inicializando na primeira chamada.

    A inicialização lê GEMINI_API_KEYS e GEMINI_MODELS do módulo de config,
    que por sua vez os carrega do .env (suporte a múltiplos valores separados por vírgula).
    """
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:  # double-checked locking
                from app.config import GEMINI_API_KEYS, GEMINI_MODELS  # noqa: PLC0415

                _client = GeminiResilientClient(
                    api_keys=GEMINI_API_KEYS,
                    models=GEMINI_MODELS,
                )
    return _client
