import { ref } from "vue"
import { defineStore } from "pinia"
import { documentsService } from "../services/documents.service"
import type {
  DocumentRead,
  DocumentListParams,
  DocumentUpdate,
  EmbeddingChunkRead,
} from "../types/documents.types"

export const useDocumentsStore = defineStore("adminDocuments", () => {
  const documents = ref<DocumentRead[]>([])
  const selectedDocument = ref<DocumentRead | null>(null)
  const chunks = ref<EmbeddingChunkRead[]>([])

  async function fetchDocuments(params?: DocumentListParams): Promise<void> {
    documents.value = await documentsService.getDocuments(params)
  }

  async function fetchDocument(id: string): Promise<void> {
    selectedDocument.value = await documentsService.getDocument(id)
  }

  async function removeDocument(id: string): Promise<void> {
    await documentsService.deleteDocument(id)
    documents.value = documents.value.filter((d) => d.id !== id)
    if (selectedDocument.value?.id === id) selectedDocument.value = null
  }

  async function reprocessDocument(id: string): Promise<DocumentRead> {
    const doc = await documentsService.reprocessDocument(id)
    const index = documents.value.findIndex((d) => d.id === id)
    if (index !== -1) documents.value[index] = doc
    if (selectedDocument.value?.id === id) selectedDocument.value = doc
    return doc
  }

  async function updateDocument(id: string, payload: DocumentUpdate): Promise<DocumentRead> {
    const doc = await documentsService.updateDocument(id, payload)
    const index = documents.value.findIndex((d) => d.id === id)
    if (index !== -1) documents.value[index] = doc
    if (selectedDocument.value?.id === id) selectedDocument.value = doc
    return doc
  }

  async function fetchDocumentChunks(id: string): Promise<void> {
    chunks.value = await documentsService.getDocumentChunks(id)
  }

  async function uploadDocument(file: File, filename?: string): Promise<DocumentRead> {
    const doc = await documentsService.uploadDocument(file, filename)
    documents.value.unshift(doc)
    return doc
  }

  return {
    documents,
    selectedDocument,
    chunks,
    fetchDocuments,
    fetchDocument,
    removeDocument,
    reprocessDocument,
    updateDocument,
    fetchDocumentChunks,
    uploadDocument,
  }
})
