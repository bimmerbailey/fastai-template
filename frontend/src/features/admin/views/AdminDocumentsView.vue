<script setup lang="ts">
import { onMounted } from "vue"
import { useAdminDocuments } from "../composables/useAdminDocuments"
import AdminDocumentsTable from "../components/AdminDocumentsTable.vue"

const { documents, isLoading, error, fetchDocuments } = useAdminDocuments()

onMounted(() => fetchDocuments())
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-foreground">Document Management</h1>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading" class="text-sm text-muted-foreground">Loading...</p>
    <AdminDocumentsTable v-else :documents="documents" />
  </div>
</template>
