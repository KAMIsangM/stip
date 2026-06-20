---
name: course-chat-panel
overview: 在课程播放页（CoursePlayer.vue）右侧新增一个 AI 对话栏，调用现有 DeepSeek provider 回答用户关于当前课程内容的问题，对话记录持久化到数据库。
design:
  styleKeywords:
    - Modern
    - Clean
    - Chat Bubble
    - Element Plus
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 16px
      weight: 600
    subheading:
      size: 13px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
      - "#337ECC"
    background:
      - "#FFFFFF"
      - "#F5F7FA"
    text:
      - "#303133"
      - "#909399"
    functional:
      - "#67C23A"
      - "#E6A23C"
      - "#F56C6C"
todos:
  - id: add-chatmessage-model
    content: 在 backend/app/models/__init__.py 中新增 ChatMessage 数据模型类
    status: pending
  - id: extend-llm-provider
    content: 扩展 DeepSeekProvider 和 BaseLLMProvider，支持 messages 列表格式调用
    status: pending
    dependencies:
      - add-chatmessage-model
  - id: create-chat-api
    content: 新建 backend/app/api/chat.py，实现对话 API 路由（发送消息 + 获取历史）
    status: pending
    dependencies:
      - extend-llm-provider
  - id: register-chat-router
    content: 在 backend/app/main.py 中注册 chat router
    status: pending
    dependencies:
      - create-chat-api
  - id: add-chat-api-frontend
    content: 新建 frontend/src/api/chat.ts，实现前端对话 API 函数
    status: pending
  - id: create-chat-panel
    content: 新建 frontend/src/components/course/ChatPanel.vue 组件
    status: pending
    dependencies:
      - add-chat-api-frontend
  - id: update-course-player-layout
    content: 修改 CoursePlayer.vue，右侧新增 ChatPanel 面板，调整布局样式
    status: pending
    dependencies:
      - create-chat-panel
---

## 产品概述

在课程播放页面（CoursePlayer.vue）右侧新增 AI 对话功能栏，用户可在学习过程中随时向 AI 提问，AI 基于当前课程内容给出回答，对话记录持久化保存。

## 核心功能

- 用户在输入框中输入问题，点击发送或按 Enter 发送
- 调用 DeepSeek LLM API 获取回答，回答过程中显示 loading 状态
- 对话上下文关联当前课程大纲和当前章节内容（RAG 简化版）
- 对话记录持久化到数据库，页面刷新后不丢失
- 前端右侧固定宽度对话面板，包含对话历史展示区和输入区
- 支持查看历史对话记录（按时间倒序）

## 技术栈

- 后端：FastAPI + SQLAlchemy + DeepSeek API（复用现有 provider）
- 前端：Vue 3 + TypeScript + Element Plus
- 数据库：复用现有 SQLite/PostgreSQL

## 实现方案

### 后端

1. **新增 ChatMessage 数据模型**（`backend/app/models/__init__.py`）

- 字段：`id, course_id, chapter_id (可选), role (user/assistant), content, created_at`
- 关联：`course_id → Course.id (CASCADE)`，可选 `chapter_id → Chapter.id`
- 直接使用 SQLAlchemy `declarative_base` 扩展，与现有模型风格一致

2. **扩展 DeepSeekProvider 支持 messages 格式**

- 现有 `chat_completion(prompt)` 只支持单 prompt
- 新增 `chat_completion_with_history(messages: list[dict])` 方法
- 或直接修改现有方法，接受 `messages` 参数（推荐，保持接口简洁）
- 同时更新 `BaseLLMProvider` 抽象类和 `ResilientLLMProvider` 包装类

3. **新增对话 API 路由**（`backend/app/api/chat.py`）

- `POST /api/v1/courses/{course_id}/chat`：发送消息
    - 请求体：`{ message: string, chapter_id?: number }`
    - 处理逻辑：

    1. 保存用户消息到 `ChatMessage`（role=user）
    2. 查询课程信息（标题、描述、章节列表）
    3. 如果指定了 `chapter_id`，查询该章节内容（从 `ContentModule.content_json` 解析）
    4. 组装 system prompt（课程内容上下文）
    5. 查询该课程最近的历史对话（最近 10 条）作为上下文
    6. 调用 LLM 获取回答
    7. 保存助手消息到 `ChatMessage`（role=assistant）
    8. 返回 `{ reply: string, message_id: number }`

- `GET /api/v1/courses/{course_id}/chat/history`：获取对话历史
    - 参数：`chapter_id?`, `limit?`, `offset?`
    - 返回对话记录列表

4. **路由注册**（`backend/app/main.py`）

- 新增 `from app.api import chat`
- 新增 `app.include_router(chat.router, prefix="/api/v1")`

### 前端

1. **新增 ChatPanel.vue 组件**（`frontend/src/components/course/ChatPanel.vue`）

- Props：`courseId: number`, `chapterId: number | null`
- 布局（从上到下）：
    - 标题栏："AI 助手"（带机器人图标）
    - 对话记录区（flex:1, overflow-y:auto）：
    - 用户消息：右对齐气泡，蓝色主题
    - AI 回复：左对齐气泡，灰色背景
    - 时间戳（可选）
    - Loading 状态：显示"思考中..."动画
    - 输入区（底部固定）：
    - `el-input` 文本框（type=textarea，支持 Enter 发送）
    - 发送按钮
- 功能：
    - 组件挂载时自动加载历史记录
    - 发送消息后自动滚动到最新
    - 禁用状态（未选择章节时可选，或始终可用）

2. **新增前端 API 函数**（`frontend/src/api/chat.ts`）

- `sendChatMessage(courseId, message, chapterId?)` → POST
- `getChatHistory(courseId, chapterId?, limit?, offset?)` → GET

3. **修改 CoursePlayer.vue 布局**

- 当前布局：`chapter-sidebar (280px)` + `player-main (flex:1)`
- 新布局：`chapter-sidebar (280px)` + `player-main (flex:1)` + `chat-panel (360px)`
- 在 `.player-body` 内新增右侧 `chat-panel` 容器
- 传递 `courseId` 和 `activeChapter` 给 `ChatPanel` 组件

## 数据库变更

- 新增 `chat_messages` 表（通过修改 `models/__init__.py` 添加 `ChatMessage` 类）
- 需要运行数据库迁移（SQLite 可直接删除重建，或添加 ALTER TABLE 脚本）

## 实现要点

- LLM 上下文组装：将课程标题、章节列表、当前章节内容（如有）拼接为 system prompt
- 历史对话上下文：取最近 10 条对话记录，格式化为 `messages` 列表传给 LLM
- 错误处理：LLM 调用失败时返回友好提示，不阻断用户体验
- 前端输入防抖：防止重复发送，发送中禁用输入框

## 设计风格

采用现代简约风格，与现有 Element Plus 设计语言保持一致。对话面板采用左右气泡布局，区分用户和 AI 消息。

## 页面结构设计

### ChatPanel 组件布局（右侧面板，宽度 360px）

**区块 1：标题栏**

- 高度 48px，背景白色，底部边框
- 左侧机器人图标 + "AI 助手" 文字
- 右侧可选"清空对话"按钮（小型）

**区块 2：对话记录区**

- 占据面板剩余空间（flex:1），溢出自动滚动
- 消息气泡布局：
- 用户消息：右对齐，蓝色渐变背景（#409eff → #337ecc），白色文字，圆角 12px，最大宽度 85%
- AI 消息：左对齐，浅灰背景（#f5f7fa），深灰文字，圆角 12px，最大宽度 85%
- 消息间距 12px，内边距 10px 14px
- 时间戳：消息下方小字（11px，#999）
- Loading 状态：AI 头像 + 跳动圆点动画（三个小圆点）

**区块 3：输入区**

- 高度约 100px，顶部边框，背景白色
- `el-input` textarea（自适应高度，最大 80px）
- 底部发送按钮（右对齐，primary 类型）
- 支持 Enter 发送，Shift+Enter 换行

## 交互设计

- 发送消息后自动滚动到最新消息
- AI 回复时显示"思考中..."加载状态
- 输入框为空时发送按钮禁用
- 面板宽度固定 360px，右侧阴影分隔

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在需要时进行代码库探索，确认文件结构和接口定义
- Expected outcome: 获取准确的代码结构信息，指导实现