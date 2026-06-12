import http from './http'

export interface CourseCreatePayload {
  title: string
  description?: string
  preset_id?: number
}

export function createCourse(data: CourseCreatePayload) {
  return http.post('/courses', data)
}

export function listCourses(params?: {
  page?: number
  page_size?: number
  status?: string
  keyword?: string
}) {
  return http.get('/courses', { params })
}

export function getCourse(courseId: number) {
  return http.get(`/courses/${courseId}`)
}

export function triggerGenerate(courseId: number) {
  return http.post(`/courses/${courseId}/generate`)
}
