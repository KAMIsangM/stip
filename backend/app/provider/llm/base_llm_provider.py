from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self, prompt: str, response_format: str = "text"
    ) -> str:
        raise NotImplementedError
