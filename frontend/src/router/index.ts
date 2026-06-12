import { createRouter, createWebHistory } from 'vue-router'
import CourseCreate from '@/views/course/CourseCreate.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: CourseCreate },
    {
      path: '/courses/:id/play',
      name: 'course-player',
      component: () => import('@/views/course/CoursePlayer.vue'),
    },
  ],
})

export default router
