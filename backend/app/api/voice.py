from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["voice"])


class TTSRequest(BaseModel):
    text: str
    voice_type: str | None = None
    speed: float = 1.0


@router.post("/voice/tts")
def synthesize_tts(body: TTSRequest):
    return {"audio_url": "", "duration": 0.0}
