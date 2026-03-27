<script setup lang="ts">
import { LogOut } from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import ThemeSwitcher from "@/components/ThemeSwitcher.vue"
import { useAuthStore } from "@/features/auth/stores/auth.store"

defineProps<{
  title?: string
}>()

const authStore = useAuthStore()
</script>

<template>
  <header class="flex h-14 items-center justify-between border-b border-border bg-card px-6">
    <h2 class="text-lg font-semibold text-foreground">{{ title ?? "Dashboard" }}</h2>

    <div class="flex items-center gap-4">
      <ThemeSwitcher />
      <span v-if="authStore.user" class="text-sm text-muted-foreground">
        {{ authStore.user.email }}
      </span>
      <Button variant="ghost" size="icon-sm" title="Logout" @click="authStore.logout()">
        <LogOut class="h-4 w-4" />
      </Button>
    </div>
  </header>
</template>
