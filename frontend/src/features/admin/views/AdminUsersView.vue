<script setup lang="ts">
import { onMounted } from "vue"
import { useAdminUsers } from "../composables/useAdminUsers"
import AdminUsersTable from "../components/AdminUsersTable.vue"

const { users, isLoading, error, fetchUsers } = useAdminUsers()

onMounted(() => fetchUsers())
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold text-foreground">User Management</h1>
    <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    <p v-if="isLoading" class="text-sm text-muted-foreground">Loading...</p>
    <AdminUsersTable v-else :users="users" />
  </div>
</template>
