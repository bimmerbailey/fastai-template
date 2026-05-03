<script setup lang="ts">
import { ref, watch } from "vue"
import { useAdminDocuments } from "../composables/useAdminDocuments"
import {
  UiDialog,
  UiDialogContent,
  UiDialogHeader,
  UiDialogTitle,
  UiDialogDescription,
  UiDialogFooter,
  UiDialogClose,
  UiButton,
  UiInput,
  UiLabel,
} from "@/components/ui"

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  "update:open": [value: boolean]
  uploaded: []
}>()

const { isLoading, uploadDocument } = useAdminDocuments()

const selectedFile = ref<File | null>(null)
const filename = ref("")

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      selectedFile.value = null
      filename.value = ""
    }
  },
)

function onFileChange(event: Event): void {
  const target = event.target as HTMLInputElement
  selectedFile.value = target.files?.[0] ?? null
}

async function onSubmit(): Promise<void> {
  if (!selectedFile.value) return
  const success = await uploadDocument(selectedFile.value, filename.value || undefined)
  if (success) {
    emit("update:open", false)
    emit("uploaded")
  }
}
</script>

<template>
  <UiDialog :open="open" @update:open="emit('update:open', $event)">
    <UiDialogContent>
      <UiDialogHeader>
        <UiDialogTitle>Upload Document</UiDialogTitle>
        <UiDialogDescription>
          Select a file to upload. Supported formats include PDF, HTML, Markdown, and plain text.
        </UiDialogDescription>
      </UiDialogHeader>
      <form class="grid gap-4" @submit.prevent="onSubmit">
        <div class="grid gap-2">
          <UiLabel for="file">File</UiLabel>
          <UiInput id="file" type="file" required @change="onFileChange" />
        </div>
        <div class="grid gap-2">
          <UiLabel for="filename">Filename (optional)</UiLabel>
          <UiInput id="filename" v-model="filename" placeholder="Override filename..." />
        </div>
        <UiDialogFooter>
          <UiDialogClose as-child>
            <UiButton variant="outline" type="button">Cancel</UiButton>
          </UiDialogClose>
          <UiButton type="submit" :disabled="!selectedFile || isLoading">
            {{ isLoading ? "Uploading..." : "Upload" }}
          </UiButton>
        </UiDialogFooter>
      </form>
    </UiDialogContent>
  </UiDialog>
</template>
