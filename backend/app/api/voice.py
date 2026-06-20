"""F-Voice API — TTS synthesis, ASR recognition, voice chat WebSocket."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import get_assets_root, get_settings
from app.provider.factory import get_asr_provider, get_llm_provider, get_tts_provider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice"])

# WebSocket connection limit (prevent resource exhaustion)
_WS_SEMAPHORE = asyncio.Semaphore(5)

# ---------------------------------------------------------------------------
# TTS cache directory
# ---------------------------------------------------------------------------
_TTS_CACHE_DIR = get_assets_root() / "_tts_cache"
_TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TTSRequest(BaseModel):
    text: str
    voice_type: str | None = None  # e.g. "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"
    speed: float = 1.0  # not yet wired into EdgeTTS; reserved for future providers


class TTSResponse(BaseModel):
    audio_url: str
    duration: float
    text_hash: str
    cached: bool


class TTSBatchRequest(BaseModel):
    """Paragraph-level TTS: each paragraph synthesized individually."""
    paragraphs: list[str]
    voice_type: str | None = None
    speed: float = 1.0


class TTSBatchItem(BaseModel):
    index: int
    text: str
    audio_url: str
    duration: float


class TTSBatchResponse(BaseModel):
    items: list[TTSBatchItem]
    total_duration: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text_hash(text: str) -> str:
    """SHA-256 hex digest of normalized text for cache keys."""
    normalized = text.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _cache_path(text: str, voice: str) -> Path:
    """Return the cache file path for a text + voice combination."""
    h = _text_hash(text)
    safe_voice = "".join(c for c in voice if c.isalnum() or c in "_-")[:32]
    return _TTS_CACHE_DIR / f"{h}_{safe_voice}.mp3"


def _estimate_duration(audio_bytes: bytes) -> float:
    """Rough MP3 duration estimate from byte size.
    MP3 at ~128 kbps ≈ 16 KB/s. Returns seconds.
    """
    return len(audio_bytes) / 16000.0


def _speed_to_rate(speed: float) -> str:
    """Convert float speed (e.g. 1.0, 1.2, 0.8) to Edge TTS rate string."""
    if speed == 1.0:
        return "+0%"
    delta = (speed - 1.0) * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.0f}%"


# ---------------------------------------------------------------------------
# POST /voice/tts — single-paragraph TTS (cached)
# ---------------------------------------------------------------------------


@router.post("/voice/tts", response_model=TTSResponse)
async def synthesize_tts(body: TTSRequest):
    """Synthesize a single text segment to speech, with file-system cache.

    Returns the asset URL for the generated/cached MP3 file.
    """
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    cfg = get_settings()["tts"]
    voice = body.voice_type or cfg["edge"]["voice"]
    cache_file = _cache_path(body.text, voice)
    cached = cache_file.exists()

    if not cached:
        tts = get_tts_provider()
        try:
            audio_bytes = await tts.synthesize(body.text, {"voice": voice, "rate": _speed_to_rate(body.speed)})
        except Exception as exc:
            logger.exception("[voice] TTS synthesis failed")
            raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {exc}")

        cache_file.write_bytes(audio_bytes)
        logger.info("[voice] Cached TTS → %s (%d bytes)", cache_file.name, len(audio_bytes))

    # Build asset URL relative to the mounted /assets static directory
    rel_path = cache_file.relative_to(get_assets_root()).as_posix()
    audio_url = f"/assets/{rel_path}"
    duration = _estimate_duration(cache_file.read_bytes())

    return TTSResponse(
        audio_url=audio_url,
        duration=round(duration, 2),
        text_hash=_text_hash(body.text),
        cached=cached,
    )


# ---------------------------------------------------------------------------
# POST /voice/tts/stream — paragraph-level streaming TTS
# ---------------------------------------------------------------------------


@router.post("/voice/tts/stream")
async def synthesize_tts_stream(body: TTSBatchRequest):
    """Stream paragraph-level TTS as raw MP3 bytes.

    Each paragraph is synthesized in order and streamed immediately.
    Use when you want progressive playback without waiting for all paragraphs.
    """
    if not body.paragraphs:
        raise HTTPException(status_code=400, detail="paragraphs must not be empty")

    cfg = get_settings()["tts"]
    voice = body.voice_type or cfg["edge"]["voice"]
    tts = get_tts_provider()

    async def audio_stream():
        for i, paragraph in enumerate(body.paragraphs):
            if not paragraph.strip():
                continue
            cache_file = _cache_path(paragraph, voice)
            if cache_file.exists():
                yield cache_file.read_bytes()
            else:
                try:
                    audio_bytes = await tts.synthesize(paragraph, {"voice": voice, "rate": _speed_to_rate(body.speed)})
                    cache_file.write_bytes(audio_bytes)
                    yield audio_bytes
                except Exception as exc:
                    logger.warning("[voice] Stream paragraph %d failed: %s", i, exc)
                    continue

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={
            "X-TTS-Paragraph-Count": str(len(body.paragraphs)),
            "Cache-Control": "public, max-age=86400",
        },
    )


# ---------------------------------------------------------------------------
# POST /voice/tts/batch — batch paragraph TTS (returns URLs)
# ---------------------------------------------------------------------------


@router.post("/voice/tts/batch", response_model=TTSBatchResponse)
async def synthesize_tts_batch(body: TTSBatchRequest):
    """Synthesize multiple paragraphs and return asset URLs for each.

    Paragraphs are processed sequentially with caching — identical text
    reuses cached audio.
    """
    if not body.paragraphs:
        raise HTTPException(status_code=400, detail="paragraphs must not be empty")

    cfg = get_settings()["tts"]
    voice = body.voice_type or cfg["edge"]["voice"]
    tts = get_tts_provider()
    items: list[TTSBatchItem] = []
    total_duration = 0.0

    for i, paragraph in enumerate(body.paragraphs):
        if not paragraph.strip():
            continue

        cache_file = _cache_path(paragraph, voice)

        if not cache_file.exists():
            try:
                audio_bytes = await tts.synthesize(paragraph, {"voice": voice, "rate": _speed_to_rate(body.speed)})
                cache_file.write_bytes(audio_bytes)
            except Exception as exc:
                logger.warning("[voice] Batch paragraph %d failed: %s", i, exc)
                continue

        rel_path = cache_file.relative_to(get_assets_root()).as_posix()
        dur = _estimate_duration(cache_file.read_bytes())
        total_duration += dur

        items.append(
            TTSBatchItem(
                index=i,
                text=paragraph,
                audio_url=f"/assets/{rel_path}",
                duration=round(dur, 2),
            )
        )

    return TTSBatchResponse(items=items, total_duration=round(total_duration, 2))


# ---------------------------------------------------------------------------
# GET /voice/tts/voices — list available Edge TTS voices
# ---------------------------------------------------------------------------


@router.get("/voice/tts/voices")
async def list_tts_voices():
    """Return a curated list of Chinese-friendly Edge TTS voices."""
    return {
        "voices": [
            {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (女声)", "gender": "female", "style": "warm"},
            {"id": "zh-CN-YunxiNeural", "name": "云希 (男声)", "gender": "male", "style": "narrator"},
            {"id": "zh-CN-YunyangNeural", "name": "云扬 (男声)", "gender": "male", "style": "news"},
            {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 (女声)", "gender": "female", "style": "lively"},
            {"id": "zh-CN-YunjianNeural", "name": "云健 (男声)", "gender": "male", "style": "sports"},
            {"id": "zh-CN-XiaochenNeural", "name": "晓辰 (女声)", "gender": "female", "style": "calm"},
            {"id": "zh-CN-XiaohanNeural", "name": "晓涵 (女声)", "gender": "female", "style": "gentle"},
            {"id": "zh-CN-XiaomengNeural", "name": "晓梦 (女声)", "gender": "female", "style": "chat"},
            {"id": "zh-CN-XiaomoNeural", "name": "晓墨 (女声)", "gender": "female", "style": "clear"},
            {"id": "zh-CN-XiaoqiuNeural", "name": "晓秋 (女声)", "gender": "female", "style": "mature"},
            {"id": "zh-CN-XiaoruiNeural", "name": "晓睿 (女声)", "gender": "female", "style": "gentle"},
            {"id": "zh-CN-XiaoshuangNeural", "name": "晓双 (女声)", "gender": "female", "style": "child"},
            {"id": "zh-CN-XiaoxuanNeural", "name": "晓萱 (女声)", "gender": "female", "style": "confident"},
            {"id": "zh-CN-XiaoyanNeural", "name": "晓颜 (女声)", "gender": "female", "style": "beautiful"},
            {"id": "zh-CN-XiaozhenNeural", "name": "晓甄 (女声)", "gender": "female", "style": "sweet"},
            {"id": "zh-CN-YunfengNeural", "name": "云枫 (男声)", "gender": "male", "style": "deep"},
            {"id": "zh-CN-YunhaoNeural", "name": "云皓 (男声)", "gender": "male", "style": "bright"},
            {"id": "zh-CN-YunxiaNeural", "name": "云夏 (男声)", "gender": "male", "style": "warm"},
            {"id": "zh-CN-YunyeNeural", "name": "云野 (男声)", "gender": "male", "style": "mature"},
            {"id": "zh-CN-YunzeNeural", "name": "云泽 (男声)", "gender": "male", "style": "elderly"},
        ],
        "default": get_settings()["tts"]["edge"]["voice"],
    }


# ---------------------------------------------------------------------------
# POST /voice/asr — audio file recognition
# ---------------------------------------------------------------------------


class ASRResponse(BaseModel):
    text: str
    confidence: float = 0.0
    language: str = "zh"


@router.post("/voice/asr", response_model=ASRResponse)
async def recognize_audio(file: UploadFile):
    """Upload an audio file (MP3/WAV/PCM) for speech recognition.

    Reads the uploaded file and sends it to the configured ASR provider.
    Returns recognized text with optional confidence score.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Read uploaded audio
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    if len(audio_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Audio file too large (max 10 MB)")

    asr = get_asr_provider()

    def audio_gen():
        yield audio_bytes

    result_texts: list[str] = []
    try:
        async for text in asr.stream_recognize(audio_gen(), {"language": "zh-CN"}):
            if text:
                result_texts.append(text)
    except Exception as exc:
        logger.exception("[voice] ASR recognition failed")
        raise HTTPException(status_code=500, detail=f"ASR recognition failed: {exc}")

    full_text = " ".join(result_texts).strip()
    if not full_text:
        return ASRResponse(text="", confidence=0.0, language="zh")

    return ASRResponse(text=full_text, confidence=0.95, language="zh")


# ---------------------------------------------------------------------------
# WebSocket /ws/v1/voice/chat — real-time voice Q&A
# ---------------------------------------------------------------------------


async def voice_chat_ws(websocket: WebSocket):
    """Real-time voice Q&A WebSocket endpoint.

    Client flow:
    1. Connect to WebSocket
    2. Send binary audio chunks (WebM/MP3/PCM)
    3. Send {"type":"end_audio"} to signal end of speech
    4. Receive {"type":"asr_result","text":"..."} with recognized text
    5. Receive {"type":"llm_reply","text":"..."} with AI answer
    6. Receive binary TTS audio chunks for the reply
    7. Receive {"type":"tts_done"} to signal end of TTS stream

    Message protocol:
        Client → Server:
          - binary: raw audio chunk
          - text JSON: {"type":"end_audio"}
          - text JSON: {"type":"text_message","content":"..."}

        Server → Client:
          - text JSON: {"type":"asr_result","text":"...","final":true}
          - text JSON: {"type":"llm_reply","text":"..."}
          - binary: TTS audio bytes
          - text JSON: {"type":"tts_done"}
          - text JSON: {"type":"error","message":"..."}
    """
    await websocket.accept()
    acquired = False

    try:
        # Acquire semaphore to limit concurrent connections
        acquired = await asyncio.wait_for(_WS_SEMAPHORE.acquire(), timeout=5.0)
    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "Server busy, please try later"})
        await websocket.close()
        return

    try:
        audio_chunks: list[bytes] = []
        text_message: str | None = None

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "error", "message": "Timeout — no data received"})
                break

            # Handle binary audio chunks
            if "bytes" in data and data["bytes"]:
                audio_chunks.append(data["bytes"])
                continue

            # Handle text/JSON messages
            if "text" in data:
                try:
                    msg = json.loads(data["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                    continue

                msg_type = msg.get("type", "")

                if msg_type == "text_message":
                    # Direct text input (skip ASR)
                    text_message = msg.get("content", "").strip()
                    if not text_message:
                        await websocket.send_json({"type": "error", "message": "Empty text message"})
                        continue

                elif msg_type == "end_audio":
                    # End of audio input → run ASR
                    if audio_chunks:
                        combined = b"".join(audio_chunks)
                        asr = get_asr_provider()

                        def audio_gen():
                            yield combined

                        recognized_parts: list[str] = []
                        async for part in asr.stream_recognize(audio_gen(), {"language": "zh-CN"}):
                            if part:
                                recognized_parts.append(part)
                        text_message = " ".join(recognized_parts).strip()
                        audio_chunks.clear()

                    if not text_message:
                        await websocket.send_json({"type": "error", "message": "No speech recognized"})
                        continue

                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})
                    continue

                # ---- ASR done, now LLM → TTS ----
                if text_message:
                    # 1. Send ASR result to client
                    await websocket.send_json({"type": "asr_result", "text": text_message, "final": True})

                    # 2. Call LLM
                    try:
                        llm = get_llm_provider()
                        llm_reply = await llm.chat_completion(
                            f"你是一位友好的AI教师。请用简洁清晰的中文回答学生的问题。\n\n学生问题：{text_message}",
                            response_format="text",
                        )
                    except Exception as exc:
                        logger.exception("[voice-ws] LLM call failed")
                        await websocket.send_json({"type": "error", "message": f"AI 回复生成失败: {exc}"})
                        continue

                    # 3. Send LLM reply text
                    await websocket.send_json({"type": "llm_reply", "text": llm_reply})

                    # 4. TTS synthesis and stream
                    try:
                        tts = get_tts_provider()
                        tts_config = {
                            "voice": get_settings()["tts"]["edge"]["voice"],
                            "rate": "+0%",
                        }
                        audio_bytes = await tts.synthesize(llm_reply, tts_config)
                        # Send audio in chunks for progressive playback
                        chunk_size = 4096
                        for i in range(0, len(audio_bytes), chunk_size):
                            await websocket.send_bytes(audio_bytes[i : i + chunk_size])
                        await websocket.send_json({"type": "tts_done"})
                    except Exception as exc:
                        logger.exception("[voice-ws] TTS synthesis failed")
                        await websocket.send_json({"type": "error", "message": f"语音合成失败: {exc}"})

                    # Reset for next utterance
                    text_message = None

    except WebSocketDisconnect:
        logger.info("[voice-ws] Client disconnected")
    except Exception as exc:
        logger.exception("[voice-ws] Unexpected error")
        try:
            await websocket.send_json({"type": "error", "message": f"Server error: {exc}"})
        except Exception:
            pass
    finally:
        if acquired:
            _WS_SEMAPHORE.release()
        try:
            await websocket.close()
        except Exception:
            pass





