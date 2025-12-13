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
          :http-request="batchOcrUpload"
          :show-file-list="false"
          multiple
          accept=".jpg,.jpeg,.png"
        >
          <el-button size="small" class="btn-outline">批量上传照片填充</el-button>
        </el-upload>
        <el-button type="primary" size="small" class="btn-ghost" @click="submit" :loading="submitting">提交作业</el-button>
      </div>
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAssignmentPaper } from '../../../services/modules/assignments'
import { submitAssignment, uploadSubmissionImage, ocrImage, getSubmissionResults } from '../../../services/modules/submissions'
import { ElMessage } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'

const route = useRoute()
const router = useRouter()
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

async function batchOcrUpload(options: any) {
  try {
    const r = await ocrImage(options.file as File)
    const text = String(r.text || '').trim()
    const emptyIds = Object.keys(answers.value).map(Number).filter(id => !(answers.value[id] || '').trim())
    if (emptyIds.length === 0) {
      ElMessage.info('没有空白题目可填充，已忽略')
      return
    }
    // 按顺序填充第一个空白题
    const targetId = emptyIds[0]!
    answers.value[targetId] = text
    computeAnswered()
    ElMessage.success('已填充到首个空白题目')
  } catch (e) {
    ElMessage.error('OCR 处理失败')
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
      student_id: 1, // Hardcoded
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
        const res = await getSubmissionResults(assignmentId, 1)
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
</script>
