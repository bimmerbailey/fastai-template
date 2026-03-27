import type { RouteRecordRaw } from "vue-router"

export const itemRoutes: RouteRecordRaw[] = [
  {
    path: "items",
    name: "items",
    component: () => import("./views/ItemsView.vue"),
  },
  {
    path: "items/:itemId",
    name: "item-detail",
    component: () => import("./views/ItemDetailView.vue"),
    props: true,
  },
]
