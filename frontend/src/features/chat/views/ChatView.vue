<script setup lang="ts">
import ConversationList from "../components/ConversationList.vue"
import ChatMessageList from "../components/ChatMessageList.vue"
import ChatInput from "../components/ChatInput.vue"
import { useChat } from "../composables/useChat"

const {
  conversations,
  activeConversation,
  messages,
  isSending,
  error,
  selectConversation,
  startNewConversation,
  sendMessage,
} = useChat()
</script>

<template>
  <div class="flex h-full gap-4">
    <div class="w-64 shrink-0 overflow-hidden rounded-lg border border-border">
      <ConversationList
        :conversations="conversations"
        :active-id="activeConversation?.id"
        @select="selectConversation"
        @create="startNewConversation()"
      />
    </div>

    <div class="flex flex-1 flex-col overflow-hidden rounded-lg border border-border">
      <p v-if="error" class="px-4 pt-2 text-sm text-destructive">{{ error }}</p>
      <ChatMessageList :messages="messages" />
      <ChatInput :disabled="isSending" @send="sendMessage" />
    </div>
  </div>
</template>
