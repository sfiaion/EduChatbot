<template>
  <div class="teacher-dashboard">
    <div v-if="loading" class="loading">加载统计数据中...</div>
    <div v-else-if="!stats" class="empty">暂无数据</div>
    <div v-else>
      <!-- Overview Cards -->
      <div class="stats-overview">
        <el-card class="stat-card">
            <template #header>平均正确率</template>
            <div class="stat-value">{{ stats.overall.average_accuracy }}%</div>
            <div class="stat-desc">共 {{ stats.overall.total_submissions }} 份提交</div>
        </el-card>
        <el-card class="stat-card">
            <template #header>参与学生</template>
            <div class="stat-value">{{ stats.overall.student_count }}</div>
            <div class="stat-desc">人</div>
        </el-card>
        <el-card class="stat-card" v-if="stats.weak_points.length > 0">
            <template #header>主要薄弱点</template>
            <div class="weak-tags">
                <el-tag v-for="wp in stats.weak_points" :key="wp.tag" type="danger" effect="plain">
                    {{ wp.tag }} ({{ wp.count }})
                </el-tag>
            </div>
        </el-card>
      </div>

      <!-- Charts -->
      <div class="charts-row">
          <el-card class="chart-card">
              <template #header>题目正确率分布</template>
              <div ref="questionChartRef" style="height: 300px;"></div>
          </el-card>
          <el-card class="chart-card">
              <template #header>错误类型分布</template>
              <div ref="errorChartRef" style="height: 300px;"></div>
          </el-card>
      </div>

      <!-- Student List -->
      <el-card class="student-list-card">
          <template #header>
              <div class="card-header">
                  <span>学生作答详情</span>
              </div>
          </template>
          <el-table :data="stats.students" stripe style="width: 100%">
              <el-table-column prop="name" label="姓名" width="180" />
              <el-table-column label="正确率" width="250">
                  <template #default="scope">
                      <el-progress :percentage="scope.row.accuracy" :status="getProgressStatus(scope.row.accuracy)" />
                  </template>
              </el-table-column>
              <el-table-column label="正确/总数">
                  <template #default="scope">
                      {{ scope.row.correct }} / {{ scope.row.total }}
                  </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                  <template #default="scope">
                      <el-button size="small" type="primary" @click="viewStudent(scope.row.id)">
                          查看详情
                      </el-button>
                  </template>
              </el-table-column>
          </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getAssignmentStats } from '../../../services/modules/submissions'
import { ElMessage } from 'element-plus'

const props = defineProps<{
    assignmentId: number
}>()

const router = useRouter()
const loading = ref(false)
const stats = ref<any>(null)
const questionChartRef = ref<HTMLElement>()
const errorChartRef = ref<HTMLElement>()

let qChart: echarts.ECharts | null = null
let eChart: echarts.ECharts | null = null

onMounted(() => {
    fetchStats()
})

async function fetchStats() {
    loading.value = true
    try {
        stats.value = await getAssignmentStats(props.assignmentId)
        setTimeout(() => initCharts(), 100)
    } catch (e) {
        ElMessage.error('获取统计数据失败')
    } finally {
        loading.value = false
    }
}

function initCharts() {
    if (!stats.value) return

    // Question Chart
    if (questionChartRef.value) {
        qChart = echarts.init(questionChartRef.value)
        const qData = stats.value.questions
        qChart.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: qData.map((q: any) => `Q${q.id}`) },
            yAxis: { type: 'value', max: 100 },
            series: [{
                data: qData.map((q: any) => q.correct_rate),
                type: 'bar',
                itemStyle: {
                    color: (params: any) => {
                        const val = params.value as number
                        return val < 60 ? '#f56c6c' : (val < 85 ? '#e6a23c' : '#67c23a')
                    }
                },
                label: { show: true, position: 'top', formatter: '{c}%' }
            }]
        })
    }

    // Error Chart
    if (errorChartRef.value) {
        eChart = echarts.init(errorChartRef.value)
        eChart.setOption({
            tooltip: { trigger: 'item' },
            legend: { orient: 'vertical', left: 'left' },
            series: [{
                type: 'pie',
                radius: '50%',
                data: stats.value.error_distribution,
                emphasis: {
                    itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
                }
            }]
        })
    }
}

function getProgressStatus(percentage: number) {
    if (percentage >= 90) return 'success'
    if (percentage >= 60) return 'warning'
    return 'exception'
}

function viewStudent(studentId: number) {
    router.push(`/results/${props.assignmentId}/student/${studentId}`)
}

// Handle resize
window.addEventListener('resize', () => {
    qChart?.resize()
    eChart?.resize()
})
</script>

<style scoped>
.teacher-dashboard { padding: 20px; }
.stats-overview { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; margin: 10px 0; }
.stat-desc { color: #909399; font-size: 14px; }
.charts-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 20px; }
.weak-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.student-list-card { margin-top: 20px; }
</style>
