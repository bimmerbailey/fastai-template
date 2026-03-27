import { ref } from "vue"
import { storeToRefs } from "pinia"
import { useItemStore } from "../stores/item.store"
import type { ItemCreate, ItemUpdate, ItemListParams } from "../types/item.types"

export function useItems() {
  const store = useItemStore()
  const { items, selectedItem } = storeToRefs(store)

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchItems(params?: ItemListParams): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchItems(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch items"
    } finally {
      isLoading.value = false
    }
  }

  async function fetchItem(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchItem(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch item"
    } finally {
      isLoading.value = false
    }
  }

  async function addItem(payload: ItemCreate): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.addItem(payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to create item"
    } finally {
      isLoading.value = false
    }
  }

  async function editItem(id: string, payload: ItemUpdate): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.editItem(id, payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to update item"
    } finally {
      isLoading.value = false
    }
  }

  async function removeItem(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.removeItem(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to delete item"
    } finally {
      isLoading.value = false
    }
  }

  return {
    items,
    selectedItem,
    isLoading,
    error,
    fetchItems,
    fetchItem,
    addItem,
    editItem,
    removeItem,
  }
}
