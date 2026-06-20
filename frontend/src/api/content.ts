import http from './http'

// ── types ──

export interface ContentModule {
  id: number
  chapter_id: number
  modal_type: string
  content_json: string | null
  file_path: string | null
}

export interface ChapterContentsResponse {
  chapter_id: number
  modal_count: number
  content_modules: ContentModule[]
  by_modal: Record<string, ContentModule[]>
  message?: string
}

// ── API ──

/** Get all content modules for a chapter */
export function getChapterContents(chapterId: number) {
  return http.get<ChapterContentsResponse>(`/chapters/${chapterId}/contents`)
}

/** Get a single content module by ID */
export function getContentModule(moduleId: number) {
  return http.get<ContentModule>(`/content/${moduleId}`)
}

/** List all available modal types */
export function listAvailableModals() {
  return http.get<{ modals: string[] }>('/modals')
}

/** Delete a content module */
export function deleteContentModule(moduleId: number) {
  return http.delete(`/content/${moduleId}`)
}
