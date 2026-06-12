"""Aliyun ASR provider — MVP primary (config asr.provider=aliyun)."""

from collections.abc import AsyncGenerator, Generator

from app.provider.asr.base_asr_provider import BaseASRProvider


class AliyunASRProvider(BaseASRProvider):
    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        # TODO: WebSocket streaming integration
        if False:
            yield ""
        return
