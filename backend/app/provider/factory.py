"""Provider factory — select LLM/TTS/ASR by config with retry + fallback wrappers."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING, TypeVar

from app.core.config import get_settings
from app.provider.asr.base_asr_provider import BaseASRProvider
from app.provider.llm.base_llm_provider import BaseLLMProvider
from app.provider.retry import with_retry_and_fallback
from app.provider.tts.base_tts_provider import BaseTTSProvider

if TYPE_CHECKING:
    pass

T = TypeVar("T")


def _llm_registry() -> dict[str, type[BaseLLMProvider]]:
    from app.provider.llm.deepseek_provider import DeepSeekProvider
    from app.provider.llm.qwen_provider import QwenProvider

    return {
        "deepseek": DeepSeekProvider,
        "qwen": QwenProvider,
    }


def _tts_registry() -> dict[str, type[BaseTTSProvider]]:
    from app.provider.tts.aliyun_tts_provider import AliyunTTSProvider
    from app.provider.tts.edge_tts_provider import EdgeTTSProvider

    return {
        "edge": EdgeTTSProvider,
        "aliyun": AliyunTTSProvider,
    }


def _asr_registry() -> dict[str, type[BaseASRProvider]]:
    from app.provider.asr.aliyun_asr_provider import AliyunASRProvider
    from app.provider.asr.tencent_asr_provider import TencentASRProvider

    return {
        "aliyun": AliyunASRProvider,
        "tencent": TencentASRProvider,
    }


def _build_provider(registry: dict[str, type[T]], name: str) -> T:
    cls = registry.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}")
    return cls()


def get_llm_provider() -> ResilientLLMProvider:
    cfg = get_settings()["llm"]
    registry = _llm_registry()
    primary = _build_provider(registry, cfg["provider"])
    fallback_name = cfg.get("fallback")
    fallback = (
        _build_provider(registry, fallback_name)
        if fallback_name and fallback_name in registry
        else None
    )
    return ResilientLLMProvider(primary, fallback)


def get_tts_provider() -> ResilientTTSProvider:
    cfg = get_settings()["tts"]
    registry = _tts_registry()
    primary = _build_provider(registry, cfg["provider"])
    fallback_name = cfg.get("fallback")
    fallback = (
        _build_provider(registry, fallback_name)
        if fallback_name and fallback_name in registry
        else None
    )
    return ResilientTTSProvider(primary, fallback)


def get_asr_provider() -> ResilientASRProvider:
    cfg = get_settings()["asr"]
    registry = _asr_registry()
    primary = _build_provider(registry, cfg["provider"])
    fallback_name = cfg.get("fallback")
    fallback = (
        _build_provider(registry, fallback_name)
        if fallback_name and fallback_name in registry
        else None
    )
    return ResilientASRProvider(primary, fallback)


class ResilientLLMProvider(BaseLLMProvider):
    def __init__(
        self,
        primary: BaseLLMProvider,
        fallback: BaseLLMProvider | None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def chat_completion(
        self, prompt: str, response_format: str = "text"
    ) -> str:
        async def primary_call() -> str:
            return await self._primary.chat_completion(prompt, response_format)

        async def fallback_call() -> str:
            assert self._fallback is not None
            return await self._fallback.chat_completion(prompt, response_format)

        return await with_retry_and_fallback(
            primary_call,
            fallback_call if self._fallback else None,
            label="llm",
        )


class ResilientTTSProvider(BaseTTSProvider):
    def __init__(
        self,
        primary: BaseTTSProvider,
        fallback: BaseTTSProvider | None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def synthesize(self, text: str, config: dict) -> bytes:
        async def primary_call() -> bytes:
            return await self._primary.synthesize(text, config)

        async def fallback_call() -> bytes:
            assert self._fallback is not None
            return await self._fallback.synthesize(text, config)

        return await with_retry_and_fallback(
            primary_call,
            fallback_call if self._fallback else None,
            label="tts",
        )


class ResilientASRProvider(BaseASRProvider):
    def __init__(
        self,
        primary: BaseASRProvider,
        fallback: BaseASRProvider | None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        provider = self._primary
        try:
            async for text in provider.stream_recognize(audio_stream, config):
                yield text
        except Exception:
            if self._fallback is None:
                raise
            async for text in self._fallback.stream_recognize(audio_stream, config):
                yield text
