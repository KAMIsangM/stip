"""Audio course generator — produces dialogue-script JSON + MP3 audio file."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import get_assets_root
from app.generator.base_generator import BaseModalGenerator
from app.provider.factory import get_tts_provider

logger = logging.getLogger(__name__)

_AUDIO_SYSTEM = """你是一个音频课程脚本设计师。根据提供的章节知识点，生成一段双AI对话式音频课程脚本。

要求：
1. 输出必须是严格的 JSON 格式
2. 对话由"教师"和"学生"两个角色交替进行
3. 教师讲解知识点，学生提问或回应，模拟真实课堂互动
4. 对话应自然流畅、深入浅出

输出格式：
{
  "title": "音频课程标题",
  "dialogues": [
    {"role": "teacher", "text": "教师讲解文本"},
    {"role": "student", "text": "学生提问或回应文本"},
    {"role": "teacher", "text": "教师回答文本"}
  ],
  "duration_estimate": 180
}"""

# Different voices for teacher and student roles
_TEACHER_VOICE = "zh-CN-YunxiNeural"    # 男声 - 教师
_STUDENT_VOICE = "zh-CN-XiaoxiaoNeural"  # 女声 - 学生
_PAUSE_MS = 500  # pause between dialogue turns (milliseconds)


class AudioGenerator(BaseModalGenerator):
    modal_type = "audio"

    async def generate(self, chapter_id: int, context: dict[str, Any]) -> dict[str, Any]:
        chapter_title = context.get("chapter_title", "未命名章节")
        kps = context.get("knowledge_points", [])
        kp_names = [kp.get("name", "") for kp in kps]

        user = f"""章节标题：{chapter_title}
知识点：{", ".join(kp_names) if kp_names else "无特定知识点"}
课程标题：{context.get("course_title", "")}

请生成 6-10 轮对话的音频课程脚本。"""

        try:
            raw = await self._call_llm(_AUDIO_SYSTEM, user)
            content = self._extract_json(raw)
        except Exception as e:
            logger.warning("[audio] LLM generation failed: %s, using fallback", e)
            content = self._fallback_content(chapter_title, kps)

        # TTS synthesis runs concurrently — doesn't block LLM for other tasks
        course_id = context.get("course_id")
        file_path = None
        try:
            file_path = await self._synthesize_audio(content, course_id, chapter_id, chapter_title)
        except Exception as e:
            logger.warning("[audio] TTS synthesis failed: %s", e)

        return {
            "modal_type": self.modal_type,
            "content_json": json.dumps(content, ensure_ascii=False),
            "file_path": file_path,
        }

    # ------------------------------------------------------------------
    # TTS synthesis
    # ------------------------------------------------------------------
    async def _synthesize_audio(
        self,
        content: dict[str, Any],
        course_id: int | None,
        chapter_id: int,
        chapter_title: str,
    ) -> str | None:
        """Synthesize dialogue script to MP3 via Edge TTS."""
        dialogues = content.get("dialogues", [])
        if not dialogues:
            return None

        tts = get_tts_provider()
        audio_chunks: list[bytes] = []

        # Silence between turns (generate a short silent chunk)
        silent_frame = b"\x00" * 1600  # ~100ms of silence placeholder

        for dialogue in dialogues:
            role = dialogue.get("role", "teacher")
            text = dialogue.get("text", "")
            if not text.strip():
                continue

            voice = _TEACHER_VOICE if role == "teacher" else _STUDENT_VOICE
            logger.debug("[audio] Synthesizing %s: %s...", role, text[:50])

            try:
                audio_bytes = await tts.synthesize(text, {"voice": voice})
                audio_chunks.append(audio_bytes)
            except Exception as e:
                logger.warning("[audio] TTS failed for dialogue turn: %s", e)
                continue

            # Small pause between turns
            await asyncio.sleep(0.2)

        if not audio_chunks:
            return None

        # Concatenate all audio chunks (MP3 concatenation is safe)
        combined = b"".join(audio_chunks)

        # Save to assets directory
        course_dir_name = f"course_{course_id}" if course_id else f"chapter_{chapter_id}"
        export_dir = get_assets_root() / course_dir_name / "audio"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c for c in chapter_title if c.isalnum() or c in " _-")[:40].strip()
        filename = f"{safe_title or 'chapter'}_{chapter_id}.mp3"
        filepath = export_dir / filename

        filepath.write_bytes(combined)
        logger.info("[audio] Exported MP3 to %s (%d bytes)", filepath, len(combined))

        return f"/assets/{course_dir_name}/audio/{filename}"

    def _fallback_content(self, chapter_title: str, kps: list[dict[str, Any]]) -> dict[str, Any]:
        kp_name = kps[0]["name"] if kps else chapter_title
        return {
            "title": f"{chapter_title} - 音频课程",
            "dialogues": [
                {
                    "role": "teacher",
                    "text": f"同学们好，今天我们来学习{chapter_title}。本章将围绕{'、'.join(kp.get('name', '') for kp in kps[:2])}等内容展开。",
                },
                {
                    "role": "student",
                    "text": f"老师，{kp_name}这个概念能再解释一下吗？",
                },
                {
                    "role": "teacher",
                    "text": f"当然可以。{kp_name}指的是……它是本章的基础，后续内容都会围绕它展开。",
                },
                {
                    "role": "student",
                    "text": "明白了，谢谢老师！",
                },
                {
                    "role": "teacher",
                    "text": "接下来我们继续看下一个知识点。请同学们做好笔记。",
                },
            ],
            "duration_estimate": 120,
        }
