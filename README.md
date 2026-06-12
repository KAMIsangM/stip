# SITP — Smart Interactive Teaching Platform

MVP scaffold: Vue 3 + FastAPI + SQLAlchemy (6 tables).

## Quick start

> **Important:** Run all backend commands from the `backend/` directory. Starting uvicorn from the project root causes `ModuleNotFoundError: No module named 'app'`.

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Course assets (audio, PPTX) are served at `/assets` from `backend/data/courses/`.

Set API keys via env vars (see `backend/config.yaml`): `DEEPSEEK_API_KEY`, `ALIYUN_ACCESS_KEY_ID`, etc.

Run repository tests:

```bash
cd backend
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Docs

- [TECH-001](docs/TECH-001_数据模型与技术锁定.md) — SRS/HLD conflict resolution
- [TECH-002](docs/TECH-002_依赖与PPT渲染方案.md) — supplemental deps & PPT rendering

## MVP defaults (config.yaml)

| Service | Primary | Fallback |
| :--- | :--- | :--- |
| LLM | DeepSeek | Qwen |
| TTS | Edge TTS | Aliyun |
| ASR | Aliyun | Tencent |
