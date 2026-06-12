"""Base modal generator — strategy pattern."""

from abc import ABC, abstractmethod


class BaseModalGenerator(ABC):
    @abstractmethod
    async def generate(self, chapter_id: int, context: dict) -> dict:
        raise NotImplementedError
