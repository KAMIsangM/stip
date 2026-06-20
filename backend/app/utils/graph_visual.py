"""Graph visual style & layout_config processor — HLD GraphVisualProcessor.

Consumes KnowledgeNode / KnowledgeEdge ORM lists and produces:
- node style dicts (color, size, label)
- layout_config for ECharts / frontend consumption
"""

from __future__ import annotations

from typing import Any

from app.models.enums import NodeType, RelationType

# ---------------------------------------------------------------------------
# colour / size mappings
# ---------------------------------------------------------------------------
_NODE_COLORS: dict[str, str] = {
    NodeType.概念.value: "#5470c6",  # blue
    NodeType.技能.value: "#91cc75",  # green
    NodeType.记忆.value: "#fac858",  # yellow
    NodeType.实践.value: "#ee6666",  # red
    NodeType.综合.value: "#fc8452",  # orange
}
_DEFAULT_COLOR = "#999"  # grey fallback

_EDGE_COLORS: dict[str, str] = {
    RelationType.PREREQUISITE.value: "#ee6666",  # red
    RelationType.CONTAINS.value: "#73c0de",  # light-blue
    RelationType.CAUSAL.value: "#3ba272",  # dark-green
    RelationType.RELATED.value: "#9a60b4",  # purple
}
_DEFAULT_EDGE_COLOR = "#aaa"

# size range by importance (0…1) → symbolSize 16…56
_SIZE_MIN = 16
_SIZE_MAX = 56


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _importance_to_size(importance: float) -> int:
    return int(_SIZE_MIN + importance * (_SIZE_MAX - _SIZE_MIN))


def _relation_to_style(rel_type: str) -> dict[str, Any]:
    return {
        "color": _EDGE_COLORS.get(rel_type, _DEFAULT_EDGE_COLOR),
        "width": 2 if rel_type == RelationType.PREREQUISITE.value else 1,
        "curveness": 0.15,
    }


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------
def compute_node_style(node_type: str, importance: float) -> dict[str, Any]:
    """Return a single node's visual style dict."""
    return {
        "color": _NODE_COLORS.get(node_type, _DEFAULT_COLOR),
        "symbolSize": _importance_to_size(importance),
    }


def build_visual_data(
    nodes: list[Any],
    edges: list[Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Transform ORM node/edge lists into frontend-friendly data lists.

    Each node dict includes: id, name, type, importance, itemStyle, symbolSize.
    Each edge dict includes: source, target, relation_type, lineStyle, label.
    """
    styled_nodes: list[dict[str, Any]] = []
    styled_edges: list[dict[str, Any]] = []

    for n in nodes:
        style = compute_node_style(n.type, n.importance)
        styled_nodes.append(
            {
                "id": n.id,
                "name": n.name,
                "type": n.type,
                "importance": n.importance,
                "description": getattr(n, "description", None),
                "itemStyle": {"color": style["color"]},
                "symbolSize": style["symbolSize"],
            }
        )

    for e in edges:
        edge_style = _relation_to_style(e.relation_type)
        styled_edges.append(
            {
                "source": e.source_node_id,
                "target": e.target_node_id,
                "relation_type": e.relation_type,
                "lineStyle": {
                    "color": edge_style["color"],
                    "width": edge_style["width"],
                    "curveness": edge_style["curveness"],
                },
                "label": {
                    "show": True,
                    "formatter": e.relation_type,
                    "fontSize": 10,
                    "color": edge_style["color"],
                },
            }
        )

    return styled_nodes, styled_edges


def build_layout_config(node_count: int) -> dict[str, Any]:
    """Generate ECharts-friendly layout_config based on node count.

    < 50 nodes  → force layout (exploratory)
    50-300      → force with stronger centering
    > 300       → circular + force hybrid (performance)
    """
    if node_count <= 50:
        return {
            "layout": "force",
            "force": {
                "repulsion": 300,
                "edgeLength": [80, 200],
                "gravity": 0.1,
                "friction": 0.6,
                "layoutAnimation": True,
            },
            "roam": True,
        }
    if node_count <= 300:
        return {
            "layout": "force",
            "force": {
                "repulsion": 180,
                "edgeLength": [60, 150],
                "gravity": 0.15,
                "friction": 0.7,
                "layoutAnimation": True,
            },
            "roam": True,
        }
    # > 300 — use circular layout base, enable force for dragging
    return {
        "layout": "circular",
        "circular": {
            "rotateLabel": False,
        },
        "force": {
            "repulsion": 100,
            "edgeLength": 30,
            "gravity": 0.2,
            "layoutAnimation": False,
        },
        "roam": True,
    }
