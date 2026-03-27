<script setup lang="ts">
import { Plus } from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import type { ConversationRead } from "../types/chat.types"

defineProps<{
  conversations: ConversationRead[]
  activeId?: string | null
}>()

defineEmits<{
  select: [id: string]
  create: []
  delete: [id: string]
}>()
</script>

<template>
  <div class="flex h-full flex-col">
    <div class="flex items-center justify-between border-b border-border p-3">
      <span class="text-sm font-medium text-foreground">Conversations</span>
      <Button variant="ghost" size="icon-sm" @click="$emit('create')">
        <Plus class="h-4 w-4" />
      </Button>
    </div>

    <div class="flex-1 overflow-y-auto">
      <button
        v-for="conv in conversations"
        :key="conv.id"
        class="w-full px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
        :class="activeId === conv.id ? 'bg-primary/10 text-primary' : 'text-foreground'"
        @click="$emit('select', conv.id)"
      >
        {{ conv.title ?? "Untitled" }}
      </button>
      <p v-if="conversations.length === 0" class="p-3 text-center text-sm text-muted-foreground">
        No conversations yet
      </p>
    </div>
  </div>
</template>
