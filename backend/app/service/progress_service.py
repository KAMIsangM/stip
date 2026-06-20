"""Generation progress service — HLD progress_service.py.

Manages generation progress tracking and provides WebSocket-ready progress data.
- init_progress()     : create a new progress record for a course
- update_progress()   : update step/status during generation
- get_progress()      : query current progress
- complete_progress() : mark generation as done
- fail_progress()     : mark generation as failed with error message
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.repository.progress_repository import ProgressRepository

logger = logging.getLogger(__name__)

# Step name mapping for human-readable labels
_STEP_NAMES: dict[int, str] = {
    0: "等待开始",
    1: "加载预设知识图谱",
    2: "LLM 生成课程大纲",
    3: "持久化章节与知识点",
    4: "生成沉浸式文本",
    5: "生成测验题目",
    6: "生成 PPT 课件",
    7: "生成思维导图",
    8: "生成音频课程",
    9: "生成互动教材",
    10: "打包完成",
}


class ProgressService:
    """Service for tracking generation progress."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ProgressRepository(db)

    # -------------------------------------------------------------------
    # init
    # -------------------------------------------------------------------
    def init_progress(
        self,
        course_id: int,
        total_steps: int = 10,
        status: str = "pending",
    ) -> dict[str, Any]:
        """Initialize a progress tracker for a course generation task."""
        existing = self._repo.get_by_course_id(course_id)
        if existing:
            self._repo.update(
                course_id,
                status=status,
                current_step=0,
                total_steps=total_steps,
                error_message=None,
            )
        else:
            self._repo.create(
                course_id=course_id,
                status=status,
                current_step=0,
                total_steps=total_steps,
            )
        return self.get_progress(course_id)

    # -------------------------------------------------------------------
    # update
    # -------------------------------------------------------------------
    def update_progress(
        self,
        course_id: int,
        *,
        current_step: int | None = None,
        status: str | None = None,
        total_steps: int | None = None,
        step_name: str | None = None,
    ) -> dict[str, Any]:
        """Update progress step and/or status."""
        progress = self._repo.update(
            course_id,
            current_step=current_step,
            status=status,
            total_steps=total_steps,
        )
        if progress is None:
            logger.warning("No progress record for course %d", course_id)
            return self.init_progress(course_id)

        return self._to_dict(progress, step_name)

    # -------------------------------------------------------------------
    # get
    # -------------------------------------------------------------------
    def get_progress(self, course_id: int, step_name: str | None = None) -> dict[str, Any]:
        """Get current progress for a course."""
        progress = self._repo.get_by_course_id(course_id)
        if progress is None:
            return {
                "course_id": course_id,
                "status": "not_started",
                "current_step": 0,
                "total_steps": 0,
                "step_name": "未开始",
                "percentage": 0,
                "error_message": None,
            }
        return self._to_dict(progress, step_name)

    # -------------------------------------------------------------------
    # complete / fail
    # -------------------------------------------------------------------
    def complete_progress(self, course_id: int) -> dict[str, Any]:
        """Mark generation as successfully completed."""
        progress = self._repo.get_by_course_id(course_id)
        if progress is None:
            logger.warning("No progress record for course %d", course_id)
            return self.init_progress(course_id, status="done")

        self._repo.update(
            course_id,
            status="done",
            current_step=progress.total_steps,
        )
        return self.get_progress(course_id, step_name="完成")

    def fail_progress(self, course_id: int, error_message: str) -> dict[str, Any]:
        """Mark generation as failed with error."""
        self._repo.update(
            course_id,
            status="failed",
            error_message=error_message,
        )
        return self.get_progress(course_id, step_name="失败")

    # -------------------------------------------------------------------
    # helper
    # -------------------------------------------------------------------
    def _to_dict(self, progress: Any, step_name: str | None = None) -> dict[str, Any]:
        total = progress.total_steps or 1
        current = progress.current_step or 0
        pct = round((current / total) * 100) if total > 0 else 0
        name = step_name or _STEP_NAMES.get(current, f"步骤 {current}")

        return {
            "course_id": progress.course_id,
            "status": progress.status,
            "current_step": current,
            "total_steps": total,
            "step_name": name,
            "percentage": pct,
            "error_message": progress.error_message,
        }
