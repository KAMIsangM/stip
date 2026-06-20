"""Content API routes — GET chapter contents, list available modals."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.service.content_service import ContentService

router = APIRouter(tags=["content"])


# ---------------------------------------------------------------------------
# GET /api/v1/chapters/{chapter_id}/contents
# ---------------------------------------------------------------------------

@router.get("/chapters/{chapter_id}/contents")
def get_chapter_contents(
    chapter_id: int,
    db: Session = Depends(get_db),
):
    """Get all content modules for a chapter."""
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
):
    """Get a single content module by ID."""
    svc = ContentService(db)
    result = svc.get_module(module_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Content module {module_id} not found")
    return result


# ---------------------------------------------------------------------------
# DELETE /api/v1/content/{module_id}
# ---------------------------------------------------------------------------

@router.delete("/content/{module_id}", status_code=204)
def delete_content_module(
    module_id: int,
    db: Session = Depends(get_db),
):
    """Delete a content module."""
    svc = ContentService(db)
    if not svc.delete_module(module_id):
        raise HTTPException(status_code=404, detail=f"Content module {module_id} not found")
