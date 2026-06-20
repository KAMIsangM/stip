"""Mind map generator — creates structured mind map data from knowledge graph."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

_MINDMAP_SYSTEM = """你是一个知识结构设计师。根据提供的章节知识点，生成一个层级化思维导图。

要求：
1. 输出必须是严格的 JSON 格式
2. 导图以章节标题为根节点
3. 每个知识点为二级节点，其子概念为三级节点
4. 结构应体现知识的层级关系

输出格式：
{
  "root": {
    "name": "根节点标题",
    "children": [
      {
        "name": "知识点1",
        "children": [
          {"name": "子概念A"},
          {"name": "子概念B"}
        ]
      }
    ]
  }
}"""


class MindMapGenerator(BaseModalGenerator):
    modal_type = "mindmap"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        kp_names = [kp.get("name", "") for kp in kps]

        user = f"""章节标题：{chapter_title}
知识点：{", ".join(kp_names) if kp_names else "无特定知识点"}
课程标题：{context.get("course_title", "")}

请生成思维导图结构数据。"""

        try:
            raw = await self._call_llm(_MINDMAP_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[mindmap] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": None,
        }

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        children = []
        for kp in kps:
            children.append({
                "name": kp.get("name", ""),
                "children": [{"name": "概念理解"}, {"name": "实践应用"}],
            })

        if not children:
            children = [{"name": chapter_title, "children": [{"name": "核心内容"}]}]

        return {
            "root": {
                "name": chapter_title,
                "children": children,
            }
        }
