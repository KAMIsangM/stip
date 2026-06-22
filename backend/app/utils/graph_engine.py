"""NetworkX graph engine — see HLD graph_engine.py."""

from __future__ import annotations

import math
from typing import Any

import networkx as nx

from app.models.enums import RelationType

# ---------------------------------------------------------------------------
# edge-type → base weight mapping (lower = preferred)
# ---------------------------------------------------------------------------
_EDGE_TYPE_WEIGHT: dict[str, float] = {
    RelationType.PREREQUISITE.value: 1.0,
    RelationType.CONTAINS.value: 2.0,
    RelationType.CAUSAL.value: 2.0,
    RelationType.RELATED.value: 3.0,
}

# importance amplification factor — higher value = more bias toward high-importance nodes
_IMPORTANCE_ALPHA: float = 0.5


class GraphCycleError(Exception):
    """Raised when a cycle is detected in the prerequisite subgraph."""

    def __init__(self, message: str = "Graph cycle detected in prerequisite edges", cycle: list[int] | None = None):
        super().__init__(message)
        self.cycle = cycle or []


def _edge_weight(relation_type: str) -> float:
    """Map a relation-type string to its base traversal weight."""
    return _EDGE_TYPE_WEIGHT.get(relation_type, 3.0)


def _importance_penalty(importance: float) -> float:
    """Convert node importance (0–1) to a positive edge penalty.

    Higher importance → lower penalty → paths that go through this node are cheaper.
    """
    clamped = max(0.0, min(1.0, importance))
    # importance=1.0 → penalty=0.5 (minimum)
    # importance=0.0 → penalty=2.0 (maximum)
    return 2.0 - clamped * 1.5


def _build_weighted_graph(
    g: nx.DiGraph,
) -> nx.DiGraph:
    """Create a weighted copy of *g* using the split-node technique.

    Split-node technique:
    1.  Replace each original node *v* with two vertices: v_in and v_out.
    2.  All incoming edges connect to v_in; all outgoing edges start from v_out.
    3.  Add a directed edge v_in → v_out whose weight = _importance_penalty(importance(v)).
    4.  Each original edge (u→v) is re-routed as u_out → v_in with weight = _edge_weight(relation_type).

    This allows Dijkstra to penalise low-importance nodes while keeping all edge
    weights strictly positive, which is required for Dijkstra's algorithm.

    Returns a new DiGraph where:
    - node IDs are the original integer IDs (for backward compat API), BUT
    - we use a naming convention "id::in" / "id::out" internally for the split
      vertices.  The ``shortest_path`` wrapper maps them back.
    """
    wg = nx.DiGraph()

    for node_id, attrs in g.nodes(data=True):
        importance = attrs.get("importance", 0.5)
        wg.add_node(f"{node_id}::in", original_id=node_id, importance=importance)
        wg.add_node(f"{node_id}::out", original_id=node_id, importance=importance)
        # split-edge: in → out carries the importance penalty
        wg.add_edge(f"{node_id}::in", f"{node_id}::out", weight=_importance_penalty(importance))

    for u, v, attrs in g.edges(data=True):
        base_w = _edge_weight(attrs.get("relation_type", RelationType.RELATED.value))
        wg.add_edge(f"{u}::out", f"{v}::in", weight=base_w)

    return wg


def build_digraph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> nx.DiGraph:
    """Build a NetworkX DiGraph from node/edge dictionaries.

    Each edge receives a ``weight`` attribute derived from its relation type,
    and each node retains its ``importance`` (default 0.5 if missing).
    """
    g = nx.DiGraph()
    for n in nodes:
        node_attrs = {k: v for k, v in n.items() if k != "id"}
        node_attrs.setdefault("importance", 0.5)
        g.add_node(n["id"], **node_attrs)
    for e in edges:
        rt = e.get("relation_type", RelationType.RELATED.value)
        g.add_edge(
            e["source_node_id"],
            e["target_node_id"],
            relation_type=rt,
            weight=_edge_weight(rt),
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


def shortest_path(
    g: nx.DiGraph,
    source: int,
    target: int,
    weighted: bool = True,
) -> list[int] | None:
    """Return shortest path between two nodes, or None if unreachable.

    Knowledge-graph relations (related/contains/causal/prerequisite) are
    semantically undirected — the visual graph in the frontend is also
    undirected.  Therefore this function always treats the graph as
    *undirected* for path finding, even though edges are stored with
    source/target direction in the database.

    When *weighted* is True (default):
        Uses edge-type weights AND node importance to influence path cost.
        Higher-importance nodes and prerequisite-type edges are preferred.

    When *weighted* is False:
        Falls back to plain BFS (unweighted) on the undirected projection.
    """
    # Always treat the graph as undirected — knowledge relations are bidirectional
    ug = g.to_undirected()

    if not weighted:
        try:
            return nx.shortest_path(ug, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    # ---- weighted path on undirected graph --------------------------------
    # Build a weighted undirected graph from the original directed edges.
    # For each undirected edge, use the minimum weight of the directed edge(s)
    # that exist in the original graph.
    wg = nx.Graph()
    for nid, attrs in g.nodes(data=True):
        wg.add_node(nid, **attrs)

    for u, v, attrs in g.edges(data=True):
        w = attrs.get("weight", _edge_weight(attrs.get("relation_type", "related")))
        # If reverse edge also exists, take the min weight
        if g.has_edge(v, u):
            rw = g[v][u].get("weight", _edge_weight(g[v][u].get("relation_type", "related")))
            w = min(w, rw)
        if wg.has_edge(u, v):
            wg[u][v]["weight"] = min(wg[u][v]["weight"], w)
        else:
            wg.add_edge(u, v, weight=w)

    # Incorporate node importance as a penalty on edges incident to each node.
    # For each undirected edge (u, v), the final weight is:
    #   edge_weight + importance_penalty(u) + importance_penalty(v)
    # This keeps all weights strictly positive (required for Dijkstra).
    for u, v in wg.edges():
        imp_u = wg.nodes[u].get("importance", 0.5)
        imp_v = wg.nodes[v].get("importance", 0.5)
        wg[u][v]["weight"] += _importance_penalty(imp_u) + _importance_penalty(imp_v)

    try:
        return list(nx.shortest_path(wg, source=source, target=target, weight="weight"))
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
