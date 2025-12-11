import { api } from '../apiClient'

export async function getWrongbook(studentId: number, groupBy: string) {
  const r = await api.get('/api/wrongbook/list', { params: { student_id: studentId, group_by: groupBy } })
  return r.data as any[]
}
