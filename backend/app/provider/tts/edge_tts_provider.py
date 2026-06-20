"""Edge TTS provider — MVP primary (config tts.provider=edge)."""

from app.core.config import get_settings
from app.provider.tts.base_tts_provider import BaseTTSProvider


class EdgeTTSProvider(BaseTTSProvider):
    async def synthesize(self, text: str, config: dict) -> bytes:
        import edge_tts

        cfg = get_settings()["tts"]["edge"]
        voice = config.get("voice", cfg["voice"])
        rate = config.get("rate", "+0%")
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)
