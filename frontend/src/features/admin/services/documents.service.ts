import { adminApi } from "@/lib/api"
import type { DocumentRead, DocumentListParams } from "../types/documents.types"

export const documentsService = {
  async getDocuments(params?: DocumentListParams): Promise<DocumentRead[]> {
    return adminApi<DocumentRead[]>("/documents", { params })
  },

  async getDocument(id: string): Promise<DocumentRead> {
    return adminApi<DocumentRead>(`/documents/${id}`)
  },

  async deleteDocument(id: string): Promise<void> {
    await adminApi(`/documents/${id}`, { method: "DELETE" })
  },

  async reprocessDocument(id: string): Promise<DocumentRead> {
    return adminApi<DocumentRead>(`/documents/${id}/reprocess`, { method: "POST" })
  },
}
