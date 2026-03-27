import type { RouteRecordRaw } from "vue-router"

export const chatRoutes: RouteRecordRaw[] = [
  {
    path: "chat",
    name: "chat",
    component: () => import("./views/ChatView.vue"),
  },
]
