<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-blue" style="margin:0;">作业列表</h2>
        <span style="margin-left:8px; color:#606266;">选择作业查看结果</span>
      </div>
    </div>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="assignments.length === 0" class="empty">暂无作业</div>
    
    <div v-else class="grid">
        <div v-for="item in assignments" :key="item.id" class="assignment-card soft-hover" @click="goDetail(item.id)">
            <div class="card-header">
                <h3>{{ item.title || `作业 #${item.id}` }}</h3>
                <el-tag size="small" :type="item.deadline ? 'warning' : 'info'">
                    {{ item.deadline ? '有截止日期' : '无截止日期' }}
                </el-tag>
            </div>
            <div class="card-body">
                <p>发布时间: {{ formatDate(item.created_at) }}</p>
                <p v-if="item.deadline">截止时间: {{ formatDate(item.deadline) }}</p>
            </div>
            <div class="card-footer">
                <el-button type="primary" size="small" @click.stop="goDetail(item.id)">
                    查看结果 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAssignmentsList } from '../../../services/modules/submissions'
import { ArrowRight } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const assignments = ref<any[]>([])

onMounted(async () => {
    loading.value = true
    try {
        assignments.value = await getAssignmentsList()
    } finally {
        loading.value = false
    }
})

function goDetail(id: number) {
    router.push(`/results/${id}`)
}

function formatDate(dateStr: string) {
    return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}
</script>

<style scoped>
.page-wrap { padding: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.assignment-card {
    background: #fff;
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.3s;
}
.assignment-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.card-header h3 { margin: 0; font-size: 18px; color: #303133; }
.card-body {
    color: #606266;
    font-size: 14px;
    margin-bottom: 16px;
}
.card-body p { margin: 4px 0; }
.card-footer { text-align: right; }
</style>
