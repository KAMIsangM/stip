"""PPT generator — outputs slide JSON for frontend carousel rendering + .pptx file + narration MP3s."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from app.core.config import get_assets_root
from app.generator.base_generator import BaseModalGenerator
from app.provider.factory import get_tts_provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Design constants — Academic Education style (warm & approachable)
# ---------------------------------------------------------------------------
_COLOR_PRIMARY = RGBColor(0x1A, 0x56, 0xA8)       # Deep blue (main)
_COLOR_PRIMARY_DARK = RGBColor(0x0F, 0x3B, 0x78)   # Darker blue for gradient bottom
_COLOR_ACCENT = RGBColor(0xE8, 0xF0, 0xFE)          # Light blue accent
_COLOR_ACCENT_STRONG = RGBColor(0xA8, 0xC8, 0xFA)   # Mid blue (decor bar)
_COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_COLOR_NEAR_WHITE = RGBColor(0xFA, 0xFC, 0xFF)      # Warm white background
_COLOR_TEXT = RGBColor(0x2D, 0x37, 0x47)             # Dark gray text
_COLOR_TEXT_LIGHT = RGBColor(0x5F, 0x6B, 0x7A)       # Lighter gray
_COLOR_BULLET = RGBColor(0x1A, 0x56, 0xA8)           # Bullet dot color

_FONT_FAMILY = "Microsoft YaHei"  # 微软雅黑
_SLIDE_W = Inches(13.333)
_SLIDE_H = Inches(7.5)

_PPT_SYSTEM = """你是一位资深教学设计专家和PPT课件设计师，擅长制作高质量的教学幻灯片。你的任务是根据提供的章节信息和知识点，生成一套内容详实、教学逻辑严谨的PPT课件。

## 核心设计原则

1. **输出必须是严格的 JSON 格式**，不可包含任何解释性文字
2. **幻灯片数量**：根据知识点数量和复杂度灵活调整，通常 5-10 张（知识点多的章节应更多）
3. **教学逻辑顺序**：引入热身 → 概念讲解 → 深入分析 → 案例/应用 → 互动/检验 → 总结回顾
4. **知识点全覆盖**：必须覆盖所有提供的知识点，不能遗漏任何重要知识点
5. **内容要有教学深度**：不能只是标题式罗列，要有具体的解释、例证、对比和延伸

## 每张幻灯片的详细要求

### title（标题）
- 简洁有力，通常 4-15 字
- 准确概括本页核心主题
- 各页标题之间逻辑递进

### bullets（要点列表）
- 每个要点必须是一句**完整的、有信息量的话**（15-50字），不能只是短语或标签
- 要点之间逻辑递进，由浅入深
- 要点应包含：概念定义、核心原理、公式或规则、实际例证、注意事项等
- 每页 3-5 个要点
- 严禁要点内容空洞，如"本节将介绍XX"这种无实质内容的句子
- 对于重要知识点，要点中应包含具体数值、公式、案例等可操作信息

### notes（讲解备注，用于语音旁白生成）
- 是一段**流畅完整的讲稿**（150-300字），适合真人朗读
- 对 bullets 中的每个要点进行深入展开和讲解
- 使用"我们""大家""同学们"等亲切称呼，增强课堂代入感
- 自然融入"例如""需要注意的是""思考一下"等教学引导语
- 适当加入设问、停顿提示（如"这里请大家思考一下"）
- 语言风格：专业但不生硬，亲切但不随意

## 知识点覆盖要求

1. 必须覆盖上下文中提供的**所有知识点**
2. 重要知识点（importance ≥ 0.8）应分配独立幻灯片或更多篇幅
3. 不同知识点之间应有自然过渡和逻辑衔接
4. 如果知识点之间存在前驱后继关系，应体现教学顺序

## 输出格式

{
  "title": "课件标题（通常是章节标题或更生动的变体）",
  "slides": [
    {
      "title": "幻灯片标题",
      "bullets": ["包含具体内容的完整句子1", "包含具体内容的完整句子2", "包含具体内容的完整句子3"],
      "notes": "这是一段完整的讲稿，对以上要点进行详细展开和讲解，适合语音朗读..."
    }
  ]
}"""

_NARRATION_VOICE = "zh-CN-YunxiNeural"  # 旁白配音 - 男声


class PPTGenerator(BaseModalGenerator):
    modal_type = "ppt"

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
请根据以上信息，生成一套教学PPT课件。要求：
1. 覆盖所有知识点，重要知识点给予更多篇幅
2. 幻灯片之间逻辑递进，有明确的教学主线
3. 每个要点都要有实质内容，不要空洞的占位文字
4. notes 备注要写成可直接朗读的讲稿"""

        try:
            raw = await self._call_llm(_PPT_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[ppt] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        course_id = context.get("course_id")

        # Run PPTX export and narration TTS in parallel
        pptx_task = asyncio.create_task(
            self._export_pptx_async(content, course_id, chapter_id, chapter_title)
        )
        narration_task = asyncio.create_task(
            self._synthesize_narrations(content, course_id, chapter_id, chapter_title)
        )

        file_path, narration_urls = await asyncio.gather(
            pptx_task, narration_task, return_exceptions=True,
        )

        if isinstance(file_path, Exception):
            logger.warning("[ppt] PPTX export failed: %s", file_path)
            file_path = None
        if isinstance(narration_urls, Exception):
            logger.warning("[ppt] Narration TTS failed: %s", narration_urls)
            narration_urls = []

        # Inject narration URLs into content JSON for frontend
        content["narration_urls"] = narration_urls

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": file_path,
        }

    # ------------------------------------------------------------------
    # Async wrapper for PPTX export (runs in thread pool)
    # ------------------------------------------------------------------
    async def _export_pptx_async(
        self,
        content: dict[str, Any],
        course_id: int | None,
        chapter_id: int,
        chapter_title: str,
    ) -> str | None:
        """Run PPTX export in a thread to avoid blocking the event loop."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._export_pptx, content, course_id, chapter_id, chapter_title,
        )

    # ------------------------------------------------------------------
    # PPTX export — Academic Education style
    # ------------------------------------------------------------------
    def _export_pptx(
        self,
        content: dict[str, Any],
        course_id: int | None,
        chapter_id: int,
        chapter_title: str,
    ) -> str | None:
        """Export slides JSON to a beautifully designed .pptx file."""
        slides = content.get("slides", [])
        if not slides:
            return None

        prs = Presentation()
        prs.slide_width = _SLIDE_W
        prs.slide_height = _SLIDE_H

        total = len(slides)
        for idx, slide_data in enumerate(slides):
            if idx == 0:
                self._add_title_slide(prs, slide_data, chapter_title)
            else:
                self._add_content_slide(prs, slide_data, chapter_title, idx + 1, total)

        # Save to assets directory
        course_dir_name = f"course_{course_id}" if course_id else f"chapter_{chapter_id}"
        export_dir = get_assets_root() / course_dir_name / "ppt"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in " _-")[:40].strip()
        filename = f"{safe_title or 'chapter'}_{chapter_id}.pptx"
        filepath = export_dir / filename

        prs.save(str(filepath))
        logger.info("[ppt] Exported .pptx to %s", filepath)

        return f"/assets/{course_dir_name}/ppt/{filename}"

    # ------------------------------------------------------------------
    # Title slide — gradient blue background, centered white title
    # ------------------------------------------------------------------
    def _add_title_slide(
        self,
        prs: Any,
        slide_data: dict[str, Any],
        chapter_title: str,
    ) -> None:
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)

        # Gradient background via stacked rectangles
        self._draw_gradient_bg(slide)

        # Decorative circle top-right
        self._add_decor_circle(slide, Inches(9.5), Inches(-1.5), Inches(4.0))

        # Decorative circle bottom-left
        self._add_decor_circle(slide, Inches(-1.5), Inches(5.5), Inches(3.0))

        # Centered title
        title_text = slide_data.get("title", chapter_title)
        left = Inches(1.5)
        top = Inches(2.2)
        width = Inches(10.3)
        height = Inches(1.8)

        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = title_text
        self._set_font(run, Pt(40), _COLOR_WHITE, bold=True)

        # Subtitle / chapter label
        sub_left = Inches(1.5)
        sub_top = Inches(4.2)
        sub_width = Inches(10.3)
        sub_height = Inches(1.2)

        subBox = slide.shapes.add_textbox(sub_left, sub_top, sub_width, sub_height)
        stf = subBox.text_frame
        stf.word_wrap = True
        sp = stf.paragraphs[0]
        sp.alignment = PP_ALIGN.CENTER
        srun = sp.add_run()
        srun.text = chapter_title
        self._set_font(srun, Pt(22), _COLOR_ACCENT_STRONG, bold=False)

        # Footer line
        self._add_footer_line(slide, chapter_title)

    # ------------------------------------------------------------------
    # Content slide — header bar + left decor + content card
    # ------------------------------------------------------------------
    def _add_content_slide(
        self,
        prs: Any,
        slide_data: dict[str, Any],
        chapter_title: str,
        page_num: int,
        total: int,
    ) -> None:
        slide_layout = prs.slide_layouts[6]  # Blank
        slide = prs.slides.add_slide(slide_layout)

        # Warm white background
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = _COLOR_NEAR_WHITE

        # Top header bar
        header = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), _SLIDE_W, Inches(1.15),
        )
        header.fill.solid()
        header.fill.fore_color.rgb = _COLOR_PRIMARY
        header.line.fill.background()  # no border

        # Header title text
        h_title = slide.shapes.add_textbox(
            Inches(1.0), Inches(0.15), Inches(10.5), Inches(0.85),
        )
        htf = h_title.text_frame
        htf.word_wrap = True
        hp = htf.paragraphs[0]
        hp.alignment = PP_ALIGN.LEFT
        hrun = hp.add_run()
        hrun.text = slide_data.get("title", "")
        self._set_font(hrun, Pt(30), _COLOR_WHITE, bold=True)

        # Left decorative bar
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.15), Inches(0.12), Inches(5.85),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = _COLOR_ACCENT_STRONG
        bar.line.fill.background()

        # Bottom accent line (thin)
        bot_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(0), Inches(7.0), _SLIDE_W, Inches(0.04),
        )
        bot_line.fill.solid()
        bot_line.fill.fore_color.rgb = _COLOR_ACCENT
        bot_line.line.fill.background()

        # Bullet content area
        bullets = slide_data.get("bullets", [])
        content_left = Inches(1.2)
        content_top = Inches(1.7)
        content_width = Inches(10.8)

        # Light card background behind bullets
        if bullets:
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, content_left, content_top,
                content_width, Inches(min(4.5, len(bullets) * 0.65 + 0.5)),
            )
            card.fill.solid()
            card.fill.fore_color.rgb = _COLOR_WHITE
            card.line.color.rgb = _COLOR_ACCENT
            card.line.width = Pt(1)
            # Rounded corners
            self._set_shape_radius(card)

        txBox = slide.shapes.add_textbox(
            Inches(1.8), Inches(2.0), Inches(9.8), Inches(4.2),
        )
        tf = txBox.text_frame
        tf.word_wrap = True

        for i, bullet_text in enumerate(bullets):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()

            p.space_before = Pt(12)
            p.space_after = Pt(6)

            # Custom bullet dot
            run_bullet = p.add_run()
            run_bullet.text = "● "
            self._set_font(run_bullet, Pt(14), _COLOR_BULLET, bold=False)

            # Bullet text
            run_text = p.add_run()
            run_text.text = bullet_text
            self._set_font(run_text, Pt(20), _COLOR_TEXT, bold=False)

        # Speaker notes
        notes_text = slide_data.get("notes", "")
        if notes_text:
            try:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = notes_text  # type: ignore[union-attr]
            except Exception:
                pass

        # Footer
        self._add_footer(slide, chapter_title, page_num, total)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _draw_gradient_bg(self, slide: Any) -> None:
        """Draw a vertical gradient from deep blue (top) to mid blue (bottom) using rectangles."""
        steps = 30
        band_h = int(_SLIDE_H / steps)

        for i in range(steps):
            t = i / (steps - 1)
            r = int(_COLOR_PRIMARY_DARK[0] + (_COLOR_PRIMARY[0] - _COLOR_PRIMARY_DARK[0]) * t)
            g = int(_COLOR_PRIMARY_DARK[1] + (_COLOR_PRIMARY[1] - _COLOR_PRIMARY_DARK[1]) * t)
            b = int(_COLOR_PRIMARY_DARK[2] + (_COLOR_PRIMARY[2] - _COLOR_PRIMARY_DARK[2]) * t)

            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0), band_h * i, _SLIDE_W, band_h,
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(r, g, b)
            shape.line.fill.background()

    @staticmethod
    def _add_decor_circle(slide: Any, left: Any, top: Any, size: Any) -> None:
        """Add a semi-transparent decorative circle."""
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, left, top, size, size,
        )
        circle.fill.solid()
        # Semi-transparent white (using light blue with opacity illusion)
        circle.fill.fore_color.rgb = RGBColor(0x25, 0x66, 0xBB)
        circle.line.fill.background()

    def _add_footer_line(self, slide: Any, chapter_title: str) -> None:
        """Add a thin footer line with chapter title on title slide."""
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(1.5), Inches(6.4), Inches(10.3), Inches(0.015),
        )
        line.fill.solid()
        line.fill.fore_color.rgb = _COLOR_ACCENT_STRONG
        line.line.fill.background()

        ft = slide.shapes.add_textbox(
            Inches(1.5), Inches(6.5), Inches(10.3), Inches(0.5),
        )
        tf = ft.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = chapter_title
        self._set_font(run, Pt(12), _COLOR_ACCENT_STRONG, bold=False)

    def _add_footer(self, slide: Any, chapter_title: str, page_num: int, total: int) -> None:
        """Add footer with chapter title and page number."""
        # Chapter title on left
        ft_left = slide.shapes.add_textbox(
            Inches(0.5), Inches(7.05), Inches(8.0), Inches(0.35),
        )
        tf = ft_left.text_frame
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = chapter_title
        self._set_font(run, Pt(10), _COLOR_TEXT_LIGHT, bold=False)

        # Page number on right
        ft_right = slide.shapes.add_textbox(
            Inches(10.0), Inches(7.05), Inches(3.0), Inches(0.35),
        )
        tf2 = ft_right.text_frame
        p2 = tf2.paragraphs[0]
        p2.alignment = PP_ALIGN.RIGHT
        run2 = p2.add_run()
        run2.text = f"{page_num} / {total}"
        self._set_font(run2, Pt(10), _COLOR_TEXT_LIGHT, bold=False)

    @staticmethod
    def _set_font(run: Any, size: Any, color: Any, *, bold: bool = False) -> None:
        """Apply font settings to a run."""
        run.font.size = size
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.name = _FONT_FAMILY
        # Set East Asian font
        rPr = run._r.get_or_add_rPr()
        ea = rPr.makeelement(qn("a:ea"), {})
        ea.set("typeface", _FONT_FAMILY)
        rPr.append(ea)

    @staticmethod
    def _set_shape_radius(shape: Any) -> None:
        """Set rounded corner radius on a shape."""
        spPr = shape._element.find(qn("a:spPr")) if shape._element.find(qn("a:spPr")) is not None else shape._element
        prstGeom = spPr.find(qn("a:prstGeom"))
        if prstGeom is not None:
            prstGeom.set("prst", "roundRect")
            # Remove existing avLst if any
            avLst = prstGeom.find(qn("a:avLst"))
            if avLst is not None:
                prstGeom.remove(avLst)

    # ------------------------------------------------------------------
    # Narration TTS synthesis
    # ------------------------------------------------------------------
    async def _synthesize_narrations(
        self,
        content: dict[str, Any],
        course_id: int | None,
        chapter_id: int,
        chapter_title: str,
    ) -> list[str]:
        """Synthesize narration MP3 for each slide via Edge TTS."""
        slides = content.get("slides", [])
        if not slides:
            return []

        tts = get_tts_provider()
        course_dir_name = f"course_{course_id}" if course_id else f"chapter_{chapter_id}"
        export_dir = get_assets_root() / course_dir_name / "narration"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in " _-")[:40].strip()
        urls: list[str] = []

        for i, slide in enumerate(slides):
            notes = slide.get("notes", "")
            if not notes.strip():
                urls.append("")
                continue

            try:
                audio_bytes = await tts.synthesize(notes, {"voice": _NARRATION_VOICE})
                filename = f"{safe_title or 'ch'}_{chapter_id}_slide_{i}.mp3"
                filepath = export_dir / filename
                filepath.write_bytes(audio_bytes)
                urls.append(f"/assets/{course_dir_name}/narration/{filename}")
                logger.debug("[ppt] Narration MP3 for slide %d: %s", i, filename)
            except Exception as e:
                logger.warning("[ppt] Narration TTS failed for slide %d: %s", i, e)
                urls.append("")

            # Small delay between TTS calls
            await asyncio.sleep(0.15)

        logger.info("[ppt] Generated %d narration MP3s", len([u for u in urls if u]))
        return urls

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        kp_names = [kp.get("name", "") for kp in kps]
        kp_types = {kp.get("name", ""): kp.get("type", "概念") for kp in kps}

        slides: list[dict[str, Any]] = []

        # Slide 1: Chapter overview
        slides.append({
            "title": f"{chapter_title} - 概述",
            "bullets": [
                f"本章主题：{chapter_title}",
                f"本章将涵盖 {len(kps)} 个核心知识点",
                f"学习目标：理解并掌握 {', '.join(kp_names[:3])}{'等' if len(kp_names) > 3 else ''} 核心概念",
            ],
            "notes": f"大家好！欢迎来到{chapter_title}的学习。本章我们将系统学习{', '.join(kp_names[:3])}等重要知识点。通过本章的学习，你将建立起完整的知识框架，并能将其应用到实际问题中。",
        })

        # Slide 2-N: Distribute knowledge points across slides (max 3 KPs per slide)
        kps_per_slide = 3
        for start in range(0, len(kp_names), kps_per_slide):
            chunk = kp_names[start:start + kps_per_slide]
            if not chunk:
                continue
            kp_items = []
            for name in chunk:
                kp_type = kp_types.get(name, "概念")
                kp_items.append(f"{name}（{kp_type}）：理解其核心定义、原理和应用场景")
            slides.append({
                "title": "核心知识点" if start == 0 else "知识拓展",
                "bullets": kp_items,
                "notes": f"接下来我们重点学习{'、'.join(chunk)}。{'对于每个知识点，我们不仅要理解概念定义，更要掌握其背后的原理和实际应用方法。' if len(chunk) > 1 else '让我们深入探讨这个知识点的核心内容。'}请同学们注意做好笔记。",
            })

        # Slide last: Summary
        slides.append({
            "title": "本章总结",
            "bullets": [
                f"回顾本章核心：{', '.join(kp_names[:3])}{'等' if len(kp_names) > 3 else ''}",
                "梳理知识体系，建立知识点之间的联系",
                "完成章节练习，检验学习效果",
                "思考：如何将本章知识应用到实际问题中？",
            ],
            "notes": f"好的，以上就是{chapter_title}的全部内容。我们学习了{', '.join(kp_names[:3])}等核心知识点。建议同学们课后整理笔记，建立自己的知识框架，并通过练习题来检验掌握程度。有任何疑问欢迎随时提问，我们下次课再见！",
        })

        return {
            "title": chapter_title,
            "slides": slides,
        }
