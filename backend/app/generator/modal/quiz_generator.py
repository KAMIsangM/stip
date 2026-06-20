"""Quiz generator — generates MCQ/true-false/short-answer questions for a chapter."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

_QUIZ_SYSTEM = """你是一个课程测验设计专家。根据提供的章节知识点，生成一套测验题目。

要求：
1. 输出必须是严格的 JSON 格式
2. 题目应覆盖章节核心知识点
3. 题型包括选择题(mcq)、判断题(tf)、简答题(short_answer)
4. 每道题包含答案和详细解析

输出格式：
{
  "quiz_title": "测验标题",
  "questions": [
    {
      "type": "mcq",
      "question": "题目文本",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "A",
      "explanation": "解析文本"
    },
    {
      "type": "tf",
      "question": "题目文本",
      "answer": true,
      "explanation": "解析文本"
    },
    {
      "type": "short_answer",
      "question": "题目文本",
      "answer": "参考答案",
      "explanation": "解析文本"
    }
  ],
  "total_score": 100,
  "pass_score": 60
}"""


class QuizGenerator(BaseModalGenerator):
    modal_type = "quiz"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        kp_names = [kp.get("name", "") for kp in kps]

        user = f"""章节标题：{chapter_title}
知识点：{", ".join(kp_names) if kp_names else "无特定知识点"}
课程标题：{context.get("course_title", "")}

请生成 3-5 道测验题目（包含选择题、判断题、简答题混合）。"""

        try:
            raw = await self._call_llm(_QUIZ_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[quiz] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": None,
        }

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        kp_name = kps[0]["name"] if kps else chapter_title
        return {
            "quiz_title": f"{chapter_title} - 章节测验",
            "questions": [
                {
                    "type": "mcq",
                    "question": f"下列关于{kp_name}的描述，正确的是？",
                    "options": [
                        f"A. {kp_name}是一个重要概念",
                        f"B. {kp_name}与本章内容无关",
                        f"C. {kp_name}是错误的表述",
                        f"D. 以上都不对",
                    ],
                    "answer": "A",
                    "explanation": f"{kp_name}是本章的核心知识点，需要重点掌握。",
                },
                {
                    "type": "tf",
                    "question": f"{chapter_title}涵盖了多个重要知识点的学习。",
                    "answer": True,
                    "explanation": f"本章确实涵盖了多个知识点的系统学习。",
                },
            ],
            "total_score": 100,
            "pass_score": 60,
        }
