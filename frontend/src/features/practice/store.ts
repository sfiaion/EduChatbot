import { defineStore } from 'pinia'
import { getPracticeList, savePracticeList, savePracticeRecord } from '../../services/modules/practice'

function loadLocal(studentId: number): number[] {
  const raw = localStorage.getItem(`practice:${studentId}`)
  if (!raw) return []
  try { return JSON.parse(raw) || [] } catch { return [] }
}
function saveLocal(studentId: number, ids: number[]) {
  localStorage.setItem(`practice:${studentId}`, JSON.stringify(ids))
}

export const usePracticeStore = defineStore('practice', {
  state: () => ({
    studentId: 1,
    list: [] as number[],
    progress: {} as Record<number, string>,
    loading: false
  }),
  actions: {
    async init(studentId = 1) {
      this.studentId = studentId
      this.list = loadLocal(studentId)
      try {
        const server = await getPracticeList(studentId)
        const merged = Array.from(new Set([...(server || []), ...this.list]))
        this.list = merged
        saveLocal(studentId, merged)
      } catch {}
    },
    async add(id: number) {
      if (!this.list.includes(id)) {
        this.list.push(id)
        saveLocal(this.studentId, this.list)
        try { await savePracticeList(this.studentId, this.list) } catch {}
      }
    },
    async remove(id: number) {
      this.list = this.list.filter(x => x !== id)
      saveLocal(this.studentId, this.list)
      try { await savePracticeList(this.studentId, this.list) } catch {}
    },
    async clear() {
      this.list = []
      saveLocal(this.studentId, this.list)
      try { await savePracticeList(this.studentId, this.list) } catch {}
    },
    async saveProgress(questionId: number, answer: string) {
      this.progress[questionId] = answer
      try { await savePracticeRecord(this.studentId, questionId, answer) } catch {}
    }
  }
})
