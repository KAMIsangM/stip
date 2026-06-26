import logging

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, chat, content, course, knowledge, voice
from app.core.config import get_assets_root, get_settings

# Ensure all application loggers are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()
assets_root = get_assets_root()

# ---- startup diagnostics ----
_llm_cfg = settings.get("llm", {})
_provider = _llm_cfg.get("provider", "???")
_deepseek_cfg = _llm_cfg.get("deepseek", {})
_api_key = _deepseek_cfg.get("api_key", "")
_api_key_masked = (_api_key[:16] + "..." + _api_key[-4:]) if len(_api_key) > 20 else _api_key[:4] + "****"
logger.info("LLM provider: %s | model: %s | base_url: %s | api_key: %s",
    _provider,
    _deepseek_cfg.get("model", "???"),
    _deepseek_cfg.get("base_url", "???"),
    _api_key_masked,
)
# -----------------------------

app = FastAPI(title="SITP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["server"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=str(assets_root)), name="assets")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(course.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")

# Register WebSocket endpoint at /ws/v1/voice/chat
@app.websocket("/ws/v1/voice/chat")
async def voice_chat_websocket(websocket: WebSocket):
    """Real-time voice Q&A WebSocket — delegates to voice router handler."""
    await voice.voice_chat_ws(websocket)
app.include_router(content.router, prefix="/api/v1")


@app.on_event("startup")
def _seed_presets_on_startup():
    """Auto-seed knowledge graph presets on first startup."""
    try:
        from app.scripts.seed_presets import seed_presets

        seed_presets()
    except Exception:
        logger.warning("Preset seeding skipped (non-fatal).", exc_info=True)


@app.get("/health")
def health():
    return {"status": "ok"}
