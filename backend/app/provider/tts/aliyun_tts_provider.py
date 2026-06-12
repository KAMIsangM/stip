"""Aliyun TTS provider — MVP fallback (config tts.fallback=aliyun)."""

from app.provider.tts.base_tts_provider import BaseTTSProvider


class AliyunTTSProvider(BaseTTSProvider):
    async def synthesize(self, text: str, config: dict) -> bytes:
        # TODO: Aliyun TTS REST/WebSocket integration
        raise NotImplementedError("Aliyun TTS not yet integrated")
