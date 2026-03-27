import { api } from "@/lib/api"
import type {
  ChatRequest,
  ChatResponse,
  ConversationRead,
  ConversationListParams,
  MessageRead,
  MessageCreate,
  MessageListParams,
} from "../types/chat.types"

export const chatService = {
  async sendMessage(payload: ChatRequest): Promise<ChatResponse> {
    return api<ChatResponse>("/chat", { method: "POST", body: payload })
  },

  async getConversations(params: ConversationListParams): Promise<ConversationRead[]> {
    return api<ConversationRead[]>("/conversations", { params })
  },

  async getConversation(id: string): Promise<ConversationRead> {
    return api<ConversationRead>(`/conversations/${id}`)
  },

  async createConversation(title?: string): Promise<ConversationRead> {
    return api<ConversationRead>("/conversations", { method: "POST", body: { title } })
  },

  async updateConversation(id: string, title: string): Promise<ConversationRead> {
    return api<ConversationRead>(`/conversations/${id}`, { method: "PATCH", body: { title } })
  },

  async deleteConversation(id: string): Promise<void> {
    await api(`/conversations/${id}`, { method: "DELETE" })
  },

  async getMessages(conversationId: string, params?: MessageListParams): Promise<MessageRead[]> {
    return api<MessageRead[]>(`/conversations/${conversationId}/messages`, { params })
  },

  async createMessage(conversationId: string, payload: MessageCreate): Promise<MessageRead> {
    return api<MessageRead>(`/conversations/${conversationId}/messages`, {
      method: "POST",
      body: { ...payload, conversation_id: conversationId },
    })
  },

  async deleteMessage(conversationId: string, messageId: string): Promise<void> {
    await api(`/conversations/${conversationId}/messages/${messageId}`, { method: "DELETE" })
  },
}
