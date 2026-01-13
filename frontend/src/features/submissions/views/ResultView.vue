<template>
  <TeacherDashboard v-if="showDashboard" :assignmentId="assignmentId" />
  <div v-else class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-teal" style="margin:0;">Grading Results</h2>
        <span style="margin-left:8px; color:#606266;">Assignment ID: {{ assignmentId }}</span>
      </div>
      <div class="toolbar-right">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="display:flex; gap:14px; color:#374151; font-weight:600;">
            <span>Accuracy {{ displayAccuracy }}%</span>
            <span>Correct {{ displayCorrect }}</span>
            <span>Wrong {{ displayWrong }}</span>
            <span v-show="comboCount >= 2" class="combo-badge">Combo ×{{ comboCount }}</span>
          </div>
          <el-switch
            v-model="showAll"
            inline-prompt
            active-text="Show All"
            inactive-text="Only Wrong"
            @change="applyModeFromToggle"
          />
          <el-button class="btn-outline" @click="practiceDrawer = true">Practice List</el-button>
        </div>
      </div>
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="results.length===0" class="card-soft" style="padding:24px; color:#909399;">No grading results</div>
    <div v-else class="results-grid">
      <div style="display:grid; grid-template-columns: 1fr; gap:20px;">
        <div
          v-for="(res, idx) in renderedResults"
          :key="idx"
          class="mac-card soft-hover"
          :id="`card-${res.question_id}`"
          :class="isCollapsed(res) ? 'is-collapsed' : ''"
          style="padding:16px;"
          :style="{ boxShadow: `inset 0 0 0 2px ${res.is_correct ? '#67c23a' : '#f56c6c'}` }"
        >
        <div class="card-header" @click="handleTitleClick(res)">
          <div style="display:flex; align-items:center; gap:8px;">
            <el-icon v-if="isCollapsed(res)"><ArrowRight /></el-icon>
            <el-icon v-else><ArrowDown /></el-icon>
            <span>Question {{ idx + 1 }}</span>
          </div>
          <el-tag :type="res.is_correct ? 'success' : 'danger'" size="small">
            {{ res.is_correct ? 'Correct' : 'Incorrect' }}
          </el-tag>
        </div>
        <el-collapse-transition>
        <div v-show="!isCollapsed(res)" style="margin-bottom:8px;">
            <strong>Student Answer:</strong>
            <div v-if="res.image_path || res.student_answer.includes('[IMAGE]')">
                <img :src="getImageUrl(res)" style="max-width:300px; border:1px solid #ddd; margin: 5px 0;" />
                <div v-if="res.student_answer && !res.student_answer.startsWith('[IMAGE]')">
                    <small>OCR Content: {{ res.student_answer }}</small>
                </div>
            </div>
            <div v-else>{{ res.student_answer }}</div>
        </div>
        </el-collapse-transition>
        
        <div v-if="!res.is_correct || !isCollapsed(res)" style="margin-top:12px; border-top:1px solid rgba(0,0,0,.06); padding-top:12px;">
            <div v-if="res.is_correct">
                <div style="color:#067b2d; font-weight:600; display:flex; align-items:center; gap:10px;">
                  <div style="display:flex; align-items:center; gap:6px;">
                    <el-icon><Check /></el-icon><span>Correct Answer</span>
                  </div>
                  <div style="display:flex; gap:6px;">
                    <el-button size="small" class="btn-outline" @click="viewQuestion(res.question_id)">View Question</el-button>
                    <el-button size="small" type="primary" @click="toggleCollapse(res)">Collapse</el-button>
                  </div>
                </div>
                <!-- Recommendations for correct answers after retry -->
                <div v-if="(res.attempt_count || 0) > 1 && getRecs(res.question_id).length > 0" style="margin-top:12px;">
                    <div style="color:#e6a23c; font-weight:600; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                       <el-icon><Star /></el-icon> Good job! Here is some practice:
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:8px;">
                        <div v-for="item in getRecs(res.question_id)" :key="item.id" class="recommend-chip">
                          <span>#{{ item.id }}</span>
                          <div style="display:flex; gap:6px;">
                            <el-button size="small" class="btn-outline" @click="viewQuestion(item.id)">View</el-button>
                            <el-button size="small" :type="inPractice(item.id) ? 'danger' : 'success'" @click="togglePractice(item.id)">
                              {{ inPractice(item.id) ? 'Remove' : 'Add' }}
                            </el-button>
                          </div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-else>
                <!-- RETRY MODE -->
                <div v-if="res.status === 'retry' && isStudent" class="retry-section" :id="`retry-box-${res.question_id}`">
                    <div class="hint-box" style="background:#f0f9eb; border:1px solid #e1f3d8; padding:12px; border-radius:8px; margin-bottom:12px;">
                       <div style="color:#67c23a; font-weight:bold; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                          <el-icon><MagicStick /></el-icon> Hint Unlocked!
                       </div>
                       <div style="color:#529b2e; font-size:14px; line-height:1.5;">
                          <LatexText :content="res.hint || 'Try to look at it from a different angle!'" />
                       </div>
                    </div>
                    
                    <div class="retry-input" style="margin-bottom:12px;">
                        <div style="margin-bottom:8px;">
                            <el-radio-group v-model="retryInputMethods[res.question_id]" size="small">
                                <el-radio-button label="text">Type Answer</el-radio-button>
                                <el-radio-button label="image">Upload Image</el-radio-button>
                            </el-radio-group>
                        </div>
                        
                        <div v-if="retryInputMethods[res.question_id] === 'text'">
                           <el-input
                              v-model="retryAnswers[res.question_id]"
                              type="textarea"
                              :rows="2"
                              placeholder="Type your new answer here..."
                              :disabled="retrying[res.question_id]"
                           />
                        </div>
                        <div v-else>
                            <el-upload
                              action=""
                              :http-request="(opts: any) => handleRetryImageUpload(opts, res.question_id)"
                              :show-file-list="false"
                              accept=".jpg,.jpeg,.png"
                              :disabled="retrying[res.question_id]"
                            >
                              <el-button type="primary" size="small">
                                <el-icon style="margin-right:4px"><Upload /></el-icon> Choose Image
                              </el-button>
                            </el-upload>
                            <div v-if="retryImagePreviews[res.question_id]" style="margin-top:10px;">
                              <img :src="retryImagePreviews[res.question_id]" style="max-width:200px; border:1px solid var(--border-soft); padding:4px; border-radius:8px;" />
                              <div style="font-size:12px; color:#666;">Ready to submit</div>
                            </div>
                        </div>
                    </div>

                    <div v-if="retrying[res.question_id] || (retryProgress[res.question_id] || 0) > 0" style="margin-bottom:12px;">
                      <div style="margin-bottom:6px; color:#374151; font-weight:500;">
                        {{ retryProgressText[res.question_id] || 'Processing...' }}
                      </div>
                      <el-progress
                        :percentage="retryProgress[res.question_id] || 0"
                        :status="retryProgressStatus[res.question_id] || 'active'"
                        :text-inside="true"
                        :stroke-width="16"
                      />
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                       <div style="display:flex; align-items:center; gap:4px; font-size:14px; color:#e6a23c;">
                           <span style="font-weight:600;">Lives:</span>
                           <el-icon v-for="n in (res.remaining_attempts || 0)" :key="n"><Star /></el-icon>
                       </div>
                       <el-button type="primary" :loading="retrying[res.question_id]" @click="handleRetry(res.question_id)">
                          <el-icon><RefreshLeft /></el-icon> Try Again
                       </el-button>
                    </div>
                </div>

                <!-- FAILED MODE -->
                <div v-else>
                    <div style="color:#f56c6c; font-weight:bold; margin-bottom:4px;">
                        <el-icon><Close /></el-icon> Incorrect Answer
                    </div>
                    <div v-if="res.error_type" style="margin-bottom:4px;">
                        <el-tag type="danger" size="small">{{ formatErrorType(res.error_type) }}</el-tag>
                    </div>
                    <div style="margin-top:8px;">
                      <el-button size="small" class="btn-outline" @click="viewQuestion(res.question_id)">View Question</el-button>
                      <el-button
                        v-if="res.status === 'failed' || res.is_correct === true"
                        size="small"
                        type="primary"
                        @click="toggleAnswer(res.question_id)"
                      >Show Answer</el-button>
                    </div>
                    <el-collapse-transition>
                      <div v-show="isAnswerShown(res.question_id)" style="margin-top:10px; padding:10px; background:#fff; border:1px dashed #ddd; border-radius:6px;">
                        <div style="margin-bottom:8px;">
                          <strong>Reference Answer:</strong>
                          <LatexText :content="answersMap[res.question_id] || 'Loading...'" />
                        </div>
                        <div v-if="res.analysis" style="color:#606266; font-size:14px; line-height:1.5;">
                          <strong>Explanation:</strong>
                          <LatexText :content="res.analysis" />
                        </div>
                      </div>
                    </el-collapse-transition>
                    <div style="margin-top:8px;">
                        <div style="color:#374151; font-weight:600; margin-bottom:6px;">Recommended Practice</div>
                    <template v-if="getRecs(res.question_id).length > 0">
                      <div style="display:flex; flex-wrap:wrap; gap:8px;">
                        <div v-for="item in getRecs(res.question_id)" :key="item.id" class="recommend-chip">
                          <span>#{{ item.id }}</span>
                          <div style="display:flex; gap:6px;">
                            <el-button size="small" class="btn-outline" @click="viewQuestion(item.id)">View Question</el-button>
                            <el-button size="small" :type="inPractice(item.id) ? 'danger' : 'success'" @click="togglePractice(item.id)">
                              {{ inPractice(item.id) ? 'Remove' : 'Add to Practice' }}
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </template>
                        <template v-else>
                          <div style="color:#909399; font-size:13px;">No similar questions found</div>
                        </template>
                    </div>
                </div>
            </div>
        </div>
      </div>
      </div>
      <!-- Practice List moved to Drawer for better layout -->
      <el-drawer v-model="practiceDrawer" title="Practice List" size="30%">
        <div style="font-size:13px; color:#606266; margin-bottom:8px;">Total {{ practice.list.length }} questions</div>
        <el-scrollbar height="420px">
          <div class="panel-list">
            <div v-for="id in practice.list" :key="id" class="panel-item" style="display:flex; justify-content:space-between; align-items:center;">
              <span>Question ID: {{ id }}</span>
              <div style="display:flex; gap:6px;">
                <el-button size="small" @click="viewQuestion(id)">View</el-button>
                <el-button size="small" type="danger" @click="practice.remove(id)">Remove</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
        <div style="margin-top:12px;">
          <el-button type="primary" style="width:100%;" @click="router.push('/practice')">Go to Practice</el-button>
        </div>
        <div class="divider-soft" style="margin:12px 0;"></div>
        <div style="font-weight:600; margin-bottom:6px;">View Past Assignments</div>
        <div style="display:flex; gap:8px;">
          <el-input-number v-model="historyId" :min="1" />
          <el-button class="btn-outline" @click="goHistory">View Results</el-button>
        </div>
      </el-drawer>
    </div>
  </div>

  

  

  <!-- 题目预览弹窗，仅展示题干，支持查看答案 -->
  <el-dialog v-model="preview" :title="preview ? ('Question '+preview.id) : ''" width="600px">
    <div v-if="preview">
      <div style="margin-bottom:8px;">
        <strong>Question:</strong>
        <LatexText :content="preview.question" />
      </div>
      <div style="margin-top:8px;">
        <el-button size="small" type="primary" @click="togglePreviewAnswer()">Show Answer</el-button>
      </div>
      <el-collapse-transition>
        <div v-show="previewShowAnswer" style="margin-top:8px;">
          <strong>Answer:</strong>
          <LatexText :content="preview.answer" />
        </div>
      </el-collapse-transition>
    </div>
    <template #footer>
      <el-button @click="preview=null">Close</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSubmissionResults, submitAssignment, type SubmissionResult, uploadSubmissionImage } from '../../../services/modules/submissions'
import { recommendForWrong, type RecommendationItem, getProblemById } from '../../../services/modules/problems'
import { Check, Close, ArrowDown, ArrowRight, MagicStick, RefreshLeft, Star, Upload } from '@element-plus/icons-vue'
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
const isStudent = computed(() => (authStore.user?.role || '') === 'student')

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
const retryAnswers = ref<Record<number, string>>({})
const retrying = ref<Record<number, boolean>>({})
const retryInputMethods = ref<Record<number, 'text' | 'image'>>({})
const retryImagePreviews = ref<Record<number, string>>({})
const retryProgress = ref<Record<number, number>>({})
const retryProgressText = ref<Record<number, string>>({})
const retryProgressStatus = ref<Record<number, 'success' | 'exception' | 'active'>>({})
const practiceDrawer = ref(false)
const comboCount = ref(0)
const displayAccuracy = ref(0)
const displayCorrect = ref(0)
const displayWrong = ref(0)
const retryTips = [
  'AI is analyzing your solution path…',
  'Checking critical steps for mistakes…',
  'Matching related concepts and common pitfalls…',
  'Generating a targeted hint…',
]

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
    const prevCorrect = correctCount.value
    const prevWrong = wrongCount.value
    const prevAccuracy = accuracy.value
    results.value = await getSubmissionResults(aid, sid)
    
    // Reset retry state
    retryAnswers.value = {}
    retrying.value = {}
    retryInputMethods.value = {}
    retryImagePreviews.value = {}
    retryProgress.value = {}
    retryProgressText.value = {}
    retryProgressStatus.value = {}

    for (const r of results.value) {
      // Default to text input
      retryInputMethods.value[r.question_id] = 'text'
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
    animateMetrics(prevCorrect, correctCount.value, prevWrong, wrongCount.value, prevAccuracy, accuracy.value)
  } catch (e) {
    ElMessage.error('Failed to load results')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Load confetti script
  const script = document.createElement('script')
  script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js'
  script.async = true
  document.body.appendChild(script)

  if (showDashboard.value) return
  await loadData(assignmentId, studentId)
  window.addEventListener('scroll', handleScroll, { passive: true })
})

function triggerConfetti() {
  if ((window as any).confetti) {
    (window as any).confetti({
      particleCount: 160,
      spread: 90,
      origin: { y: 0.6 },
      colors: ['#ffd54f','#ffca28','#ffc107','#ffe082','#fff176']
    })
  }
}

function playSuccessSound() {
  try {
    const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext
    const ctx = new Ctx()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'sine'
    o.frequency.setValueAtTime(880, ctx.currentTime)
    o.frequency.linearRampToValueAtTime(660, ctx.currentTime + 0.15)
    g.gain.setValueAtTime(0.001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.05)
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35)
    o.connect(g).connect(ctx.destination)
    o.start()
    o.stop(ctx.currentTime + 0.4)
  } catch {}
}

function playErrorBuzz() {
  try {
    const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext
    const ctx = new Ctx()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'square'
    o.frequency.setValueAtTime(240, ctx.currentTime)
    g.gain.setValueAtTime(0.001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.05)
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35)
    o.connect(g).connect(ctx.destination)
    o.start()
    o.stop(ctx.currentTime + 0.4)
  } catch {}
}

function showOverlay(id: string, text: string, type: 'correct' | 'wrong') {
  const el = document.getElementById(id)
  if (!el) return
  const overlay = document.createElement('div')
  overlay.className = `status-overlay ${type}`
  overlay.textContent = text
  el.appendChild(overlay)
  setTimeout(() => overlay.remove(), 900)
}

function addClassTransient(el: HTMLElement | null, cls: string, ms = 800) {
  if (!el) return
  el.classList.add(cls)
  setTimeout(() => el.classList.remove(cls), ms)
}

function showSuccessEffects(qid: number) {
  const card = document.getElementById(`card-${qid}`)
  addClassTransient(card, 'gold-flash', 800)
  triggerConfetti()
  playSuccessSound()
  showOverlay(`card-${qid}`, 'Correct!', 'correct')
  comboCount.value += 1
}

function showWrongEffects(qid: number) {
  const card = document.getElementById(`card-${qid}`)
  addClassTransient(card, 'shake-animation', 600)
  addClassTransient(card, 'ripple-red', 800)
  playErrorBuzz()
  if ((navigator as any).vibrate) (navigator as any).vibrate([20, 30])
  showOverlay(`card-${qid}`, 'Wrong!', 'wrong')
  comboCount.value = 0
}

async function fetchRecs() {
  const targetIds = results.value.filter(r => {
    if (!r) return false
    // Don't show recs if in retry loop
    if (r.status === 'retry') return false
    // Show if failed
    if (r.is_correct === false) return true
    // Show if correct but took multiple attempts
    if (r.is_correct && (r.attempt_count || 0) > 1) return true
    return false
  }).map(r => r.question_id)

  for (const qid of targetIds) {
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
        'knowledge': 'Knowledge Error',
        'calculation': 'Calculation Error',
        'misreading': 'Misreading',
        'logic': 'Logical Error',
        'method': 'Method Error'
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
    ElMessage.error('Failed to load question')
  }
}

async function handleRetryImageUpload(options: any, qid: number) {
    try {
        const res = await uploadSubmissionImage(options.file)
        // Store a special marker for image path, similar to PaperView
        retryAnswers.value[qid] = `[IMAGE]${res.path}`
        retryImagePreviews.value[qid] = `${import.meta.env.VITE_API_BASE_URL || ''}${res.url}`
        ElMessage.success('Image uploaded')
    } catch(e) {
        ElMessage.error('Upload failed')
    }
}

async function handleRetry(qid: number) {
  if (retrying.value[qid]) return // Prevent double submission
  if (!retryAnswers.value[qid] || !retryAnswers.value[qid].trim()) return ElMessage.warning('Please enter an answer')
  
  retrying.value[qid] = true
  retryProgress.value[qid] = 12
  retryProgressStatus.value[qid] = 'active'
  retryProgressText.value[qid] = 'Grading in progress...'
  const timer = setInterval(() => {
    const cur = retryProgress.value[qid] || 0
    if (cur < 90) {
      retryProgress.value[qid] = cur + (cur < 50 ? 8 : 4)
      const step = Math.min(retryTips.length - 1, Math.floor((retryProgress.value[qid] || 0) / 25))
      retryProgressText.value[qid] = retryTips[step]
    }
  }, 400)
  try {
    const payload = {
        assignment_id: assignmentId,
        student_id: studentId,
        answers: [{
            question_id: qid,
            student_answer: retryAnswers.value[qid]
        }]
    }
    const data = await submitAssignment(payload)
    const first = data?.results?.[0]
    let needDelay = false
    if (first) {
        if (first.status !== 'retry') {
           if (first.is_correct) {
               ElMessage.success('Correct! Well done!')
               showSuccessEffects(qid)
               needDelay = true
           } else {
               ElMessage.error('Incorrect. Max attempts reached.')
               showWrongEffects(qid)
               needDelay = true
           }
        } else {
           ElMessage.warning('Still incorrect. Check the new hint!')
           showWrongEffects(qid)
           needDelay = true
        }
    }
    if (needDelay) {
      await new Promise(resolve => setTimeout(resolve, 650))
    }
    // Reload results
    await loadData(assignmentId, studentId)
    // Clear input
    retryAnswers.value[qid] = ''
    retryImagePreviews.value[qid] = ''
    retryProgress.value[qid] = 100
    retryProgressStatus.value[qid] = 'success'
    retryProgressText.value[qid] = 'Grading completed'
  } catch(e) {
    ElMessage.error('Retry failed')
    retryProgressStatus.value[qid] = 'exception'
    retryProgressText.value[qid] = 'Grading failed'
    // Reload to sync state (e.g. in case of attempt limit mismatch or system error)
    await loadData(assignmentId, studentId)
  } finally {
    clearInterval(timer)
    retrying.value[qid] = false
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

function easeOut(t: number) {
  return 1 - Math.pow(1 - t, 3)
}
function animateNumber(from: number, to: number, setter: (v:number)=>void, duration = 800) {
  const start = performance.now()
  const step = (ts: number) => {
    const p = Math.min(1, (ts - start) / duration)
    const v = Math.round(from + (to - from) * easeOut(p))
    setter(v)
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}
function animateMetrics(pc: number, nc: number, pw: number, nw: number, pa: number, na: number) {
  animateNumber(pa, na, v => displayAccuracy.value = v)
  animateNumber(pc, nc, v => displayCorrect.value = v)
  animateNumber(pw, nw, v => displayWrong.value = v)
}
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
.mac-card { align_self: start; position: relative; }
.card-header { margin-bottom: 8px; font-weight: 600; display:flex; align-items:center; justify-content:space-between; }
.recommend-chip { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:8px 10px; border:1px solid var(--border-soft); border-radius:10px; background:#fff; }
@media (max-width: 768px) {
  .mac-card { font-size: 14px; }
}
@media (min-width: 1025px) {
  .mac-card { font-size: 16px; }
}

@keyframes popIn {
  0% { transform: scale(0.9); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.hint-box {
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.shake-animation {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

.combo-badge {
  background: linear-gradient(90deg, #ff9f1a, #ffd23f);
  color: #4a3200;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 700;
  animation: combo-pop 600ms ease-out;
}
@keyframes combo-pop {
  0% { transform: scale(0.6); opacity: 0; }
  60% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(1.0); opacity: 1; }
}
.status-overlay {
  position: absolute;
  top: 12px;
  right: 16px;
  z-index: 5;
  font-weight: 800;
  font-size: 18px;
  padding: 6px 10px;
  border-radius: 8px;
  pointer-events: none;
}
.status-overlay.correct {
  color: #2e7d32;
  background: rgba(224, 242, 231, 0.9);
  animation: bounce-in 800ms ease-out;
}
.status-overlay.wrong {
  color: #c62828;
  background: rgba(255, 235, 238, 0.9);
  transform-origin: right top;
  animation: tilt-in 700ms ease-out;
}
@keyframes bounce-in {
  0% { transform: translateY(-20px) scale(0.8); opacity: 0; }
  50% { transform: translateY(6px) scale(1.05); opacity: 1; }
  100% { transform: translateY(0) scale(1.0); opacity: 1; }
}
@keyframes tilt-in {
  0% { transform: rotate(-12deg) translateY(-12px); opacity: 0; }
  60% { transform: rotate(6deg) translateY(4px); opacity: 1; }
  100% { transform: rotate(0deg) translateY(0); opacity: 1; }
}
.gold-flash {
  box-shadow: 0 0 0 2px rgba(255,193,7,0.7), 0 0 18px rgba(255,193,7,0.6);
  animation: flash-gold 800ms ease-out;
}
@keyframes flash-gold {
  0% { box-shadow: 0 0 0 0 rgba(255,193,7,0); }
  40% { box-shadow: 0 0 0 6px rgba(255,193,7,0.6), 0 0 24px rgba(255,193,7,0.8); }
  100% { box-shadow: 0 0 0 0 rgba(255,193,7,0); }
}
.ripple-red::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(244,67,54,0.25) 0%, rgba(244,67,54,0.0) 70%);
  transform: translate(-50%, -50%) scale(1);
  animation: ripple 800ms ease-out;
}
@keyframes ripple {
  0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(18); opacity: 0; }
}
</style>
