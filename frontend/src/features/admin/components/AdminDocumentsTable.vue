<script setup lang="ts">
import type { DocumentRead } from "../types/documents.types"

defineProps<{
  documents: DocumentRead[]
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
  reprocess: [id: string]
}>()

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="rounded-md border border-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border bg-muted/50">
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Filename</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Content Type</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Size</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="doc in documents"
          :key="doc.id"
          class="border-b border-border last:border-0 hover:bg-muted/30 cursor-pointer"
          @click="$emit('select', doc.id)"
        >
          <td class="px-4 py-3 font-medium text-foreground">{{ doc.filename }}</td>
          <td class="px-4 py-3 text-muted-foreground">{{ doc.content_type }}</td>
          <td class="px-4 py-3 text-right text-muted-foreground">{{ formatSize(doc.file_size) }}</td>
          <td class="px-4 py-3">
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="{
                'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400':
                  doc.embedding_status === 'complete',
                'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400':
                  doc.embedding_status === 'pending',
                'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400':
                  doc.embedding_status === 'failed',
                'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400':
                  !['complete', 'pending', 'failed'].includes(doc.embedding_status),
              }"
            >
              {{ doc.embedding_status }}
            </span>
          </td>
          <td class="px-4 py-3 text-muted-foreground">
            {{ new Date(doc.created_at).toLocaleDateString() }}
          </td>
          <td class="px-4 py-3 text-right">
            <!-- TODO: action buttons -->
          </td>
        </tr>
        <tr v-if="documents.length === 0">
          <td colspan="6" class="px-4 py-8 text-center text-muted-foreground">No documents found</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
