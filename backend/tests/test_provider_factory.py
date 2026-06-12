"""Provider factory unit tests."""

import asyncio

from app.provider.factory import (
    ResilientLLMProvider,
    ResilientTTSProvider,
    get_asr_provider,
    get_llm_provider,
    get_tts_provider,
)
from app.provider.llm.base_llm_provider import BaseLLMProvider


def test_get_llm_provider_returns_resilient_wrapper():
    provider = get_llm_provider()
    assert isinstance(provider, ResilientLLMProvider)
    assert provider._fallback is not None


def test_get_tts_provider_returns_resilient_wrapper():
    provider = get_tts_provider()
    assert isinstance(provider, ResilientTTSProvider)


def test_get_asr_provider_returns_resilient_wrapper():
    provider = get_asr_provider()
    assert provider._primary is not None


class _FailingProvider(BaseLLMProvider):
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def chat_completion(self, prompt: str, response_format: str = "text") -> str:
        raise self._error


class _SuccessProvider(BaseLLMProvider):
    async def chat_completion(self, prompt: str, response_format: str = "text") -> str:
        return "ok"


def test_resilient_llm_fallback_on_primary_failure():
    provider = ResilientLLMProvider(
        _FailingProvider(RuntimeError("primary down")),
        _SuccessProvider(),
    )
    result = asyncio.run(provider.chat_completion("hello"))
    assert result == "ok"
