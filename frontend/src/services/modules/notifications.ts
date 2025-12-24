import { api } from '../apiClient'

export interface NotificationItem {
  id: number
  title: string
  content: string
  is_read: boolean
  type?: string | null
  created_at: string
}

export async function listNotifications() {
  const r = await api.get('/api/notifications/')
  return r.data as NotificationItem[]
}

export async function markRead(id: number) {
  return api.post(`/api/notifications/${id}/read`)
}

export async function markAllRead() {
  return api.post('/api/notifications/read-all')
}

