<template>
  <div style="padding:20px;">
    <div class="card-soft" style="padding:16px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
      <h2 class="title-gradient-teal" style="margin:0;">作业统计</h2>
      <div style="display:flex; gap:8px;">
        <el-button size="small" class="ripple">刷新</el-button>
        <el-button size="small" type="primary" class="ripple">导出</el-button>
      </div>
    </div>
    <div v-if="loading">加载中...</div>
    <div v-else-if="stats" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:20px;">
      <el-card class="card-soft" shadow="hover">
        <template #header>题目数量</template>
        <div style="font-size:24px; font-weight:bold; color:#409eff;">{{ stats.total_questions }}</div>
      </el-card>
      <el-card class="card-soft" shadow="hover">
        <template #header>已提交人数</template>
        <div style="font-size:24px; font-weight:bold; color:#67c23a;">{{ stats.total_students }}</div>
      </el-card>
      <el-card class="card-soft" shadow="hover">
        <template #header>提交率</template>
        <div style="font-size:24px; font-weight:bold; color:#F59E0B;">{{ rate }}</div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getAssignmentStats } from '../../../services/modules/assignments'
import { ElMessage } from 'element-plus'

const route = useRoute()
const assignmentId = Number(route.params.id)
const loading = ref(false)
const stats = ref<{ total_students: number; total_questions: number } | null>(null)
const rate = computed(() => {
  if (!stats.value) return '—'
  const s = stats.value
  return s.total_questions ? ((s.total_students / s.total_questions) * 100).toFixed(0) + '%' : '—'
})

onMounted(async () => {
  if (!assignmentId) return
  loading.value = true
  try {
    stats.value = await getAssignmentStats(assignmentId)
  } catch (e) {
    ElMessage.error('加载统计失败')
  } finally {
    loading.value = false
  }
})
</script>
