import { defineStore } from 'pinia'
import { listSessions, streamChat, getHistory, createSession, deleteSession } from '../../services/modules/chat'

export const useChatStore = defineStore('chat', {
  state: () => ({
    userId: 1 as number,
    sessions: [] as Array<{ session_id: string; title: string; is_pinned: boolean; created_at: string; updated_at: string }>,
    activeSessionId: '' as string,
    messages: [] as Array<{ role: 'user' | 'assistant'; content: string }>,
    loading: false as boolean
  }),
  actions: {
    async loadSessions(fetchCurrentHistory = true) {
      const data = await listSessions(this.userId)
      this.sessions = data
      
      // If no active session, select the first one
      if (!this.activeSessionId && this.sessions.length > 0) {
        this.activeSessionId = this.sessions[0]!.session_id
        if (fetchCurrentHistory) {
            this.messages = await getHistory(this.activeSessionId)
        }
      } else if (this.activeSessionId && fetchCurrentHistory) {
        try {
            this.messages = await getHistory(this.activeSessionId)
        } catch (e) {
            console.error("Failed to load history", e)
        }
      }
    },
    async selectSession(id: string) {
      if (this.activeSessionId === id) return
      this.activeSessionId = id
      this.messages = await getHistory(id)
    },
    async newSession() {
      const r = await createSession(this.userId)
      this.activeSessionId = r.session_id
      this.messages = []
      await this.loadSessions(false) 
    },
    async removeSession(id: string) {
      await deleteSession(id)
      if (this.activeSessionId === id) {
        this.activeSessionId = ''
        this.messages = []
      }
      await this.loadSessions()
    },
    async sendMessage(text: string) {
      if (this.loading) return
      this.loading = true
      
      this.messages.push({ role: 'user', content: text })
      const idx = this.messages.push({ role: 'assistant', content: '' }) - 1
      
      try {
        const sessionId = await streamChat({ 
            message: text, 
            session_id: this.activeSessionId || undefined, 
            user_id: this.userId 
        }, chunk => {
            const cur = this.messages[idx]
            if (cur) cur.content = (cur.content || '') + chunk
        })

        if (sessionId && sessionId !== this.activeSessionId) {
            this.activeSessionId = sessionId
        }
        
        await this.loadSessions(false)

      } catch (e) {
        console.error("Chat error:", e)
        const cur = this.messages[idx]
        if (cur) cur.content = (cur.content || '') + "\n[Error: Failed to send message]"
      } finally {
        this.loading = false
      }
    }
  }
})
