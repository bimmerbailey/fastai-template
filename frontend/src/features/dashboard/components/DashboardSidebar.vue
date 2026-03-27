<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import {
  LayoutDashboard,
  Package,
  MessageSquare,
  Users,
  PanelLeftClose,
  PanelLeft,
} from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/features/auth/stores/auth.store"
import { useDashboard } from "../composables/useDashboard"

const route = useRoute()
const authStore = useAuthStore()
const { sidebarCollapsed, toggleSidebar } = useDashboard()

const navItems = computed(() => {
  const items = [
    { label: "Dashboard", to: "dashboard", icon: LayoutDashboard },
    { label: "Items", to: "items", icon: Package },
    { label: "Chat", to: "chat", icon: MessageSquare },
  ]

  if (authStore.user?.is_admin) {
    items.push({ label: "Users", to: "admin-users", icon: Users })
  }

  return items
})

function isActive(routeName: string): boolean {
  return route.name === routeName
}
</script>

<template>
  <aside
    class="flex h-full flex-col border-r border-border bg-card transition-all"
    :class="sidebarCollapsed ? 'w-16' : 'w-60'"
  >
    <div class="flex items-center justify-between p-4">
      <span v-if="!sidebarCollapsed" class="text-lg font-semibold text-foreground">FastAI</span>
      <Button variant="ghost" size="icon-sm" @click="toggleSidebar">
        <PanelLeftClose v-if="!sidebarCollapsed" class="h-4 w-4" />
        <PanelLeft v-else class="h-4 w-4" />
      </Button>
    </div>

    <nav class="flex-1 space-y-1 px-2">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="{ name: item.to }"
        class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors"
        :class="
          isActive(item.to)
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        "
      >
        <component :is="item.icon" class="h-4 w-4 shrink-0" />
        <span v-if="!sidebarCollapsed">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
