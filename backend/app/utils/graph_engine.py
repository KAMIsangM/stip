"""NetworkX graph engine — see HLD graph_engine.py."""

from __future__ import annotations

from typing import Any

import networkx as nx

from app.models.enums import RelationType


class GraphCycleError(Exception):
    """Raised when a cycle is detected in the prerequisite subgraph."""

    def __init__(self, message: str = "Graph cycle detected in prerequisite edges", cycle: list[int] | None = None):
        super().__init__(message)
        self.cycle = cycle or []


def build_digraph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from node/edge dictionaries."""
    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
    for e in edges:
        g.add_edge(
            e["source_node_id"],
            e["target_node_id"],
            relation_type=e["relation_type"],
        )
    return g


def topological_sort_nodes(g: nx.DiGraph) -> list[int]:
    """Topological sort on prerequisite edges only.

    Raises GraphCycleError if a cycle is detected.
    """
    prerequisite_edges = [
        (u, v)
        for u, v, d in g.edges(data=True)
        if d.get("relation_type") == RelationType.PREREQUISITE.value
    ]
    sub = nx.DiGraph()
    sub.add_nodes_from(g.nodes())
    sub.add_edges_from(prerequisite_edges)

    if not nx.is_directed_acyclic_graph(sub):
        # find one cycle for the error message
        try:
            cycle = nx.find_cycle(sub, orientation="original")
            cycle_nodes = [u for u, v in cycle]
        except nx.NetworkXNoCycle:
            cycle_nodes = []
        raise GraphCycleError(
            message="Graph cycle detected in prerequisite edges",
            cycle=cycle_nodes,
        )

    return list(nx.topological_sort(sub))


def shortest_path(g: nx.DiGraph, source: int, target: int) -> list[int] | None:
    """Return shortest path between two nodes, or None if unreachable."""
    try:
        return nx.shortest_path(g, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def recommend_related_nodes(
    g: nx.DiGraph,
    node_id: int,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Recommend top-k related nodes via common neighbors (undirected projection).

    Returns list of {"node_id": int, "score": float} sorted descending.
    """
    if node_id not in g:
        return []

    ug = g.to_undirected()
    scores: dict[int, float] = {}
    node_neighbors = set(ug.neighbors(node_id))

    for n in ug.nodes():
        if n == node_id or n in node_neighbors:
            continue
        common = len(node_neighbors & set(ug.neighbors(n)))
        if common > 0:
            # Jaccard coefficient as score
            union = len(node_neighbors | set(ug.neighbors(n)))
            scores[n] = common / union if union > 0 else 0.0

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"node_id": nid, "score": round(score, 4)} for nid, score in ranked]


def has_cycle(g: nx.DiGraph) -> bool:
    """Check if the directed graph contains any cycle."""
    try:
        nx.find_cycle(g, orientation="original")
        return True
    except nx.NetworkXNoCycle:
        return False


def get_subgraph_neighbors(
    g: nx.DiGraph,
    node_ids: list[int],
    radius: int = 1,
) -> nx.DiGraph:
    """Extract an ego-network around given nodes with specified radius."""
    sub_nodes: set[int] = set(node_ids)
    for _ in range(radius):
        frontier: set[int] = set()
        for n in sub_nodes:
            frontier.update(g.predecessors(n))
            frontier.update(g.successors(n))
        sub_nodes.update(frontier)
    return g.subgraph(sub_nodes).copy()
