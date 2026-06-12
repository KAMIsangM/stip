"""Tencent ASR provider — MVP fallback (config asr.fallback=tencent)."""

from collections.abc import AsyncGenerator, Generator

from app.provider.asr.base_asr_provider import BaseASRProvider


class TencentASRProvider(BaseASRProvider):
    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        # TODO: Tencent ASR WebSocket integration
        if False:
            yield ""
        return
