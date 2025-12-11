<template>
  <el-container style="height:100vh;">
    <el-aside :width="asideWidth" class="sidebar-anim" style="border-right:1px solid #eee; position:relative;">
      <div style="height:56px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:20px;">
        <span v-if="!collapsed" class="text-gradient">EduChatbot</span>
        <span v-else class="text-gradient">EC</span>
        <el-button circle size="small" class="ripple" @click="toggleCollapse" style="position:absolute; right:8px;">
          <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
        </el-button>
      </div>
      <el-menu :collapse="collapsed" :default-active="active" router>
        <el-menu-item index="/chat"><el-icon><ChatLineRound /></el-icon><span>对话</span></el-menu-item>
        <el-menu-item index="/problems"><el-icon><Document /></el-icon><span>题库管理</span></el-menu-item>
        <el-menu-item index="/paper/1"><el-icon><Edit /></el-icon><span>学生作业</span></el-menu-item>
        <el-menu-item index="/practice"><el-icon><Reading /></el-icon><span>练习</span></el-menu-item>
        <el-menu-item index="/wrongbook"><el-icon><Memo /></el-icon><span>错题本</span></el-menu-item>
        <el-menu-item index="/knowledge"><el-icon><DataAnalysis /></el-icon><span>数据分析</span></el-menu-item>
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
            <el-button size="small" type="primary" class="ripple" @click="go('/paper/1')">新建作业</el-button>
            <el-button size="small" class="ripple btn-ghost" @click="go('/problems')">上传题库</el-button>
            <el-button size="small" class="ripple btn-outline" @click="go('/knowledge')">进入分析</el-button>
          </div>
          <el-badge :value="3" class="item"><el-button circle><el-icon><Bell /></el-icon></el-button></el-badge>
          <el-tag type="success">角色：{{ role }}</el-tag>
        </div>
      </el-header>
      <el-main class="app-gradient-bg" :style="{ '--aside-w': asideWidth, '--accent-color': accentColor }">
        <transition name="fade"><router-view /></transition>
        <div style="position:fixed; right:20px; bottom:20px; display:flex; flex-direction:column; gap:10px;">
          <el-badge :value="1"><el-button circle type="primary" class="ripple" @click="go('/chat')"><el-icon><ChatLineRound /></el-icon></el-button></el-badge>
          <el-button circle class="ripple" @click="go('/practice')"><el-icon><Reading /></el-icon></el-button>
          <el-button circle class="ripple" @click="go('/wrongbook')"><el-icon><Memo /></el-icon></el-button>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatLineRound, Document, Edit, Reading, Memo, DataAnalysis, Bell, Fold, Expand } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const collapsed = ref(false)
const role = '管理员'
const route = useRoute()
const router = useRouter()
const active = computed(() => route.path)
const asideWidth = computed(() => collapsed.value ? '64px' : 'clamp(200px, 22vw, 260px)')
const crumbs = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  const map: Record<string, string> = {
    chat: '对话',
    problems: '题库管理',
    paper: '学生作业',
    results: '批改结果',
    practice: '练习',
    wrongbook: '错题本',
    knowledge: '数据分析',
    stats: '作业统计'
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
    knowledge: 'title-grad-teal'
  }
  return map[first] || 'title-grad-blue'
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
  return map[first] || 'rgba(37,99,235,.08)'
})

const weightClass = computed(() => {
  const first = route.path.split('/').filter(Boolean)[0]
  return first === 'paper' ? 'breadcrumb-normal' : ''
})

function go(path: string) { router.push(path) }
function toggleCollapse() { collapsed.value = !collapsed.value }
</script>

<style scoped>
.item { margin-right: 8px; }
</style>
