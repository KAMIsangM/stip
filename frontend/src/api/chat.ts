import http from './http'

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

export interface ChatMessage {
  id: number
  course_id: number
  chapter_id: number | null
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ChatHistory {
  messages: ChatMessage[]
}

export interface ChatResponse {
  reply: ChatMessage
  user_message: ChatMessage
}

export interface SendMessagePayload {
  chapter_id?: number | null
  message: string
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Fetch chat history for a course (optionally filtered by chapter) */
export function getChatHistory(courseId: number, chapterId?: number | null) {
  return http.get<ChatHistory>(`/courses/${courseId}/chat`, {
    params: chapterId != null ? { chapter_id: chapterId } : {},
  })
}

/** Send a message and get AI reply */
export function sendMessage(courseId: number, payload: SendMessagePayload) {
  return http.post<ChatResponse>(`/courses/${courseId}/chat`, payload)
}

export interface ClearChatResult {
  deleted_count: number
}

/** Clear chat history for a course (optionally filtered by chapter) */
export function clearChatHistory(courseId: number, chapterId?: number | null) {
  return http.delete<ClearChatResult>(`/courses/${courseId}/chat`, {
    params: chapterId != null ? { chapter_id: chapterId } : {},
  })
}
