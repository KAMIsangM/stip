"""Knowledge graph API — GET /courses/{id}/knowledge-graph + CRUD for nodes/edges."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Course, KnowledgeEdge, KnowledgeNode, User
from app.models.enums import NodeType, RelationType
from app.service.knowledge_service import (
    build_from_preset,
    delete_preset,
    get_graph_for_visualization,
    get_recommendations,
    get_shortest_path,
    get_sorted_nodes,
    list_presets,
    save_as_preset,
)
from app.utils.graph_engine import GraphCycleError

router = APIRouter(tags=["knowledge"])


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _verify_course_owner(db: Session, course_id: int, user_id: int) -> None:
    """Verify the course exists and belongs to the current user."""
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail=f"课程 {course_id} 不存在")


# ---------------------------------------------------------------------------
# request / response schemas
# ---------------------------------------------------------------------------


class NodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default=NodeType.概念.value)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    description: str | None = None


class NodeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    type: str | None = None
    importance: float | None = Field(None, ge=0.0, le=1.0)
    description: str | None = None


class EdgeCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    relation_type: str = Field(default=RelationType.RELATED.value)


class EdgeUpdate(BaseModel):
    relation_type: str | None = None


class PresetApplyRequest(BaseModel):
    preset_id: int


class PresetSaveRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


# ---------------------------------------------------------------------------
# knowledge-graph read
# ---------------------------------------------------------------------------


@router.get("/courses/{course_id}/knowledge-graph")
def get_knowledge_graph(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return full knowledge graph for visualization."""
    _verify_course_owner(db, course_id, current_user.id)
    return get_graph_for_visualization(course_id, db)


@router.get("/courses/{course_id}/knowledge-graph/sorted")
def get_sorted_knowledge_nodes(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return topologically sorted knowledge nodes (prerequisite order)."""
    _verify_course_owner(db, course_id, current_user.id)
    try:
        return {"nodes": get_sorted_nodes(course_id, db)}
    except GraphCycleError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/courses/{course_id}/knowledge-graph/shortest-path")
def find_shortest_path(
    course_id: int,
    source: int = Query(...),
    target: int = Query(...),
    weighted: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find shortest path between two knowledge nodes.

    Set *weighted* to False for plain BFS; True (default) enables
    edge-type weights and node-importance bias.
    """
    _verify_course_owner(db, course_id, current_user.id)
    path = get_shortest_path(course_id, source, target, db, weighted=weighted)
    if path is None:
        return {"path": None, "message": "No path found between the nodes"}
    return {"path": path}


@router.get("/courses/{course_id}/knowledge-graph/recommendations")
def recommend_nodes(
    course_id: int,
    node_id: int = Query(...),
    top_k: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recommend related nodes for a given node."""
    _verify_course_owner(db, course_id, current_user.id)
    return {"recommendations": get_recommendations(course_id, node_id, db, top_k=top_k)}


# ---------------------------------------------------------------------------
# presets
# ---------------------------------------------------------------------------


@router.get("/knowledge-graph/presets")
def get_presets():
    """List available preset knowledge graphs."""
    return {"presets": list_presets()}


@router.delete("/knowledge-graph/presets/{preset_id}", status_code=204)
def delete_preset_endpoint(preset_id: int):
    """Delete a preset knowledge graph JSON file."""
    try:
        success = delete_preset(preset_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"预设 {preset_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除预设失败: {str(e)}")


@router.post("/courses/{course_id}/knowledge-graph/apply-preset")
def apply_preset(
    course_id: int,
    body: PresetApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply a preset knowledge graph to a course."""
    _verify_course_owner(db, course_id, current_user.id)
    try:
        nodes, edges = build_from_preset(course_id, body.preset_id, db)
        db.commit()
        return {
            "message": "Preset applied",
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/knowledge-graph/save-preset", status_code=201)
def save_preset(
    course_id: int,
    body: PresetSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save the current course knowledge graph as a new preset."""
    _verify_course_owner(db, course_id, current_user.id)
    try:
        result = save_as_preset(
            course_id=course_id,
            name=body.name,
            description=body.description or "",
            db=db,
        )
        return {
            "message": "Preset saved successfully",
            "preset": result,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# node CRUD
# ---------------------------------------------------------------------------


@router.post("/courses/{course_id}/knowledge-graph/nodes", status_code=201)
def create_knowledge_node(
    course_id: int,
    body: NodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge node for a course."""
    _verify_course_owner(db, course_id, current_user.id)
    # validate type
    if body.type not in {e.value for e in NodeType}:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid node type '{body.type}'. Valid types: {[e.value for e in NodeType]}",
        )

    node = KnowledgeNode(
        course_id=course_id,
        name=body.name,
        type=body.type,
        importance=body.importance,
        description=body.description,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return {
        "id": node.id,
        "course_id": node.course_id,
        "name": node.name,
        "type": node.type,
        "importance": node.importance,
        "description": node.description,
    }


@router.put("/courses/{course_id}/knowledge-graph/nodes/{node_id}")
def update_knowledge_node(
    course_id: int,
    node_id: int,
    body: NodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing knowledge node."""
    _verify_course_owner(db, course_id, current_user.id)
    node = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.id == node_id,
            KnowledgeNode.course_id == course_id,
        )
        .first()
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Knowledge node not found")

    if body.name is not None:
        node.name = body.name
    if body.type is not None:
        if body.type not in {e.value for e in NodeType}:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid node type '{body.type}'",
            )
        node.type = body.type
    if body.importance is not None:
        node.importance = body.importance
    if body.description is not None:
        node.description = body.description

    db.commit()
    db.refresh(node)
    return {
        "id": node.id,
        "course_id": node.course_id,
        "name": node.name,
        "type": node.type,
        "importance": node.importance,
        "description": node.description,
    }


@router.delete("/courses/{course_id}/knowledge-graph/nodes/{node_id}", status_code=204)
def delete_knowledge_node(
    course_id: int,
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge node. Connected edges are deleted first (FK ondelete also set)."""
    _verify_course_owner(db, course_id, current_user.id)
    node = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.id == node_id,
            KnowledgeNode.course_id == course_id,
        )
        .first()
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Knowledge node not found")

    # Delete connected edges (belt-and-suspenders: FK ondelete also configured)
    db.query(KnowledgeEdge).filter(
        (KnowledgeEdge.source_node_id == node_id)
        | (KnowledgeEdge.target_node_id == node_id),
        KnowledgeEdge.course_id == course_id,
    ).delete(synchronize_session="fetch")

    db.delete(node)
    db.commit()


# ---------------------------------------------------------------------------
# edge CRUD
# ---------------------------------------------------------------------------


@router.post("/courses/{course_id}/knowledge-graph/edges", status_code=201)
def create_knowledge_edge(
    course_id: int,
    body: EdgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge edge between two nodes."""
    _verify_course_owner(db, course_id, current_user.id)
    # validate relation_type
    if body.relation_type not in {e.value for e in RelationType}:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid relation type '{body.relation_type}'. Valid: {[e.value for e in RelationType]}",
        )

    # validate both nodes exist and belong to this course
    src_node = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.id == body.source_node_id,
            KnowledgeNode.course_id == course_id,
        )
        .first()
    )
    tgt_node = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.id == body.target_node_id,
            KnowledgeNode.course_id == course_id,
        )
        .first()
    )
    if src_node is None:
        raise HTTPException(status_code=404, detail="Source node not found")
    if tgt_node is None:
        raise HTTPException(status_code=404, detail="Target node not found")

    # check for duplicate edge
    existing = (
        db.query(KnowledgeEdge)
        .filter(
            KnowledgeEdge.course_id == course_id,
            KnowledgeEdge.source_node_id == body.source_node_id,
            KnowledgeEdge.target_node_id == body.target_node_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Edge already exists between these nodes")

    edge = KnowledgeEdge(
        course_id=course_id,
        source_node_id=body.source_node_id,
        target_node_id=body.target_node_id,
        relation_type=body.relation_type,
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return {
        "id": edge.id,
        "course_id": edge.course_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "relation_type": edge.relation_type,
    }


@router.put("/courses/{course_id}/knowledge-graph/edges/{edge_id}")
def update_knowledge_edge(
    course_id: int,
    edge_id: int,
    body: EdgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing knowledge edge."""
    _verify_course_owner(db, course_id, current_user.id)
    edge = (
        db.query(KnowledgeEdge)
        .filter(
            KnowledgeEdge.id == edge_id,
            KnowledgeEdge.course_id == course_id,
        )
        .first()
    )
    if edge is None:
        raise HTTPException(status_code=404, detail="Knowledge edge not found")

    if body.relation_type is not None:
        if body.relation_type not in {e.value for e in RelationType}:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid relation type '{body.relation_type}'",
            )
        edge.relation_type = body.relation_type

    db.commit()
    db.refresh(edge)
    return {
        "id": edge.id,
        "course_id": edge.course_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "relation_type": edge.relation_type,
    }


@router.delete("/courses/{course_id}/knowledge-graph/edges/{edge_id}", status_code=204)
def delete_knowledge_edge(
    course_id: int,
    edge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge edge."""
    _verify_course_owner(db, course_id, current_user.id)
    edge = (
        db.query(KnowledgeEdge)
        .filter(
            KnowledgeEdge.id == edge_id,
            KnowledgeEdge.course_id == course_id,
        )
        .first()
    )
    if edge is None:
        raise HTTPException(status_code=404, detail="Knowledge edge not found")

    db.delete(edge)
    db.commit()
