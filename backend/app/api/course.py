"""Course API routes — F001 Smart Course Generation.

POST   /api/v1/courses                    — Create course + generate syllabus
GET    /api/v1/courses                    — List courses (paginated, filterable)
GET    /api/v1/courses/{course_id}        — Get course detail
DELETE /api/v1/courses/{course_id}        — Delete course + all related data
POST   /api/v1/courses/{course_id}/generate — Trigger multi-modal content generation (F002)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.generator.generate_scheduler import GenerateScheduler
from app.models import User
from app.repository.course_repository import CourseRepository
from app.service.course_service import CourseService
from app.service.progress_service import ProgressService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["courses"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="课程标题")
    description: str | None = Field(None, description="课程描述")
    preset_id: int | None = Field(None, description="预置知识图谱 ID，可选")


class CourseCreateResponse(BaseModel):
    course_info: dict[str, Any]
    chapters: list[dict[str, Any]]
    generation_progress: dict[str, Any] | None


class CourseListResponse(BaseModel):
    total: int
    list: list[dict[str, Any]]
    page: int
    page_size: int


class CourseDetailResponse(BaseModel):
    course_info: dict[str, Any]
    chapters: list[dict[str, Any]]
    generation_progress: dict[str, Any] | None


class GenerateResponse(BaseModel):
    task_id: int
    status: str
    estimated_time: int


# ---------------------------------------------------------------------------
# POST /api/v1/courses — Create course + generate syllabus
# ---------------------------------------------------------------------------

@router.post("/courses", response_model=dict)
async def create_course(
    body: CourseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new course and generate syllabus via LLM (synchronous).

    The syllabus includes chapters, knowledge points with types/importance,
    and prerequisite relationships. If preset_id is provided, the preset
    knowledge graph is seeded into the course before syllabus generation.
    """
    try:
        service = CourseService(db)
        result = await service.create_course(
            title=body.title,
            description=body.description,
            preset_id=body.preset_id,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.exception("Failed to create course")
        raise HTTPException(status_code=500, detail=f"课程创建失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /api/v1/courses — List courses
# ---------------------------------------------------------------------------

@router.get("/courses", response_model=dict)
def list_courses(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List courses with pagination and optional filtering.

    - page: page number (1-indexed)
    - page_size: items per page (default 10)
    - status: filter by course status (draft/outlined/generating/ready/error)
    - keyword: search in title and description
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于 0")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="每页数量必须在 1-100 之间")

    try:
        service = CourseService(db)
        result = service.list_courses(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword,
            user_id=current_user.id,
        )
        return result
    except Exception as e:
        logger.exception("Failed to list courses")
        raise HTTPException(status_code=500, detail=f"查询课程列表失败: {str(e)}")


# ---------------------------------------------------------------------------
# GET /api/v1/courses/{course_id} — Get course detail
# ---------------------------------------------------------------------------

@router.get("/courses/{course_id}", response_model=dict)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full course detail including chapters and generation progress."""
    try:
        # Verify course belongs to user
        repo = CourseRepository(db)
        course = repo.get_by_id(course_id, user_id=current_user.id)
        if course is None:
            raise LookupError(f"Course {course_id} not found")
        service = CourseService(db)
        result = await service.get_course_detail(course_id)
        return result
    except LookupError:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")
    except Exception as e:
        logger.exception("Failed to get course detail")
        raise HTTPException(status_code=500, detail=f"查询课程详情失败: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE /api/v1/courses/{course_id} — Delete course
# ---------------------------------------------------------------------------

@router.delete("/courses/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a course and all its related data (chapters, knowledge nodes/edges,
    content modules, progress records).

    This is a cascading delete — everything tied to this course will be removed.
    """
    try:
        repo = CourseRepository(db)
        # Verify ownership
        course = repo.get_by_id(course_id, user_id=current_user.id)
        if course is None:
            raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")
        success = repo.delete(course_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete course")
        raise HTTPException(status_code=500, detail=f"删除课程失败: {str(e)}")


# ---------------------------------------------------------------------------
# POST /api/v1/courses/{course_id}/generate — Trigger content generation
# ---------------------------------------------------------------------------

@router.post("/courses/{course_id}/generate", response_model=dict)
async def trigger_generate(
    course_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger multi-modal content generation for a course (F002).

    This endpoint starts the async generation pipeline and returns immediately.
    Progress can be tracked via WebSocket or polling GET /courses/{course_id}.
    """
    # Verify ownership
    repo = CourseRepository(db)
    course = repo.get_by_id(course_id, user_id=current_user.id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")

    # Verify course exists and get detail
    service = CourseService(db)
    try:
        detail = await service.get_course_detail(course_id)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")

    course_status = detail["course_info"]["status"]
    if course_status not in ("outlined", "ready"):
        raise HTTPException(
            status_code=400,
            detail=f"课程状态为 '{course_status}'，需要先完成大纲生成（status=outlined）",
        )

    # Build generation context and launch async scheduler
    chapter_count = len(detail["chapters"])
    course_title = detail["course_info"]["title"]
    course_description = detail["course_info"].get("description")

    # Launch generation as background task
    async def _run_generation():
        scheduler = GenerateScheduler(db, course_id)
        await scheduler.run(
            chapters=detail["chapters"],
            modal_types=None,  # generate all modal types
            course_title=course_title,
            course_description=course_description,
        )
        # Update course status after generation
        course_repo = CourseRepository(db)
        course_repo.update(course_id, status="ready")

    background_tasks.add_task(_run_generation)

    return {
        "task_id": course_id,
        "status": "running",
        "estimated_time": max(30, chapter_count * 15),
        "total_steps": chapter_count * 6,  # 6 modal types per chapter
        "message": "内容生成任务已提交，请通过 WebSocket 或轮询查看进度",
    }


# ---------------------------------------------------------------------------
# GET /api/v1/courses/{course_id}/progress — Poll progress
# ---------------------------------------------------------------------------

@router.get("/courses/{course_id}/progress")
def get_progress(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll current generation progress for a course."""
    # Verify ownership
    repo = CourseRepository(db)
    course = repo.get_by_id(course_id, user_id=current_user.id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")
    svc = ProgressService(db)
    return svc.get_progress(course_id)


# ---------------------------------------------------------------------------
# WebSocket /ws/v1/generation/{course_id} — Real-time progress push
# ---------------------------------------------------------------------------

@router.websocket("/ws/generation/{course_id}")
async def ws_generation_progress(
    websocket: WebSocket,
    course_id: int,
):
    """WebSocket endpoint for real-time generation progress updates.

    The server pushes progress updates every 1 second while the client
    is connected. When the generation completes or fails, a final message
    is sent and the connection is closed.
    """
    await websocket.accept()
    logger.info("WebSocket connected for course %d", course_id)

    import asyncio

    try:
        while True:
            # Create a new DB session per poll (WebSocket is long-lived)
            db_session = next(get_db())
            try:
                svc = ProgressService(db_session)
                progress = svc.get_progress(course_id)
                await websocket.send_json(progress)

                # If done or failed, send final update and close
                if progress["status"] in ("done", "failed"):
                    await websocket.send_json({
                        **progress,
                        "message": "Generation completed" if progress["status"] == "done" else "Generation failed",
                    })
                    break
            finally:
                db_session.close()

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for course %d", course_id)
    except Exception as e:
        logger.exception("WebSocket error for course %d", course_id)
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
