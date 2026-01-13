import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/features/auth/views/LoginView.vue') },
    { path: '/register', component: () => import('@/features/auth/views/RegisterView.vue') },
    { path: '/chat', component: () => import('@/features/chat/views/ChatView.vue') },
    { path: '/knowledge', component: () => import('@/features/knowledge/views/KnowledgeGraph.vue') },
    { path: '/problems', component: () => import('@/features/problems/views/ProblemsView.vue') },
    { path: '/student-assignments', component: () => import('@/features/assignments/views/StudentAssignmentsView.vue') },
    { path: '/paper/:id', component: () => import('@/features/submissions/views/PaperView.vue') },
    { path: '/results', component: () => import('@/features/submissions/views/ResultsListView.vue') },
    { path: '/results/:assignmentId', component: () => import('@/features/submissions/views/ResultView.vue') },
    { path: '/results/:assignmentId/student/:studentId', component: () => import('@/features/submissions/views/ResultView.vue') },
    { path: '/stats/:id', component: () => import('@/features/assignments/views/StatsView.vue') },
    { path: '/ocr', component: () => import('@/features/submissions/views/OCRView.vue') },
    { path: '/practice', component: () => import('@/features/practice/views/PracticeView.vue') },
    { path: '/wrongbook', component: () => import('@/features/wrongbook/views/WrongBook.vue') },
    { path: '/notifications', component: () => import('@/features/notifications/views/NotificationsView.vue') },
    { path: '/classes', component: () => import('@/features/classes/views/ClassManagementView.vue') },
    { path: '/profile', component: () => import('@/features/profile/views/ProfileView.vue') },
    { path: '/', redirect: '/classes' }
  ]
})

router.beforeEach((to, _from, next) => {
  const publicPages = ['/login', '/register'];
  const authRequired = !publicPages.includes(to.path);
  const loggedIn = localStorage.getItem('token');

  if (authRequired && !loggedIn) {
    return next('/login');
  }

  function getRole(): string | null {
    const t = localStorage.getItem('token') || '';
    if (!t || !t.includes('.')) return null;
    try {
      const base64Url = t.split('.')[1];
      if (!base64Url) return null;
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload).role || null;
    } catch { return null; }
  }
  const role = getRole();
  if (to.path === '/') {
    if (role === 'teacher' || role === 'admin') return next('/problems');
    if (role === 'student') return next('/student-assignments');
    return next('/classes');
  }

  next();
})

export default router
