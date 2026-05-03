import { createRouter, createWebHistory } from "vue-router"
import { authRoutes } from "@/features/auth/routes"
import { chatRoutes } from "@/features/chat/routes"
import { adminRoutes } from "@/features/admin/routes"
import { useAuthStore } from "@/features/auth/stores/auth.store"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    ...authRoutes,
    {
      path: "/",
      component: () => import("@/features/dashboard/views/DashboardView.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "dashboard",
          component: () => import("@/features/dashboard/views/DashboardHomeView.vue"),
        },
        ...chatRoutes,
        ...adminRoutes,
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (to.matched.some((r) => r.meta.requiresAuth) && !authStore.token) {
    return { name: "login" }
  }

  if (to.name === "login" && authStore.token) {
    return { name: "dashboard" }
  }

  // Lazy-load user on page refresh when token exists but user is not yet fetched
  if (authStore.token && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch {
      authStore.logout()
      return { name: "login" }
    }
  }

  if (to.matched.some((r) => r.meta.requiresAdmin) && !authStore.user?.is_admin) {
    return { name: "dashboard" }
  }
})

export default router
