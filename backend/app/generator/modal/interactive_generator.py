"""Advanced interactive teaching material generator.

Upgraded from simple drag-sort to rich HTML animation generation:
- AI generates structured animation description JSON per knowledge point
- Jinja2 templates render self-contained HTML animations (anime.js CDN)
- Supports: sort animation, data structure animation, flowchart step-by-step,
  formula derivation, code execution visualization
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.core.config import get_assets_root
from app.generator.base_generator import BaseModalGenerator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jinja2 template environment
# ---------------------------------------------------------------------------
_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "interactive"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,  # We're generating full HTML, need raw injection
)

# ---------------------------------------------------------------------------
# Template selection map: animation_type → template file
# ---------------------------------------------------------------------------
_TEMPLATE_MAP = {
    "sort_animation": "sort_animation.html",
    "data_structure": "data_structure.html",
    "flowchart_step": "flowchart_step.html",
    "formula_derivation": "formula_derivation.html",
    "code_execution": "code_execution.html",
}

# ---------------------------------------------------------------------------
# New AI system prompt — generates animation description JSON
# ---------------------------------------------------------------------------
_INTERACTIVE_SYSTEM = """你是一位高级互动教材设计师和动画工程师。你的任务是根据提供的章节知识点，为每个知识点生成一个可渲染为 HTML 动画的结构化 JSON 描述。

## 动画类型选择规则

根据知识点的性质，从以下 5 种动画类型中选择最合适的一种：

1. **sort_animation** — 排序算法可视化
   - 适用于：冒泡排序、快速排序、归并排序、选择排序、插入排序等
   - 需要生成：初始数组 + 每步的状态变化（比较、交换、已排序标记）

2. **data_structure** — 数据结构操作动画
   - 适用于：链表插入/删除、栈push/pop、队列enqueue/dequeue、二叉树遍历等
   - 需要生成：节点坐标位置 + 每步的节点高亮、指针移动、插入动画

3. **flowchart_step** — 流程图逐步演示
   - 适用于：算法流程、业务流程、决策过程、if-else分支逻辑等
   - 需要生成：流程节点列表 + 每步高亮哪个节点

4. **formula_derivation** — 公式推导动画
   - 适用于：数学公式推导、物理公式变换、化学方程式配平等
   - 需要生成：初始公式 + 每步推导内容和公式 HTML 表示

5. **code_execution** — 代码执行可视化
   - 适用于：展示代码逐步执行过程、变量变化追踪、算法断点调试
   - 需要生成：代码行列表 + 每步执行的行号、变量快照、输出内容

## 输出格式（严格的 JSON）

你必须为每个知识点生成一个动画对象，放入 animations 数组中。

```json
{
  "title": "互动教材标题",
  "animations": [
    {
      "knowledge_point": "知识点名称",
      "animation_type": "sort_animation",
      "title": "动画标题",
      "description": "简短描述（10-20字）",
      "explanation": "详细的算法/原理说明（50-150字）",
      "algorithm_name": "冒泡排序",
      "initial_array": [5, 3, 8, 1, 9, 2],
      "element_count": 6,
      "steps": [
        {
          "array": [3, 5, 8, 1, 9, 2],
          "comparing": [0, 1],
          "swapping": [0, 1],
          "sorted": [],
          "description": "比较 5 和 3，5>3，交换"
        }
      ]
    },
    {
      "knowledge_point": "知识点名称2",
      "animation_type": "data_structure",
      "title": "动画标题",
      "ds_type": "linked_list",
      "ds_type_name": "链表",
      "description": "简短描述",
      "explanation": "数据结构操作说明",
      "steps": [
        {
          "nodes": [{"x": 50, "y": 80, "w": 55, "h": 40, "label": "A", "shape": "rect"}],
          "edges": [{"x1": 105, "y1": 100, "x2": 155, "y2": 100}],
          "highlight_nodes": [0],
          "highlight_edges": [],
          "pointer_pos": {"x": 77, "y": 70},
          "pointer_label": "head",
          "inserted_nodes": [],
          "description": "初始链表状态"
        }
      ]
    },
    {
      "animation_type": "flowchart_step",
      "steps": [
        {
          "nodes": [
            {"label": "开始", "type": "start"},
            {"label": "条件判断?", "type": "decision"},
            {"label": "满足条件 → 操作A", "type": "result"},
            {"label": "不满足 → 操作B", "type": "result"}
          ],
          "highlight_index": 0,
          "completed_indices": [],
          "description": "步骤说明 — node类型可选: start, decision, result"
        }
      ]
    },
    {
      "animation_type": "formula_derivation",
      "initial_formula": "E = mc²",
      "steps": [
        {
          "content": "根据爱因斯坦质能方程 E = mc²...",
          "explanation": "第一步推导说明",
          "formula_html": "E = mc<sup>2</sup>"
        }
      ]
    },
    {
      "animation_type": "code_execution",
      "code_filename": "example.py",
      "code_lines": ["def add(a, b):", "    return a + b", "", "result = add(2, 3)"],
      "steps": [
        {
          "line": 0,
          "variables": {},
          "changed_vars": [],
          "output": "",
          "description": "定义函数 add"
        }
      ]
    }
  ],
  "exercises": [
    {
      "type": "drag_sort",
      "instruction": "请将以下步骤按正确顺序排列",
      "items": ["步骤A", "步骤B", "步骤C"],
      "correct_order": [0, 1, 2]
    }
  ],
  "glossary": [
    {"term": "术语", "definition": "定义"}
  ]
}
```

## 关键要求

1. **每个知识点必须生成一个动画**，animations 数组不能为空
2. **steps 数组必须足够详细**：sort_animation 至少 4 步，data_structure 至少 3 步，flowchart_step 至少 3 步
3. **sort_animation 的 steps**：必须包含完整的排序过程，每步都要有 comparing 和 swapping 信息
4. **data_structure 的节点坐标**：节点间距 70-100px，x 从 30 开始，y 从 60 开始
5. **flowchart_step 的 nodes**：至少 3 个节点，节点类型：开始用 type="start"，判断用 type="decision"，结果/操作用 type="result"。按流程顺序排列节点，highlight_index 按顺序递增
6. **formula_derivation 的 formula_html**：使用 HTML 标签表示公式，如上标 <sup>、下标 <sub>、希腊字母用 Unicode
7. **code_execution 的 code_lines**：代码行数 5-15 行，steps 至少 4 步
8. **exercises 保留**：为整个章节保留至少 1 个互动练习题
9. **输出必须是严格 JSON**，不要包含 ```json 以外的任何文字"""


class InteractiveGenerator(BaseModalGenerator):
    """Advanced interactive material generator.

    Generates structured animation JSON via LLM, then renders it
    into self-contained HTML files using Jinja2 templates.
    """

    modal_type = "interactive_html"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        course_id = context.get("course_id")

        # Build detailed knowledge point context
        kp_lines: list[str] = []
        for i, kp in enumerate(kps, 1):
            name = kp.get("name", "")
            kp_type = kp.get("type", "")
            importance = kp.get("importance", "")
            extra = []
            if kp_type:
                extra.append(f"类型：{kp_type}")
            if importance != "":
                extra.append(f"重要性：{importance}")
            suffix = f"（{'；'.join(extra)}）" if extra else ""
            kp_lines.append(f"{i}. {name}{suffix}")

        kp_text = "\n".join(kp_lines) if kp_lines else "无特定知识点"

        user = f"""章节标题：{chapter_title}
课程标题：{context.get("course_title", "")}

本章知识点：
{kp_text}

请为每个知识点生成合适的动画演示。注意：
- 根据知识点类型选择最合适的动画类型
- 概念型知识点适合 flowchart_step 或 formula_derivation
- 技能型/实践型知识点适合 sort_animation、data_structure 或 code_execution
- 确保 steps 数组足够详细，能清晰展示完整过程"""

        try:
            raw = await self._call_llm(_INTERACTIVE_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[interactive] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        # Render HTML files for each animation
        html_files = await self._render_animations(content, course_id, chapter_id, chapter_title)

        # Add HTML file paths to content for frontend
        content["html_files"] = html_files

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": html_files[0] if html_files else None,
        }

    # ------------------------------------------------------------------
    # HTML rendering via Jinja2
    # ------------------------------------------------------------------
    async def _render_animations(
        self,
        content: dict[str, Any],
        course_id: int | None,
        chapter_id: int,
        chapter_title: str,
    ) -> list[str]:
        """Render each animation into a self-contained HTML file."""
        import asyncio

        animations = content.get("animations", [])
        if not animations:
            return []

        # Ensure output directory exists
        course_dir_name = f"course_{course_id}" if course_id else f"chapter_{chapter_id}"
        export_dir = get_assets_root() / course_dir_name / "interactive"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in " _-")[:40].strip()
        html_paths: list[str] = []

        loop = asyncio.get_running_loop()

        for idx, anim in enumerate(animations):
            anim_type = anim.get("animation_type", "")
            template_name = _TEMPLATE_MAP.get(anim_type)

            if not template_name:
                logger.warning("[interactive] Unknown animation_type: %s, skipping", anim_type)
                continue

            try:
                template = _jinja_env.get_template(template_name)

                # Prepare template context with JSON-serialized steps
                template_context = self._prepare_template_context(anim, content)

                # Render in thread pool to avoid blocking
                html_content = await loop.run_in_executor(
                    None, template.render, template_context,
                )

                # Save HTML file
                kp_name = anim.get("knowledge_point", f"anim_{idx}")
                safe_kp = "".join(c for c in kp_name if c.isalnum() or c in " _-")[:30].strip()
                filename = f"{safe_title or 'chapter'}_{chapter_id}_{safe_kp or idx}.html"
                filepath = export_dir / filename
                filepath.write_text(html_content, encoding="utf-8")

                url_path = f"/assets/{course_dir_name}/interactive/{filename}"
                html_paths.append(url_path)
                logger.info("[interactive] Rendered HTML: %s", url_path)

            except Exception as e:
                logger.warning("[interactive] Failed to render template %s: %s", template_name, e)

        logger.info("[interactive] Rendered %d animation HTML files", len(html_paths))
        return html_paths

    def _prepare_template_context(
        self, anim: dict[str, Any], content: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepare context dict for Jinja2 template rendering."""
        anim_type = anim.get("animation_type", "")
        steps = anim.get("steps", [])

        ctx = {
            "title": anim.get("title", content.get("title", "互动教材")),
            "description": anim.get("description", ""),
            "explanation": anim.get("explanation", ""),
            "steps_json": json.dumps(steps, ensure_ascii=False),
        }

        # Type-specific context
        if anim_type == "sort_animation":
            ctx["algorithm_name"] = anim.get("algorithm_name", "排序算法")
            ctx["initial_array"] = json.dumps(anim.get("initial_array", []))
            ctx["element_count"] = anim.get("element_count", len(anim.get("initial_array", [])))

        elif anim_type == "data_structure":
            ctx["ds_type"] = anim.get("ds_type", "linked_list")
            ctx["ds_type_name"] = anim.get("ds_type_name", "数据结构")

        elif anim_type == "flowchart_step":
            # Transform LLM flat-node format to tree-friendly format
            steps = anim.get("steps", [])
            # Extract unique nodes from the first step
            raw_nodes = steps[0].get("nodes", []) if steps else []
            node_list = []
            for i, n in enumerate(raw_nodes):
                ntype = n.get("type", "normal")
                css_type = "start" if ntype == "start" else ("decision" if ntype == "decision" else "result")
                node_list.append({"id": f"n{i}", "text": n.get("label", ""), "type": css_type})
            ctx["nodes_json"] = json.dumps(node_list, ensure_ascii=False)

            # Build step sequence from highlight_index progression
            steps_desc = []
            for step in steps:
                hi = step.get("highlight_index", len(steps_desc))
                nid = f"n{hi}" if hi < len(node_list) else "n0"
                steps_desc.append({"id": nid, "desc": step.get("description", "")})
            ctx["steps_descriptions_json"] = json.dumps(steps_desc, ensure_ascii=False)

        elif anim_type == "code_execution":
            ctx["code_filename"] = anim.get("code_filename", "code.py")
            ctx["code_lines_json"] = json.dumps(anim.get("code_lines", []), ensure_ascii=False)

        elif anim_type == "formula_derivation":
            ctx["initial_formula"] = anim.get("initial_formula", "F = ma")

        return ctx

    # ------------------------------------------------------------------
    # Fallback content
    # ------------------------------------------------------------------
    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        kp_names = [kp.get("name", "") for kp in kps]

        animations = []
        for kp_name in kp_names[:3]:
            animations.append({
                "knowledge_point": kp_name,
                "animation_type": "flowchart_step",
                "title": f"{kp_name} - 学习流程",
                "description": f"{kp_name}的学习步骤演示",
                "explanation": f"本节将逐步学习{kp_name}的核心概念和应用方法。通过分步演示，帮助理解每个关键环节。",
                "steps": [
                    {
                        "nodes": [
                            {"label": "开始学习", "type": "start"},
                            {"label": f"理解{kp_name}概念", "type": "decision"},
                            {"label": "掌握核心原理", "type": "decision"},
                            {"label": "实践应用", "type": "result"},
                            {"label": "总结回顾", "type": "result"},
                        ],
                        "highlight_index": 0,
                        "completed_indices": [],
                        "description": "第一步：开始进入学习环节",
                    },
                    {
                        "nodes": [
                            {"label": "开始学习", "type": "start"},
                            {"label": f"理解{kp_name}概念", "type": "decision"},
                            {"label": "掌握核心原理", "type": "decision"},
                            {"label": "实践应用", "type": "result"},
                            {"label": "总结回顾", "type": "result"},
                        ],
                        "highlight_index": 1,
                        "completed_indices": [0],
                        "description": "第二步：深入理解基本概念定义",
                    },
                    {
                        "nodes": [
                            {"label": "开始学习", "type": "start"},
                            {"label": f"理解{kp_name}概念", "type": "decision"},
                            {"label": "掌握核心原理", "type": "decision"},
                            {"label": "实践应用", "type": "result"},
                            {"label": "总结回顾", "type": "result"},
                        ],
                        "highlight_index": 2,
                        "completed_indices": [0, 1],
                        "description": "第三步：掌握核心原理与机制",
                    },
                    {
                        "nodes": [
                            {"label": "开始学习", "type": "start"},
                            {"label": f"理解{kp_name}概念", "type": "decision"},
                            {"label": "掌握核心原理", "type": "decision"},
                            {"label": "实践应用", "type": "result"},
                            {"label": "总结回顾", "type": "result"},
                        ],
                        "highlight_index": 3,
                        "completed_indices": [0, 1, 2],
                        "description": "第四步：通过实践巩固知识",
                    },
                    {
                        "nodes": [
                            {"label": "开始学习", "type": "start"},
                            {"label": f"理解{kp_name}概念", "type": "decision"},
                            {"label": "掌握核心原理", "type": "decision"},
                            {"label": "实践应用", "type": "result"},
                            {"label": "总结回顾", "type": "result"},
                        ],
                        "highlight_index": 4,
                        "completed_indices": [0, 1, 2, 3],
                        "description": "第五步：总结归纳，形成知识体系",
                    },
                ],
            })

        return {
            "title": chapter_title,
            "animations": animations,
            "exercises": [
                {
                    "type": "drag_sort",
                    "instruction": "请将以下概念按学习顺序排列",
                    "items": kp_names[:4] if kp_names else [chapter_title],
                    "correct_order": list(range(min(4, len(kp_names)))),
                }
            ],
            "glossary": [
                {"term": kp.get("name", ""), "definition": f"{kp.get('name', '')}的相关定义"}
                for kp in kps[:3]
            ],
        }
