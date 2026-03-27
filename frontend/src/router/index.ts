import { createRouter, createWebHistory } from "vue-router"
import { authRoutes } from "@/features/auth/routes"
import { itemRoutes } from "@/features/items/routes"
import { chatRoutes } from "@/features/chat/routes"
import { adminRoutes } from "@/features/admin/routes"

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
        ...itemRoutes,
        ...chatRoutes,
        ...adminRoutes,
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem("auth_token")

  if (to.matched.some((r) => r.meta.requiresAuth) && !token) {
    return { name: "login" }
  }

  if (to.name === "login" && token) {
    return { name: "dashboard" }
  }
})

export default router
