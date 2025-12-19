<template>
  <TeacherDashboard v-if="showDashboard" :assignmentId="assignmentId" />
  <div v-else class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-teal" style="margin:0;">批改结果</h2>
        <span style="margin-left:8px; color:#606266;">作业ID：{{ assignmentId }}</span>
      </div>
      <div class="toolbar-right">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="display:flex; gap:14px; color:#374151; font-weight:600;">
            <span>正确率 {{ accuracy }}%</span>
            <span>正确 {{ correctCount }}</span>
            <span>错误 {{ wrongCount }}</span>
          </div>
          <el-switch
            v-model="showAll"
            inline-prompt
            active-text="显示全部"
            inactive-text="仅错误"
            @change="applyModeFromToggle"
          />
        </div>
      </div>
    </div>
    <div v-if="loading">加载中...</div>
    <div v-else-if="results.length===0" class="card-soft" style="padding:24px; color:#909399;">暂无批改结果</div>
    <div v-else class="results-grid">
      <div style="display:grid; grid-template-columns: 1fr; gap:20px;">
        <div
          v-for="(res, idx) in renderedResults"
          :key="idx"
          class="mac-card soft-hover"
          :class="isCollapsed(res) ? 'is-collapsed' : ''"
          style="padding:16px;"
          :style="{ boxShadow: `inset 0 0 0 2px ${res.is_correct ? '#67c23a' : '#f56c6c'}` }"
        >
        <div class="card-header" @click="handleTitleClick(res)">
          <div style="display:flex; align-items:center; gap:8px;">
            <el-icon v-if="isCollapsed(res)"><ArrowRight /></el-icon>
            <el-icon v-else><ArrowDown /></el-icon>
            <span>第 {{ idx + 1 }} 题</span>
          </div>
          <el-tag :type="res.is_correct ? 'success' : 'danger'" size="small">
            {{ res.is_correct ? '正确' : '错误' }}
          </el-tag>
        </div>
        <el-collapse-transition>
        <div v-show="!isCollapsed(res)" style="margin-bottom:8px;">
            <strong>学生答案：</strong>
            <div v-if="res.image_path || res.student_answer.includes('[IMAGE]')">
                <img :src="getImageUrl(res)" style="max-width:300px; border:1px solid #ddd; margin: 5px 0;" />
                <div v-if="res.student_answer && !res.student_answer.startsWith('[IMAGE]')">
                    <small>OCR识别内容: {{ res.student_answer }}</small>
                </div>
            </div>
            <div v-else>{{ res.student_answer }}</div>
        </div>
        </el-collapse-transition>
        
        <div v-if="!res.is_correct || !isCollapsed(res)" style="margin-top:12px; border-top:1px solid rgba(0,0,0,.06); padding-top:12px;">
            <div v-if="res.is_correct">
                <div style="color:#067b2d; font-weight:600; display:flex; align-items:center; gap:10px;">
                  <div style="display:flex; align-items:center; gap:6px;">
                    <el-icon><Check /></el-icon><span>回答正确</span>
                  </div>
                  <div style="display:flex; gap:6px;">
                    <el-button size="small" class="btn-outline" @click="viewQuestion(res.question_id)">查看题目</el-button>
                    <el-button size="small" type="primary" @click="toggleCollapse(res)">折叠</el-button>
                  </div>
                </div>
            </div>
            <div v-else>
                <div style="color:#f56c6c; font-weight:bold; margin-bottom:4px;">
                    <el-icon><Close /></el-icon> 回答错误
                </div>
                <div v-if="res.error_type" style="margin-bottom:4px;">
                    <el-tag type="danger" size="small">{{ formatErrorType(res.error_type) }}</el-tag>
                </div>
                <div style="margin-top:8px;">
                  <el-button size="small" class="btn-outline" @click="viewQuestion(res.question_id)">查看题目</el-button>
                  <el-button size="small" type="primary" @click="toggleAnswer(res.question_id)">查看答案</el-button>
                </div>
                <el-collapse-transition>
                  <div v-show="isAnswerShown(res.question_id)" style="margin-top:10px; padding:10px; background:#fff; border:1px dashed #ddd; border-radius:6px;">
                    <div style="margin-bottom:8px;">
                      <strong>标准答案：</strong>
                      <LatexText :content="answersMap[res.question_id] || '加载中...'" />
                    </div>
                    <div v-if="res.analysis" style="color:#606266; font-size:14px; line-height:1.5;">
                      <strong>解析：</strong>
                      <LatexText :content="res.analysis" />
                    </div>
                  </div>
                </el-collapse-transition>
                <div style="margin-top:8px;">
                    <div style="color:#374151; font-weight:600; margin-bottom:6px;">推荐练习</div>
                <template v-if="getRecs(res.question_id).length > 0">
                  <div style="display:flex; flex-wrap:wrap; gap:8px;">
                    <div v-for="item in getRecs(res.question_id)" :key="item.id" class="recommend-chip">
                      <span>#{{ item.id }}</span>
                      <div style="display:flex; gap:6px;">
                        <el-button size="small" class="btn-outline" @click="viewQuestion(item.id)">查看题目</el-button>
                        <el-button size="small" :type="inPractice(item.id) ? 'danger' : 'success'" @click="togglePractice(item.id)">
                          {{ inPractice(item.id) ? '删除' : '加入练习清单' }}
                        </el-button>
                      </div>
                    </div>
                  </div>
                </template>
                    <template v-else>
                      <div style="color:#909399; font-size:13px;">暂未找到合适的相似题目</div>
                    </template>
                </div>
            </div>
        </div>
      </div>
      </div>
      <div class="aside-sticky" style="max-width:300px; justify-self:end;">
        <div class="panel">
          <div class="panel-title">练习清单</div>
          <div style="font-size:13px; color:#606266;">共 {{ practice.list.length }} 题</div>
          <el-scrollbar height="420px" style="margin-top:6px;">
            <div class="panel-list">
              <div v-for="id in practice.list" :key="id" class="panel-item" style="display:flex; justify-content:space-between; align-items:center;">
                <span>题目ID：{{ id }}</span>
                <div style="display:flex; gap:6px;">
                  <el-button size="small" @click="viewQuestion(id)">查看</el-button>
                  <el-button size="small" type="danger" @click="practice.remove(id)">删除</el-button>
                </div>
              </div>
            </div>
          </el-scrollbar>
          <div style="margin-top:12px;">
            <el-button type="primary" style="width:100%;" @click="router.push('/practice')">去练习</el-button>
          </div>
          <div class="divider-soft" style="margin:12px 0;"></div>
          <div style="font-weight:600; margin-bottom:6px;">查看历史作业</div>
          <div style="display:flex; gap:8px;">
            <el-input-number v-model="historyId" :min="1" />
            <el-button class="btn-outline" @click="goHistory">查看结果</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  

  

  <!-- 题目预览弹窗，仅展示题干，支持查看答案 -->
  <el-dialog v-model="preview" :title="preview ? ('题目 '+preview.id) : ''" width="600px">
    <div v-if="preview">
      <div style="margin-bottom:8px;">
        <strong>题干：</strong>
        <LatexText :content="preview.question" />
      </div>
      <div style="margin-top:8px;">
        <el-button size="small" type="primary" @click="togglePreviewAnswer()">查看答案</el-button>
      </div>
      <el-collapse-transition>
        <div v-show="previewShowAnswer" style="margin-top:8px;">
          <strong>答案：</strong>
          <LatexText :content="preview.answer" />
        </div>
      </el-collapse-transition>
    </div>
    <template #footer>
      <el-button @click="preview=null">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSubmissionResults, type SubmissionResult } from '../../../services/modules/submissions'
import { recommendForWrong, type RecommendationItem, getProblemById } from '../../../services/modules/problems'
import { Check, Close, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { nextTick, onBeforeUnmount, computed } from 'vue'
import LatexText from '../../../components/LatexText.vue'
import { usePracticeStore } from '../../practice/store'
import TeacherDashboard from '../components/TeacherDashboard.vue'
import { useAuthStore } from '../../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const assignmentId = Number(route.params.assignmentId)
const studentId = Number(route.params.studentId) || 1

const isTeacher = computed(() => ['teacher', 'admin'].includes(authStore.user?.role || ''))
const showDashboard = computed(() => isTeacher.value && !route.params.studentId)

const loading = ref(false)
const results = ref<SubmissionResult[]>([])
const renderedResults = ref<SubmissionResult[]>([])
const recs = ref<Record<number, RecommendationItem[]>>({})
const practice = usePracticeStore()
const preview = ref<{ id: number; question: string; answer: string } | null>(null)
const previewShowAnswer = ref(false)
const answersMap = ref<Record<number, string>>({})
const shownMap = ref<Record<number, boolean>>({})
const historyId = ref(assignmentId)
const collapsedMap = ref<Record<number, boolean>>({})
const showAll = ref<boolean>(localStorage.getItem('results_view_mode') === 'all')
const listRenderCount = ref(20)

// Watch for route changes to handle component reuse (e.g. Dashboard -> Detail)
import { watch } from 'vue'
watch(
  () => route.path,
  async () => {
    // Re-evaluate IDs and permissions
    const newAssignId = Number(route.params.assignmentId)
    const newStudentId = Number(route.params.studentId) || 1
    
    // Reset state
    results.value = []
    loading.value = false
    
    // Check dashboard condition again (computed properties update automatically, but logic needs to run)
    if (showDashboard.value) return 
    
    // Load data
    await loadData(newAssignId, newStudentId)
  }
)

async function loadData(aid: number, sid: number) {
  if (!aid) return
  loading.value = true
  try {
    await practice.init(sid)
    results.value = await getSubmissionResults(aid, sid)
    for (const r of results.value) {
      try {
        const q = await getProblemById(r.question_id)
        answersMap.value[r.question_id] = q.answer
      } catch {}
    }
    initCollapse()
    applyMode()
    initRenderedResults()
    await fetchRecs()
    restoreScroll()
  } catch (e) {
    ElMessage.error('加载结果失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (showDashboard.value) return
  await loadData(assignmentId, studentId)
  window.addEventListener('scroll', handleScroll, { passive: true })
})

async function fetchRecs() {
  const wrongIds = results.value.filter(r => r && r.is_correct === false).map(r => r.question_id)
  for (const qid of wrongIds) {
    try {
      const r = await recommendForWrong(qid, studentId, 'high', 5)
      recs.value[qid] = r.items || []
    } catch (_) {
      recs.value[qid] = []
    }
  }
}

function initCollapse() {
  for (const r of results.value) {
    collapsedMap.value[r.question_id] = r.is_correct && !showAll.value
  }
}
function applyMode() {
  for (const r of results.value) {
    collapsedMap.value[r.question_id] = r.is_correct && !showAll.value
  }
  localStorage.setItem('results_view_mode', showAll.value ? 'all' : 'onlyWrong')
}
function applyModeFromToggle() {
  applyMode()
}
function isCollapsed(res: SubmissionResult) {
  return !!collapsedMap.value[res.question_id]
}
function toggleCollapse(res: SubmissionResult) {
  collapsedMap.value[res.question_id] = !collapsedMap.value[res.question_id]
}
function handleTitleClick(res: SubmissionResult) {
  if (res.is_correct) toggleCollapse(res)
}

function getImageUrl(res: SubmissionResult) {
    const sa = String(res.student_answer || '')
    let raw = res.image_path || ''
    if (!raw && sa.startsWith('[IMAGE]')) {
        const firstLine = sa.split('\n')[0] || ''
        raw = firstLine.replace('[IMAGE]', '')
    }
    if (!raw) return ''
    const path = raw.startsWith('/') ? raw : `/${raw}`
    const base = import.meta.env.VITE_API_BASE_URL || ''
    return base ? `${base}${path}` : path
}

function formatErrorType(type: string) {
    const map: Record<string, string> = {
        'knowledge': '知识点错误',
        'calculation': '计算错误',
        'misreading': '审题错误',
        'logic': '逻辑错误',
        'method': '方法错误'
    }
    return map[type] || type
}

function getRecs(qid: number) {
  return recs.value[qid] || []
}

async function viewQuestion(id: number) {
  try {
    const q = await getProblemById(id)
    preview.value = { id: q.id, question: q.question, answer: q.answer }
    previewShowAnswer.value = false
  } catch (e) {
    ElMessage.error('加载题目失败')
  }
}

function inPractice(id: number) {
  return practice.list.includes(id)
}
async function togglePractice(id: number) {
  if (inPractice(id)) await practice.remove(id)
  else await practice.add(id)
}

function toggleAnswer(qid: number) {
  shownMap.value[qid] = !shownMap.value[qid]
}
function isAnswerShown(qid: number) {
  return !!shownMap.value[qid]
}
function togglePreviewAnswer() {
  previewShowAnswer.value = !previewShowAnswer.value
}
function goHistory() {
  const id = Number(historyId.value || assignmentId)
  if (id > 0) router.push(`/results/${id}`)
}

const correctCount = computed(() => results.value.filter(r => r.is_correct).length)
const wrongCount = computed(() => results.value.filter(r => r.is_correct === false).length)
const accuracy = computed(() => {
  const total = results.value.length || 1
  return Math.round((correctCount.value / total) * 100)
})

function initRenderedResults() {
  listRenderCount.value = Math.min(20, results.value.length)
  renderedResults.value = results.value.slice(0, listRenderCount.value)
}
function handleScroll() {
  sessionStorage.setItem('results_scrollY', String(window.scrollY))
  const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 400
  if (nearBottom && listRenderCount.value < results.value.length) {
    listRenderCount.value = Math.min(results.value.length, listRenderCount.value + 20)
    renderedResults.value = results.value.slice(0, listRenderCount.value)
  }
}
function restoreScroll() {
  nextTick(() => {
    const y = Number(sessionStorage.getItem('results_scrollY') || '0')
    if (y > 0) window.scrollTo({ top: y })
  })
}
onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.results-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
}
@media (max-width: 1024px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
}
.mac-card { transition: all .3s ease; }
.mac-card:hover { transform: translateY(-1px); }
.mac-card.is-collapsed { padding: 8px !important; min-height: 44px; overflow: hidden; }
.mac-card { align-self: start; }
.card-header { margin-bottom: 8px; font-weight: 600; display:flex; align-items:center; justify-content:space-between; }
.recommend-chip { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:8px 10px; border:1px solid var(--border-soft); border-radius:10px; background:#fff; }
@media (max-width: 768px) {
  .mac-card { font-size: 14px; }
}
@media (min-width: 1025px) {
  .mac-card { font-size: 16px; }
}
</style>
