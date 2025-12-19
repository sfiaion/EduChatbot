<template>
  <!-- Full Screen for Login/Register -->
  <div v-if="isAuthPage" style="height:100vh; width:100vw; overflow:hidden;">
    <router-view />
  </div>

  <!-- Main Layout for App -->
  <el-container v-else style="height:100vh;">
    <el-aside :width="asideWidth" class="sidebar-anim sidebar-gradient" style="border-right:1px solid var(--border-soft); position:relative;">
      <div style="height:56px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:26px;">
        <span v-if="!collapsed" class="text-gradient">EduChatbot</span>
        <span v-else class="text-gradient">EC</span>
        <el-button circle size="small" class="ripple" @click="toggleCollapse" style="position:absolute; right:8px;">
          <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
        </el-button>
      </div>
      <el-menu :collapse="collapsed" :default-active="active" router class="side-nav">
        <!-- Common -->
        <el-menu-item index="/chat"><el-icon><ChatLineRound /></el-icon><span>学习助手</span></el-menu-item>
        
        <!-- Teacher / Admin -->
        <el-menu-item v-if="authStore.role === 'teacher' || authStore.role === 'admin'" index="/problems"><el-icon><Document /></el-icon><span>题库管理</span></el-menu-item>
        <el-menu-item v-if="authStore.role === 'teacher' || authStore.role === 'admin' || authStore.role === 'student'" index="/results"><el-icon><DataAnalysis /></el-icon><span>批改结果</span></el-menu-item>
        <el-menu-item v-if="authStore.role === 'teacher' || authStore.role === 'admin'" index="/knowledge"><el-icon><DataAnalysis /></el-icon><span>数据分析</span></el-menu-item>

        <!-- Student / Admin -->
        <el-menu-item v-if="authStore.role === 'student' || authStore.role === 'admin'" index="/student-assignments"><el-icon><Edit /></el-icon><span>学生作业</span></el-menu-item>
        <el-menu-item v-if="authStore.role === 'student' || authStore.role === 'admin'" index="/practice"><el-icon><Reading /></el-icon><span>练习</span></el-menu-item>
        <el-menu-item v-if="authStore.role === 'student' || authStore.role === 'admin'" index="/wrongbook"><el-icon><Memo /></el-icon><span>错题本</span></el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #eee; height:56px;">
        <div style="display:flex; align-items:center; gap:8px;">
          <el-breadcrumb separator="/" :class="['breadcrumb-strong', gradClass, weightClass]">
            <el-breadcrumb-item v-for="(b,i) in crumbs" :key="i">{{ b }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="display:flex; gap:8px;">
            <el-button v-if="authStore.role === 'teacher' || authStore.role === 'admin'" size="small" type="primary" class="ripple" @click="go('/problems')">新建作业</el-button>
            <el-button v-if="authStore.role === 'teacher' || authStore.role === 'admin'" size="small" class="ripple btn-outline" @click="go('/knowledge')">进入分析</el-button>
          </div>
          <el-badge :value="3" class="item"><el-button circle><el-icon><Bell /></el-icon></el-button></el-badge>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-profile-header">
               <el-avatar :size="32" :src="authStore.user?.avatar || undefined" style="background:#4f46e5; cursor:pointer;">
                  {{ (authStore.user?.nickname || authStore.user?.username || 'U')[0].toUpperCase() }}
               </el-avatar>
               <span class="header-username">{{ authStore.user?.nickname || authStore.user?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="logout" divided style="color: #ef4444;">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="app-gradient-bg" :style="{ '--aside-w': asideWidth, '--accent-color': accentColor }">
        <transition name="fade"><router-view /></transition>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatLineRound, Document, Edit, Reading, Memo, DataAnalysis, Bell, Fold, Expand, User } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const collapsed = ref(false)
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isAuthPage = computed(() => ['/login', '/register'].includes(route.path))
const roleDisplay = computed(() => {
  const r = authStore.role
  if (r === 'admin') return '管理员'
  if (r === 'teacher') return '教师'
  if (r === 'student') return '学生'
  return ''
})

const active = computed(() => route.path)
const asideWidth = computed(() => collapsed.value ? '64px' : 'clamp(200px, 22vw, 260px)')
const crumbs = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  const map: Record<string, string> = {
    chat: '学习助手',
    problems: '题库管理',
    'student-assignments': '学生作业',
    paper: '学生作业',
    results: '批改结果',
    practice: '练习',
    wrongbook: '错题本',
    knowledge: '数据分析',
    stats: '作业统计',
    profile: '个人资料'
  }
  return parts.map(p => map[p] || p)
})

const gradClass = computed(() => {
  const first = route.path.split('/').filter(Boolean)[0]
  const map: Record<string, string> = {
    chat: 'title-grad-blue',
    problems: 'title-grad-violet',
    paper: 'title-grad-teal',
    results: 'title-grad-teal',
    practice: 'title-grad-blue',
    wrongbook: 'title-grad-violet',
    knowledge: 'title-grad-teal',
    profile: 'title-grad-blue'
  }
  const key = first || 'chat'
  return map[key] || 'title-grad-blue'
})

const accentColor = computed(() => {
  const first = route.path.split('/').filter(Boolean)[0]
  const map: Record<string, string> = {
    chat: 'rgba(37,99,235,.08)',
    problems: 'rgba(124,58,237,.08)',
    paper: 'rgba(16,185,129,.08)',
    results: 'rgba(16,185,129,.08)',
    practice: 'rgba(37,99,235,.08)',
    wrongbook: 'rgba(124,58,237,.08)',
    knowledge: 'rgba(16,185,129,.08)'
  }
  const key = first || 'chat'
  return map[key] || 'rgba(37,99,235,.08)'
})

const weightClass = computed(() => {
  const first = route.path.split('/').filter(Boolean)[0]
  return first === 'paper' ? 'breadcrumb-normal' : ''
})

function go(path: string) { router.push(path) }
function toggleCollapse() { collapsed.value = !collapsed.value }

function handleCommand(command: string) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    authStore.logout()
  }
}
</script>

<style scoped>
.item { margin-right: 8px; }
.user-profile-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  padding: 4px 8px;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.user-profile-header:hover {
  background-color: rgba(0,0,0,0.05);
}
.header-username {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
