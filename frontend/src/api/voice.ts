import http from './http'

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

export interface TTSRequest {
  text: string
  voice_type?: string
  speed?: number
}

export interface TTSResponse {
  audio_url: string
  duration: number
  text_hash: string
  cached: boolean
}

export interface TTSBatchRequest {
  paragraphs: string[]
  voice_type?: string
  speed?: number
}

export interface TTSBatchItem {
  index: number
  text: string
  audio_url: string
  duration: number
}

export interface TTSBatchResponse {
  items: TTSBatchItem[]
  total_duration: number
}

export interface VoiceInfo {
  id: string
  name: string
  gender: string
  style: string
}

export interface VoiceListResponse {
  voices: VoiceInfo[]
  default: string
}

export interface ASRResponse {
  text: string
  confidence: number
  language: string
}

// ---------------------------------------------------------------------------
// TTS API
// ---------------------------------------------------------------------------

/** Synthesize a single text segment to speech (cached) */
export function synthesizeTTS(data: TTSRequest) {
  return http.post<TTSResponse>('/voice/tts', data)
}

/** Stream paragraph-level TTS as raw MP3 (returns blob) */
export function synthesizeTTSStream(data: TTSBatchRequest) {
  return http.post('/voice/tts/stream', data, { responseType: 'blob' })
}

/** Batch synthesize multiple paragraphs, returns URLs */
export function synthesizeTTSBatch(data: TTSBatchRequest) {
  return http.post<TTSBatchResponse>('/voice/tts/batch', data)
}

/** List available TTS voices */
export function listVoices() {
  return http.get<VoiceListResponse>('/voice/tts/voices')
}

// ---------------------------------------------------------------------------
// ASR API
// ---------------------------------------------------------------------------

/** Upload an audio file for speech recognition */
export function recognizeAudio(file: File | Blob) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<ASRResponse>('/voice/asr', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ---------------------------------------------------------------------------
// WebSocket voice chat
// ---------------------------------------------------------------------------

export interface VoiceChatMessage {
  type: 'asr_result' | 'llm_reply' | 'tts_done' | 'error'
  text?: string
  message?: string
  final?: boolean
}

/**
 * Create a WebSocket connection for real-time voice Q&A.
 *
 * Returns an object with methods to send audio/text and register callbacks.
 *
 * Usage:
 *   const chat = createVoiceChat()
 *   chat.onMessage = (msg) => { ... }
 *   chat.onAudio = (chunk) => { // play audio }
 *   chat.sendAudioChunk(audioBlob)
 *   chat.endAudio()
 *   chat.sendText('你好')
 *   chat.close()
 */
export function createVoiceChat() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/ws/v1/voice/chat`
  const ws = new WebSocket(wsUrl)
  ws.binaryType = 'arraybuffer'

  const listeners = {
    onMessage: null as ((msg: VoiceChatMessage) => void) | null,
    onAudio: null as ((chunk: ArrayBuffer) => void) | null,
    onOpen: null as (() => void) | null,
    onClose: null as (() => void) | null,
    onError: null as ((err: Event) => void) | null,
  }

  ws.onopen = () => listeners.onOpen?.()
  ws.onclose = () => listeners.onClose?.()
  ws.onerror = (e) => listeners.onError?.(e)

  ws.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
      listeners.onAudio?.(event.data)
      return
    }
    try {
      const msg: VoiceChatMessage = JSON.parse(event.data)
      listeners.onMessage?.(msg)
    } catch {
      // ignore malformed messages
    }
  }

  return {
    ws,

    /** Set callback for JSON messages (asr_result, llm_reply, tts_done, error) */
    get onMessage() { return listeners.onMessage },
    set onMessage(cb: ((msg: VoiceChatMessage) => void) | null) { listeners.onMessage = cb },

    /** Set callback for binary audio chunks from TTS */
    get onAudio() { return listeners.onAudio },
    set onAudio(cb: ((chunk: ArrayBuffer) => void) | null) { listeners.onAudio = cb },

    get onOpen() { return listeners.onOpen },
    set onOpen(cb: (() => void) | null) { listeners.onOpen = cb },

    get onClose() { return listeners.onClose },
    set onClose(cb: (() => void) | null) { listeners.onClose = cb },

    get onError() { return listeners.onError },
    set onError(cb: ((err: Event) => void) | null) { listeners.onError = cb },

    /** Send raw audio chunk (binary) */
    sendAudioChunk(chunk: Blob | ArrayBuffer) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(chunk instanceof Blob ? chunk : new Blob([chunk]))
      }
    },

    /** Signal end of audio input to trigger ASR */
    endAudio() {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'end_audio' }))
      }
    },

    /** Send text directly (skip ASR) */
    sendText(content: string) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'text_message', content }))
      }
    },

    /** Close the WebSocket connection */
    close() {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    },
  }
}
