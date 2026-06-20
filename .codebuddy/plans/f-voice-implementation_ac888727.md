---
name: f-voice-implementation
overview: 实现 F-Voice 语音功能模块，包括：完善 TTS/ASR Provider 实现、完善 voice API 路由（TTS 合成 + WebSocket 实时语音问答）、前端 VoicePanel 组件、PPT 语音旁白播放功能。
design:
  architecture:
    framework: vue
  fontSystem:
    fontFamily: system-ui
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
      - "#67C23A"
    background:
      - "#FFFFFF"
      - "#F5F7FA"
    text:
      - "#303133"
      - "#909399"
    functional:
      - "#F56C6C"
      - "#E6A23C"
todos:
  - id: complete-voice-api
    content: 完善 backend/app/api/voice.py，实现 TTS 合成端点（含缓存）
    status: completed
  - id: implement-aliyun-asr
    content: 实现 AliyunASRProvider，完成阿里云 ASR 集成
    status: completed
    dependencies:
      - complete-voice-api
  - id: add-asr-api
    content: 新增 POST /api/v1/voice/asr 端点，支持音频文件上传识别
    status: completed
    dependencies:
      - implement-aliyun-asr
  - id: add-voice-ws
    content: 新增 WebSocket /ws/v1/voice/chat 实时语音问答端点
    status: completed
    dependencies:
      - implement-aliyun-asr
  - id: create-frontend-voice-api
    content: 新建 frontend/src/api/voice.ts，定义语音相关 API 函数
    status: completed
  - id: enhance-audio-player
    content: 增强 AudioPlayer.vue，添加自动播放和进度控制功能
    status: completed
    dependencies:
      - complete-voice-api
  - id: update-ppt-viewer
    content: 修改 PptViewer.vue，旁白音频自动播放和切换控制
    status: completed
    dependencies:
      - enhance-audio-player
---

## 产品概述

F-Voice 语音功能模块为智能教学平台提供完整的语音交互能力，包括语音合成（TTS）、语音识别（ASR）和语音旁白播放三大子功能。模块复用项目已有的 Provider 框架（`BaseTTSProvider`、`BaseASRProvider`）和 Factory 模式，完善占位实现，新增 API 端点和前端交互组件。

## 核心功能

### 1. 语音合成（TTS）

- 调用 TTS Provider 将文本转换为自然语音
- 支持段落级流式合成（StreamingResponse 返回 MP3 流）
- 语音缓存机制：相同文本哈希后缓存 MP3 文件，避免重复合成
- 支持 voice_type 和 speed 参数

### 2. 语音识别（ASR）

- 实现 `AliyunASRProvider` 或新增 `FunASRProvider`（本地开源方案）
- 支持中英文混合识别
- 提供两种识别方式：文件上传识别（`POST /api/v1/voice/asr`）和实时流式识别（WebSocket）

### 3. 语音旁白播放

- PPT 课件播放时自动同步播放语音旁白（已部分实现）
- 支持暂停/继续/重播控制
- 切换幻灯片时自动切换对应旁白音频

### 4. 实时语音问答（新增）

- WebSocket 端点：`/ws/v1/voice/chat`
- 前端录音 → 实时发送到 WebSocket → ASR 转文本 → LLM 生成回答 → TTS 合成语音 → 返回音频流

## API 接口

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| POST | `/api/v1/voice/tts` | 文本转语音合成（返回音频 URL 或流） |
| GET | `/api/v1/voice/tts/cache/{hash}` | 获取缓存的语音文件 |
| POST | `/api/v1/voice/asr` | 上传音频文件进行识别 |
| WS | `/ws/v1/voice/chat` | 实时语音问答交互 |
| GET | `/api/v1/voice/voices` | 获取可用语音列表 |


## 技术约束

- TTS 优先使用 Edge TTS（免费，已集成），可选 Aliyun TTS
- ASR 优先使用 Aliyun ASR API（配置中已定义），可选本地 FunASR
- 语音缓存存储在 `data/courses/voice_cache/` 目录
- 前端录音使用 Web Audio API + MediaRecorder API

## 技术栈

### 后端

- **框架**: FastAPI（复用现有）
- **TTS**: edge-tts（已集成）+ Aliyun TTS（可选）
- **ASR**: Aliyun ASR SDK / FunASR（本地开源）
- **音频处理**: pydub（可选，用于格式转换）
- **WebSocket**: FastAPI WebSocket 支持

### 前端

- **框架**: Vue 3 + TypeScript + Element Plus（复用现有）
- **录音**: MediaRecorder API（浏览器原生）
- **音频播放**: HTML5 Audio API（已有 `AudioPlayer.vue`）
- **WebSocket 客户端**: 原生 WebSocket

## 实现方案

### 1. 完善 TTS API（`backend/app/api/voice.py`）

**现有问题**: `synthesize_tts` 端点返回空 `audio_url`

**修改方案**:

```python
@router.post("/voice/tts")
async def synthesize_tts(body: TTSRequest):
    # 1. 计算文本哈希，检查缓存
    text_hash = hashlib.md5(body.text.encode()).hexdigest()
    cache_path = get_assets_root() / "voice_cache" / f"{text_hash}.mp3"
    
    if cache_path.exists():
        return {"audio_url": f"/assets/voice_cache/{text_hash}.mp3", "cached": True}
    
    # 2. 调用 TTS Provider
    tts = get_tts_provider()
    audio_bytes = await tts.synthesize(body.text, {
        "voice": body.voice_type,
        "rate": f"+{int((body.speed - 1) * 100)}%"
    })
    
    # 3. 保存到缓存
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(audio_bytes)
    
    return {"audio_url": f"/assets/voice_cache/{text_hash}.mp3", "duration": 0.0}
```

**关键决策**:

- 使用同步哈希检查（MD5）快速判断缓存命中
- 缓存目录挂载到 `/assets/voice_cache/`，通过 StaticFiles 直接提供服务
- 支持可选的文字转语音流式返回（StreamingResponse）用于实时播放

### 2. 实现 ASR Provider

#### 方案 A：完善 AliyunASRProvider（推荐用于生产）

**依赖**: `aliyun-python-sdk-core` + 阿里云 ASR SDK

**实现要点**:

- 使用阿里云智能语音交互 SDK 的 RESTful API
- 支持文件上传识别（非流式）和 WebSocket 流式识别
- 配置从 `config.yaml` 读取（`asr.aliyun.*`）

#### 方案 B：新增 FunASRProvider（推荐用于本地开发）

**依赖**: `funasr` + `modelscope`

**实现要点**:

- 本地部署，无需 API Key
- 支持实时流式识别
- 需要单独的运行环境（CPU/GPU）

**决策**: 先实现 AliyunASRProvider（与配置一致），FunASR 作为可选扩展。

### 3. 新增 ASR API（`backend/app/api/voice.py` 扩展）

```python
@router.post("/voice/asr")
async def recognize_speech(
    audio_file: UploadFile = File(...),
    language: str = Form("zh-CN"),
):
    """Upload audio file for ASR recognition."""
    asr = get_asr_provider()
    
    # Read audio file as generator
    def audio_gen():
        yield from audio_file.file.read()
    
    result_texts = []
    async for text in asr.stream_recognize(audio_gen(), {"language": language}):
        result_texts.append(text)
    
    return {"text": " ".join(result_texts), "language": language}
```

### 4. 实时语音问答 WebSocket

**端点**: `WebSocket /ws/v1/voice/chat`

**消息协议**:

```
// Client → Server
{"type": "audio_chunk", "data": "base64_audio_data"}
{"type": "text_message", "content": "用户文本消息"}
{"type": "end_audio"}

// Server → Client  
{"type": "asr_result", "text": "识别出的文本"}
{"type": "llm_reply", "text": "LLM 回答文本"}
{"type": "tts_audio", "data": "base64_audio_data", "final": true}
```

**实现流程**:

1. 接收客户端音频流
2. 调用 ASR Provider 实时识别
3. 识别完成后，调用 LLM 生成回答
4. 调用 TTS Provider 合成回答语音
5. 返回音频流给客户端

### 5. 语音旁白播放（前端）

**已有实现**:

- `PptViewer.vue` 已支持 `narrationUrls` prop
- `AudioPlayer.vue` 已有基础播放功能

**需要完善**:

- 在 `PptViewer.vue` 中，当 `currentNarration` 变化时自动播放
- 添加播放进度条和暂停/继续控制
- 切换幻灯片时自动停止当前播放，开始新播放

### 6. 数据库变更

**新增表**: `voice_cache`（可选，用文件系统缓存替代更简单）

**决策**: 使用文件系统缓存（`data/courses/voice_cache/`），不新增数据库表。

## 目录结构

```
backend/
├── app/
│   ├── api/
│   │   └── voice.py              [MODIFY] 完善 TTS/ASR API
│   ├── provider/
│   │   ├── asr/
│   │   │   ├── base_asr_provider.py     [NO CHANGE] 已定义抽象接口
│   │   │   ├── aliyun_asr_provider.py   [MODIFY] 实现 Aliyun ASR
│   │   │   └── funasr_provider.py       [NEW] 可选：FunASR 本地实现
│   │   └── tts/
│   │       └── aliyun_tts_provider.py   [MODIFY] 实现 Aliyun TTS（可选）
│   └── models/
│       └── __init__.py           [NO CHANGE] 无需新增模型

frontend/
├── src/
│   ├── api/
│   │   └── voice.ts             [NEW] 语音相关 API 函数
│   ├── components/
│   │   └── course/
│   │       └── VoiceRecorder.vue [NEW] 语音录制组件（可选）
│   └── composables/
│       └── useAudioPlayer.ts    [NEW] 音频播放 composable（可选）
```

## 关键代码结构

### TTSRequest（扩展）

```python
class TTSRequest(BaseModel):
    text: str
    voice_type: str | None = None  # e.g., "zh-CN-XiaoxiaoNeural"
    speed: float = 1.0  # 0.5 ~ 2.0
    stream: bool = False  # 是否流式返回
```

### ASR Provider 接口（已有）

```python
class BaseASRProvider(ABC):
    @abstractmethod
    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        """Stream ASR recognition, yield partial results."""
```

## 实现要点

1. **缓存策略**: TTS 结果按 `{text_hash}_{voice}_{speed}` 缓存，避免重复 API 调用
2. **错误处理**: TTS/ASR 调用失败时返回友好错误，不阻断用户体验
3. **并发控制**: ASR WebSocket 连接需要限制并发数（使用 Semaphore）
4. **前端录音**: 使用 `MediaRecorder.isTypeSupported()` 检查支持的格式，优先使用 `audio/webm` 或 `audio/mp4`
5. **性能优化**: TTS 合成大段文本时，按标点符号分割后并行合成，最后合并

## 依赖安装

```
# 后端
pip install edge-tts  # 已实现
pip install aliyun-python-sdk-core  # Aliyun ASR
pip install funasr modelscope  # 可选：本地 ASR

# 前端（无需额外依赖）
# MediaRecorder API 和 WebSocket 是浏览器原生支持
```

## 设计风格

采用现代简约风格，与现有 Element Plus 设计语言保持一致。语音功能相关 UI 遵循以下原则：

1. **一致性**: 与现有 `ChatPanel.vue` 和 `AudioPlayer.vue` 风格统一
2. **易用性**: 录音按钮有明确的视觉反馈（录音中动画）
3. **渐进增强**: 不支持录音的浏览器显示友好提示

## 页面结构设计

### VoiceRecorder 组件（可选，用于实时语音问答）

**布局**: 小型浮动按钮或 ChatPanel 内的录音图标

**区块 1：录音按钮**

- 默认状态：麦克风图标（灰色）
- 录音中：红色脉冲动画 + 计时器
- 完成后：显示识别文本 + 播放按钮

**区块 2：语音设置面板**（可选）

- 选择语音类型（男声/女声）
- 语速调节（滑块）
- 麦克风选择（下拉框）

## 交互设计

1. **按下录音**: 长按或点击录音按钮开始录音
2. **实时反馈**: 录音波形动画（使用 Web Audio API 分析）
3. **识别结果**: 实时显示 ASR 识别文本
4. **播放回答**: TTS 合成的回答自动播放，显示播放进度

## 组件复用

- 复用现有 `AudioPlayer.vue` 用于语音播放
- 复用现有 `ChatPanel.vue` 的布局结构
- 新增 `VoiceRecorder.vue` 仅封装录音逻辑

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 在需要时进行代码库探索，确认文件结构和接口定义
- Expected outcome: 获取准确的代码结构信息，指导实现