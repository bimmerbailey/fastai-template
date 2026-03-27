export interface ItemRead {
  id: string
  name: string
  cost: number
  description: string
  quantity: number
  created_at: string
  updated_at: string
}

export interface ItemCreate {
  name: string
  cost?: number
  description?: string
  quantity?: number
}

export interface ItemUpdate {
  name?: string
  cost?: number
  description?: string
  quantity?: number
}

export interface ItemListParams {
  offset?: number
  limit?: number
}
