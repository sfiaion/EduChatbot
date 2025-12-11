<template>
  <div style="padding:20px; max-width:800px; margin:0 auto;">
    <h2>批改结果</h2>
    <div v-if="loading">加载中...</div>
    <div v-else>
      <div v-for="(res, idx) in results" :key="idx" 
           style="margin-bottom:24px; padding:16px; border:1px solid #eee; border-radius:8px;"
           :style="{ borderColor: res.is_correct ? '#67c23a' : '#f56c6c', backgroundColor: res.is_correct ? '#f0f9eb' : '#fef0f0' }"
      >
        <div style="margin-bottom:12px; font-weight:bold;">第 {{ idx + 1 }} 题</div>
        <div style="margin-bottom:8px;">
            <strong>学生答案：</strong>
            <div v-if="res.image_path || res.student_answer.includes('[IMAGE]')">
                <img :src="getImageUrl(res)" style="max-width:300px; border:1px solid #ddd; margin: 5px 0;" />
                <div v-if="res.student_answer && !res.student_answer.startsWith('[IMAGE]')">
                    <small>OCR识别内容: {{ res.student_answer }}</small>
                </div>
            </div>
            <div v-else>{{ res.student_answer }}</div>
        </div>
        
        <div style="margin-top:12px; border-top:1px dashed #ccc; padding-top:12px;">
            <div v-if="res.is_correct" style="color:#67c23a; font-weight:bold;">
                <el-icon><Check /></el-icon> 回答正确
            </div>
            <div v-else>
                <div style="color:#f56c6c; font-weight:bold; margin-bottom:4px;">
                    <el-icon><Close /></el-icon> 回答错误
                </div>
                <div v-if="res.error_type" style="margin-bottom:4px;">
                    <el-tag type="danger" size="small">{{ formatErrorType(res.error_type) }}</el-tag>
                </div>
                <div style="margin-top:8px;">
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
                    <div style="color:#333; font-weight:500; margin-bottom:6px;">相似练习（巩固）：</div>
                <template v-if="getRecs(res.question_id).length > 0">
                  <ul style="padding-left:18px; margin:0;">
                    <li v-for="item in getRecs(res.question_id)" :key="item.id">
                          题目ID：{{ item.id }}（相似度 {{ item.score.toFixed(2) }}）
                          <el-button size="small" type="primary" style="margin-left:8px;" @click="viewQuestion(item.id)">查看题目</el-button>
                          <el-button size="small" style="margin-left:6px;" @click="addPractice(item.id)">加入练习清单</el-button>
                    </li>
                  </ul>
                </template>
                    <template v-else>
                      <div style="color:#909399; font-size:13px;">暂未找到合适的相似题目</div>
                    </template>
                </div>
            </div>
        </div>
      </div>
      
      <div style="text-align:center; margin-top:20px;">
        <el-button @click="router.push('/problems')">返回题库</el-button>
      </div>
    </div>
  </div>

  <!-- 右上角切换推荐档位 -->
  <div style="position:fixed; right:24px; top:24px; background:#fff; border:1px solid #eee; padding:8px 12px; border-radius:6px;">
    <span style="margin-right:8px; color:#606266;">推荐档位</span>
    <el-select v-model="slot" size="small" style="width:120px;" @change="fetchRecs">
      <el-option label="高相似" value="high" />
      <el-option label="中相似" value="mid" />
      <el-option label="低相似" value="low" />
    </el-select>
  </div>

  <!-- 练习清单 -->
  <div v-if="practice.list.length" style="position:fixed; left:24px; bottom:24px; background:#fff; border:1px solid #eee; padding:8px 12px; border-radius:6px; max-width:360px;">
    <div style="font-weight:600; margin-bottom:6px;">练习清单</div>
    <div style="font-size:13px; color:#606266;">共 {{ practice.list.length }} 题</div>
    <ul style="padding-left:18px; margin:6px 0 0;">
      <li v-for="id in practice.list" :key="id">题目ID：{{ id }}</li>
    </ul>
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
import { Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import LatexText from '../../../components/LatexText.vue'
import { usePracticeStore } from '../../practice/store'

const route = useRoute()
const router = useRouter()
const assignmentId = Number(route.params.assignmentId)
const studentId = Number(route.params.studentId) || 1

const loading = ref(false)
const results = ref<SubmissionResult[]>([])
const recs = ref<Record<number, RecommendationItem[]>>({})
const slot = ref<'high'|'mid'|'low'>('high')
const practice = usePracticeStore()
const preview = ref<{ id: number; question: string; answer: string } | null>(null)
const previewShowAnswer = ref(false)
const answersMap = ref<Record<number, string>>({})
const shownMap = ref<Record<number, boolean>>({})

onMounted(async () => {
  if (!assignmentId) return
  loading.value = true
  try {
    await practice.init(studentId)
    results.value = await getSubmissionResults(assignmentId, studentId)
    for (const r of results.value) {
      try {
        const q = await getProblemById(r.question_id)
        answersMap.value[r.question_id] = q.answer
      } catch {}
    }
    await fetchRecs()
  } catch (e) {
    ElMessage.error('加载结果失败')
  } finally {
    loading.value = false
  }
})

async function fetchRecs() {
  const wrongIds = results.value.filter(r => r && r.is_correct === false).map(r => r.question_id)
  for (const qid of wrongIds) {
    try {
      const r = await recommendForWrong(qid, studentId, slot.value, 5)
      recs.value[qid] = r.items || []
    } catch (_) {
      recs.value[qid] = []
    }
  }
}

function getImageUrl(res: SubmissionResult) {
    const sa = (res.student_answer || '')
    const raw = res.image_path || (sa.startsWith('[IMAGE]') ? sa.split('\n')[0].replace('[IMAGE]', '') : '')
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

function addPractice(id: number) {
  practice.add(id)
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
</script>
