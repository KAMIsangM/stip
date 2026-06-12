from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import course, knowledge, voice
from app.core.config import get_assets_root, get_settings

settings = get_settings()
assets_root = get_assets_root()

app = FastAPI(title="SITP API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["server"]["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=str(assets_root)), name="assets")

app.include_router(course.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
