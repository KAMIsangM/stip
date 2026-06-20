from datetime import datetime, timezone, timedelta

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# China Standard Time (UTC+8)
CST = timezone(timedelta(hours=8))


def _now_cst() -> datetime:
    """Return current time in China Standard Time (UTC+8)."""
    return datetime.now(CST).replace(tzinfo=None)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey("chapters.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now_cst
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now_cst
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now_cst, onupdate=_now_cst
    )

    chapters: Mapped[list["Chapter"]] = relationship(back_populates="course")
    knowledge_nodes: Mapped[list["KnowledgeNode"]] = relationship(back_populates="course")
    knowledge_edges: Mapped[list["KnowledgeEdge"]] = relationship(back_populates="course")
    generation_progress: Mapped["GenerationProgress | None"] = relationship(
        back_populates="course", uselist=False
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    knowledge_node_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped["Course"] = relationship(back_populates="chapters")
    content_modules: Mapped[list["ContentModule"]] = relationship(back_populates="chapter")


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    importance: Mapped[float] = mapped_column(nullable=False, default=0.5)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped["Course"] = relationship(back_populates="knowledge_nodes")


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    source_node_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)

    course: Mapped["Course"] = relationship(back_populates="knowledge_edges")


class ContentModule(Base):
    __tablename__ = "content_modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), nullable=False)
    modal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    chapter: Mapped["Chapter"] = relationship(back_populates="content_modules")


class GenerationProgress(Base):
    __tablename__ = "generation_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_now_cst, onupdate=_now_cst
    )

    course: Mapped["Course"] = relationship(back_populates="generation_progress")
