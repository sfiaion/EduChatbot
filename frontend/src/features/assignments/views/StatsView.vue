<template>
  <div style="padding:20px;">
    <div class="card-soft" style="padding:16px; margin-bottom:16px; display:flex; justify-content:space-between; align-items:center;">
      <h2 class="title-gradient-teal" style="margin:0;">Assignment Stats</h2>
      <div style="display:flex; gap:8px;">
        <el-button size="small" class="ripple">Refresh</el-button>
        <el-button size="small" type="primary" class="ripple">Export</el-button>
      </div>
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="stats" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:20px;">
      <el-card class="card-soft" shadow="hover">
        <template #header>Total Questions</template>
        <div style="font-size:24px; font-weight:bold; color:#409eff;">{{ stats.total_questions }}</div>
      </el-card>
      <el-card class="card-soft" shadow="hover">
        <template #header>Students Submitted</template>
        <div style="font-size:24px; font-weight:bold; color:#67c23a;">{{ stats.total_students }}</div>
      </el-card>
      <el-card class="card-soft" shadow="hover">
        <template #header>Submission Rate</template>
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
    ElMessage.error('Failed to load stats')
  } finally {
    loading.value = false
  }
})
</script>
