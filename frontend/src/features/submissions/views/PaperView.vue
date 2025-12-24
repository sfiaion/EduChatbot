<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-blue" style="margin:0;">学生作业</h2>
        <div v-if="submitting" style="margin-top:8px; max-width:480px;">
          <div style="margin-bottom:6px; color:#374151; font-weight:500;">{{ submitProgressText }}</div>
          <el-progress :percentage="submitProgress" :status="submitStatus" :text-inside="true" :stroke-width="18" />
        </div>
      </div>
      <div class="toolbar-right" style="color:#6b7280;">
        共 {{ questions.length }} 题
        <el-upload
          action=""
          :http-request="splitUpload"
          :show-file-list="false"
          multiple
          accept=".jpg,.jpeg,.png"
        >
          <el-button size="small" class="btn-outline">整页上传（自动切分）</el-button>
        </el-upload>
        <input ref="batchInput" type="file" accept=".jpg,.jpeg,.png" multiple style="display:none" @change="handleBatchFiles" />
        <el-button size="small" class="btn-outline" @click="triggerBatch">整页批量上传（多张）</el-button>
        <el-button type="primary" size="small" class="btn-ghost" @click="submit" :loading="submitting">提交作业</el-button>
      </div>
    </div>
    <div v-if="splitUploading" style="margin:8px 0; max-width:480px;">
      <div style="margin-bottom:6px; color:#374151; font-weight:500;">{{ splitProgressText }}</div>
      <el-progress :percentage="splitProgress" :status="splitStatus" :text-inside="true" :stroke-width="16" />
    </div>
    <div class="card-soft" style="margin-bottom:12px; padding:10px; color:#4b5563;">
      <strong>题号书写规范：</strong>
      <span>请在纸面用清晰编号标注每题，推荐格式：1. 2. 3. 或 (1)(2)(3)，也可“第1题”。每题内容与题号在同一块区域，题号后建议留空格。</span>
    </div>
    <div v-if="loading">加载中...</div>
    <div v-else-if="questions.length===0" style="color:#909399;">您暂无作业</div>
    <div v-else class="page-grid">
      <div>
        <div
          v-for="(q, idx) in questions"
          :key="q.id"
          class="mac-card soft-hover"
          style="margin-bottom:16px; padding:16px;"
        >
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div style="font-weight:600; color:#334155;">第 {{ idx + 1 }} 题</div>
            <el-tag type="success" size="small">题号 {{ q.id }}</el-tag>
          </div>
          <div style="margin-bottom:12px; white-space:pre-wrap;">
            <LatexText :content="q.question" />
          </div>
          <div class="divider-soft"></div>
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
            <el-radio-group v-model="inputMethods[q.id]" size="small">
              <el-radio-button label="text">输入答案</el-radio-button>
              <el-radio-button label="image">上传图片</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="inputMethods[q.id] === 'text'">
            <el-input
              v-model="answers[q.id]"
              type="textarea"
              :rows="3"
              placeholder="请输入答案"
            />
          </div>
          <div v-else>
            <el-upload
              action=""
              :http-request="(opts: any) => handleImageUpload(opts, q.id)"
              :show-file-list="false"
              accept=".jpg,.jpeg,.png"
            >
              <el-button type="primary" size="small">选择图片</el-button>
            </el-upload>
            <div v-if="imagePreviews[q.id]" style="margin-top:10px;">
              <img :src="imagePreviews[q.id]" style="max-width:200px; border:1px solid var(--border-soft); padding:4px; border-radius:8px;" />
              <div style="font-size:12px; color:#666;">已上传</div>
            </div>
          </div>
        </div>
      </div>
      <div class="aside-sticky">
        <div class="panel">
          <div class="panel-title">作业概览</div>
          <div class="panel-list">
            <div class="panel-item">
              <span>题目数量</span><strong>{{ questions.length }}</strong>
            </div>
            <div class="panel-item">
              <span>已输入答案</span><strong>{{ answeredCount }}</strong>
            </div>
          </div>
          <div style="margin-top:12px;">
            <el-button type="primary" style="width:100%;" @click="submit" :loading="submitting">提交作业</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <el-dialog v-model="splitDialog" title="整页切分预览" width="720px">
    <div v-if="splitBlocks.length===0" style="color:#909399;">未识别到题块，请确认题号书写清晰</div>
    <div v-else>
      <div style="margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
        <div style="color:#374151; font-weight:600;">识别到 {{ splitBlocks.length }} 个题块</div>
        <div style="display:flex; gap:8px;">
          <el-button size="small" class="btn-outline" @click="autoAssign">按题号自动匹配</el-button>
          <el-button size="small" type="primary" @click="confirmSplit">确认填充到作业</el-button>
        </div>
      </div>
      <el-scrollbar height="420px">
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div v-for="(group, gIndex) in groupedByPage" :key="gIndex">
            <div style="font-weight:600; color:#374151; margin:6px 0;">第 {{ group.page }} 页</div>
            <div style="display:flex; flex-direction:column; gap:10px;">
              <div v-for="(b, i) in group.blocks" :key="`${group.page}-${i}`" class="panel-item" style="align-items:flex-start;">
                <div style="flex:1;">
                  <div style="color:#6b7280; margin-bottom:6px;">建议题号：{{ b.question_no ?? '未识别' }}</div>
                  <div style="white-space:pre-wrap;"><LatexText :content="b.text" /></div>
                </div>
                <div style="width:220px;">
                  <el-select v-model="splitMap[b.index]" placeholder="选择对应题目" style="width:100%;">
                    <el-option
                      v-for="(q, idx) in questions"
                      :key="q.id"
                      :label="`第 ${idx+1} 题`"
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
      <el-button @click="splitDialog=false">关闭</el-button>
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
const submitProgressText = ref('准备提交...')
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
const splitProgressText = ref('正在上传并切分...')
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
      ElMessage.info('您暂无作业')
      questions.value = []
    } else {
      ElMessage.error('加载作业失败')
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
        ElMessage.success('图片上传成功')
        computeAnswered()
    } catch(e) {
        ElMessage.error('上传失败')
    }
}

async function splitUpload(options: any) {
  try {
    splitUploading.value = true
    splitProgress.value = 8
    splitStatus.value = 'active'
    splitProgressText.value = '正在上传...'
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
    splitProgressText.value = splitBlocks.value.length > 0 ? '切分完成' : '未识别到题块'
  } catch (e) {
    ElMessage.error('整页切分失败')
    splitStatus.value = 'exception'
    splitProgressText.value = '切分失败'
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
  splitProgressText.value = '正在上传并切分多页...'
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
    splitProgressText.value = '切分完成'
  } catch (_) {
    splitStatus.value = 'exception'
    splitProgressText.value = '切分失败'
    ElMessage.error('多页切分失败')
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
  ElMessage.success(`已填充 ${applied} 个题块`)
  if (Object.keys(styleCache).length > 0) {
    localStorage.setItem(NUMBER_STYLE_CACHE_KEY, JSON.stringify(styleCache))
  }
}

async function submit() {
  submitting.value = true
  submitProgress.value = 10
  submitStatus.value = 'active'
  submitProgressText.value = '正在提交答案...'
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
    ElMessage.success('作业已提交，正在批改...')
    submitProgressText.value = '正在批改...'

    // 现实友好：轮询结果到达后再跳转（最多等待 10 秒）
    const start = Date.now()
    const poll = async () => {
      try {
        const res = await getSubmissionResults(assignmentId, authStore.user?.student_id || 0)
        if (Array.isArray(res) && res.length > 0) {
          clearInterval(timer)
          submitProgress.value = 100
          submitStatus.value = 'success'
          submitProgressText.value = '批改完成'
          router.push(`/results/${assignmentId}`)
          return
        }
      } catch (_) {}
      if (Date.now() - start < 10000) {
        setTimeout(poll, 800)
      } else {
        // 超时仍然跳转，页面会自己请求并显示加载失败提示
        clearInterval(timer)
        submitProgress.value = 95
        submitStatus.value = 'active'
        submitProgressText.value = '批改耗时较长，正在跳转结果页...'
        router.push(`/results/${assignmentId}`)
      }
    }
    poll()
    
  } catch (e) {
    ElMessage.error('提交失败')
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
      '您有未提交的作业内容，离开后可能丢失进度。是否确认离开？',
      '提示',
      { confirmButtonText: '离开', cancelButtonText: '取消', type: 'warning' }
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
