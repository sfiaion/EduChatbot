import { api } from '../apiClient'

export async function submitAssignment(payload: { assignment_id: number; student_id: number; answers: {question_id: number, student_answer: string}[] }) {
  const r = await api.post('/api/submissions/', payload)
  return r.data as { status: string; submitted_count: number; results: SubmissionResult[] }
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
  status?: 'success' | 'retry' | 'failed'
  hint?: string
  attempt_count?: number
  remaining_attempts?: number
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

export async function ocrSplit(file: File) {
  const form = new FormData()
  form.append('file', file)
  const r = await api.post('/api/submissions/ocr_split', form)
  return r.data as { blocks: Array<{ question_no: number | null; text: string }> }
}

export async function getAssignmentStats(assignmentId: number) {
    const r = await api.get(`/api/submissions/stats/${assignmentId}`)
    return r.data as {
        overall: { average_accuracy: number, total_submissions: number, student_count: number },
        questions: { id: number, text: string, correct_rate: number, wrong_count: number }[],
        students: { id: number, name: string, accuracy: number, submitted: boolean }[],
        weak_points: { tag: string, count: number }[],
        error_distribution: { name: string, value: number }[]
    }
}

export async function getAssignmentsList() {
    const r = await api.get('/api/assignments/')
    return r.data as Array<{
        id: number
        title: string
        deadline: string | null
        created_at: string
        teacher_id: number
        class_id: number
    }>
}
