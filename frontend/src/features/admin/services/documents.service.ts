import { adminApi } from "@/lib/api"
import type {
  DocumentRead,
  DocumentListParams,
  DocumentUpdate,
  EmbeddingChunkRead,
} from "../types/documents.types"

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

  async updateDocument(id: string, payload: DocumentUpdate): Promise<DocumentRead> {
    return adminApi<DocumentRead>(`/documents/${id}`, { method: "PATCH", body: payload })
  },

  async getDocumentChunks(id: string): Promise<EmbeddingChunkRead[]> {
    return adminApi<EmbeddingChunkRead[]>(`/documents/${id}/chunks`)
  },

  async uploadDocument(file: File, filename?: string): Promise<DocumentRead> {
    const formData = new FormData()
    formData.append("file", file)
    if (filename) formData.append("filename", filename)
    return adminApi<DocumentRead>("/documents", { method: "POST", body: formData })
  },
}
