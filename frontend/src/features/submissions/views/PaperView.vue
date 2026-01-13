<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-blue" style="margin:0;">Student Assignment</h2>
        <div v-if="submitting" style="margin-top:8px; max-width:480px;">
          <div style="margin-bottom:6px; color:#374151; font-weight:500;">{{ submitProgressText }}</div>
          <el-progress :percentage="submitProgress" :status="submitStatus" :text-inside="true" :stroke-width="18" />
        </div>
      </div>
      <div class="toolbar-right" style="color:#6b7280;">
        Total {{ questions.length }} questions
        <el-upload
          action=""
          :http-request="splitUpload"
          :show-file-list="false"
          multiple
          accept=".jpg,.jpeg,.png"
        >
          <el-button size="small" class="btn-outline">Upload Full Page (Auto Split)</el-button>
        </el-upload>
        <input ref="batchInput" type="file" accept=".jpg,.jpeg,.png" multiple style="display:none" @change="handleBatchFiles" />
        <el-button size="small" class="btn-outline" @click="triggerBatch">Upload Multiple Pages</el-button>
        <el-button type="primary" size="small" class="btn-ghost" @click="submit" :loading="submitting">Submit Assignment</el-button>
      </div>
    </div>
    <div v-if="splitUploading" style="margin:8px 0; max-width:480px;">
      <div style="margin-bottom:6px; color:#374151; font-weight:500;">{{ splitProgressText }}</div>
      <el-progress :percentage="splitProgress" :status="splitStatus" :text-inside="true" :stroke-width="16" />
    </div>
    <div class="card-soft" style="margin-bottom:12px; padding:10px; color:#4b5563;">
      <strong>Numbering Guide:</strong>
      <span>Please mark each question with clear numbers on paper, e.g., 1. 2. 3. or (1)(2)(3). Keep the number and content in the same area; leave a space after the number.</span>
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="questions.length===0" style="color:#909399;">No assignments</div>
    <div v-else class="page-grid">
      <div>
        <div
          v-for="(q, idx) in questions"
          :key="q.id"
          class="mac-card soft-hover"
          style="margin-bottom:16px; padding:16px;"
        >
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div style="font-weight:600; color:#334155;">Question {{ idx + 1 }}</div>
            <el-tag type="success" size="small">ID {{ q.id }}</el-tag>
          </div>
          <div style="margin-bottom:12px; white-space:pre-wrap;">
            <LatexText :content="q.question" />
          </div>
          <div class="divider-soft"></div>
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
            <el-radio-group v-model="inputMethods[q.id]" size="small">
              <el-radio-button label="text">Type Answer</el-radio-button>
              <el-radio-button label="image">Upload Image</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="inputMethods[q.id] === 'text'">
            <el-input
              v-model="answers[q.id]"
              type="textarea"
              :rows="3"
              placeholder="Enter answer"
            />
          </div>
          <div v-else>
            <el-upload
              action=""
              :http-request="(opts: any) => handleImageUpload(opts, q.id)"
              :show-file-list="false"
              accept=".jpg,.jpeg,.png"
            >
              <el-button type="primary" size="small">Choose Image</el-button>
            </el-upload>
            <div v-if="imagePreviews[q.id]" style="margin-top:10px;">
              <img :src="imagePreviews[q.id]" style="max-width:200px; border:1px solid var(--border-soft); padding:4px; border-radius:8px;" />
              <div style="font-size:12px; color:#666;">Uploaded</div>
            </div>
          </div>
        </div>
      </div>
      <div class="aside-sticky">
        <div class="panel">
          <div class="panel-title">Assignment Overview</div>
          <div class="panel-list">
            <div class="panel-item">
              <span>Question Count</span><strong>{{ questions.length }}</strong>
            </div>
            <div class="panel-item">
              <span>Answers Entered</span><strong>{{ answeredCount }}</strong>
            </div>
          </div>
          <div style="margin-top:12px;">
            <el-button type="primary" style="width:100%;" @click="submit" :loading="submitting">Submit Assignment</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <el-dialog v-model="splitDialog" title="Full Page Split Preview" width="720px">
    <div v-if="splitBlocks.length===0" style="color:#909399;">No blocks detected. Please ensure numbering is clear.</div>
    <div v-else>
      <div style="margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <div style="color:#374151; font-weight:600;">Detected {{ splitBlocks.length }} blocks</div>
        <div style="display:flex; gap:8px;">
          <el-button size="small" class="btn-outline" @click="autoAssign">Auto Match by Number</el-button>
          <el-button size="small" type="primary" @click="confirmSplit">Apply to Assignment</el-button>
        </div>
      </div>
      <el-scrollbar height="420px">
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div v-for="(group, gIndex) in groupedByPage" :key="gIndex">
            <div style="font-weight:600; color:#374151; margin:6px 0;">Page {{ group.page }}</div>
            <div style="display:flex; flex-direction:column; gap:10px;">
              <div v-for="(b, i) in group.blocks" :key="`${group.page}-${i}`" class="panel-item" style="align-items:flex-start;">
                <div style="flex:1;">
                  <div style="color:#6b7280; margin-bottom:6px;">Suggested Number: {{ b.question_no ?? 'N/A' }}</div>
                  <div style="white-space:pre-wrap;"><LatexText :content="b.text" /></div>
                </div>
                <div style="width:220px;">
                  <el-select v-model="splitMap[b.index]" placeholder="Select Question" style="width:100%;">
                    <el-option
                      v-for="(q, idx) in questions"
                      :key="q.id"
                      :label="`Question ${idx+1}`"
                      :value="q.id"
                    />
                  </el-select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>
    </div>
    <template #footer>
      <el-button @click="splitDialog=false">Close</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { getAssignmentPaper } from '../../../services/modules/assignments'
import { submitAssignment, uploadSubmissionImage, getSubmissionResults, ocrSplit } from '../../../services/modules/submissions'
import { ElMessage, ElMessageBox } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'
import { useAuthStore } from '../../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const assignmentId = Number(route.params.id)

const loading = ref(false)
const submitting = ref(false)
const submitProgress = ref(0)
const submitStatus = ref<'success'|'exception'|'active'>('active')
const submitProgressText = ref('Preparing to submit...')
const questions = ref<{id: number; question: string}[]>([])
const answers = ref<Record<number, string>>({})
const inputMethods = ref<Record<number, 'text' | 'image'>>({})
const imagePreviews = ref<Record<number, string>>({})
const answeredCount = ref(0)
const splitDialog = ref(false)
const splitBlocks = ref<Array<{ page: number; index: number; question_no: number | null; text: string }>>([])
const splitMap = ref<Record<number, number>>({})
const splitUploading = ref(false)
const splitProgress = ref(0)
const splitStatus = ref<'success'|'exception'|'active'>('active')
const splitProgressText = ref('Uploading and splitting...')
const splitPageCounter = ref(0)
const batchInput = ref<HTMLInputElement | null>(null)
const NUMBER_STYLE_CACHE_KEY = 'split_number_style_map'

const groupedByPage = computed(() => {
  const map: Record<number, Array<{ page: number; index: number; question_no: number | null; text: string }>> = {}
  for (const b of splitBlocks.value) {
    const arr = map[b.page] || (map[b.page] = [])
    arr.push(b)
  }
  const pages = Object.keys(map).map(n => Number(n)).sort((a, b) => a - b)
  return pages.map(p => ({ page: p, blocks: map[p] }))
})

onMounted(async () => {
  if (!assignmentId) return
  loading.value = true
  try {
    questions.value = await getAssignmentPaper(assignmentId)
    questions.value.forEach(q => {
      answers.value[q.id] = ''
      inputMethods.value[q.id] = 'text'
    })
    computeAnswered()
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404) {
      ElMessage.info('No assignments')
      questions.value = []
    } else {
      ElMessage.error('Failed to load assignment')
    }
  } finally {
    loading.value = false
  }
})

function computeAnswered() {
  answeredCount.value = Object.values(answers.value).filter(v => (v || '').trim().length > 0).length
}

async function handleImageUpload(options: any, qid: number) {
    try {
        const res = await uploadSubmissionImage(options.file)
        // Store a special marker for image path
        answers.value[qid] = `[IMAGE]${res.path}`
    imagePreviews.value[qid] = `${import.meta.env.VITE_API_BASE_URL || ''}${res.url}`
        ElMessage.success('Image uploaded')
        computeAnswered()
    } catch(e) {
        ElMessage.error('Upload failed')
    }
}

async function splitUpload(options: any) {
  try {
    splitUploading.value = true
    splitProgress.value = 8
    splitStatus.value = 'active'
    splitProgressText.value = 'Uploading...'
    const timer = setInterval(() => {
      if (splitProgress.value < 90) splitProgress.value += splitProgress.value < 50 ? 6 : 3
    }, 400)
    const r = await ocrSplit(options.file as File)
    const page = ++splitPageCounter.value
    const blocks = (r.blocks || []).map((b: any, idx: number) => ({ page, index: splitBlocks.value.length + idx, question_no: b.question_no, text: b.text }))
    splitBlocks.value = splitBlocks.value.concat(blocks)
    splitMap.value = { ...splitMap.value }
    splitDialog.value = true
    clearInterval(timer)
    splitProgress.value = splitBlocks.value.length > 0 ? 100 : 95
    splitStatus.value = splitBlocks.value.length > 0 ? 'success' : 'exception'
    splitProgressText.value = splitBlocks.value.length > 0 ? 'Split completed' : 'No blocks detected'
  } catch (e) {
    ElMessage.error('Full-page split failed')
    splitStatus.value = 'exception'
    splitProgressText.value = 'Split failed'
  }
  finally {
    setTimeout(() => { splitUploading.value = false }, 500)
  }
}

function triggerBatch() {
  batchInput.value?.click()
}
async function handleBatchFiles(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  splitUploading.value = true
  splitProgress.value = 6
  splitStatus.value = 'active'
  splitProgressText.value = 'Uploading and splitting multiple pages...'
  const files = Array.from(input.files)
  const timer = setInterval(() => {
    if (splitProgress.value < 90) splitProgress.value += splitProgress.value < 50 ? 5 : 3
  }, 400)
  try {
    for (const f of files) {
      const r = await ocrSplit(f)
      const page = ++splitPageCounter.value
      const blocks = (r.blocks || []).map((b: any, idx: number) => ({ page, index: splitBlocks.value.length + idx, question_no: b.question_no, text: b.text }))
      splitBlocks.value = splitBlocks.value.concat(blocks)
    }
    splitDialog.value = true
    splitProgress.value = 100
    splitStatus.value = 'success'
    splitProgressText.value = 'Split completed'
  } catch (_) {
    splitStatus.value = 'exception'
    splitProgressText.value = 'Split failed'
    ElMessage.error('Multi-page split failed')
  } finally {
    clearInterval(timer)
    setTimeout(() => { splitUploading.value = false }, 600)
    input.value = '' // reset
  }
}

function autoAssign() {
  const cachedRaw = localStorage.getItem(NUMBER_STYLE_CACHE_KEY)
  const cached: Record<number, number> = cachedRaw ? JSON.parse(cachedRaw) : {}
  for (const b of splitBlocks.value) {
    const qno = b.question_no
    let targetIndex: number | undefined
    if (typeof qno === 'number') {
      if (cached[qno]) targetIndex = cached[qno]
      else targetIndex = qno
    }
    if (typeof targetIndex === 'number' && targetIndex >= 1 && targetIndex <= questions.value.length) {
      const target = questions.value[targetIndex - 1]
      if (target) splitMap.value[b.index] = target.id
    }
  }
}

function confirmSplit() {
  let applied = 0
  const styleCache: Record<number, number> = {}
  for (const b of splitBlocks.value) {
    const qid = splitMap.value[b.index]
    if (qid) {
      answers.value[qid] = b.text || ''
      inputMethods.value[qid] = 'text'
      applied++
      if (typeof b.question_no === 'number') {
        const idx = questions.value.findIndex(q => q.id === qid)
        if (idx >= 0) styleCache[b.question_no] = idx + 1
      }
    }
  }
  computeAnswered()
  splitDialog.value = false
  ElMessage.success(`Applied ${applied} blocks`)
  if (Object.keys(styleCache).length > 0) {
    localStorage.setItem(NUMBER_STYLE_CACHE_KEY, JSON.stringify(styleCache))
  }
}

async function submit() {
  submitting.value = true
  submitProgress.value = 10
  submitStatus.value = 'active'
  submitProgressText.value = 'Submitting answers...'
  const timer = setInterval(() => {
    if (submitProgress.value < 90) {
      submitProgress.value += submitProgress.value < 50 ? 6 : 3
    }
  }, 400)
  try {
    const payload = {
      assignment_id: assignmentId,
      student_id: authStore.user?.student_id || 0, 
      answers: Object.entries(answers.value).map(([qid, ans]) => ({
        question_id: Number(qid),
        student_answer: ans
      }))
    }
    await submitAssignment(payload)
    ElMessage.success('Assignment submitted, grading in progress...')
    submitProgressText.value = 'Grading...'

    // User-friendly: poll results then redirect (max 10s)
    const start = Date.now()
    const poll = async () => {
      try {
        const res = await getSubmissionResults(assignmentId, authStore.user?.student_id || 0)
        if (Array.isArray(res) && res.length > 0) {
          clearInterval(timer)
          submitProgress.value = 100
          submitStatus.value = 'success'
          submitProgressText.value = 'Grading completed'
          router.push(`/results/${assignmentId}`)
          return
        }
      } catch (_) {}
      if (Date.now() - start < 10000) {
        setTimeout(poll, 800)
      } else {
        // Timeout: still redirect; results page will fetch and show status
        clearInterval(timer)
        submitProgress.value = 95
        submitStatus.value = 'active'
        submitProgressText.value = 'Grading takes longer, redirecting to results...'
        router.push(`/results/${assignmentId}`)
      }
    }
    poll()
    
  } catch (e) {
    submitProgressText.value = 'Submission encountered issues, verifying results...'
    submitStatus.value = 'active'
    const start = Date.now()
    const verify = async () => {
      try {
        const res = await getSubmissionResults(assignmentId, authStore.user?.student_id || 0)
        if (Array.isArray(res) && res.length > 0) {
          clearInterval(timer)
          submitProgress.value = 100
          submitStatus.value = 'success'
          submitProgressText.value = 'Grading completed'
          router.push(`/results/${assignmentId}`)
          return
        }
      } catch (_) {}
      if (Date.now() - start < 10000) {
        setTimeout(verify, 800)
      } else {
        clearInterval(timer)
        submitProgress.value = 0
        submitStatus.value = 'exception'
        submitProgressText.value = 'Submission failed'
        ElMessage.error('Submission failed')
      }
    }
    verify()
  } finally {
    submitting.value = false
  }
}

onBeforeRouteLeave((to, from, next) => {
  void to; void from;
  // Check if user has entered any answers and not submitted successfully
  // submitStatus === 'success' means we are redirecting after submission
  if (answeredCount.value > 0 && !submitting.value && submitStatus.value !== 'success') {
    ElMessageBox.confirm(
      'You have unsaved answers. Leaving may lose progress. Confirm to leave?',
      'Notice',
      { confirmButtonText: 'Leave', cancelButtonText: 'Cancel', type: 'warning' }
    ).then(() => {
      next()
    }).catch(() => {
      next(false)
    })
  } else {
    next()
  }
})
</script>
