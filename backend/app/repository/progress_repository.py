"""Generation progress data access — HLD progress_repository.py."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GenerationProgress


class ProgressRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        course_id: int,
        status: str,
        current_step: int = 0,
        total_steps: int = 0,
        error_message: str | None = None,
    ) -> GenerationProgress:
        progress = GenerationProgress(
            course_id=course_id,
            status=status,
            current_step=current_step,
            total_steps=total_steps,
            error_message=error_message,
        )
        self._db.add(progress)
        self._db.commit()
        self._db.refresh(progress)
        return progress

    def get_by_course_id(self, course_id: int) -> GenerationProgress | None:
        stmt = select(GenerationProgress).where(
            GenerationProgress.course_id == course_id
        )
        return self._db.scalars(stmt).one_or_none()

    def update(
        self,
        course_id: int,
        *,
        status: str | None = None,
        current_step: int | None = None,
        total_steps: int | None = None,
        error_message: str | None = None,
    ) -> GenerationProgress | None:
        progress = self.get_by_course_id(course_id)
        if progress is None:
            return None
        if status is not None:
            progress.status = status
        if current_step is not None:
            progress.current_step = current_step
        if total_steps is not None:
            progress.total_steps = total_steps
        if error_message is not None:
            progress.error_message = error_message
        self._db.commit()
        self._db.refresh(progress)
        return progress

    def delete(self, course_id: int) -> bool:
        progress = self.get_by_course_id(course_id)
        if progress is None:
            return False
        self._db.delete(progress)
        self._db.commit()
        return True
