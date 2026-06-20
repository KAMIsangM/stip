"""Content service — manages generated content modules.

Provides:
- get_chapter_contents() : list all content modules for a chapter
- generate_modal_content() : generate a single modal for a chapter
- delete_module() : remove a content module
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.generator.modal import _MODAL_REGISTRY
from app.repository.content_repository import ContentRepository

logger = logging.getLogger(__name__)


class ContentService:
    """Service for querying and managing generated content modules."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ContentRepository(db)

    # ------------------------------------------------------------------
    # query
    # ------------------------------------------------------------------
    def get_chapter_contents(self, chapter_id: int) -> dict[str, Any]:
        """Get all content modules for a chapter, organized by modal type."""
        modules = self._repo.list_by_chapter_id(chapter_id)

        by_modal: dict[str, list[dict[str, Any]]] = {}
        for m in modules:
            item = {
                "id": m.id,
                "chapter_id": m.chapter_id,
                "modal_type": m.modal_type,
                "content_json": m.content_json,
                "file_path": m.file_path,
            }
            by_modal.setdefault(m.modal_type, []).append(item)

        return {
            "chapter_id": chapter_id,
            "modal_count": len(modules),
            "content_modules": [item for items in by_modal.values() for item in items],
            "by_modal": {k: v for k, v in by_modal.items()},
        }

    def get_module(self, module_id: int) -> dict[str, Any] | None:
        """Get a single content module by ID."""
        module = self._repo.get_by_id(module_id)
        if module is None:
            return None
        return {
            "id": module.id,
            "chapter_id": module.chapter_id,
            "modal_type": module.modal_type,
            "content_json": module.content_json,
            "file_path": module.file_path,
        }

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------
    async def generate_modal_content(
        self,
        chapter_id: int,
        modal_type: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a single modal content for a chapter.

        Args:
            chapter_id: target chapter ID
            modal_type: one of text/quiz/ppt/mindmap/audio/interactive_html
            context: {chapter_title, knowledge_points, course_title, ...}

        Returns:
            The persisted content module dict
        """
        generator_cls = _MODAL_REGISTRY.get(modal_type)
        if generator_cls is None:
            raise ValueError(f"Unknown modal type: {modal_type}")

        generator = generator_cls()
        result = await generator.generate(chapter_id, context)

        module = self._repo.create(
            chapter_id=chapter_id,
            modal_type=result["modal_type"],
            content_json=result.get("content_json"),
            file_path=result.get("file_path"),
        )

        logger.info(
            "[ContentService] Generated %s for chapter %d → module %d",
            modal_type, chapter_id, module.id,
        )

        return {
            "id": module.id,
            "chapter_id": module.chapter_id,
            "modal_type": module.modal_type,
            "content_json": module.content_json,
            "file_path": module.file_path,
        }

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------
    def delete_module(self, module_id: int) -> bool:
        """Delete a content module."""
        return self._repo.delete(module_id)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def list_available_modals() -> list[str]:
        """List all supported modal types."""
        return sorted(_MODAL_REGISTRY.keys())
