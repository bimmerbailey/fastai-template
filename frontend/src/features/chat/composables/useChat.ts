import { ref } from "vue"
import { storeToRefs } from "pinia"
import { useChatStore } from "../stores/chat.store"
import type { ConversationListParams } from "../types/chat.types"

export function useChat() {
  const store = useChatStore()
  const { conversations, activeConversation, messages } = storeToRefs(store)

  const isLoading = ref(false)
  const isSending = ref(false)
  const error = ref<string | null>(null)

  async function fetchConversations(params: ConversationListParams): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchConversations(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch conversations"
    } finally {
      isLoading.value = false
    }
  }

  async function selectConversation(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.selectConversation(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to load conversation"
    } finally {
      isLoading.value = false
    }
  }

  async function startNewConversation(title?: string): Promise<void> {
    error.value = null
    try {
      await store.startNewConversation(title)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to create conversation"
    }
  }

  async function sendMessage(text: string): Promise<void> {
    isSending.value = true
    error.value = null
    try {
      await store.sendMessage(text)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to send message"
    } finally {
      isSending.value = false
    }
  }

  async function deleteConversation(id: string): Promise<void> {
    error.value = null
    try {
      await store.deleteConversation(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to delete conversation"
    }
  }

  return {
    conversations,
    activeConversation,
    messages,
    isLoading,
    isSending,
    error,
    fetchConversations,
    selectConversation,
    startNewConversation,
    sendMessage,
    deleteConversation,
  }
}
