"""Course data access — HLD course_repository.py."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Chapter, Course


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        status: str = "draft",
    ) -> Course:
        course = Course(user_id=user_id, title=title, description=description, status=status)
        self._db.add(course)
        self._db.commit()
        self._db.refresh(course)
        return course

    def get_by_id(self, course_id: int, user_id: int | None = None) -> Course | None:
        stmt = (
            select(Course)
            .options(
                joinedload(Course.chapters),
                joinedload(Course.generation_progress),
            )
            .where(Course.id == course_id)
        )
        if user_id is not None:
            stmt = stmt.where(Course.user_id == user_id)
        return self._db.scalars(stmt).unique().one_or_none()

    def get_by_title(self, title: str, user_id: int | None = None) -> Course | None:
        """Find a course by exact title match (case-insensitive), optionally filtered by user."""
        from sqlalchemy import func

        stmt = select(Course).where(func.lower(Course.title) == title.lower())
        if user_id is not None:
            stmt = stmt.where(Course.user_id == user_id)
        return self._db.scalars(stmt).one_or_none()

    def list_all(self, skip: int = 0, limit: int = 100, user_id: int | None = None) -> list[Course]:
        stmt = select(Course).order_by(Course.id.desc()).offset(skip).limit(limit)
        if user_id is not None:
            stmt = stmt.where(Course.user_id == user_id)
        return list(self._db.scalars(stmt).all())

    def update(
        self,
        course_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Course | None:
        course = self.get_by_id(course_id)
        if course is None:
            return None
        if title is not None:
            course.title = title
        if description is not None:
            course.description = description
        if status is not None:
            course.status = status
        self._db.commit()
        self._db.refresh(course)
        return course

    def delete(self, course_id: int) -> bool:
        import time

        course = self.get_by_id(course_id)
        if course is None:
            return False
        # 手动级联删除子记录，避免外键约束问题
        self.delete_chapters_by_course_id(course_id)
        self._db.delete(course)
        # SQLite 并发写时可能遇到锁，重试 3 次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._db.commit()
                return True
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    self._db.rollback()
                else:
                    self._db.rollback()
                    raise
        return False

    def create_chapter(
        self,
        course_id: int,
        title: str,
        order: int,
        knowledge_node_ids: str | None = None,
    ) -> Chapter:
        chapter = Chapter(
            course_id=course_id,
            title=title,
            order=order,
            knowledge_node_ids=knowledge_node_ids,
        )
        self._db.add(chapter)
        self._db.commit()
        self._db.refresh(chapter)
        return chapter

    def get_chapters_by_course_id(self, course_id: int) -> list[Chapter]:
        stmt = (
            select(Chapter)
            .where(Chapter.course_id == course_id)
            .order_by(Chapter.order)
        )
        return list(self._db.scalars(stmt).all())

    def delete_chapters_by_course_id(self, course_id: int) -> int:
        import time

        chapters = self.get_chapters_by_course_id(course_id)
        for chapter in chapters:
            self._db.delete(chapter)
        # SQLite 并发写时可能遇到锁，重试 3 次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._db.commit()
                return len(chapters)
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    self._db.rollback()
                else:
                    self._db.rollback()
                    raise
        return 0
