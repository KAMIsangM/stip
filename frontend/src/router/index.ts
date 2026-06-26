import { createRouter, createWebHistory } from 'vue-router'
import CourseCreate from '@/views/course/CourseCreate.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: CourseCreate,
      meta: { requiresAuth: true },
    },
    {
      path: '/courses/:id/play',
      name: 'course-player',
      component: () => import('@/views/course/CoursePlayer.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { requiresAuth: false },
    },
  ],
})

// Route guard: redirect unauthenticated users to login
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('sitp_access_token')

  if (to.meta.requiresAuth && !token) {
    // Redirect to login, preserve the intended destination
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if ((to.name === 'login' || to.name === 'register') && token) {
    // Redirect logged-in users to home
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
