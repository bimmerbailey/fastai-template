export interface DocumentRead {
  id: string
  filename: string
  content_type: string
  file_size: number
  storage_path: string
  content_hash: string
  embedding_status: string
  created_at: string
  updated_at: string
}

export interface DocumentListParams {
  offset?: number
  limit?: number
  embedding_status?: string
}
