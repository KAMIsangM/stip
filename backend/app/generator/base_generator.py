"""Base modal generator — strategy pattern.

All modal generators extend this base class and implement the async generate()
method. The GenerateScheduler calls generate() for each chapter-modal pair.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.provider.factory import get_llm_provider

logger = logging.getLogger(__name__)


class BaseModalGenerator(ABC):
    """Abstract base for all modal content generators."""

    modal_type: str = ""  # must be set by subclasses

    @abstractmethod
    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        """Generate modal content for a chapter.

        Args:
            chapter_id: The target chapter's database ID.
            context: A dict with keys:
                - chapter_title: str
                - knowledge_points: list of {name, type, importance}
                - course_title: str
                - course_description: str | None

        Returns:
            A dict with keys:
                - modal_type: str
                - content_json: str (JSON-serialized content)
                - file_path: str | None
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # helpers shared by subclasses
    # ------------------------------------------------------------------
    @staticmethod
    def _build_prompt(system: str, user: str) -> str:
        """Combine system and user prompts."""
        return f"{system}\n\n{user}"

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract JSON dict from LLM response (handles markdown code fences)."""
        import re

        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        src = m.group(1).strip() if m else text.strip()
        return json.loads(src)

    async def _call_llm(self, system: str, user: str) -> str:
        """Call LLM with retry/fallback and return raw response."""
        llm = get_llm_provider()
        prompt = self._build_prompt(system, user)
        logger.info("[%s] Calling LLM for chapter generation…", self.modal_type)
        try:
            result = await llm.chat_completion(prompt)
            logger.info("[%s] LLM response received (len=%d)", self.modal_type, len(result))
            return result
        except Exception as e:
            logger.error("[%s] LLM call FAILED: %s", self.modal_type, e)
            raise
