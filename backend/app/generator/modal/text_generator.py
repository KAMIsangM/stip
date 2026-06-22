"""Immersive text generator — generates structured teaching text with embedded questions."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

_TEXT_SYSTEM = """你是一位资深课程讲师，拥有丰富的教学经验。你的任务是根据提供的章节信息和知识点，生成高质量的沉浸式教学文本。

## 核心要求

1. **输出必须是严格的 JSON 格式**，不可包含任何解释性文字
2. **教学文本应深入浅出、生动有趣**：
   - 使用通俗易懂的语言解释复杂概念
   - 善用类比、比喻帮助理解
   - 穿插实际案例和应用场景
   - 保持知识密度，每个段落都要有实质内容
3. **嵌入式检验问题**：在关键知识点后自动插入 1-2 个检验问题，帮助学习者巩固理解
4. **段落结构清晰**：每个 section 有明确的子主题，段落之间逻辑递进
5. **重要：sections 中每个 heading 必须使用具体的子主题名称**（如"概述"、"核心概念"、"深入理解"、"实践应用"、"常见误区"、"案例分析"等），严禁重复章节标题
6. **知识点全覆盖**：必须覆盖所有提供的知识点，不能遗漏
7. **每个段落至少 80 字**：确保有足够的内容深度

## 输出格式

{
  "sections": [
    {
      "heading": "小节标题（具体子主题，不包含章节标题）",
      "paragraphs": ["段落1（至少80字的完整教学内容）", "段落2（至少80字的完整教学内容）"],
      "embedded_questions": [
        {"question": "基于本小节内容的检验问题", "answer": "正确答案", "explanation": "答案解析，说明为什么这是正确答案"}
      ]
    }
  ],
  "summary": "本节总结（150-300字，概括核心内容和学习要点）",
  "further_reading": ["推荐阅读1（具体书名/文章名+作者）", "推荐阅读2"]
}"""


class TextGenerator(BaseModalGenerator):
    modal_type = "text"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])

        # Build detailed knowledge point info for richer context
        kp_lines: list[str] = []
        for i, kp in enumerate(kps, 1):
            name = kp.get("name", "")
            kp_type = kp.get("type", "")
            importance = kp.get("importance", "")
            prerequisites = kp.get("prerequisites", [])
            extra = []
            if kp_type:
                extra.append(f"类型：{kp_type}")
            if importance != "":
                extra.append(f"重要性：{importance}")
            if prerequisites:
                extra.append(f"前置知识：{', '.join(prerequisites)}")
            suffix = f"（{'；'.join(extra)}）" if extra else ""
            kp_lines.append(f"{i}. {name}{suffix}")
        kp_text = "\n".join(kp_lines) if kp_lines else "无特定知识点"

        course_desc = context.get("course_description", "")
        desc_line = f"\n课程简介：{course_desc}" if course_desc else ""

        user = f"""## 课程信息
课程标题：{context.get("course_title", "")}{desc_line}

## 本章信息
章节标题：{chapter_title}

## 本章知识点（请全部覆盖）
{kp_text}

## 任务要求
请根据以上信息，生成沉浸式教学文本。要求：
1. 覆盖所有知识点，根据重要性合理分配篇幅
2. 每个 section 的段落要有足够的教学深度
3. 嵌入式问题要紧扣知识点，具有检验效果
4. 推荐阅读要具体可查，不要编造"""

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
        kp_names = [kp.get("name", "") for kp in kps]
        kp_types = {kp.get("name", ""): kp.get("type", "概念") for kp in kps}

        sections: list[dict[str, Any]] = []

        # Section 1: Overview
        sections.append({
            "heading": "概述",
            "paragraphs": [
                f"在本章中，我们将系统学习{chapter_title}的相关内容。本章涵盖了{'、'.join(kp_names[:4])}{'等' if len(kp_names) > 4 else ''} {len(kps)} 个核心知识点。",
                f"通过本章的学习，你将建立起对{chapter_title}的完整认知框架，理解其核心概念、原理和实际应用。建议在学习过程中做好笔记，遇到不理解的地方及时回顾。",
            ],
            "embedded_questions": [
                {
                    "question": f"本章的核心学习目标是什么？",
                    "answer": f"系统掌握{chapter_title}中的{'、'.join(kp_names[:3])}等核心知识点。",
                    "explanation": f"本章旨在帮助学习者建立对{chapter_title}的全面理解。",
                }
            ],
        })

        # Section 2-N: Distribute knowledge points
        for start in range(0, len(kp_names), 3):
            chunk = kp_names[start:start + 3]
            if not chunk:
                continue
            chunk_detail = []
            for name in chunk:
                kp_type = kp_types.get(name, "概念")
                chunk_detail.append(f"{name}（{kp_type}）")

            sections.append({
                "heading": f"核心概念：{'、'.join(chunk[:2])}" if start == 0 else f"知识拓展：{'、'.join(chunk[:2])}",
                "paragraphs": [
                    f"让我们深入探讨{'、'.join(chunk_detail)}。{'这些概念是理解本章内容的基础。' if start == 0 else '这些知识点进一步拓展了本章的知识体系。'}",
                    f"理解{'、'.join(chunk)}不仅需要记忆定义，更需要通过实际案例和应用来加深理解。请结合生活中的例子来思考这些概念。",
                ],
                "embedded_questions": [
                    {
                        "question": f"请简述{'、'.join(chunk)}的核心内容。",
                        "answer": f"{'、'.join(chunk)}是{chapter_title}中的重要知识点，需要结合上下文理解其定义和应用。",
                        "explanation": "掌握这些知识点是理解后续内容的基础。",
                    }
                ],
            })

        # Last section: Summary
        sections.append({
            "heading": "本章总结",
            "paragraphs": [
                f"本章我们系统学习了{chapter_title}的核心内容，涵盖了{'、'.join(kp_names[:4])}{'等' if len(kp_names) > 4 else ''}知识点。",
                "建议同学们课后整理思维导图，建立知识点之间的联系，并通过练习题来检验掌握程度。知识的真正掌握在于能够灵活运用，请尝试将这些知识应用到实际问题中。",
            ],
            "embedded_questions": [
                {
                    "question": f"回顾本章，你学到了哪些最重要的内容？",
                    "answer": f"本章主要学习了{'、'.join(kp_names[:3])}等核心知识点。",
                    "explanation": "通过回顾总结，可以加深对知识体系的理解。",
                }
            ],
        })

        return {
            "sections": sections,
            "summary": f"本章系统介绍了{chapter_title}，涵盖{'、'.join(kp_names[:4])}{'等' if len(kp_names) > 4 else ''}知识点。学习者在掌握这些知识后，应能够理解其核心原理并应用于实际问题中。",
            "further_reading": [
                f"《{chapter_title}入门指南》",
                f"《深入理解{'、'.join(kp_names[:2])}》" if len(kp_names) >= 2 else f"《{chapter_title}实战》",
            ],
        }
