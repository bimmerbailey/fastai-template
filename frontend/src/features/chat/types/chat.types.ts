export interface ConversationRead {
  id: string
  user_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface MessageRead {
  id: string
  conversation_id: string
  role: "user" | "assistant"
  content_text: string | null
  created_at: string
}

export interface MessageCreate {
  role: "user" | "assistant"
  content_text: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatUsage {
  input_tokens: number
  output_tokens: number
  requests: number
}

export interface ChatResponse {
  message: string
  model: string
  conversation_id: string
  usage?: ChatUsage
}

export interface ConversationListParams {
  user_id: string
  offset?: number
  limit?: number
}

export interface MessageListParams {
  offset?: number
  limit?: number
}
