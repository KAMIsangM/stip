import http from './http'

export function getChapterContents(chapterId: number) {
  return http.get(`/chapters/${chapterId}/contents`)
}
