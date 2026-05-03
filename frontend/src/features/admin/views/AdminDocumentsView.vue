<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { useAdminDocuments } from "../composables/useAdminDocuments"
import AdminDocumentsTable from "../components/AdminDocumentsTable.vue"
import AdminDocumentUploadDialog from "../components/AdminDocumentUploadDialog.vue"
import {
  UiButton,
  UiDialog,
  UiDialogContent,
  UiDialogHeader,
  UiDialogTitle,
  UiDialogDescription,
  UiDialogFooter,
  UiDialogClose,
} from "@/components/ui"
import { Upload } from "lucide-vue-next"

const router = useRouter()
const { documents, isLoading, error, fetchDocuments, removeDocument, reprocessDocument } =
  useAdminDocuments()

function handleSelect(id: string): void {
  router.push({ name: "admin-document-detail", params: { id } })
}

const showUploadDialog = ref(false)
const showDeleteDialog = ref(false)
const deleteTargetId = ref<string | null>(null)
const deleteTargetName = ref("")

function confirmDelete(id: string): void {
  const doc = documents.value.find((d) => d.id === id)
  deleteTargetName.value = doc?.filename ?? "this document"
  deleteTargetId.value = id
  showDeleteDialog.value = true
}

async function executeDelete(): Promise<void> {
  if (!deleteTargetId.value) return
  await removeDocument(deleteTargetId.value)
  showDeleteDialog.value = false
  deleteTargetId.value = null
}

async function handleReprocess(id: string): Promise<void> {
  await reprocessDocument(id)
}

onMounted(() => fetchDocuments())
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold text-foreground">Document Management</h1>
      <UiButton @click="showUploadDialog = true">
        <Upload class="h-4 w-4" />
        Upload Document
      </UiButton>
    </div>

    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading" class="text-sm text-muted-foreground">Loading...</p>

    <AdminDocumentsTable
      v-else
      :documents="documents"
      @select="handleSelect"
      @delete="confirmDelete"
      @reprocess="handleReprocess"
    />

    <AdminDocumentUploadDialog v-model:open="showUploadDialog" />

    <UiDialog v-model:open="showDeleteDialog">
      <UiDialogContent>
        <UiDialogHeader>
          <UiDialogTitle>Delete Document</UiDialogTitle>
          <UiDialogDescription>
            Are you sure you want to delete "{{ deleteTargetName }}"? This will permanently remove
            the document, its stored file, and all embeddings.
          </UiDialogDescription>
        </UiDialogHeader>
        <UiDialogFooter>
          <UiDialogClose as-child>
            <UiButton variant="outline">Cancel</UiButton>
          </UiDialogClose>
          <UiButton variant="destructive" :disabled="isLoading" @click="executeDelete">
            {{ isLoading ? "Deleting..." : "Delete" }}
          </UiButton>
        </UiDialogFooter>
      </UiDialogContent>
    </UiDialog>
  </div>
</template>
