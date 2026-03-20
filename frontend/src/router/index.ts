import { createRouter, createWebHistory } from 'vue-router'
import { authRoutes } from '@/features/auth/routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...authRoutes,
    {
      path: '/',
      redirect: '/login',
    },
  ],
})

export default router
