"""Immersive text generator — generates structured teaching text with embedded questions."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

_TEXT_SYSTEM = """你是一个资深课程讲师。根据提供的章节信息和知识点，生成沉浸式教学文本。

要求：
1. 输出必须是严格的 JSON 格式
2. 教学文本应深入浅出、生动有趣
3. 在关键知识点后自动插入 1-2 个嵌入式检验问题
4. 文本应分为多个段落，每个段落有明确的主题
5. **重要：sections 中每个 heading 必须使用具体的子主题名称（如"概述"、"核心概念"、"实践应用"、"常见问题"等），严禁重复章节标题**

输出格式：
{
  "sections": [
    {
      "heading": "小节标题（使用具体子主题，不要包含章节标题）",
      "paragraphs": ["段落1文本", "段落2文本"],
      "embedded_questions": [
        {"question": "问题文本", "answer": "答案", "explanation": "解析"}
      ]
    }
  ],
  "summary": "本节总结",
  "further_reading": ["推荐阅读1", "推荐阅读2"]
}"""


class TextGenerator(BaseModalGenerator):
    modal_type = "text"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        kp_names = [kp.get("name", "") for kp in kps]

        user = f"""章节标题：{chapter_title}
知识点：{", ".join(kp_names) if kp_names else "无特定知识点"}
课程标题：{context.get("course_title", "")}

请生成沉浸式教学文本。"""

        try:
            raw = await self._call_llm(_TEXT_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[text] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": None,
        }

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "sections": [
                {
                    "heading": "概述",
                    "paragraphs": [
                        f"本章将介绍{'、'.join(kp.get('name', '') for kp in kps[:3]) if kps else chapter_title}的核心内容。",
                        "请认真学习本章知识点，理解其原理与应用。",
                    ],
                    "embedded_questions": [
                        {
                            "question": f"请简述{chapter_title}的核心概念是什么？",
                            "answer": f"{chapter_title}涉及的核心概念需要结合上下文理解。",
                            "explanation": "建议回顾本章知识点加深理解。",
                        }
                    ],
                }
            ],
            "summary": f"本章介绍了{chapter_title}的基本概念。",
            "further_reading": [],
        }
