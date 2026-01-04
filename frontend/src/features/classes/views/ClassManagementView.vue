<template>
  <div class="page-wrap">
    <div class="toolbar card-soft" style="margin-bottom:12px;">
      <div class="toolbar-left">
        <h2 class="title-gradient-indigo" style="margin:0;">Class Management</h2>
      </div>
      <div class="toolbar-right" style="display:flex; gap:8px;">
        <el-button size="small" class="btn-outline" @click="refresh">Refresh</el-button>
      </div>
    </div>
    <div class="grid" v-if="!isStudent">
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Members</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="m in members" :key="`${m.role}-${m.id}`" class="panel-item">
              <span>{{ m.role==='teacher' ? 'Teacher' : 'Student' }}: {{ m.name }}</span>
              <el-tag v-if="m.student_number" size="small" type="info">{{ m.student_number }}</el-tag>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Handle Requests</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="r in requests" :key="r.id" class="panel-item" style="justify-content:space-between;">
              <div>
                <div style="font-weight:600;">{{ r.student_name }}</div>
                <div style="font-size:12px; color:#6b7280;">Apply to join: {{ r.class_name }}</div>
              </div>
              <div style="display:flex; gap:6px;">
                <el-button size="small" type="primary" @click="accept(r)">Accept</el-button>
                <el-button size="small" @click="reject(r)">Reject</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Invite Students</div>
        <div style="display:flex; gap:8px; margin-top:8px; align-items:center;">
          <el-input v-model="inviteName" placeholder="Student Username" style="max-width:240px;" />
          <el-select v-model="selectedClassId" placeholder="Select Class" style="width: 220px;">
            <el-option v-for="c in teacherClasses" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-button type="primary" @click="invite">Send Invite</el-button>
        </div>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Create New Class</div>
        <div style="display:flex; gap:8px; margin-top:8px;">
          <el-input v-model="newClassName" placeholder="Class Name" style="max-width:240px;" />
          <el-button type="primary" @click="createNewClass">Create</el-button>
        </div>
      </div>
    </div>
    <div class="grid" v-else>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Members</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="m in members" :key="`${m.role}-${m.id}`" class="panel-item">
              <span>{{ m.role==='teacher' ? 'Teacher' : 'Student' }}: {{ m.name }}</span>
              <el-tag v-if="m.student_number" size="small" type="info">{{ m.student_number }}</el-tag>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">My Invitations</div>
        <el-scrollbar height="420px" style="margin-top:8px;">
          <div class="panel-list">
            <div v-for="r in requests" :key="r.id" class="panel-item" style="justify-content:space-between;">
              <div>
                <div style="font-weight:600;">From: {{ r.class_name }}</div>
              </div>
              <div style="display:flex; gap:6px;">
                <el-button size="small" type="primary" @click="accept(r)">Accept</el-button>
                <el-button size="small" @click="reject(r)">Reject</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      <div class="mac-card soft-hover" style="padding:12px;">
        <div class="panel-title">Apply to Join Class</div>
        <div style="display:flex; gap:8px; margin-top:8px;">
          <el-input v-model="applyClass" placeholder="Class Name" style="max-width:240px;" />
          <el-button type="primary" @click="apply">Submit Application</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listMembers, listRequests, handleRequest, inviteStudent, applyJoin, createClass, listTeacherClasses, type ClassMember, type ClassRequest } from '../../../services/modules/classes'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const isStudent = computed(() => auth.role === 'student')
const members = ref<ClassMember[]>([])
const requests = ref<ClassRequest[]>([])
const inviteName = ref('')
const applyClass = ref('')
const teacherClasses = ref<Array<{ id: number; name: string }>>([])
const selectedClassId = ref<number | null>(null)
const newClassName = ref('')

async function refresh() {
  try {
    members.value = await listMembers()
    requests.value = await listRequests()
    if (!isStudent.value) {
      teacherClasses.value = await listTeacherClasses()
      selectedClassId.value = teacherClasses.value.length > 0 ? teacherClasses.value[0]!.id : null
    }
  } catch {
    ElMessage.error('Load failed')
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
  if (!selectedClassId.value) {
    ElMessage.warning('Please select a class')
    return
  }
  try {
    await inviteStudent(inviteName.value, selectedClassId.value)
    ElMessage.success('Invitation sent')
  } catch {
    ElMessage.error('Invitation failed')
  }
}

async function apply() {
  if (!applyClass.value) return
  try {
    await applyJoin(applyClass.value)
    ElMessage.success('Application submitted')
  } catch {
    ElMessage.error('Application failed')
  }
}

async function createNewClass() {
  if (!newClassName.value.trim()) {
    ElMessage.warning('Please enter class name')
    return
  }
  try {
    const r = await createClass(newClassName.value.trim())
    teacherClasses.value.push({ id: r.class_id, name: r.class_name })
    selectedClassId.value = r.class_id
    newClassName.value = ''
    ElMessage.success('Class created')
  } catch {
    ElMessage.error('Create failed')
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
