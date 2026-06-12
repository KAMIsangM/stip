import http from './http'

export function getKnowledgeGraph(courseId: number) {
  return http.get(`/courses/${courseId}/knowledge-graph`)
}
