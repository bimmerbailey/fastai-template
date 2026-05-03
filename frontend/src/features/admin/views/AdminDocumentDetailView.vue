<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAdminDocuments } from "../composables/useAdminDocuments"
import {
  UiButton,
  UiCard,
  UiCardHeader,
  UiCardTitle,
  UiCardContent,
  UiCardAction,
  UiInput,
  UiLabel,
  UiDialog,
  UiDialogContent,
  UiDialogHeader,
  UiDialogTitle,
  UiDialogDescription,
  UiDialogFooter,
  UiDialogClose,
} from "@/components/ui"
import { ArrowLeft, RefreshCw, Trash2, Pencil, Save, X } from "lucide-vue-next"

const route = useRoute()
const router = useRouter()
const documentId = computed(() => route.params.id as string)

const {
  selectedDocument,
  chunks,
  isLoading,
  error,
  fetchDocument,
  updateDocument,
  fetchDocumentChunks,
  removeDocument,
  reprocessDocument,
} = useAdminDocuments()

const isEditing = ref(false)
const editForm = ref({ filename: "" })
const showDeleteDialog = ref(false)

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function startEdit(): void {
  if (!selectedDocument.value) return
  editForm.value.filename = selectedDocument.value.filename
  isEditing.value = true
}

function cancelEdit(): void {
  isEditing.value = false
}

async function saveEdit(): Promise<void> {
  await updateDocument(documentId.value, { filename: editForm.value.filename })
  isEditing.value = false
}

async function handleReprocess(): Promise<void> {
  await reprocessDocument(documentId.value)
}

async function executeDelete(): Promise<void> {
  await removeDocument(documentId.value)
  showDeleteDialog.value = false
  router.push({ name: "admin-documents" })
}

function goBack(): void {
  router.push({ name: "admin-documents" })
}

onMounted(async () => {
  await fetchDocument(documentId.value)
  await fetchDocumentChunks(documentId.value)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <UiButton variant="ghost" size="icon-sm" title="Back to documents" @click="goBack">
          <ArrowLeft class="h-4 w-4" />
        </UiButton>
        <h1 class="text-2xl font-semibold text-foreground">
          {{ selectedDocument?.filename ?? "Document Detail" }}
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <UiButton variant="outline" :disabled="isLoading" @click="handleReprocess">
          <RefreshCw class="h-4 w-4" />
          Reprocess
        </UiButton>
        <UiButton variant="destructive" @click="showDeleteDialog = true">
          <Trash2 class="h-4 w-4" />
          Delete
        </UiButton>
      </div>
    </div>

    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading && !selectedDocument" class="text-sm text-muted-foreground">Loading...</p>

    <!-- Metadata Card -->
    <UiCard v-if="selectedDocument">
      <UiCardHeader>
        <UiCardTitle>Document Metadata</UiCardTitle>
        <UiCardAction>
          <div class="flex items-center gap-2">
            <template v-if="!isEditing">
              <UiButton variant="outline" size="sm" @click="startEdit">
                <Pencil class="h-3.5 w-3.5" />
                Edit
              </UiButton>
            </template>
            <template v-else>
              <UiButton variant="outline" size="sm" @click="cancelEdit">
                <X class="h-3.5 w-3.5" />
                Cancel
              </UiButton>
              <UiButton size="sm" :disabled="isLoading" @click="saveEdit">
                <Save class="h-3.5 w-3.5" />
                Save
              </UiButton>
            </template>
          </div>
        </UiCardAction>
      </UiCardHeader>
      <UiCardContent>
        <dl class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Filename</dt>
            <dd v-if="!isEditing" class="mt-1 text-sm text-foreground">
              {{ selectedDocument.filename }}
            </dd>
            <div v-else class="mt-1">
              <UiLabel class="sr-only" for="edit-filename">Filename</UiLabel>
              <UiInput id="edit-filename" v-model="editForm.filename" />
            </div>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Content Type</dt>
            <dd class="mt-1 text-sm text-foreground">{{ selectedDocument.content_type }}</dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">File Size</dt>
            <dd class="mt-1 text-sm text-foreground">
              {{ formatSize(selectedDocument.file_size) }}
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Status</dt>
            <dd class="mt-1">
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                :class="{
                  'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400':
                    selectedDocument.embedding_status === 'complete',
                  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400':
                    selectedDocument.embedding_status === 'pending',
                  'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400':
                    selectedDocument.embedding_status === 'failed',
                  'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400': ![
                    'complete',
                    'pending',
                    'failed',
                  ].includes(selectedDocument.embedding_status),
                }"
              >
                {{ selectedDocument.embedding_status }}
              </span>
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Storage Path</dt>
            <dd class="mt-1 text-sm text-foreground break-all">
              {{ selectedDocument.storage_path }}
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Content Hash</dt>
            <dd class="mt-1 text-sm font-mono text-foreground break-all">
              {{ selectedDocument.content_hash }}
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Created</dt>
            <dd class="mt-1 text-sm text-foreground">
              {{ new Date(selectedDocument.created_at).toLocaleString() }}
            </dd>
          </div>
          <div>
            <dt class="text-sm font-medium text-muted-foreground">Updated</dt>
            <dd class="mt-1 text-sm text-foreground">
              {{ new Date(selectedDocument.updated_at).toLocaleString() }}
            </dd>
          </div>
        </dl>
      </UiCardContent>
    </UiCard>

    <!-- Chunks Card -->
    <UiCard v-if="selectedDocument">
      <UiCardHeader>
        <UiCardTitle>Embedding Chunks ({{ chunks.length }})</UiCardTitle>
      </UiCardHeader>
      <UiCardContent>
        <div v-if="chunks.length === 0" class="text-sm text-muted-foreground">
          No chunks found. The document may still be processing or has a non-extractable content
          type.
        </div>
        <div v-else class="space-y-3">
          <div v-for="chunk in chunks" :key="chunk.id" class="rounded-md border border-border p-3">
            <div class="mb-2 flex items-center justify-between">
              <span class="text-xs font-medium text-muted-foreground">
                Chunk #{{ chunk.chunk_index }}
              </span>
              <span class="text-xs text-muted-foreground">{{ chunk.embedding_model }}</span>
            </div>
            <p class="whitespace-pre-wrap text-sm text-foreground">{{ chunk.chunk_text }}</p>
          </div>
        </div>
      </UiCardContent>
    </UiCard>

    <!-- Delete Confirmation Dialog -->
    <UiDialog v-model:open="showDeleteDialog">
      <UiDialogContent>
        <UiDialogHeader>
          <UiDialogTitle>Delete Document</UiDialogTitle>
          <UiDialogDescription>
            Are you sure you want to delete "{{ selectedDocument?.filename }}"? This will
            permanently remove the document, its stored file, and all embeddings.
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
