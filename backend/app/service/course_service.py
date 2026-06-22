"""Course service — HLD course_service.py.

Core business logic for F001-F004:
- create_course()          : create course + generate syllabus via LLM
- get_course_detail()      : course info + chapters + scene plan + progress
- list_courses()           : paginated list with filtering
- _generate_syllabus()     : LLM prompt → structured outline
- _parse_syllabus_json()   : robust JSON parsing from LLM response
- _plan_scenes()           : map knowledge node types → teaching modalities (F003)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Chapter, KnowledgeEdge, KnowledgeNode
from app.models.enums import NodeType
from app.repository.course_repository import CourseRepository
from app.repository.knowledge_repository import KnowledgeRepository
from app.repository.progress_repository import ProgressRepository
from app.provider.factory import get_llm_provider
from app.service import knowledge_service
from app.service.progress_service import ProgressService

logger = logging.getLogger(__name__)


# ===========================================================================
# Syllabus generation prompt template
# ===========================================================================
_SYLLABUS_SYSTEM_PROMPT = """你是一个资深课程设计师。根据用户提供的学习主题，生成一份结构化的课程大纲。

要求：
1. 输出必须是严格的 JSON 格式，不要包含任何其他文字
2. 课程大纲应包含 3-6 个章节，每个章节包含若干小节（知识点）
3. 每个知识点需要标注类型：概念 / 技能 / 记忆 / 实践 / 综合
4. 每个知识点需要标注重要程度：0.0-1.0 的浮点数
5. 知识点之间应体现丰富的关系（不仅仅是前驱后继），包括：
   - prerequisite（前驱后继）：B 需要先掌握 A 才能学
   - contains（包含）：大概念包含子概念
   - causal（因果）：A 是 B 的原因/前提条件
   - related（关联）：A 和 B 有紧密关联但不构成严格的前驱或包含关系
6. 【重要】edges 字段是必填的！你必须为至少 40% 的边使用非 prerequisite 的关系类型
7. 同一章节内的相邻知识点默认用 related，大概念与其子概念用 contains，因果关系用 causal

输出格式示例：
{
  "title": "课程标题",
  "description": "课程简介",
  "chapters": [
    {
      "title": "第1章 章节名称",
      "order": 1,
      "knowledge_points": [
        {"name": "知识点名称", "type": "概念", "importance": 0.9, "prerequisites": []},
        {"name": "知识点名称", "type": "实践", "importance": 0.8, "prerequisites": ["前置知识点名称"]}
      ]
    }
  ],
  "edges": [
    {"source": "前置知识点名称", "target": "知识点名称", "relation_type": "prerequisite"},
    {"source": "概念A", "target": "概念B", "relation_type": "contains"},
    {"source": "原因C", "target": "结果D", "relation_type": "causal"},
    {"source": "概念E", "target": "概念F", "relation_type": "related"}
  ]
}

注意：
- prerequisites 字段中的值必须是同一课程中其他知识点的 name
- 【重要】edges 字段是必填的，不是可选的！你必须在 edges 中列出所有关系，包括 prerequisite 类型的关系也要显式列出
- 所有在 prerequisites 中声明的依赖关系，也必须在 edges 中重复声明（relation_type 为 "prerequisite"）
- 同时必须在 edges 中补充至少 40% 的非 prerequisite 关系（contains / causal / related）
- 章节之间知识点可以存在跨章节的关系
- 确保 JSON 格式完全合法，不要有尾随逗号"""


# ===========================================================================
# Syllabus JSON parsing helpers
# ===========================================================================
def _extract_json_from_text(text: str) -> str:
    """Extract JSON object from LLM response that may contain extra text."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()

    brace_start = text.find("{")
    if brace_start == -1:
        raise ValueError("No JSON object found in LLM response")
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : i + 1]
    raise ValueError("Unbalanced braces in LLM response")


def _parse_syllabus_json(raw: str) -> dict[str, Any]:
    """Robustly parse syllabus JSON from LLM response string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    extracted = _extract_json_from_text(raw)
    return json.loads(extracted)


def _validate_syllabus(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize parsed syllabus structure."""
    if not isinstance(data, dict):
        raise ValueError("Syllabus root must be a JSON object")

    title = data.get("title", "未命名课程")
    description = data.get("description", "")

    chapters = data.get("chapters", [])
    if not isinstance(chapters, list) or len(chapters) == 0:
        raise ValueError("Syllabus must contain at least one chapter")

    normalized_chapters: list[dict[str, Any]] = []
    all_kp_names: set[str] = set()

    for i, ch in enumerate(chapters):
        if not isinstance(ch, dict):
            continue
        ch_title = ch.get("title", f"第{i+1}章")
        ch_order = ch.get("order", i + 1)
        kps = ch.get("knowledge_points", [])

        normalized_kps: list[dict[str, Any]] = []
        for kp in kps:
            if not isinstance(kp, dict):
                continue
            name = kp.get("name", "")
            if not name:
                continue
            all_kp_names.add(name)
            normalized_kps.append({
                "name": name,
                "type": kp.get("type", "概念"),
                "importance": float(kp.get("importance", 0.5)),
                "prerequisites": kp.get("prerequisites", []) or [],
            })

        if normalized_kps:
            normalized_chapters.append({
                "title": ch_title,
                "order": int(ch_order),
                "knowledge_points": normalized_kps,
            })

    if not normalized_chapters:
        raise ValueError("Syllabus has no valid chapters with knowledge points")

    # Validate edges if present (LLM may output additional relation types)
    raw_edges = data.get("edges", [])
    normalized_edges: list[dict[str, str]] = []
    valid_relation_types = {"prerequisite", "contains", "causal", "related"}
    if isinstance(raw_edges, list):
        for edge in raw_edges:
            if not isinstance(edge, dict):
                continue
            source = edge.get("source", "")
            target = edge.get("target", "")
            rt = edge.get("relation_type", "prerequisite")
            if not source or not target:
                continue
            if rt not in valid_relation_types:
                rt = "prerequisite"
            normalized_edges.append({
                "source": source,
                "target": target,
                "relation_type": rt,
            })

    # Log edge diversity from LLM output for diagnostics
    edge_type_counts: dict[str, int] = {}
    for e in normalized_edges:
        rt = e.get("relation_type", "prerequisite")
        edge_type_counts[rt] = edge_type_counts.get(rt, 0) + 1
    if normalized_edges:
        logger.info(
            "LLM edges parsed: %d total, types=%s",
            len(normalized_edges), edge_type_counts,
        )
    else:
        logger.warning(
            "LLM did NOT output 'edges' field — will rely on prerequisites only "
            "(post-processing will auto-diversify)"
        )

    return {
        "title": str(title),
        "description": str(description),
        "chapters": normalized_chapters,
        "edges": normalized_edges,
    }


# ===========================================================================
# Teaching scene plan — F003: map node types to modal combos
# ===========================================================================

# Mapping from knowledge-point type to recommended teaching modalities
# SRS §3.2: concept → text+mindmap, practice → interactive+quiz, synthesis → ppt+audio
_NODE_TYPE_MODAL_MAP: dict[str, list[str]] = {
    "概念": ["text", "mindmap"],
    "技能": ["text", "quiz", "interactive_html"],
    "记忆": ["text", "quiz"],
    "实践": ["interactive_html", "quiz"],
    "综合": ["ppt", "audio", "mindmap"],
}

_DEFAULT_MODALS = ["text", "mindmap"]


def _plan_scenes_for_chapter(
    knowledge_points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a teaching scene plan for one chapter.

    Returns a dict with:
      - recommended_modals: unique modal types for this chapter
      - knowledge_point_scenes: per-KP modal assignment
    """
    modal_set: set[str] = set()
    kp_scenes: list[dict[str, Any]] = []

    for kp in knowledge_points:
        kp_type = kp.get("type", "概念")
        modals = _NODE_TYPE_MODAL_MAP.get(kp_type, _DEFAULT_MODALS)
        modal_set.update(modals)
        kp_scenes.append({
            "name": kp.get("name", ""),
            "type": kp_type,
            "importance": kp.get("importance", 0.5),
            "modals": modals,
        })

    return {
        "recommended_modals": sorted(modal_set),
        "knowledge_point_scenes": kp_scenes,
    }


def _build_full_scene_plan(
    chapters_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a full scene plan for the entire course.

    Returns:
      - chapters: per-chapter scene plans
      - global_modals: all modal types used across the course
      - chapter_count: total chapters
    """
    global_modals: set[str] = set()
    chapter_scenes: list[dict[str, Any]] = []

    for ch in chapters_data:
        scene = _plan_scenes_for_chapter(ch.get("knowledge_points", []))
        scene["chapter_title"] = ch.get("title", "")
        scene["chapter_order"] = ch.get("order", 0)
        chapter_scenes.append(scene)
        global_modals.update(scene["recommended_modals"])

    return {
        "chapters": chapter_scenes,
        "global_modals": sorted(global_modals),
        "chapter_count": len(chapter_scenes),
    }


# ===========================================================================
# CourseService
# ===========================================================================
class CourseService:
    """Business logic for course creation, listing, detail retrieval."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._course_repo = CourseRepository(db)
        self._knowledge_repo = KnowledgeRepository(db)
        self._progress_repo = ProgressRepository(db)

    # -----------------------------------------------------------------------
    # create_course — the core F001 flow
    # -----------------------------------------------------------------------
    async def create_course(
        self,
        title: str,
        description: str | None = None,
        preset_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a course and generate syllabus via LLM.

        Flow:
        1. Persist the course record (status=draft)
        2. Init progress tracker
        3. If preset_id is given, copy preset knowledge graph into course
        4. Call LLM to generate structured syllabus
        5. Parse and validate syllabus JSON
        6. Persist chapters and knowledge nodes/edges
        7. Build teaching scene plan (F003)
        8. Update course title/description from LLM output (if better)
        9. Update progress → done, status → "outlined"
        10. Return full course data with scene_plan
        """
        # Step 1: Create course record
        course = self._course_repo.create(
            title=title,
            description=description,
            status="draft",
        )
        course_id = course.id
        logger.info("Course created: id=%d, title=%s", course_id, title)

        # Step 2: Init progress tracker (F004)
        self._progress_repo.create(
            course_id=course_id,
            status="outline_generating",
            current_step=0,
            total_steps=3,  # preset → LLM → persist
        )

        # Step 3: Optionally seed preset knowledge graph
        preset_knowledge_nodes: list[dict[str, Any]] = []
        if preset_id is not None:
            self._progress_repo.update(course_id, current_step=1)
            try:
                nodes, edges = knowledge_service.build_from_preset(
                    course_id, preset_id, self._db
                )
                preset_knowledge_nodes = [
                    {"name": n.name, "type": n.type, "importance": n.importance}
                    for n in nodes
                ]
                logger.info(
                    "Preset %d seeded: %d nodes, %d edges",
                    preset_id,
                    len(nodes),
                    len(edges),
                )
            except ValueError as e:
                logger.warning("Preset %d not found, proceeding without: %s", preset_id, e)

        # Step 4: Generate syllabus via LLM
        self._progress_repo.update(course_id, current_step=2)
        syllabus = await self._generate_syllabus(
            topic=title,
            description=description,
            preset_nodes=preset_knowledge_nodes,
        )

        # Step 5: Persist chapters and knowledge graph
        chapters_data = syllabus.get("chapters", [])
        edges_data = syllabus.get("edges", [])
        self._persist_syllabus(course_id, chapters_data, edges_data)

        # Step 6: Build teaching scene plan (F003)
        scene_plan = _build_full_scene_plan(chapters_data)

        # Step 7: Update course title/description if LLM produced better ones
        llm_title = syllabus.get("title", "")
        llm_desc = syllabus.get("description", "")
        if llm_title and llm_title != title:
            self._course_repo.update(course_id, title=llm_title)
        if llm_desc and llm_desc != description:
            self._course_repo.update(course_id, description=llm_desc)

        # Step 8: Update status to "outlined" and progress → done
        self._course_repo.update(course_id, status="outlined")
        self._progress_repo.update(
            course_id,
            status="done",
            current_step=3,
        )

        # Step 9: Return complete course data
        result = await self.get_course_detail(course_id)
        result["scene_plan"] = scene_plan
        return result

    # -----------------------------------------------------------------------
    # get_course_detail
    # -----------------------------------------------------------------------
    async def get_course_detail(self, course_id: int) -> dict[str, Any]:
        """Get full course detail: info + chapters + scene_plan + progress."""
        course = self._course_repo.get_by_id(course_id)
        if course is None:
            raise LookupError(f"Course {course_id} not found")

        chapters = self._course_repo.get_chapters_by_course_id(course_id)

        # Build knowledge node id→name mapping for chapter display
        node_map: dict[int, str] = {}
        node_type_map: dict[int, str] = {}
        for node in self._knowledge_repo.list_nodes_by_course_id(course_id):
            node_map[node.id] = node.name
            node_type_map[node.id] = node.type

        # Build chapters output with scene info
        chapters_out: list[dict[str, Any]] = []
        for ch in chapters:
            kp_names: list[str] = []
            kp_details: list[dict[str, Any]] = []
            if ch.knowledge_node_ids:
                try:
                    ids = json.loads(ch.knowledge_node_ids)
                    if isinstance(ids, list):
                        for nid in ids:
                            name = node_map.get(nid, str(nid))
                            kp_names.append(name)
                            kp_details.append({
                                "id": nid,
                                "name": name,
                                "type": node_type_map.get(nid, "概念"),
                            })
                except (json.JSONDecodeError, TypeError):
                    pass

            # Build scene plan for this chapter (F003)
            scene = _plan_scenes_for_chapter(kp_details) if kp_details else {}

            chapters_out.append({
                "id": ch.id,
                "title": ch.title,
                "order": ch.order,
                "knowledge_points": kp_names,
                "knowledge_point_details": kp_details,
                "scene_plan": scene,
            })

        # Build course-level scene plan
        all_kp_details: list[dict[str, Any]] = []
        for ch in chapters_out:
            all_kp_details.extend(ch.get("knowledge_point_details", []))
        course_scene_plan = _build_full_scene_plan([
            {"title": ch["title"], "order": ch["order"], "knowledge_points": ch.get("knowledge_point_details", [])}
            for ch in chapters_out
        ])

        progress = None
        if course.generation_progress:
            gp = course.generation_progress
            progress = {
                "status": gp.status,
                "current_step": gp.current_step,
                "total_steps": gp.total_steps,
                "error_message": gp.error_message,
            }

        return {
            "course_info": {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "status": course.status,
                "created_at": course.created_at.isoformat() if course.created_at else None,
                "updated_at": course.updated_at.isoformat() if course.updated_at else None,
            },
            "chapters": chapters_out,
            "scene_plan": course_scene_plan,
            "generation_progress": progress,
        }

    # -----------------------------------------------------------------------
    # list_courses
    # -----------------------------------------------------------------------
    def list_courses(
        self,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        """Paginated course list with optional filtering."""
        skip = max(0, (page - 1) * page_size)

        all_courses = self._course_repo.list_all(skip=0, limit=10_000)

        filtered = all_courses
        if status:
            filtered = [c for c in filtered if c.status == status]
        if keyword:
            kw = keyword.lower()
            filtered = [
                c
                for c in filtered
                if kw in (c.title or "").lower()
                or kw in (c.description or "").lower()
            ]

        total = len(filtered)
        paged = filtered[skip : skip + page_size]

        items = [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in paged
        ]

        return {
            "total": total,
            "list": items,
            "page": page,
            "page_size": page_size,
        }

    # -----------------------------------------------------------------------
    # Internal: syllabus generation via LLM
    # -----------------------------------------------------------------------
    async def _generate_syllabus(
        self,
        topic: str,
        description: str | None = None,
        preset_nodes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Call LLM to generate a structured course syllabus."""
        prompt_parts = [
            "请为以下学习主题生成课程大纲：",
            f"主题：{topic}",
        ]
        if description:
            prompt_parts.append(f"补充描述：{description}")
        if preset_nodes:
            kp_list = [n["name"] for n in preset_nodes]
            prompt_parts.append(
                f"以下知识点已存在于知识库中，请尽可能将其融入课程大纲：{', '.join(kp_list)}"
            )

        user_prompt = "\n".join(prompt_parts)
        full_prompt = f"{_SYLLABUS_SYSTEM_PROMPT}\n\n{user_prompt}"

        llm = get_llm_provider()
        logger.info("Calling LLM for syllabus generation (topic=%s)...", topic)

        try:
            raw_response = await llm.chat_completion(full_prompt)
            logger.info("LLM syllabus response received (len=%d)", len(raw_response))
            logger.info("LLM raw response (first 300 chars): %s", raw_response[:300])
        except Exception as e:
            logger.error("LLM call failed — falling back to static syllabus: %s", e)
            return self._fallback_syllabus(topic, description)

        try:
            parsed = _parse_syllabus_json(raw_response)
            validated = _validate_syllabus(parsed)
            logger.info(
                "Syllabus generated: %d chapters, title=%s",
                len(validated["chapters"]),
                validated["title"],
            )
            return validated
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("Failed to parse syllabus JSON: %s", e)
            logger.debug("Raw response: %s", raw_response[:1000])
            return self._fallback_syllabus(topic, description)

    # -----------------------------------------------------------------------
    # Internal: persist chapters and knowledge nodes from syllabus
    # -----------------------------------------------------------------------
    def _persist_syllabus(
        self,
        course_id: int,
        chapters_data: list[dict[str, Any]],
        edges_data: list[dict[str, str]] | None = None,
    ) -> None:
        """Persist chapters and knowledge nodes/edges parsed from syllabus.

        Deduplication: if a knowledge node with the same name already exists in
        the database (e.g. from a preset), reuse it instead of creating a duplicate.
        """
        all_kp_map: dict[str, KnowledgeNode] = {}

        # Pre-populate map with existing nodes from DB (e.g. preset nodes)
        existing_nodes = self._knowledge_repo.list_nodes_by_course_id(course_id)
        for node in existing_nodes:
            all_kp_map[node.name] = node

        for ch_data in chapters_data:
            chapter = self._course_repo.create_chapter(
                course_id=course_id,
                title=ch_data["title"],
                order=ch_data["order"],
            )

            kp_ids: list[int] = []
            for kp_data in ch_data.get("knowledge_points", []):
                name = kp_data["name"]

                if name not in all_kp_map:
                    node = self._knowledge_repo.create_node(
                        course_id=course_id,
                        name=name,
                        node_type=kp_data["type"],
                        importance=kp_data["importance"],
                    )
                    all_kp_map[name] = node
                else:
                    node = all_kp_map[name]
                    # Update type/importance if LLM provides richer data
                    # (only if the existing node was from a preset with defaults)
                    if kp_data.get("type") and node.type in ("概念", "concept"):
                        node.type = kp_data["type"]
                    if kp_data.get("importance", 0.5) != 0.5 and node.importance == 0.5:
                        node.importance = kp_data["importance"]

                kp_ids.append(node.id)

            chapter.knowledge_node_ids = json.dumps(kp_ids, ensure_ascii=False)
            self._db.flush()

        # Track created edges to avoid duplicates
        created_edges: set[tuple[str, str]] = set()

        def _create_edge_if_new(
            source_name: str, target_name: str, relation_type: str
        ) -> None:
            """Create an edge only if not already created (dedup by source+target)."""
            edge_key = (source_name, target_name)
            if edge_key in created_edges:
                return
            source_node = all_kp_map.get(source_name)
            target_node = all_kp_map.get(target_name)
            if source_node is None or target_node is None:
                logger.warning(
                    "Edge node not found: '%s' → '%s' — skipping",
                    source_name, target_name,
                )
                return
            try:
                self._knowledge_repo.create_edge(
                    course_id=course_id,
                    source_node_id=source_node.id,
                    target_node_id=target_node.id,
                    relation_type=relation_type,
                )
                created_edges.add(edge_key)
            except Exception as e:
                logger.warning(
                    "Failed to create edge %s → %s: %s",
                    source_name, target_name, e,
                )

        # Step 1: Create edges from prerequisites (always "prerequisite" type)
        for ch_data in chapters_data:
            for kp_data in ch_data.get("knowledge_points", []):
                name = kp_data["name"]
                for prereq_name in kp_data.get("prerequisites", []):
                    _create_edge_if_new(prereq_name, name, "prerequisite")

        # Step 2: Create edges from LLM-generated edges (may have other relation types)
        if edges_data:
            for edge in edges_data:
                source = edge.get("source", "")
                target = edge.get("target", "")
                rt = edge.get("relation_type", "prerequisite")
                if source and target:
                    _create_edge_if_new(source, target, rt)

        # Step 3: Post-process — if all edges are "prerequisite", auto-diversify
        # using heuristic rules so the knowledge graph isn't flat.
        self._diversify_edge_types(
            course_id, chapters_data, all_kp_map, created_edges
        )

        self._db.commit()
        logger.info(
            "Syllabus persisted: %d chapters, %d knowledge nodes, %d edges",
            len(chapters_data),
            len(all_kp_map),
            len(created_edges),
        )

    # -------------------------------------------------------------------
    # Heuristic edge-type diversification (fallback when LLM produces
    # only prerequisite edges or no edges at all)
    # -------------------------------------------------------------------
    def _diversify_edge_types(
        self,
        course_id: int,
        chapters_data: list[dict[str, Any]],
        all_kp_map: dict[str, KnowledgeNode],
        created_edges: set[tuple[str, str]],
    ) -> None:
        """Auto-diversify relation types when LLM output lacks variety.

        Heuristics (applied in order, only to existing prerequisite edges):
        1. contains: source name is a broader concept of target name
           (e.g. "机器学习" → "监督学习", "数据结构" → "二叉树")
        2. causal: source name contains 原因/背景/动机/问题,
           or target name contains 结果/影响/效果/应用
        3. related: same-chapter adjacent knowledge points (default fallback)
        """
        # Build chapter → knowledge_point_names mapping
        chapter_kp_names: list[list[str]] = []
        for ch_data in chapters_data:
            names = [
                kp["name"] for kp in ch_data.get("knowledge_points", [])
            ]
            chapter_kp_names.append(names)

        # Build kp_name → chapter_index mapping
        kp_chapter: dict[str, int] = {}
        for ci, names in enumerate(chapter_kp_names):
            for name in names:
                kp_chapter[name] = ci

        # Count current relation types
        from sqlalchemy import text
        rows = self._db.execute(
            text(
                "SELECT relation_type, source_node_id, target_node_id "
                "FROM knowledge_edges WHERE course_id = :cid"
            ),
            {"cid": course_id},
        ).fetchall()

        edge_map: dict[tuple[int, int], str] = {}
        for row in rows:
            edge_map[(row[1], row[2])] = row[0]

        # If we already have non-prerequisite edges, skip diversification
        non_pre_count = sum(
            1 for rt in edge_map.values() if rt != "prerequisite"
        )
        total_edges = len(edge_map)
        if total_edges > 0 and non_pre_count / total_edges >= 0.2:
            logger.info(
                "Edge types already diverse (%d/%d non-prerequisite), skipping auto-diversify",
                non_pre_count, total_edges,
            )
            return

        logger.info(
            "Edge types need diversification: %d/%d non-prerequisite. "
            "Applying heuristic rules...",
            non_pre_count, total_edges,
        )

        # Build id→name and name→id maps for quick lookup
        id_to_name: dict[int, str] = {}
        name_to_id: dict[str, int] = {}
        for name, node in all_kp_map.items():
            id_to_name[node.id] = name
            name_to_id[name] = node.id

        # Collect all existing edges for re-typing
        edges_to_update: list[tuple[int, int, str]] = []
        processed: set[tuple[int, int]] = set()

        # Rule 1: contains — source is broader concept of target
        for (src_id, tgt_id), rt in edge_map.items():
            if rt != "prerequisite" or (src_id, tgt_id) in processed:
                continue
            src_name = id_to_name.get(src_id, "")
            tgt_name = id_to_name.get(tgt_id, "")
            if not src_name or not tgt_name:
                continue
            # Heuristic: source name is a substring or shorter broader term
            # that the target is a specific instance of
            if _is_contains_relation(src_name, tgt_name):
                edges_to_update.append((src_id, tgt_id, "contains"))
                processed.add((src_id, tgt_id))

        # Rule 2: causal — source is cause/motivation, target is effect/result
        for (src_id, tgt_id), rt in edge_map.items():
            if rt != "prerequisite" or (src_id, tgt_id) in processed:
                continue
            src_name = id_to_name.get(src_id, "")
            tgt_name = id_to_name.get(tgt_id, "")
            if not src_name or not tgt_name:
                continue
            if _is_causal_relation(src_name, tgt_name):
                edges_to_update.append((src_id, tgt_id, "causal"))
                processed.add((src_id, tgt_id))

        # Rule 3: related — same-chapter adjacent knowledge points
        for (src_id, tgt_id), rt in edge_map.items():
            if rt != "prerequisite" or (src_id, tgt_id) in processed:
                continue
            src_name = id_to_name.get(src_id, "")
            tgt_name = id_to_name.get(tgt_id, "")
            if not src_name or not tgt_name:
                continue
            src_ch = kp_chapter.get(src_name, -1)
            tgt_ch = kp_chapter.get(tgt_name, -1)
            if src_ch == tgt_ch and src_ch >= 0:
                edges_to_update.append((src_id, tgt_id, "related"))
                processed.add((src_id, tgt_id))

        # Apply updates
        if edges_to_update:
            for src_id, tgt_id, new_rt in edges_to_update:
                self._db.execute(
                    text(
                        "UPDATE knowledge_edges SET relation_type = :rt "
                        "WHERE course_id = :cid AND source_node_id = :sid "
                        "AND target_node_id = :tid"
                    ),
                    {
                        "rt": new_rt,
                        "cid": course_id,
                        "sid": src_id,
                        "tid": tgt_id,
                    },
                )
            self._db.flush()
            logger.info(
                "Auto-diversified %d edges: %s",
                len(edges_to_update),
                ", ".join(
                    f"{id_to_name.get(s,'?')}→{id_to_name.get(t,'?')}={rt}"
                    for s, t, rt in edges_to_update[:10]
                ),
            )
        else:
            logger.info("No edges eligible for auto-diversification")

    # -----------------------------------------------------------------------
    # Internal: fallback syllabus when LLM fails
    # -----------------------------------------------------------------------
    def _fallback_syllabus(
        self, topic: str, description: str | None = None
    ) -> dict[str, Any]:
        """Generate a minimal syllabus without LLM as a fallback."""
        logger.warning(
            "⚠️ Using FALLBACK syllabus (NO LLM call) for topic=%s — "
            "check your API key and network connectivity!", topic
        )
        return {
            "title": topic + " (Fallback)",
            "description": description or f"{topic} 相关课程内容",
            "chapters": [
                {
                    "title": "概述",
                    "order": 1,
                    "knowledge_points": [
                        {
                            "name": f"{topic} 基本概念",
                            "type": "概念",
                            "importance": 0.9,
                            "prerequisites": [],
                        }
                    ],
                },
                {
                    "title": "核心内容",
                    "order": 2,
                    "knowledge_points": [
                        {
                            "name": f"{topic} 核心原理",
                            "type": "概念",
                            "importance": 1.0,
                            "prerequisites": [f"{topic} 基本概念"],
                        },
                        {
                            "name": f"{topic} 实践应用",
                            "type": "实践",
                            "importance": 0.8,
                            "prerequisites": [f"{topic} 核心原理"],
                        },
                    ],
                },
                {
                    "title": "进阶与总结",
                    "order": 3,
                    "knowledge_points": [
                        {
                            "name": f"{topic} 综合案例",
                            "type": "综合",
                            "importance": 0.7,
                            "prerequisites": [f"{topic} 实践应用"],
                        }
                    ],
                },
            ],
            "edges": [
                {"source": f"{topic} 基本概念", "target": f"{topic} 核心原理", "relation_type": "prerequisite"},
                {"source": f"{topic} 核心原理", "target": f"{topic} 实践应用", "relation_type": "prerequisite"},
                {"source": f"{topic} 实践应用", "target": f"{topic} 综合案例", "relation_type": "related"},
            ],
        }


# ===========================================================================
# Heuristic helpers for edge-type diversification
# ===========================================================================
_CONTAINS_KEYWORDS = [
    ("机器学习", "监督学习"), ("机器学习", "无监督学习"),
    ("机器学习", "深度学习"), ("数据结构", "二叉树"),
    ("数据结构", "链表"), ("数据结构", "栈"),
    ("数据结构", "队列"), ("算法", "排序"),
    ("算法", "搜索"), ("网络", "TCP"),
    ("网络", "HTTP"), ("数据库", "SQL"),
    ("数据库", "索引"), ("操作系统", "进程"),
    ("操作系统", "线程"), ("编程语言", "面向对象"),
    ("面向对象", "封装"), ("面向对象", "继承"),
    ("面向对象", "多态"),
]


def _is_contains_relation(src_name: str, tgt_name: str) -> bool:
    """Check if src is a broader concept that contains tgt."""
    # 1. Exact keyword match from known hierarchies
    for broad, narrow in _CONTAINS_KEYWORDS:
        if broad in src_name and narrow in tgt_name:
            return True

    # 2. tgt name is longer and contains src name as substring
    #    e.g. "测试" contains "单元测试", "继承" contains "多重继承"
    if len(tgt_name) > len(src_name) and src_name in tgt_name:
        return True

    # 3. src name ends with 基础/原理/概念 and tgt is more specific
    for suffix in ("基础", "原理", "概念", "概述", "体系"):
        if src_name.endswith(suffix):
            base = src_name[: -len(suffix)]
            if base and base in tgt_name:
                return True

    return False


_CAUSAL_SOURCE_PATTERNS = ("原因", "背景", "动机", "问题", "挑战", "需求", "痛点", "瓶颈")
_CAUSAL_TARGET_PATTERNS = ("结果", "影响", "效果", "应用", "实践", "案例", "解决方案", "对策", "优化")


def _is_causal_relation(src_name: str, tgt_name: str) -> bool:
    """Check if src→tgt is a causal relationship."""
    src_lower = src_name.lower()
    tgt_lower = tgt_name.lower()

    # Source has cause/motivation keywords
    for kw in _CAUSAL_SOURCE_PATTERNS:
        if kw in src_lower:
            return True

    # Target has effect/result keywords
    for kw in _CAUSAL_TARGET_PATTERNS:
        if kw in tgt_lower:
            return True

    return False
