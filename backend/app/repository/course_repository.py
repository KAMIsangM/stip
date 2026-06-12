"""Course data access — HLD course_repository.py."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Chapter, Course


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        title: str,
        description: str | None = None,
        status: str = "draft",
    ) -> Course:
        course = Course(title=title, description=description, status=status)
        self._db.add(course)
        self._db.commit()
        self._db.refresh(course)
        return course

    def get_by_id(self, course_id: int) -> Course | None:
        stmt = (
            select(Course)
            .options(
                joinedload(Course.chapters),
                joinedload(Course.generation_progress),
            )
            .where(Course.id == course_id)
        )
        return self._db.scalars(stmt).unique().one_or_none()

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Course]:
        stmt = select(Course).order_by(Course.id.desc()).offset(skip).limit(limit)
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
        course = self.get_by_id(course_id)
        if course is None:
            return False
        self._db.delete(course)
        self._db.commit()
        return True

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
        chapters = self.get_chapters_by_course_id(course_id)
        for chapter in chapters:
            self._db.delete(chapter)
        self._db.commit()
        return len(chapters)
