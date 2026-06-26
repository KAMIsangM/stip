"""Content API routes — GET chapter contents, list available modals."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Chapter, Course, User
from app.service.content_service import ContentService

router = APIRouter(tags=["content"])


def _verify_chapter_owner(db: Session, chapter_id: int, user_id: int) -> None:
    """Verify the chapter's course belongs to the current user."""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if chapter is None:
        raise HTTPException(status_code=404, detail=f"章节 {chapter_id} 不存在")
    course = db.query(Course).filter(Course.id == chapter.course_id, Course.user_id == user_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail=f"章节 {chapter_id} 不存在")


# ---------------------------------------------------------------------------
# GET /api/v1/chapters/{chapter_id}/contents
# ---------------------------------------------------------------------------

@router.get("/chapters/{chapter_id}/contents")
def get_chapter_contents(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all content modules for a chapter."""
    _verify_chapter_owner(db, chapter_id, current_user.id)
    svc = ContentService(db)
    result = svc.get_chapter_contents(chapter_id)
    if result["modal_count"] == 0:
        return {**result, "message": "该章节尚未生成内容"}
    return result


# ---------------------------------------------------------------------------
# GET /api/v1/modals — list available modal types
# ---------------------------------------------------------------------------

@router.get("/modals")
def list_available_modals():
    """List all supported modal types."""
    return {"modals": ContentService.list_available_modals()}


# ---------------------------------------------------------------------------
# GET /api/v1/content/{module_id}
# ---------------------------------------------------------------------------

@router.get("/content/{module_id}")
def get_content_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single content module by ID."""
    svc = ContentService(db)
    result = svc.get_module(module_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Content module {module_id} not found")
    _verify_chapter_owner(db, result["chapter_id"], current_user.id)
    return result


# ---------------------------------------------------------------------------
# DELETE /api/v1/content/{module_id}
# ---------------------------------------------------------------------------

@router.delete("/content/{module_id}", status_code=204)
def delete_content_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a content module."""
    svc = ContentService(db)
    result = svc.get_module(module_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Content module {module_id} not found")
    _verify_chapter_owner(db, result["chapter_id"], current_user.id)
    if not svc.delete_module(module_id):
        raise HTTPException(status_code=404, detail=f"Content module {module_id} not found")
