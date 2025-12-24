import { api } from '../apiClient'

export interface ClassMember {
  id: number
  name: string
  role: 'teacher' | 'student'
  student_number?: string
}

export interface ClassRequest {
  id: number
  student_name: string
  class_name: string
  type: 'apply' | 'invite'
  status: string
  created_at: string
}

export async function listMembers() {
  const r = await api.get('/api/classes/members')
  return r.data as ClassMember[]
}

export async function applyJoin(className: string) {
  return api.post('/api/classes/join', null, { params: { class_name: className } })
}

export async function inviteStudent(username: string) {
  return api.post('/api/classes/invite', null, { params: { student_username: username } })
}

export async function listRequests() {
  const r = await api.get('/api/classes/requests')
  return r.data as ClassRequest[]
}

export async function handleRequest(id: number, action: 'accept' | 'reject') {
  return api.post(`/api/classes/requests/${id}/${action}`)
}

