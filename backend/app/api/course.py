from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["courses"])


class CourseCreateRequest(BaseModel):
    title: str
    description: str | None = None
    preset_id: int | None = None


@router.post("/courses")
def create_course(body: CourseCreateRequest, db: Session = Depends(get_db)):
    # TODO: CourseService.create
    return {"course_id": 0, "title": body.title, "status": "draft", "chapters": []}


@router.get("/courses")
def list_courses(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    return {"total": 0, "list": [], "page": page, "page_size": page_size}


@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    return {
        "course_info": {"id": course_id, "title": "", "status": "draft"},
        "chapters": [],
        "generation_progress": None,
    }


@router.post("/courses/{course_id}/generate")
def trigger_generate(course_id: int, db: Session = Depends(get_db)):
    return {"task_id": 0, "status": "pending", "estimated_time": 60}
