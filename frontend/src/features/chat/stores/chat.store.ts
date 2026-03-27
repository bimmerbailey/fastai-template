import { ref } from "vue"
import { defineStore } from "pinia"
import { chatService } from "../services/chat.service"
import type {
  ConversationRead,
  MessageRead,
  ChatResponse,
  ConversationListParams,
} from "../types/chat.types"

export const useChatStore = defineStore("chat", () => {
  const conversations = ref<ConversationRead[]>([])
  const activeConversation = ref<ConversationRead | null>(null)
  const messages = ref<MessageRead[]>([])

  async function fetchConversations(params: ConversationListParams): Promise<void> {
    conversations.value = await chatService.getConversations(params)
  }

  async function selectConversation(id: string): Promise<void> {
    activeConversation.value = await chatService.getConversation(id)
    messages.value = await chatService.getMessages(id)
  }

  async function startNewConversation(title?: string): Promise<ConversationRead> {
    const conversation = await chatService.createConversation(title)
    conversations.value.unshift(conversation)
    activeConversation.value = conversation
    messages.value = []
    return conversation
  }

  async function sendMessage(text: string): Promise<ChatResponse> {
    const response = await chatService.sendMessage({
      message: text,
      conversation_id: activeConversation.value?.id,
    })

    if (!activeConversation.value) {
      activeConversation.value = await chatService.getConversation(response.conversation_id)
      conversations.value.unshift(activeConversation.value)
    }

    messages.value = await chatService.getMessages(response.conversation_id)
    return response
  }

  async function deleteConversation(id: string): Promise<void> {
    await chatService.deleteConversation(id)
    conversations.value = conversations.value.filter((c) => c.id !== id)
    if (activeConversation.value?.id === id) {
      activeConversation.value = null
      messages.value = []
    }
  }

  return {
    conversations,
    activeConversation,
    messages,
    fetchConversations,
    selectConversation,
    startNewConversation,
    sendMessage,
    deleteConversation,
  }
})
