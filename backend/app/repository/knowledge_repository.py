"""Knowledge graph data access — HLD knowledge_repository.py."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeEdge, KnowledgeNode


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_node(
        self,
        course_id: int,
        name: str,
        node_type: str,
        importance: float = 0.5,
        description: str | None = None,
    ) -> KnowledgeNode:
        node = KnowledgeNode(
            course_id=course_id,
            name=name,
            type=node_type,
            importance=importance,
            description=description,
        )
        self._db.add(node)
        self._db.commit()
        self._db.refresh(node)
        return node

    def get_node_by_id(self, node_id: int) -> KnowledgeNode | None:
        return self._db.get(KnowledgeNode, node_id)

    def list_nodes_by_course_id(self, course_id: int) -> list[KnowledgeNode]:
        stmt = (
            select(KnowledgeNode)
            .where(KnowledgeNode.course_id == course_id)
            .order_by(KnowledgeNode.id)
        )
        return list(self._db.scalars(stmt).all())

    def update_node(
        self,
        node_id: int,
        *,
        name: str | None = None,
        node_type: str | None = None,
        importance: float | None = None,
        description: str | None = None,
    ) -> KnowledgeNode | None:
        node = self.get_node_by_id(node_id)
        if node is None:
            return None
        if name is not None:
            node.name = name
        if node_type is not None:
            node.type = node_type
        if importance is not None:
            node.importance = importance
        if description is not None:
            node.description = description
        self._db.commit()
        self._db.refresh(node)
        return node

    def delete_node(self, node_id: int) -> bool:
        node = self.get_node_by_id(node_id)
        if node is None:
            return False
        self._db.delete(node)
        self._db.commit()
        return True

    def create_edge(
        self,
        course_id: int,
        source_node_id: int,
        target_node_id: int,
        relation_type: str,
    ) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            course_id=course_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=relation_type,
        )
        self._db.add(edge)
        self._db.commit()
        self._db.refresh(edge)
        return edge

    def get_edge_by_id(self, edge_id: int) -> KnowledgeEdge | None:
        return self._db.get(KnowledgeEdge, edge_id)

    def list_edges_by_course_id(self, course_id: int) -> list[KnowledgeEdge]:
        stmt = (
            select(KnowledgeEdge)
            .where(KnowledgeEdge.course_id == course_id)
            .order_by(KnowledgeEdge.id)
        )
        return list(self._db.scalars(stmt).all())

    def delete_edge(self, edge_id: int) -> bool:
        edge = self.get_edge_by_id(edge_id)
        if edge is None:
            return False
        self._db.delete(edge)
        self._db.commit()
        return True

    def delete_all_by_course_id(self, course_id: int) -> None:
        for edge in self.list_edges_by_course_id(course_id):
            self._db.delete(edge)
        for node in self.list_nodes_by_course_id(course_id):
            self._db.delete(node)
        self._db.commit()
