import { api } from "@/lib/api"
import type { ItemRead, ItemCreate, ItemUpdate, ItemListParams } from "../types/item.types"

export const itemService = {
  async getItems(params?: ItemListParams): Promise<ItemRead[]> {
    return api<ItemRead[]>("/items", { params })
  },

  async getItem(id: string): Promise<ItemRead> {
    return api<ItemRead>(`/items/${id}`)
  },

  async createItem(payload: ItemCreate): Promise<ItemRead> {
    return api<ItemRead>("/items", { method: "POST", body: payload })
  },

  async updateItem(id: string, payload: ItemUpdate): Promise<ItemRead> {
    return api<ItemRead>(`/items/${id}`, { method: "PATCH", body: payload })
  },

  async deleteItem(id: string): Promise<void> {
    await api(`/items/${id}`, { method: "DELETE" })
  },
}
