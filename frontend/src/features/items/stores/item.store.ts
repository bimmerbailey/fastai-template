import { ref } from "vue"
import { defineStore } from "pinia"
import { itemService } from "../services/item.service"
import type { ItemRead, ItemCreate, ItemUpdate, ItemListParams } from "../types/item.types"

export const useItemStore = defineStore("items", () => {
  const items = ref<ItemRead[]>([])
  const selectedItem = ref<ItemRead | null>(null)

  async function fetchItems(params?: ItemListParams): Promise<void> {
    items.value = await itemService.getItems(params)
  }

  async function fetchItem(id: string): Promise<void> {
    selectedItem.value = await itemService.getItem(id)
  }

  async function addItem(payload: ItemCreate): Promise<ItemRead> {
    const item = await itemService.createItem(payload)
    items.value.push(item)
    return item
  }

  async function editItem(id: string, payload: ItemUpdate): Promise<ItemRead> {
    const item = await itemService.updateItem(id, payload)
    const index = items.value.findIndex((i) => i.id === id)
    if (index !== -1) items.value[index] = item
    if (selectedItem.value?.id === id) selectedItem.value = item
    return item
  }

  async function removeItem(id: string): Promise<void> {
    await itemService.deleteItem(id)
    items.value = items.value.filter((i) => i.id !== id)
    if (selectedItem.value?.id === id) selectedItem.value = null
  }

  return {
    items,
    selectedItem,
    fetchItems,
    fetchItem,
    addItem,
    editItem,
    removeItem,
  }
})
