"""Interactive HTML generator — produces structured interactive teaching material."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

_INTERACTIVE_SYSTEM = """你是一个互动教材设计师。根据提供的章节知识点，生成互动式HTML教材内容。

要求：
1. 输出必须是严格的 JSON 格式
2. 内容应包含可视化元素描述（流程图、对比表、代码示例等）
3. 包含至少 2 个互动练习（拖拽排序、填空、代码执行等）
4. 每个知识点都应有对应的讲解和示例

输出格式：
{
  "title": "教材标题",
  "sections": [
    {
      "heading": "小节标题",
      "content": "讲解文本（支持 Markdown）",
      "visual_type": "flowchart",
      "visual_data": {"nodes": [], "edges": []},
      "interactive_exercise": {
        "type": "drag_sort",
        "instruction": "操作说明",
        "items": ["项1", "项2"],
        "correct_order": [0, 1]
      }
    }
  ],
  "glossary": [{"term": "术语", "definition": "定义"}]
}"""


class InteractiveGenerator(BaseModalGenerator):
    modal_type = "interactive_html"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        kp_names = [kp.get("name", "") for kp in kps]

        user = f"""章节标题：{chapter_title}
知识点：{", ".join(kp_names) if kp_names else "无特定知识点"}
课程标题：{context.get("course_title", "")}

请生成互动式教材内容。"""

        try:
            raw = await self._call_llm(_INTERACTIVE_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[interactive] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": None,
        }

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "title": chapter_title,
            "sections": [
                {
                    "heading": f"{chapter_title} 概述",
                    "content": f"## {chapter_title}\n\n本章将介绍{'、'.join(kp.get('name', '') for kp in kps[:3])}等核心知识点。",
                    "visual_type": "flowchart",
                    "visual_data": {"nodes": [], "edges": []},
                    "interactive_exercise": {
                        "type": "drag_sort",
                        "instruction": "请将以下概念按学习顺序排列",
                        "items": [kp.get("name", "") for kp in kps[:4]] if kps else [chapter_title],
                        "correct_order": list(range(min(4, len(kps)))),
                    },
                }
            ],
            "glossary": [{"term": kp.get("name", ""), "definition": f"{kp.get('name', '')}的相关定义"} for kp in kps[:3]],
        }
