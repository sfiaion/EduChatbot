import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/chat', component: () => import('@/features/chat/views/ChatView.vue') },
    { path: '/knowledge', component: () => import('@/features/knowledge/views/KnowledgeGraph.vue') },
    { path: '/problems', component: () => import('@/features/problems/views/ProblemsView.vue') },
    { path: '/paper/:id', component: () => import('@/features/submissions/views/PaperView.vue') },
    { path: '/results/:assignmentId', component: () => import('@/features/submissions/views/ResultView.vue') },
    { path: '/stats/:id', component: () => import('@/features/assignments/views/StatsView.vue') },
    { path: '/ocr', component: () => import('@/features/submissions/views/OCRView.vue') },
    { path: '/practice', component: () => import('@/features/practice/views/PracticeView.vue') },
    { path: '/wrongbook', component: () => import('@/features/wrongbook/views/WrongBook.vue') },
    { path: '/', redirect: '/chat' }
  ]
})

export default router
