import { api } from '../apiClient'

export async function getPracticeList(studentId: number) {
  const r = await api.get('/api/practice/list', { params: { student_id: studentId } })
  return r.data as number[]
}

export async function savePracticeList(studentId: number, ids: number[]) {
  await api.post('/api/practice/list', { student_id: studentId, ids })
}

export async function savePracticeRecord(studentId: number, questionId: number, answer: string) {
  await api.post('/api/practice/record', { student_id: studentId, question_id: questionId, answer })
}

export async function submitPracticeAnswer(questionId: number, answer: string) {
  const r = await api.post('/api/practice/submit', { question_id: questionId, answer })
  return r.data as { is_correct: boolean, correct_answer: string }
}
