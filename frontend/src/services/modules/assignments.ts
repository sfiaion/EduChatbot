import { api } from '../apiClient'

export interface AssignmentCreate {
  title: string
  teacher_id: number
  class_id: number
  deadline?: string
  assigned_student_ids?: number[]
  assigned_question_ids: number[]
}

export async function getAssignmentsList() {
  const r = await api.get('/api/assignments/')
  return r.data as any[]
}

export async function createAssignment(data: AssignmentCreate) {
  return api.post('/api/assignments/', data)
}

export async function getAssignmentPaper(id: number) {
  const r = await api.get(`/api/assignments/${id}/paper`)
  return r.data as { id: number; question: string }[]
}

export async function getAssignmentStats(id: number) {
  const r = await api.get(`/api/assignments/${id}/stats`)
  return r.data as { total_students: number; total_questions: number }
}
