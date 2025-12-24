import { api } from '../apiClient'

export async function getTeacherClasses() {
  const r = await api.get('/api/teacher/classes')
  return r.data as Array<{ id: number; name: string }>
}

