from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["knowledge"])


@router.get("/courses/{course_id}/knowledge-graph")
def get_knowledge_graph(course_id: int, db: Session = Depends(get_db)):
    return {"nodes": [], "edges": [], "layout_config": {}}
