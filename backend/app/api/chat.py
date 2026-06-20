"""Chat API — AI Q&A for course content with conversation history."""

import json
import logging

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Chapter, ChatMessage, ContentModule, Course
from app.provider.llm.deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/courses", tags=["chat"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    chapter_id: int | None = Field(default=None, description="当前章节 ID，用于注入上下文")
    message: str = Field(..., min_length=1, description="用户提问内容")


class ChatMessageOut(BaseModel):
    id: int
    course_id: int
    chapter_id: int | None
    role: str
    content: str
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat(sep=" ")
        return v


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageOut]


class ChatResponse(BaseModel):
    reply: ChatMessageOut
    user_message: ChatMessageOut


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_course_context(db: Session, course_id: int, chapter_id: int | None) -> str:
    """Assemble course outline + current chapter content as system context."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return ""

    parts: list[str] = []

    # Course title and description
    parts.append(f"你是一位课程助教 AI，正在帮助学生学习课程：「{course.title}」。")
    if course.description:
        parts.append(f"课程简介：{course.description}")

    # Course outline (all chapter titles)
    chapters = db.query(Chapter).filter(Chapter.course_id == course_id).order_by(Chapter.order).all()
    if chapters:
        outline_lines = ["\n## 课程大纲"]
        for ch in chapters:
            marker = " ← 当前章节" if (chapter_id and ch.id == chapter_id) else ""
            outline_lines.append(f"- 第{ch.order}章：{ch.title}{marker}")
            # Include knowledge point names
            if ch.knowledge_node_ids:
                try:
                    node_ids = json.loads(ch.knowledge_node_ids)
                    if isinstance(node_ids, list):
                        from app.models import KnowledgeNode
                        nodes = db.query(KnowledgeNode).filter(
                            KnowledgeNode.id.in_(node_ids)
                        ).all()
                        if nodes:
                            kp_names = [n.name for n in nodes]
                            outline_lines.append(f"  知识点：{'、'.join(kp_names)}")
                except (json.JSONDecodeError, TypeError):
                    pass
        parts.append("\n".join(outline_lines))

    # Current chapter content summary
    if chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            parts.append(f"\n## 当前章节内容：第{chapter.order}章「{chapter.title}」")
            content_modules = (
                db.query(ContentModule).filter(ContentModule.chapter_id == chapter_id).all()
            )
            for cm in content_modules:
                if cm.content_json and cm.modal_type in ("text", "ppt"):
                    try:
                        data = json.loads(cm.content_json)
                        if cm.modal_type == "text":
                            sections = data.get("sections", [])
                            for sec in sections[:3]:  # limit to first 3 sections
                                heading = sec.get("heading", "")
                                paras = sec.get("paragraphs", [])
                                if heading:
                                    parts.append(f"\n### {heading}")
                                for p in paras[:2]:  # limit paragraphs
                                    parts.append(p[:500])  # limit length
                        elif cm.modal_type == "ppt":
                            slides = data.get("slides", [])
                            for slide in slides[:5]:
                                title = slide.get("title", "")
                                content = slide.get("content", "")
                                if title:
                                    parts.append(f"- 幻灯片：{title}")
                                if content:
                                    parts.append(f"  {str(content)[:300]}")
                    except (json.JSONDecodeError, TypeError):
                        pass

    return "\n".join(parts)


def _get_llm():
    return DeepSeekProvider()


# ---------------------------------------------------------------------------
# GET  /courses/{course_id}/chat  — fetch chat history
# ---------------------------------------------------------------------------


@router.get("/{course_id}/chat", response_model=ChatHistoryOut)
def get_chat_history(
    course_id: int,
    chapter_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return recent chat messages for a course (optionally filtered by chapter)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    q = (
        db.query(ChatMessage)
        .filter(ChatMessage.course_id == course_id)
        .order_by(ChatMessage.created_at.desc())
    )
    if chapter_id is not None:
        q = q.filter(ChatMessage.chapter_id == chapter_id)
    rows = q.limit(limit).all()
    # Return in chronological order
    rows.reverse()
    return ChatHistoryOut(messages=[ChatMessageOut.model_validate(r) for r in rows])


# ---------------------------------------------------------------------------
# POST /courses/{course_id}/chat  — send a message & get AI reply
# ---------------------------------------------------------------------------


@router.post("/{course_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    course_id: int,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    """Send a question and get an AI reply contextualized to the course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    chapter_id = req.chapter_id
    if chapter_id:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter or chapter.course_id != course_id:
            raise HTTPException(status_code=404, detail="章节不存在或不属于此课程")

    # 1. Save user message
    user_msg = ChatMessage(
        course_id=course_id,
        chapter_id=chapter_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Build conversation context
    system_context = _build_course_context(db, course_id, chapter_id)

    # 3. Fetch recent history (last 20 messages) for continuity
    recent = (
        db.query(ChatMessage)
        .filter(ChatMessage.course_id == course_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    recent.reverse()  # chronological

    # 4. Compose messages for LLM
    llm_messages: list[dict] = []
    if system_context:
        llm_messages.append({"role": "system", "content": system_context})
    for m in recent:
        llm_messages.append({"role": m.role, "content": m.content})

    # 5. Call LLM
    llm = _get_llm()
    try:
        reply_text = await llm.chat_completion(prompt="", messages=llm_messages)
    except Exception as e:
        logger.error("LLM chat failed for course %d: %s", course_id, e)
        raise HTTPException(status_code=502, detail=f"AI 回答生成失败: {str(e)}")

    # 6. Save assistant reply
    assistant_msg = ChatMessage(
        course_id=course_id,
        chapter_id=chapter_id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        reply=ChatMessageOut.model_validate(assistant_msg),
        user_message=ChatMessageOut.model_validate(user_msg),
    )


# ---------------------------------------------------------------------------
# DELETE /courses/{course_id}/chat  — clear chat history
# ---------------------------------------------------------------------------


class ClearChatResponse(BaseModel):
    deleted_count: int


@router.delete("/{course_id}/chat", response_model=ClearChatResponse)
def clear_chat_history(
    course_id: int,
    chapter_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Delete chat messages for a course (optionally filtered by chapter)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    q = db.query(ChatMessage).filter(ChatMessage.course_id == course_id)
    if chapter_id is not None:
        q = q.filter(ChatMessage.chapter_id == chapter_id)

    deleted_count = q.delete(synchronize_session="fetch")
    db.commit()

    return ClearChatResponse(deleted_count=deleted_count)
