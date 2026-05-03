import type { RouteRecordRaw } from "vue-router"

export const adminRoutes: RouteRecordRaw[] = [
  {
    path: "admin/users",
    name: "admin-users",
    component: () => import("./views/AdminUsersView.vue"),
    meta: { requiresAdmin: true },
  },
  {
    path: "admin/documents",
    name: "admin-documents",
    component: () => import("./views/AdminDocumentsView.vue"),
    meta: { requiresAdmin: true },
  },
  {
    path: "admin/documents/:id",
    name: "admin-document-detail",
    component: () => import("./views/AdminDocumentDetailView.vue"),
    meta: { requiresAdmin: true },
  },
  {
    path: "admin/embeddings",
    name: "admin-embeddings",
    component: () => import("./views/AdminEmbeddingsView.vue"),
    meta: { requiresAdmin: true },
  },
]
