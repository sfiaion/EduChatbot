<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-indigo" style="margin:0;">班级管理</h2>
      </div>
      <div class="toolbar-right" style="display:flex; gap:8px;">
        <el-button size="small" class="btn-outline" @click="refresh">刷新</el-button>
      </div>
    </div>
    <div class="grid" v-if="!isStudent">
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">成员</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="m in members" :key="`${m.role}-${m.id}`" class="panel-item">
              <span>{{ m.role==='teacher' ? '教师' : '学生' }}：{{ m.name }}</span>
              <el-tag v-if="m.student_number" size="small" type="info">{{ m.student_number }}</el-tag>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">处理申请</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="r in requests" :key="r.id" class="panel-item" style="justify-content:space-between;">
              <div>
                <div style="font-weight:600;">{{ r.student_name }}</div>
                <div style="font-size:12px; color:#6b7280;">申请加入：{{ r.class_name }}</div>
              </div>
              <div style="display:flex; gap:6px;">
                <el-button size="small" type="primary" @click="accept(r)">同意</el-button>
                <el-button size="small" @click="reject(r)">拒绝</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">邀请学生</div>
        <div style="display:flex; gap:8px; margin-top:8px;">
          <el-input v-model="inviteName" placeholder="学生用户名" style="max-width:240px;" />
          <el-button type="primary" @click="invite">发送邀请</el-button>
        </div>
      </div>
    </div>
    <div class="grid" v-else>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">成员</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="m in members" :key="`${m.role}-${m.id}`" class="panel-item">
              <span>{{ m.role==='teacher' ? '教师' : '学生' }}：{{ m.name }}</span>
              <el-tag v-if="m.student_number" size="small" type="info">{{ m.student_number }}</el-tag>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">我的邀请</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="r in requests" :key="r.id" class="panel-item" style="justify-content:space-between;">
              <div>
                <div style="font-weight:600;">来自：{{ r.class_name }}</div>
              </div>
              <div style="display:flex; gap:6px;">
                <el-button size="small" type="primary" @click="accept(r)">接受</el-button>
                <el-button size="small" @click="reject(r)">拒绝</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">申请加入班级</div>
        <div style="display:flex; gap:8px; margin-top:8px;">
          <el-input v-model="applyClass" placeholder="班级名称" style="max-width:240px;" />
          <el-button type="primary" @click="apply">发送申请</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listMembers, listRequests, handleRequest, inviteStudent, applyJoin, type ClassMember, type ClassRequest } from '../../../services/modules/classes'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const isStudent = computed(() => auth.role === 'student')
const members = ref<ClassMember[]>([])
const requests = ref<ClassRequest[]>([])
const inviteName = ref('')
const applyClass = ref('')

async function refresh() {
  try {
    members.value = await listMembers()
    requests.value = await listRequests()
  } catch {
    ElMessage.error('加载失败')
  }
}

async function accept(r: ClassRequest) {
  try {
    await handleRequest(r.id, 'accept')
    await refresh()
  } catch {}
}

async function reject(r: ClassRequest) {
  try {
    await handleRequest(r.id, 'reject')
    await refresh()
  } catch {}
}

async function invite() {
  if (!inviteName.value) return
  try {
    await inviteStudent(inviteName.value)
    ElMessage.success('邀请已发送')
  } catch {
    ElMessage.error('邀请失败')
  }
}

async function apply() {
  if (!applyClass.value) return
  try {
    await applyJoin(applyClass.value)
    ElMessage.success('申请已发送')
  } catch {
    ElMessage.error('申请失败')
  }
}

onMounted(refresh)
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 16px;
}
.panel-title {
  font-weight: 600;
  color: #374151;
}
.panel-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.panel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
}
</style>

