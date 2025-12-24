<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-blue" style="margin:0;">练习</h2>
        <span style="margin-left:8px; color:#606266;">{{ index+1 }} / {{ questions.length }}</span>
      </div>
      <div class="toolbar-right">
        <el-button size="small" class="btn-outline" @click="prev" :disabled="index===0">上一题</el-button>
        <el-button size="small" class="btn-ghost" @click="next" :disabled="index>=questions.length-1">下一题</el-button>
      </div>
    </div>
    <div v-if="questions.length===0" style="color:#909399;">练习清单为空</div>
    <div v-else class="page-grid">
      <div class="mac-card soft-hover" style="padding:16px;">
        <LatexText :content="current.question" />
        <div class="divider-soft"></div>
        <el-input v-model="answer" type="textarea" :rows="4" placeholder="输入答案" />
        <div style="margin-top:12px; display:flex; gap:8px;">
          <el-button type="primary" @click="save">暂存进度</el-button>
          <el-button type="success" @click="submit" :disabled="isSubmitted">提交答案</el-button>
        </div>
        
        <div v-if="isSubmitted" style="margin-top:16px; padding:12px; border-radius:8px;" :style="{ background: isCorrect ? '#f0f9eb' : '#fef0f0', color: isCorrect ? '#67c23a' : '#f56c6c' }">
            <div style="font-weight:bold; font-size:16px; margin-bottom:8px;">
                {{ isCorrect ? '回答正确！' : '回答错误' }}
            </div>
            <div v-if="!isCorrect">
                <strong>标准答案：</strong>
                <LatexText :content="correctAnswer" />
            </div>
        </div>
      </div>
      <div class="aside-sticky">
        <div class="panel">
          <div class="panel-title">练习清单</div>
          <el-scrollbar height="420px">
            <div class="panel-list">
              <div
                v-for="(q, i) in questions"
                :key="q.id"
                class="panel-item"
                :style="i===index ? 'box-shadow: inset 0 0 0 2px var(--ring-soft);' : ''"
                @click="jump(i)"
              >
                <span>#{{ q.id }}</span>
                <el-tag size="small" :type="store.progress[q.id] ? 'success' : 'info'">
                  {{ store.progress[q.id] ? '已作答' : '未作答' }}
                </el-tag>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { usePracticeStore } from '../store'
import { getProblemById } from '../../../services/modules/problems'
import { submitPracticeAnswer } from '../../../services/modules/practice'
import LatexText from '../../../components/LatexText.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = usePracticeStore()
const questions = ref<{id:number; question:string; answer:string}[]>([])
const index = ref(0)
const answer = ref('')
const isSubmitted = ref(false)
const isCorrect = ref(false)
const correctAnswer = ref('')

const current = computed(() => questions.value[index.value] || { id:0, question:'', answer:'' })

onMounted(async () => {
  await store.init(1)
  for (const id of store.list) {
    try {
      const q = await getProblemById(id)
      questions.value.push({ id: q.id, question: q.question, answer: q.answer })
    } catch {}
  }
  loadProgress()
})

function loadProgress() {
  const cur = current.value
  answer.value = store.progress[cur.id] || ''
  isSubmitted.value = false
  isCorrect.value = false
  correctAnswer.value = ''
}
function prev() { if (index.value>0) { index.value--; loadProgress() } }
function next() { if (index.value<questions.value.length-1) { index.value++; loadProgress() } }
async function save() { const cur = current.value; await store.saveProgress(cur.id, answer.value); ElMessage.success('已保存') }

async function submit() {
  if (!answer.value.trim()) {
      ElMessage.warning('请输入答案')
      return
  }
  const cur = current.value
  try {
      const res = await submitPracticeAnswer(cur.id, answer.value)
      isSubmitted.value = true
      isCorrect.value = res.is_correct
      correctAnswer.value = res.correct_answer
      // Auto save progress
      await store.saveProgress(cur.id, answer.value)
  } catch (e) {
      ElMessage.error('提交失败')
  }
}

function jump(i:number){ index.value=i; loadProgress() }

function handleKey(e: KeyboardEvent){
  if (e.key === 'ArrowLeft') prev()
  else if (e.key === 'ArrowRight') next()
}
onMounted(() => window.addEventListener('keydown', handleKey))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKey))

onBeforeRouteLeave((to, from, next) => {
  void to; void from;
  if (answer.value && !isSubmitted.value) {
     ElMessageBox.confirm(
       '当前题目未提交，是否保存进度？',
       '提示',
       { 
         confirmButtonText: '保存', 
         cancelButtonText: '不保存', 
         type: 'warning',
         distinguishCancelAndClose: true
       }
     ).then(async () => {
       await save()
       next()
     }).catch((action) => {
       if (action === 'cancel') {
         next()
       } else {
         next(false)
       }
     })
  } else {
    next()
  }
})
</script>
