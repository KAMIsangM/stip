"""Knowledge graph service — HLD knowledge_service.py.

Provides:
- build_from_preset()   : copy preset nodes/edges into a course
- get_sorted_nodes()     : topological sort of prerequisite graph
- get_graph_for_visualization() : full node/edge/layout data for frontend
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import KnowledgeEdge, KnowledgeNode
from app.utils.graph_engine import (
    GraphCycleError,
    build_digraph,
    recommend_related_nodes,
    shortest_path,
    topological_sort_nodes,
)
from app.utils.graph_visual import build_layout_config, build_visual_data

# ---------------------------------------------------------------------------
# preset seed data path
# ---------------------------------------------------------------------------
_PRESETS_DIR = Path(__file__).resolve().parents[1] / "data" / "presets"


def _load_preset_json(preset_id: int) -> dict[str, Any] | None:
    """Load a preset JSON file by numeric id."""
    preset_path = _PRESETS_DIR / f"preset_{preset_id:03d}.json"
    if not preset_path.exists():
        return None
    with open(preset_path, encoding="utf-8") as f:
        return json.load(f)


def _list_available_presets() -> list[dict[str, Any]]:
    """List all available preset metadata (id + name + node_count)."""
    if not _PRESETS_DIR.exists():
        return []
    result: list[dict[str, Any]] = []
    for p in sorted(_PRESETS_DIR.glob("preset_*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            result.append(
                {
                    "id": data.get("id", 0),
                    "name": data.get("name", p.stem),
                    "node_count": len(data.get("nodes", [])),
                    "edge_count": len(data.get("edges", [])),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    return result


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------
def _load_preset_from_db(preset_id: int, db: Session) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]] | None:
    """Try loading a preset from DB templates (course_id=0 + preset_name matching).

    Returns (nodes, edges) or None if not found.
    """
    # Match by description containing the preset identifier
    # course_id=0 templates store preset_id in their name pattern
    # Actually: just use all course_id=0 nodes as a single template
    # Better: we don't split by preset_id in DB — we keep it simple:
    # JSON files are the primary source; DB seed is for backup.
    return None


def _copy_template_nodes_to_course(
    course_id: int,
    template_nodes: list[dict[str, Any]],
    template_edges: list[dict[str, Any]],
    db: Session,
    existing_names: set[str] | None = None,
) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
    """Copy a set of template nodes/edges into a course (idempotent).

    Skips nodes whose name already exists in the course.
    Returns the newly created (nodes, edges).
    """
    if existing_names is None:
        existing_names = {
            n.name for n in
            db.query(KnowledgeNode.name).filter(KnowledgeNode.course_id == course_id).all()
        }

    id_map: dict[int, int] = {}
    skipped = 0

    nodes: list[KnowledgeNode] = []
    for nd in template_nodes:
        if nd["name"] in existing_names:
            skipped += 1
            continue
        node = KnowledgeNode(
            course_id=course_id,
            name=nd["name"],
            type=nd.get("type", "概念"),
            importance=nd.get("importance", 0.5),
            description=nd.get("description"),
        )
        db.add(node)
        db.flush()
        id_map[nd["id"]] = node.id
        nodes.append(node)

    edges: list[KnowledgeEdge] = []
    for ed in template_edges:
        src = id_map.get(ed["source_node_id"])
        tgt = id_map.get(ed["target_node_id"])
        if src is None or tgt is None:
            continue
        edge = KnowledgeEdge(
            course_id=course_id,
            source_node_id=src,
            target_node_id=tgt,
            relation_type=ed.get("relation_type", "related"),
        )
        db.add(edge)
        edges.append(edge)

    db.flush()
    return nodes, edges


def build_from_preset(
    course_id: int,
    preset_id: int,
    db: Session,
) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
    """Copy preset nodes & edges into a course (idempotent: skips existing by name).

    First tries JSON file, then falls back to DB templates (course_id=0).
    Returns the newly created (nodes, edges).
    """
    # Collect existing node names for this course (idempotency guard)
    existing_names = {
        n.name for n in
        db.query(KnowledgeNode.name).filter(KnowledgeNode.course_id == course_id).all()
    }

    # Primary: JSON file
    preset = _load_preset_json(preset_id)
    if preset is not None:
        return _copy_template_nodes_to_course(
            course_id,
            preset.get("nodes", []),
            preset.get("edges", []),
            db,
            existing_names=existing_names,
        )

    # Fallback: DB templates (course_id=0)
    template_nodes_db = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.course_id == 0)
        .all()
    )
    template_edges_db = (
        db.query(KnowledgeEdge)
        .filter(KnowledgeEdge.course_id == 0)
        .all()
    )

    if not template_nodes_db:
        raise ValueError(f"Preset {preset_id} not found")

    template_nodes = [
        {"id": n.id, "name": n.name, "type": n.type, "importance": n.importance, "description": n.description}
        for n in template_nodes_db
    ]
    template_edges = [
        {"source_node_id": e.source_node_id, "target_node_id": e.target_node_id, "relation_type": e.relation_type}
        for e in template_edges_db
    ]

    return _copy_template_nodes_to_course(course_id, template_nodes, template_edges, db, existing_names=existing_names)


def get_sorted_nodes(
    course_id: int,
    db: Session,
) -> list[dict[str, Any]]:
    """Return topologically sorted knowledge nodes (prerequisite order).

    Raises GraphCycleError if a cycle is detected.
    """
    nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.course_id == course_id)
        .all()
    )
    edges = (
        db.query(KnowledgeEdge)
        .filter(KnowledgeEdge.course_id == course_id)
        .all()
    )

    node_dicts = [
        {"id": n.id, "name": n.name, "type": n.type, "importance": n.importance}
        for n in nodes
    ]
    edge_dicts = [
        {
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "relation_type": e.relation_type,
        }
        for e in edges
    ]

    if not node_dicts:
        return []

    g = build_digraph(node_dicts, edge_dicts)
    sorted_ids = topological_sort_nodes(g)

    node_by_id = {n["id"]: n for n in node_dicts}
    return [node_by_id[nid] for nid in sorted_ids if nid in node_by_id]


def get_graph_for_visualization(
    course_id: int,
    db: Session,
) -> dict[str, Any]:
    """Return full graph data for frontend ECharts rendering.

    Includes styled nodes, styled edges, and layout_config.
    """
    nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.course_id == course_id)
        .all()
    )
    edges = (
        db.query(KnowledgeEdge)
        .filter(KnowledgeEdge.course_id == course_id)
        .all()
    )

    styled_nodes, styled_edges = build_visual_data(nodes, edges)
    layout_config = build_layout_config(len(styled_nodes))

    return {
        "nodes": styled_nodes,
        "edges": styled_edges,
        "layout_config": layout_config,
    }


def list_presets() -> list[dict[str, Any]]:
    """Return metadata for all available preset knowledge graphs."""
    return _list_available_presets()


def get_shortest_path(
    course_id: int,
    source_id: int,
    target_id: int,
    db: Session,
) -> list[int] | None:
    """Find shortest path between two nodes in the course graph."""
    nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.course_id == course_id)
        .all()
    )
    edges = (
        db.query(KnowledgeEdge)
        .filter(KnowledgeEdge.course_id == course_id)
        .all()
    )

    node_dicts = [
        {"id": n.id, "name": n.name, "type": n.type, "importance": n.importance}
        for n in nodes
    ]
    edge_dicts = [
        {
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "relation_type": e.relation_type,
        }
        for e in edges
    ]

    g = build_digraph(node_dicts, edge_dicts)
    return shortest_path(g, source_id, target_id)


def get_recommendations(
    course_id: int,
    node_id: int,
    db: Session,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Recommend related nodes for a given node."""
    nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.course_id == course_id)
        .all()
    )
    edges = (
        db.query(KnowledgeEdge)
        .filter(KnowledgeEdge.course_id == course_id)
        .all()
    )

    node_dicts = [
        {"id": n.id, "name": n.name, "type": n.type, "importance": n.importance}
        for n in nodes
    ]
    edge_dicts = [
        {
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "relation_type": e.relation_type,
        }
        for e in edges
    ]

    g = build_digraph(node_dicts, edge_dicts)
    return recommend_related_nodes(g, node_id, top_k)
