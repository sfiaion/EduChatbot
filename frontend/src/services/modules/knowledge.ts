import { api } from '../apiClient'

export interface GraphNode {
  id: string
  label: string
}

export interface GraphEdge {
  source: string
  target: string
}

export async function searchKnowledgeNodes(q: string) {
  const r = await api.get('/api/knowledge/search', { params: { q } })
  return r.data as Array<{ name: string }>
}

export async function getKnowledgeSubgraph(center: string) {
  const r = await api.get('/api/knowledge-graph', { params: { center } })
  return r.data as { nodes: GraphNode[]; edges: GraphEdge[] }
}

export async function getBreakpoints(classId: number, startDate: string, endDate: string, topK = 3) {
  const r = await api.get('/api/knowledge-graph/breakpoints', {
    params: { top_k: topK },
    headers: { 'Class-ID': String(classId), 'Start-Date': startDate, 'End-Date': endDate }
  })
  return r.data as Array<{ name: string; diff: number }>
}

export async function getNodeAnalysis(name: string, classId: number, startDate: string, endDate: string) {
  const r = await api.get(`/api/knowledge-graph/node/${encodeURIComponent(name)}`, {
    headers: { 'Class-ID': String(classId), 'Start-Date': startDate, 'End-Date': endDate }
  })
  return r.data as {
    node: {
      name: string
      total_errors: number
      daily_errors: Record<string, number>
      content: string
      longest_path: number
    }
    preceding_nodes: Array<{ name: string; total_errors: number }>
  }
}

export async function listAllKnowledgeNodes(limit = 500) {
  const r = await api.get('/api/knowledge/all', { params: { limit } })
  return r.data as Array<{ name: string }>
}

export async function getCandidateNodes(classId: number, startDate: string, endDate: string, limit = 20) {
  const r = await api.get('/api/knowledge-graph/candidates', {
    params: { limit },
    headers: { 'Class-ID': String(classId), 'Start-Date': startDate, 'End-Date': endDate }
  })
  return r.data as Array<string>
}
