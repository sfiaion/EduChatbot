import { api } from '../apiClient'

export async function submitAssignment(payload: { assignment_id: number; student_id: number; answers: {question_id: number, student_answer: string}[] }) {
  return api.post('/api/submissions/', payload)
}

export async function uploadSubmissionImage(file: File) {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post('/api/submissions/upload_image', form)
  return r.data as { path: string; url: string }
}

export interface SubmissionResult {
  question_id: number
  student_answer: string
  image_path?: string
  is_correct: boolean
  error_type?: string
  analysis?: string
}

export async function getSubmissionResults(assignmentId: number, studentId: number) {
    const r = await api.get(`/api/submissions/results`, { params: { assignment_id: assignmentId, student_id: studentId } })
    return r.data as SubmissionResult[]
}

export async function ocrImage(file: File) {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post('/api/submissions/ocr', form)
  return r.data as { text: string }
}
