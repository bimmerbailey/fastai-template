<script setup lang="ts">
import type { MessageRead } from "../types/chat.types"

defineProps<{
  messages: MessageRead[]
}>()
</script>

<template>
  <div class="flex-1 space-y-4 overflow-y-auto p-4">
    <div
      v-for="msg in messages"
      :key="msg.id"
      class="flex"
      :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <div
        class="max-w-[75%] rounded-lg px-4 py-2 text-sm"
        :class="
          msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
        "
      >
        {{ msg.content_text }}
      </div>
    </div>
    <p v-if="messages.length === 0" class="text-center text-sm text-muted-foreground">
      Send a message to start the conversation
    </p>
  </div>
</template>
