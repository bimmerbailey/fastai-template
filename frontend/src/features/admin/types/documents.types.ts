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

export interface DocumentUpdate {
  filename?: string
}

export interface EmbeddingChunkRead {
  id: string
  source_type: string
  source_id: string
  chunk_text: string
  chunk_index: number
  embedding_model: string
  metadata_: Record<string, unknown>
  created_at: string
}
