<script setup lang="ts">
import type { UserRead } from "../types/admin.types"

defineProps<{
  users: UserRead[]
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
}>()
</script>

<template>
  <div class="rounded-md border border-border">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border bg-muted/50">
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Email</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
          <th class="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
          <th class="px-4 py-3 text-center font-medium text-muted-foreground">Admin</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="user in users"
          :key="user.id"
          class="border-b border-border last:border-0 hover:bg-muted/30 cursor-pointer"
          @click="$emit('select', user.id)"
        >
          <td class="px-4 py-3 font-medium text-foreground">{{ user.email }}</td>
          <td class="px-4 py-3 text-muted-foreground">
            {{ [user.first_name, user.last_name].filter(Boolean).join(" ") || "—" }}
          </td>
          <td class="px-4 py-3">
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="{
                'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400':
                  user.status === 'active',
                'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400':
                  user.status === 'pending_verification',
                'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400':
                  user.status === 'suspended' || user.status === 'locked',
              }"
            >
              {{ user.status }}
            </span>
          </td>
          <td class="px-4 py-3 text-center">{{ user.is_admin ? "Yes" : "No" }}</td>
          <td class="px-4 py-3 text-right">
            <!-- TODO: action buttons -->
          </td>
        </tr>
        <tr v-if="users.length === 0">
          <td colspan="5" class="px-4 py-8 text-center text-muted-foreground">No users found</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
