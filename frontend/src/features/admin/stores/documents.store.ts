import { ref } from "vue"
import { defineStore } from "pinia"
import { documentsService } from "../services/documents.service"
import type { DocumentRead, DocumentListParams } from "../types/documents.types"

export const useDocumentsStore = defineStore("adminDocuments", () => {
  const documents = ref<DocumentRead[]>([])
  const selectedDocument = ref<DocumentRead | null>(null)

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

  return {
    documents,
    selectedDocument,
    fetchDocuments,
    fetchDocument,
    removeDocument,
    reprocessDocument,
  }
})
