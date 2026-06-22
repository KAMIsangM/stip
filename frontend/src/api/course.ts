import http from './http'

// ---------------------------------------------------------------------------
// Type definitions
// ---------------------------------------------------------------------------

export interface CourseCreatePayload {
  title: string
  description?: string
  preset_id?: number
}

export interface CourseInfo {
  id: number
  title: string
  description: string | null
  status: string
  created_at: string | null
  updated_at: string | null
}

export interface ChapterInfo {
  id: number
  title: string
  order: number
  knowledge_points: string[]
}

export interface GenerationProgressInfo {
  status: string
  current_step: number
  total_steps: number
  error_message: string | null
}

export interface ProgressInfo {
  course_id: number
  status: string
  current_step: number
  total_steps: number
  step_name: string
  percentage: number
  error_message: string | null
}

export interface ScenePlan {
  chapters: SceneChapter[]
  global_modals: string[]
  chapter_count: number
}

export interface SceneChapter {
  chapter_title: string
  chapter_order: number
  recommended_modals: string[]
  knowledge_point_scenes: KnowledgePointScene[]
}

export interface KnowledgePointScene {
  name: string
  type: string
  importance: number
  modals: string[]
}

export interface CourseDetail {
  course_info: CourseInfo
  chapters: ChapterInfo[]
  scene_plan: ScenePlan | null
  generation_progress: GenerationProgressInfo | null
}

export interface CourseListResult {
  total: number
  list: CourseInfo[]
  page: number
  page_size: number
}

export interface GenerateResult {
  task_id: number
  status: string
  estimated_time: number
  message?: string
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Create a new course and trigger syllabus generation */
export function createCourse(data: CourseCreatePayload) {
  return http.post<CourseDetail>('/courses', data)
}

/** List courses with pagination and filtering */
export function listCourses(params?: {
  page?: number
  page_size?: number
  status?: string
  keyword?: string
}) {
  return http.get<CourseListResult>('/courses', { params })
}

/** Get course detail including chapters and progress */
export function getCourse(courseId: number) {
  return http.get<CourseDetail>(`/courses/${courseId}`)
}

/** Trigger multi-modal content generation for a course */
export function triggerGenerate(courseId: number) {
  return http.post<GenerateResult>(`/courses/${courseId}/generate`)
}

/** Poll generation progress (HTTP fallback) */
export function getProgress(courseId: number) {
  return http.get<ProgressInfo>(`/courses/${courseId}/progress`)
}

/** Delete a course and all its related data */
export function deleteCourse(courseId: number) {
  return http.delete(`/courses/${courseId}`)
}
