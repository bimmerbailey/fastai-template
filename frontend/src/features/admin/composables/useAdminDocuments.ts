import { ref } from "vue"
import { storeToRefs } from "pinia"
import { useDocumentsStore } from "../stores/documents.store"
import type { DocumentListParams, DocumentUpdate } from "../types/documents.types"

export function useAdminDocuments() {
  const store = useDocumentsStore()
  const { documents, selectedDocument, chunks } = storeToRefs(store)

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDocuments(params?: DocumentListParams): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchDocuments(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch documents"
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDocument(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchDocument(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch document"
    } finally {
      isLoading.value = false
    }
  }

  async function updateDocument(id: string, payload: DocumentUpdate): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.updateDocument(id, payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to update document"
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDocumentChunks(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchDocumentChunks(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch document chunks"
    } finally {
      isLoading.value = false
    }
  }

  async function removeDocument(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.removeDocument(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to delete document"
    } finally {
      isLoading.value = false
    }
  }

  async function reprocessDocument(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.reprocessDocument(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to reprocess document"
    } finally {
      isLoading.value = false
    }
  }

  async function uploadDocument(file: File, filename?: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await store.uploadDocument(file, filename)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to upload document"
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    documents,
    selectedDocument,
    chunks,
    isLoading,
    error,
    fetchDocuments,
    fetchDocument,
    updateDocument,
    fetchDocumentChunks,
    removeDocument,
    reprocessDocument,
    uploadDocument,
  }
}
