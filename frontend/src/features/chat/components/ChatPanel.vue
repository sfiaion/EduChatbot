<template>
  <div style="flex:1; display:flex; height:100%;">
    <div style="flex:1; display:flex; flex-direction:column;">
      <div ref="list" style="flex:1; overflow:auto; padding:16px; padding-bottom:96px;">
        <div v-for="(m,i) in chat.messages" :key="i" style="margin-bottom:10px; display:flex; gap:8px;" :style="m.role==='user' ? 'justify-content:flex-end;' : 'justify-content:flex-start;'">
          <el-avatar :size="28" :style="m.role==='user' ? 'background:#409eff;' : 'background:#67c23a;'">{{ m.role==='user' ? '我' : '助' }}</el-avatar>
          <div :style="m.role==='user' ? userStyle : assistantStyle">
            {{ m.content }}
            <div style="text-align:right; font-size:12px; color:#909399; margin-top:6px;">{{ now }}</div>
          </div>
        </div>
      </div>
      <div style="position:fixed; left:var(--aside-w); right:0; bottom:0; border-top:1px solid #eee; padding:12px; display:flex; gap:12px; background: rgba(255,255,255,.9); backdrop-filter: blur(8px); box-shadow: 0 -6px 16px rgba(0,0,0,.06);">
        <el-input v-model="text" placeholder="输入消息" />
        <el-button type="primary" :loading="chat.loading" @click="send">发送</el-button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '../store'
const chat = useChatStore()
const text = ref('')
const list = ref<HTMLDivElement|null>(null)
const userStyle = 'max-width:70%; background:linear-gradient(135deg, #3b82f6, #2563EB); color:#fff; padding:10px; border-radius:10px 10px 0 10px; white-space:pre-wrap; box-shadow:0 6px 18px rgba(37,99,235,.18);'
const assistantStyle = 'max-width:70%; background:linear-gradient(135deg, #f8fafc, #eef2ff); color:#303133; padding:10px; border-radius:10px 10px 10px 0; white-space:pre-wrap; box-shadow:0 6px 18px rgba(0,0,0,.08);'
const now = new Date().toLocaleTimeString()

async function send() {
  if (!text.value) return
  await chat.sendMessage(text.value)
  text.value = ''
}

watch(
  () => chat.messages.map(m => m.content).join('\n'),
  async () => {
    await nextTick()
    const el = list.value
    if (el) el.scrollTop = el.scrollHeight
  }
)
</script>
