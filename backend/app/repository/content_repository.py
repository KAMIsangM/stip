"""Content module data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContentModule


class ContentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        chapter_id: int,
        modal_type: str,
        content_json: str | None = None,
        file_path: str | None = None,
    ) -> ContentModule:
        module = ContentModule(
            chapter_id=chapter_id,
            modal_type=modal_type,
            content_json=content_json,
            file_path=file_path,
        )
        self._db.add(module)
        self._db.commit()
        self._db.refresh(module)
        return module

    def get_by_id(self, content_id: int) -> ContentModule | None:
        return self._db.get(ContentModule, content_id)

    def list_by_chapter_id(self, chapter_id: int) -> list[ContentModule]:
        stmt = (
            select(ContentModule)
            .where(ContentModule.chapter_id == chapter_id)
            .order_by(ContentModule.id)
        )
        return list(self._db.scalars(stmt).all())

    def update(
        self,
        content_id: int,
        *,
        content_json: str | None = None,
        file_path: str | None = None,
    ) -> ContentModule | None:
        module = self.get_by_id(content_id)
        if module is None:
            return None
        if content_json is not None:
            module.content_json = content_json
        if file_path is not None:
            module.file_path = file_path
        self._db.commit()
        self._db.refresh(module)
        return module

    def delete(self, content_id: int) -> bool:
        module = self.get_by_id(content_id)
        if module is None:
            return False
        self._db.delete(module)
        self._db.commit()
        return True
