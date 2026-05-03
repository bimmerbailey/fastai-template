<script setup lang="ts">
import { onMounted } from "vue"
import ConversationList from "../components/ConversationList.vue"
import ChatMessageList from "../components/ChatMessageList.vue"
import ChatInput from "../components/ChatInput.vue"
import { useChat } from "../composables/useChat"

const {
  conversations,
  activeConversation,
  messages,
  isThinking,
  isSending,
  error,
  fetchConversations,
  selectConversation,
  startNewConversation,
  sendMessage,
} = useChat()

onMounted(() => {
  fetchConversations()
})
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
      <ChatMessageList :messages="messages" :is-thinking="isThinking" />
      <ChatInput :disabled="isSending" @send="sendMessage" />
    </div>
  </div>
</template>
