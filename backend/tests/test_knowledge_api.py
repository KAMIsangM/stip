"""Knowledge graph API integration tests — F003 module."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import Base, SessionLocal
from app.models import Course, KnowledgeNode, KnowledgeEdge, Chapter, ContentModule, GenerationProgress
from app.models.enums import NodeType, RelationType

client = TestClient(app)
API = "/api/v1"


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test module and clean after."""
    from app.core.database import engine
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up test data in dependency order (children first)
    db = SessionLocal()
    try:
        db.query(ContentModule).delete()
        db.query(GenerationProgress).delete()
        db.query(KnowledgeEdge).delete()
        db.query(KnowledgeNode).delete()
        db.query(Chapter).delete()
        db.query(Course).delete()
        db.commit()
    finally:
        db.close()


def _create_course_db(title="测试课程") -> dict:
    """Create a course directly via DB to avoid LLM call overhead."""
    db = SessionLocal()
    try:
        course = Course(title=title, description="测试用", status="draft")
        db.add(course)
        db.commit()
        db.refresh(course)
        return {"id": course.id, "title": course.title}
    finally:
        db.close()


def _create_node(course_id: int, name: str, ntype="概念", importance=0.5, description=None):
    payload = {"name": name, "type": ntype, "importance": importance}
    if description:
        payload["description"] = description
    r = client.post(f"{API}/courses/{course_id}/knowledge-graph/nodes", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _create_edge(course_id: int, src: int, tgt: int, rel="related"):
    r = client.post(
        f"{API}/courses/{course_id}/knowledge-graph/edges",
        json={"source_node_id": src, "target_node_id": tgt, "relation_type": rel},
    )
    return r


# ═══════════════════════════════════════════
# 1. Presets
# ═══════════════════════════════════════════


class TestPresets:
    def test_list_presets(self):
        r = client.get(f"{API}/knowledge-graph/presets")
        assert r.status_code == 200
        data = r.json()
        assert "presets" in data
        assert isinstance(data["presets"], list)

    def test_apply_preset(self):
        course = _create_course_db("预设测试课程")
        cid = course["id"]
        # Get available presets first
        pr = client.get(f"{API}/knowledge-graph/presets")
        presets = pr.json()["presets"]
        if not presets:
            pytest.skip("No presets available")
        preset_id = presets[0]["id"]

        r = client.post(f"{API}/courses/{cid}/knowledge-graph/apply-preset", json={"preset_id": preset_id})
        assert r.status_code == 200
        data = r.json()
        assert data["node_count"] > 0

        # Verify graph populated
        gr = client.get(f"{API}/courses/{cid}/knowledge-graph")
        assert gr.status_code == 200
        gdata = gr.json()
        assert len(gdata["nodes"]) == data["node_count"]

    def test_apply_preset_idempotent(self):
        """Re-applying same preset should not duplicate nodes."""
        course = _create_course_db("幂等测试课程")
        cid = course["id"]
        pr = client.get(f"{API}/knowledge-graph/presets")
        presets = pr.json()["presets"]
        if not presets:
            pytest.skip("No presets available")
        preset_id = presets[0]["id"]

        r1 = client.post(f"{API}/courses/{cid}/knowledge-graph/apply-preset", json={"preset_id": preset_id})
        assert r1.status_code == 200
        cnt1 = r1.json()["node_count"]

        r2 = client.post(f"{API}/courses/{cid}/knowledge-graph/apply-preset", json={"preset_id": preset_id})
        assert r2.status_code == 200
        # Second apply should create 0 new nodes (all names already exist)
        assert r2.json()["node_count"] == 0

        # Graph node count should still be cnt1
        gr = client.get(f"{API}/courses/{cid}/knowledge-graph")
        assert len(gr.json()["nodes"]) == cnt1

    def test_apply_nonexistent_preset(self):
        course = _create_course_db("不存在预设")
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/apply-preset", json={"preset_id": 99999})
        assert r.status_code == 404

    def test_apply_missing_body(self):
        course = _create_course_db("缺参数")
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/apply-preset", json={})
        assert r.status_code == 422


# ═══════════════════════════════════════════
# 2. Graph query
# ═══════════════════════════════════════════


class TestGraphQuery:
    def test_empty_graph(self):
        course = _create_course_db("空图谱")
        r = client.get(f"{API}/courses/{course['id']}/knowledge-graph")
        assert r.status_code == 200
        data = r.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert "layout_config" in data

    def test_graph_with_data(self):
        course = _create_course_db("有数据图谱")
        cid = course["id"]
        a = _create_node(cid, "节点A")
        b = _create_node(cid, "节点B")
        _create_edge(cid, a["id"], b["id"], "prerequisite")

        r = client.get(f"{API}/courses/{cid}/knowledge-graph")
        assert r.status_code == 200
        data = r.json()
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_nonexistent_course_graph(self):
        r = client.get(f"{API}/courses/99999/knowledge-graph")
        assert r.status_code == 200
        assert r.json()["nodes"] == []


# ═══════════════════════════════════════════
# 3. Topological sort
# ═══════════════════════════════════════════


class TestSortedNodes:
    def test_empty_sorted(self):
        course = _create_course_db("空排序")
        r = client.get(f"{API}/courses/{course['id']}/knowledge-graph/sorted")
        assert r.status_code == 200
        assert r.json()["nodes"] == []

    def test_sorted_order(self):
        course = _create_course_db("排序测试")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        c = _create_node(cid, "C")
        _create_edge(cid, a["id"], b["id"], "prerequisite")
        _create_edge(cid, b["id"], c["id"], "prerequisite")

        r = client.get(f"{API}/courses/{cid}/knowledge-graph/sorted")
        assert r.status_code == 200
        names = [n["name"] for n in r.json()["nodes"]]
        # A must come before B, B before C
        assert names.index("A") < names.index("B") < names.index("C")


# ═══════════════════════════════════════════
# 4. Shortest path
# ═══════════════════════════════════════════


class TestShortestPath:
    def test_shortest_path_found(self):
        course = _create_course_db("最短路径")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        c = _create_node(cid, "C")
        _create_edge(cid, a["id"], b["id"])
        _create_edge(cid, b["id"], c["id"])

        r = client.get(f"{API}/courses/{cid}/knowledge-graph/shortest-path", params={"source": a["id"], "target": c["id"]})
        assert r.status_code == 200
        assert r.json()["path"] == [a["id"], b["id"], c["id"]]

    def test_no_path(self):
        course = _create_course_db("无路径")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        r = client.get(f"{API}/courses/{cid}/knowledge-graph/shortest-path", params={"source": a["id"], "target": b["id"]})
        assert r.status_code == 200
        assert r.json()["path"] is None

    def test_missing_params(self):
        r = client.get(f"{API}/courses/1/knowledge-graph/shortest-path")
        assert r.status_code == 422


# ═══════════════════════════════════════════
# 5. Recommendations
# ═══════════════════════════════════════════


class TestRecommendations:
    def test_recommendations(self):
        course = _create_course_db("推荐测试")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        _create_edge(cid, a["id"], b["id"], "related")

        r = client.get(f"{API}/courses/{cid}/knowledge-graph/recommendations", params={"node_id": a["id"], "top_k": 5})
        assert r.status_code == 200
        assert "recommendations" in r.json()

    def test_topk_boundary(self):
        course = _create_course_db("topk边界")
        cid = course["id"]
        a = _create_node(cid, "X")
        r = client.get(f"{API}/courses/{cid}/knowledge-graph/recommendations", params={"node_id": a["id"], "top_k": 50})
        assert r.status_code == 422

    def test_nonexistent_node(self):
        course = _create_course_db("不存在节点推荐")
        r = client.get(f"{API}/courses/{course['id']}/knowledge-graph/recommendations", params={"node_id": 99999})
        assert r.status_code == 200
        assert r.json()["recommendations"] == []


# ═══════════════════════════════════════════
# 6. Node CRUD
# ═══════════════════════════════════════════


class TestNodeCRUD:
    def test_create_node(self):
        course = _create_course_db("节点创建")
        cid = course["id"]
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/nodes", json={"name": "变量", "type": "概念", "importance": 0.8})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "变量"
        assert data["type"] == "概念"
        assert data["importance"] == 0.8

    def test_create_with_description(self):
        course = _create_course_db("带描述节点")
        cid = course["id"]
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/nodes", json={"name": "循环", "type": "技能", "description": "for/while"})
        assert r.status_code == 201
        assert r.json()["description"] == "for/while"

    def test_create_invalid_type(self):
        course = _create_course_db("无效类型")
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/nodes", json={"name": "x", "type": "bad"})
        assert r.status_code == 422

    def test_create_empty_name(self):
        course = _create_course_db("空名称")
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/nodes", json={"name": "", "type": "概念"})
        assert r.status_code == 422

    def test_create_importance_out_of_range(self):
        course = _create_course_db("超界重要度")
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/nodes", json={"name": "x", "importance": 1.5})
        assert r.status_code == 422

    def test_create_importance_boundary_zero(self):
        course = _create_course_db("重要度0")
        cid = course["id"]
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/nodes", json={"name": "x", "importance": 0})
        assert r.status_code == 201

    def test_update_node(self):
        course = _create_course_db("更新节点")
        cid = course["id"]
        node = _create_node(cid, "旧名")
        r = client.put(f"{API}/courses/{cid}/knowledge-graph/nodes/{node['id']}", json={"name": "新名"})
        assert r.status_code == 200
        assert r.json()["name"] == "新名"

    def test_update_nonexistent(self):
        course = _create_course_db("更新不存在")
        r = client.put(f"{API}/courses/{course['id']}/knowledge-graph/nodes/99999", json={"name": "x"})
        assert r.status_code == 404

    def test_update_cross_course(self):
        c1 = _create_course_db("课程A")
        c2 = _create_course_db("课程B")
        node = _create_node(c1["id"], "跨课节点")
        r = client.put(f"{API}/courses/{c2['id']}/knowledge-graph/nodes/{node['id']}", json={"name": "hack"})
        assert r.status_code == 404

    def test_delete_node(self):
        course = _create_course_db("删除节点")
        cid = course["id"]
        node = _create_node(cid, "待删除")
        r = client.delete(f"{API}/courses/{cid}/knowledge-graph/nodes/{node['id']}")
        assert r.status_code == 204

    def test_delete_nonexistent(self):
        course = _create_course_db("删除不存在")
        r = client.delete(f"{API}/courses/{course['id']}/knowledge-graph/nodes/99999")
        assert r.status_code == 404

    def test_delete_node_cascades_edges(self):
        """Deleting a node should also delete its connected edges (FK CASCADE)."""
        course = _create_course_db("级联删除")
        cid = course["id"]
        a = _create_node(cid, "源")
        b = _create_node(cid, "目标")
        e = _create_edge(cid, a["id"], b["id"])
        assert e.status_code == 201
        edge_id = e.json()["id"]

        # Delete source node
        r = client.delete(f"{API}/courses/{cid}/knowledge-graph/nodes/{a['id']}")
        assert r.status_code == 204

        # Edge should be gone
        gr = client.get(f"{API}/courses/{cid}/knowledge-graph")
        gdata = gr.json()
        edge_ids = [ed["id"] for ed in gdata["edges"]]
        assert edge_id not in edge_ids


# ═══════════════════════════════════════════
# 7. Edge CRUD
# ═══════════════════════════════════════════


class TestEdgeCRUD:
    def test_create_edge(self):
        course = _create_course_db("边创建")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        r = _create_edge(cid, a["id"], b["id"], "prerequisite")
        assert r.status_code == 201
        assert r.json()["relation_type"] == "prerequisite"

    def test_create_edge_default_type(self):
        course = _create_course_db("默认边类型")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/edges", json={"source_node_id": a["id"], "target_node_id": b["id"]})
        assert r.status_code == 201
        assert r.json()["relation_type"] == "related"

    def test_create_edge_source_not_found(self):
        course = _create_course_db("源不存在")
        cid = course["id"]
        b = _create_node(cid, "B")
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/edges", json={"source_node_id": 99999, "target_node_id": b["id"]})
        assert r.status_code == 404

    def test_create_edge_target_not_found(self):
        course = _create_course_db("目标不存在")
        cid = course["id"]
        a = _create_node(cid, "A")
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/edges", json={"source_node_id": a["id"], "target_node_id": 99999})
        assert r.status_code == 404

    def test_create_edge_invalid_type(self):
        course = _create_course_db("无效边类型")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        r = client.post(f"{API}/courses/{cid}/knowledge-graph/edges", json={"source_node_id": a["id"], "target_node_id": b["id"], "relation_type": "bad"})
        assert r.status_code == 422

    def test_create_duplicate_edge(self):
        course = _create_course_db("重复边")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        r1 = _create_edge(cid, a["id"], b["id"])
        assert r1.status_code == 201
        r2 = _create_edge(cid, a["id"], b["id"])
        assert r2.status_code == 409

    def test_create_edge_cross_course(self):
        c1 = _create_course_db("课程X")
        c2 = _create_course_db("课程Y")
        a = _create_node(c1["id"], "AX")
        b = _create_node(c2["id"], "BY")
        # Try creating edge in c2 using c1's node
        r = client.post(f"{API}/courses/{c2['id']}/knowledge-graph/edges", json={"source_node_id": a["id"], "target_node_id": b["id"]})
        assert r.status_code == 404

    def test_update_edge(self):
        course = _create_course_db("更新边")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        e = _create_edge(cid, a["id"], b["id"])
        edge_id = e.json()["id"]
        r = client.put(f"{API}/courses/{cid}/knowledge-graph/edges/{edge_id}", json={"relation_type": "causal"})
        assert r.status_code == 200
        assert r.json()["relation_type"] == "causal"

    def test_update_nonexistent_edge(self):
        course = _create_course_db("更新不存在边")
        r = client.put(f"{API}/courses/{course['id']}/knowledge-graph/edges/99999", json={"relation_type": "causal"})
        assert r.status_code == 404

    def test_delete_edge(self):
        course = _create_course_db("删除边")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        e = _create_edge(cid, a["id"], b["id"])
        r = client.delete(f"{API}/courses/{cid}/knowledge-graph/edges/{e.json()['id']}")
        assert r.status_code == 204

    def test_delete_nonexistent_edge(self):
        course = _create_course_db("删除不存在边")
        r = client.delete(f"{API}/courses/{course['id']}/knowledge-graph/edges/99999")
        assert r.status_code == 404

    def test_delete_edge_preserves_nodes(self):
        course = _create_course_db("删边留节点")
        cid = course["id"]
        a = _create_node(cid, "A")
        b = _create_node(cid, "B")
        e = _create_edge(cid, a["id"], b["id"])
        r = client.delete(f"{API}/courses/{cid}/knowledge-graph/edges/{e.json()['id']}")
        assert r.status_code == 204

        gr = client.get(f"{API}/courses/{cid}/knowledge-graph")
        gdata = gr.json()
        node_ids = [n["id"] for n in gdata["nodes"]]
        assert a["id"] in node_ids
        assert b["id"] in node_ids
        assert len(gdata["edges"]) == 0


# ═══════════════════════════════════════════
# 8. Boundary tests
# ═══════════════════════════════════════════


class TestBoundary:
    def test_node_name_200_chars(self):
        course = _create_course_db("200字符名")
        name = "A" * 200
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/nodes", json={"name": name, "type": "概念"})
        assert r.status_code == 201

    def test_node_name_201_chars(self):
        course = _create_course_db("201字符名")
        name = "A" * 201
        r = client.post(f"{API}/courses/{course['id']}/knowledge-graph/nodes", json={"name": name, "type": "概念"})
        assert r.status_code == 422

    def test_invalid_course_id(self):
        r = client.get(f"{API}/courses/abc/knowledge-graph")
        assert r.status_code == 422
