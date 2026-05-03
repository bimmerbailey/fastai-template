<script setup lang="ts">
import type { MessageRead } from "../types/chat.types"

defineProps<{
  messages: MessageRead[]
  isThinking?: boolean
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
    <div v-if="isThinking" class="flex justify-start">
      <div class="max-w-[75%] rounded-lg bg-muted px-4 py-2 text-sm text-foreground">
        <span class="thinking-dots">
          <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
        </span>
      </div>
    </div>
    <p
      v-if="messages.length === 0 && !isThinking"
      class="text-center text-sm text-muted-foreground"
    >
      Send a message to start the conversation
    </p>
  </div>
</template>

<style scoped>
.thinking-dots .dot {
  animation: blink 1.4s infinite both;
  font-size: 1.25rem;
  line-height: 1;
}

.thinking-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.2;
  }
  40% {
    opacity: 1;
  }
}
</style>
