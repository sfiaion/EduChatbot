<template>
  <div style="padding:12px 20px; max-width:800px; margin:0 auto;">
    <h2 class="title-gradient-blue" style="margin:0 0 8px;">练习</h2>
    <div v-if="questions.length===0" style="color:#909399;">练习清单为空</div>
    <div v-else>
      <div style="margin-bottom:16px;">
        <el-button size="small" @click="prev" :disabled="index===0">上一题</el-button>
        <el-button size="small" @click="next" :disabled="index>=questions.length-1">下一题</el-button>
        <span style="margin-left:12px; color:#606266;">{{ index+1 }} / {{ questions.length }}</span>
      </div>
      <div style="padding:16px; border:1px solid #eee; border-radius:8px; background:#fff;">
        <LatexText :content="current.question" />
        <div style="margin-top:12px;">
          <el-input v-model="answer" type="textarea" :rows="3" placeholder="输入答案" />
        </div>
        <div style="margin-top:12px;">
          <el-button type="primary" @click="save">保存进度</el-button>
          <el-button style="margin-left:8px;" @click="reveal">查看答案</el-button>
        </div>
        <el-collapse-transition>
          <div v-show="showAnswer" style="margin-top:10px; padding:10px; border:1px dashed #ddd; border-radius:6px;">
            <strong>标准答案：</strong>
            <LatexText :content="current.answer" />
          </div>
        </el-collapse-transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePracticeStore } from '../store'
import { getProblemById } from '../../../services/modules/problems'
import LatexText from '../../../components/LatexText.vue'
import { ElMessage } from 'element-plus'

const store = usePracticeStore()
const questions = ref<{id:number; question:string; answer:string}[]>([])
const index = ref(0)
const answer = ref('')
const showAnswer = ref(false)

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
}
function prev() { if (index.value>0) { index.value--; showAnswer.value=false; loadProgress() } }
function next() { if (index.value<questions.value.length-1) { index.value++; showAnswer.value=false; loadProgress() } }
async function save() { const cur = current.value; await store.saveProgress(cur.id, answer.value); ElMessage.success('已保存') }
function reveal() { showAnswer.value = !showAnswer.value }
</script>
