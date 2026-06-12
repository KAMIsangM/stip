from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator


class BaseASRProvider(ABC):
    @abstractmethod
    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield  # pragma: no cover
