<template>
  <div style="padding:20px; max-width:900px; margin:0 auto;">
    <div class="card-soft" style="padding:16px; display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <h2 class="title-gradient-blue" style="margin:0;">学生作业</h2>
      <div style="color:#6b7280;">共 {{ questions.length }} 题</div>
    </div>
    <div v-if="loading">加载中...</div>
    <div v-else>
      <div v-for="(q, idx) in questions" :key="q.id" class="card-soft" style="margin-bottom:24px; padding:16px;">
        <div style="margin-bottom:12px; font-weight:bold;">第 {{ idx + 1 }} 题</div>
        <div style="margin-bottom:12px; white-space:pre-wrap;">
             <LatexText :content="q.question" />
        </div>
        
        <div style="margin-bottom:12px;">
            <el-radio-group v-model="inputMethods[q.id]">
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
                :http-request="(opts) => handleImageUpload(opts, q.id)"
                :show-file-list="false"
                accept=".jpg,.jpeg,.png"
            >
                <el-button type="primary">选择图片</el-button>
            </el-upload>
            <div v-if="imagePreviews[q.id]" style="margin-top:10px;">
                <img :src="imagePreviews[q.id]" style="max-width:200px; border:1px solid #ddd; padding:4px;" />
                <div style="font-size:12px; color:#666;">已上传</div>
            </div>
        </div>
      </div>
      <div style="position:fixed; right:24px; bottom:24px;">
        <el-button type="primary" size="large" class="ripple" @click="submit" :loading="submitting">提交作业</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAssignmentPaper } from '../../../services/modules/assignments'
import { submitAssignment, uploadSubmissionImage } from '../../../services/modules/submissions'
import { ElMessage } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'

const route = useRoute()
const router = useRouter()
const assignmentId = Number(route.params.id)

const loading = ref(false)
const submitting = ref(false)
const questions = ref<{id: number; question: string}[]>([])
const answers = ref<Record<number, string>>({})
const inputMethods = ref<Record<number, 'text' | 'image'>>({})
const imagePreviews = ref<Record<number, string>>({})

onMounted(async () => {
  if (!assignmentId) return
  loading.value = true
  try {
    questions.value = await getAssignmentPaper(assignmentId)
    questions.value.forEach(q => {
      answers.value[q.id] = ''
      inputMethods.value[q.id] = 'text'
    })
  } catch (e) {
    ElMessage.error('加载作业失败')
  } finally {
    loading.value = false
  }
})

async function handleImageUpload(options: any, qid: number) {
    try {
        const res = await uploadSubmissionImage(options.file)
        // Store a special marker for image path
        answers.value[qid] = `[IMAGE]${res.path}`
        imagePreviews.value[qid] = `${import.meta.env.VITE_API_BASE_URL || ''}${res.url}`
        ElMessage.success('图片上传成功')
    } catch(e) {
        ElMessage.error('上传失败')
    }
}

async function submit() {
  submitting.value = true
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

    // 现实友好：轮询结果到达后再跳转（最多等待 10 秒）
    const start = Date.now()
    const poll = async () => {
      try {
        const res = await getSubmissionResults(assignmentId, 1)
        if (Array.isArray(res) && res.length > 0) {
          router.push(`/results/${assignmentId}`)
          return
        }
      } catch (_) {}
      if (Date.now() - start < 10000) {
        setTimeout(poll, 800)
      } else {
        // 超时仍然跳转，页面会自己请求并显示加载失败提示
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
