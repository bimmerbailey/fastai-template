import type { RouteRecordRaw } from "vue-router"

export const adminRoutes: RouteRecordRaw[] = [
  {
    path: "admin/users",
    name: "admin-users",
    component: () => import("./views/AdminUsersView.vue"),
    meta: { requiresAdmin: true },
  },
]
