# TECH-002: 补充依赖与 PPT 前端渲染方案

## 1. Meta
| Key | Value |
| :--- | :--- |
| Owner | @dev |
| Status | Done |
| Due | 2026-06-12 |

## 2. Intent
- **Goal:** 补齐 HLD 未列但 MVP 实现必需的依赖，并锁定 PPT 在线播放方案。
- **NOT Doing:**
  1. `@vue-office/pptx` 全量 PPTX 解析（体积大、兼容性风险）
  2. 服务端实时转图片流水线（P1 优化项）

## 3. Tech Lock-in
| Layer | Choice | Reason |
| :--- | :--- | :--- |
| 前端构建 | Vite 5 + Vue 3 + TypeScript | Vue 3 标配；HMR p99 < 500ms 本地 dev |
| 后端 HTTP 客户端 | httpx (async) | LLM 异步调用，替代同步 requests |
| PPT 导出 | python-pptx | HLD PPTGenerator 导出 .pptx |
| TTS | edge-tts | MVP 零成本默认 Provider |
| ASGI 服务器 | uvicorn | FastAPI 标准运行时 |
| PPT 在线播放 | Slide JSON + 图片 URL 轮播组件 | LLM 产出结构化 slides；首包渲染 ≤1s |

## 4. 后端依赖（requirements.txt）
| 包 | 用途 |
| :--- | :--- |
| fastapi | API 框架 |
| uvicorn[standard] | ASGI 服务 |
| sqlalchemy | ORM |
| alembic | 数据库迁移 |
| httpx | 异步 LLM/HTTP |
| pyyaml | config.yaml 加载 |
| python-pptx | PPTX 导出 |
| edge-tts | Edge TTS Provider |
| networkx | 知识图谱图计算 |
| aiomysql / aiosqlite | 异步 DB 驱动（可选，MVP 同步引擎即可） |

## 5. 前端依赖（package.json）
| 包 | 用途 |
| :--- | :--- |
| vite | 构建与 dev server |
| vue / vue-router / pinia | 框架与状态 |
| element-plus | UI 组件 |
| axios | HTTP + 重试 |
| echarts | 知识图谱力导向图 |
| @vue-office/pptx | **不采用**；见 §6 |

## 6. PPT 渲染方案（MVP）
**数据流：**
1. `PPTGenerator` 调用 LLM 生成 `content_json.slides[]`：`{ title, bullets[], image_url?, notes }`
2. 可选：`python-pptx` 导出 `.pptx` 至 `data/courses/{course_id}/ppt/`
3. TTS 按 slide 生成旁白音频路径列表
4. 前端 `PptViewer.vue`：Element Plus 轮播 + 每页标题/要点 + `<img>` + `AudioPlayer` 同步旁白

**组件：** `frontend/src/components/course/PptViewer.vue`

**降级：** 无配图时使用占位图；无 pptx 文件时仅 JSON 轮播仍可播放。

## 7. DoD (Definition of Done)
- [x] `backend/requirements.txt` 含 httpx、python-pptx、edge-tts、uvicorn、pyyaml
- [x] `frontend/package.json` 含 vite
- [x] `PptViewer.vue` 脚手架组件存在
- [x] TECH-002 与 TECH-001 无冲突
