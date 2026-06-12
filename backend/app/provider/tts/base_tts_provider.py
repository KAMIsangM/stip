from abc import ABC, abstractmethod


class BaseTTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, config: dict) -> bytes:
        raise NotImplementedError
