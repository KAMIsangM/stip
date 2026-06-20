import http from './http'

// ── knowledge-graph read ──

export function getKnowledgeGraph(courseId: number) {
  return http.get(`/courses/${courseId}/knowledge-graph`)
}

export function getSortedNodes(courseId: number) {
  return http.get(`/courses/${courseId}/knowledge-graph/sorted`)
}

export function getShortestPath(courseId: number, source: number, target: number) {
  return http.get(`/courses/${courseId}/knowledge-graph/shortest-path`, {
    params: { source, target },
  })
}

export function getRecommendations(courseId: number, nodeId: number, topK = 5) {
  return http.get(`/courses/${courseId}/knowledge-graph/recommendations`, {
    params: { node_id: nodeId, top_k: topK },
  })
}

// ── presets ──

export function listPresets() {
  return http.get('/knowledge-graph/presets')
}

export function applyPreset(courseId: number, presetId: number) {
  return http.post(`/courses/${courseId}/knowledge-graph/apply-preset`, {
    preset_id: presetId,
  })
}

// ── node CRUD ──

export interface NodeCreatePayload {
  name: string
  type?: string
  importance?: number
  description?: string | null
}

export interface NodeUpdatePayload {
  name?: string
  type?: string
  importance?: number
  description?: string | null
}

export function createNode(courseId: number, payload: NodeCreatePayload) {
  return http.post(`/courses/${courseId}/knowledge-graph/nodes`, payload)
}

export function updateNode(courseId: number, nodeId: number, payload: NodeUpdatePayload) {
  return http.put(`/courses/${courseId}/knowledge-graph/nodes/${nodeId}`, payload)
}

export function deleteNode(courseId: number, nodeId: number) {
  return http.delete(`/courses/${courseId}/knowledge-graph/nodes/${nodeId}`)
}

// ── edge CRUD ──

export interface EdgeCreatePayload {
  source_node_id: number
  target_node_id: number
  relation_type?: string
}

export interface EdgeUpdatePayload {
  relation_type?: string
}

export function createEdge(courseId: number, payload: EdgeCreatePayload) {
  return http.post(`/courses/${courseId}/knowledge-graph/edges`, payload)
}

export function updateEdge(courseId: number, edgeId: number, payload: EdgeUpdatePayload) {
  return http.put(`/courses/${courseId}/knowledge-graph/edges/${edgeId}`, payload)
}

export function deleteEdge(courseId: number, edgeId: number) {
  return http.delete(`/courses/${courseId}/knowledge-graph/edges/${edgeId}`)
}
