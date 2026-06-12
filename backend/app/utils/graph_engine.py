"""NetworkX graph engine — see HLD graph_engine.py."""

from __future__ import annotations

import networkx as nx

from app.models.enums import RelationType


def build_digraph(
    nodes: list[dict],
    edges: list[dict],
) -> nx.DiGraph:
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
    prerequisite_edges = [
        (u, v)
        for u, v, d in g.edges(data=True)
        if d.get("relation_type") == RelationType.PREREQUISITE.value
    ]
    sub = nx.DiGraph()
    sub.add_nodes_from(g.nodes())
    sub.add_edges_from(prerequisite_edges)
    if not nx.is_directed_acyclic_graph(sub):
        raise ValueError("Graph cycle detected in prerequisite edges")
    return list(nx.topological_sort(sub))
