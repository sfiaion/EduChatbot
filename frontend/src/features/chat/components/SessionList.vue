<template>
  <div style="width:300px; border-right:1px solid #eee; height:100%; display:flex; flex-direction:column;">
    <div style="padding:12px; display:flex; align-items:center; justify-content:space-between;">
      <div class="title-gradient-blue" style="font-weight:700; font-size:20px;">Sessions</div>
      <el-button type="primary" size="small" @click="newChat">New Chat</el-button>
    </div>
    <div style="padding:0 12px 12px;">
      <el-input v-model="q" placeholder="Search sessions" clearable />
    </div>
    <div style="flex:1; overflow:auto;">
      <div
        v-for="s in filtered"
        :key="s.session_id"
        class="session-item"
        :class="{ active: s.session_id === chat.activeSessionId }"
        @click="select(s.session_id)"
      >
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <div style="font-weight:500; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{ s.title || 'Untitled Session' }}</div>
            <el-button link type="danger" size="small" @click.stop="remove(s.session_id)">Delete</el-button>
        </div>
        <div style="font-size:12px; color:#909399; margin-top:4px;">{{ formatTime(s.updated_at) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '../store'
import { ElMessageBox } from 'element-plus'
import { computed, ref } from 'vue'

const chat = useChatStore()
const q = ref('')
const filtered = computed(() => {
  const t = q.value.trim().toLowerCase()
  if (!t) return chat.sessions
  return chat.sessions.filter(s => (s.title || '').toLowerCase().includes(t))
})

function select(id: string) { chat.selectSession(id) }
async function newChat() { await chat.newSession() }

async function remove(id: string) {
  try {
    await ElMessageBox.confirm('Delete this session?', 'Confirm', { type: 'warning' })
    await chat.removeSession(id)
  } catch {
    // cancelled
  }
}

function formatTime(iso: string) {
    if (!iso) return ''
    return new Date(iso).toLocaleString()
}
</script>

<style scoped>
.session-item {
    padding: 12px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background .15s ease;
}
.session-item:hover {
    background-color: #fafafa;
}
.session-item.active {
    background-color: #f0f7ff;
    border-left: 3px solid #409eff;
}
</style>
