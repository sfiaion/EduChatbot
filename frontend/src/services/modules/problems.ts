import { api } from '../apiClient'

export interface Question {
  id: number
  question: string
  normalized_question: string
  answer: string
  difficulty_tag: string
  knowledge_tag: string
  created_at: string
}

export interface QuestionListResult {
    total: number
    items: Question[]
}

export async function listQuestions(skip = 0, limit = 20, difficulty?: string, knowledge?: string) {
  const r = await api.get('/api/problems/', { params: { skip, limit, difficulty, knowledge } })
  return r.data as QuestionListResult
}

export async function uploadQuestions(file: File) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/api/problems/upload', form)
}

export interface RecommendationItem {
  id: number
  score: number
}
export async function recommendForWrong(questionId: number, studentId: number, slot: 'high'|'mid'|'low' = 'high', expect = 5) {
  const r = await api.post(`/api/problems/${questionId}/recommendation`, {
    question_id: questionId,
    student_id: studentId,
    slot,
    expect_num: expect
  })
  return r.data as { base_question_id: number; slot: string; expected: number; found: number; items: RecommendationItem[] }
}

export async function getProblemById(id: number) {
  const r = await api.get(`/api/problems/${id}`)
  return r.data as { id: number; question: string; normalized_question: string; answer: string; difficulty_tag: string; knowledge_tag: string }
}
