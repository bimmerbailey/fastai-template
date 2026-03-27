import { ref } from "vue"
import { storeToRefs } from "pinia"
import { useAdminStore } from "../stores/admin.store"
import type { UserCreate, UserUpdate, UserListParams } from "../types/admin.types"

export function useAdminUsers() {
  const store = useAdminStore()
  const { users, selectedUser } = storeToRefs(store)

  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(params?: UserListParams): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.fetchUsers(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to fetch users"
    } finally {
      isLoading.value = false
    }
  }

  async function addUser(payload: UserCreate): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.addUser(payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to create user"
    } finally {
      isLoading.value = false
    }
  }

  async function editUser(id: string, payload: UserUpdate): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.editUser(id, payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to update user"
    } finally {
      isLoading.value = false
    }
  }

  async function removeUser(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      await store.removeUser(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to delete user"
    } finally {
      isLoading.value = false
    }
  }

  return {
    users,
    selectedUser,
    isLoading,
    error,
    fetchUsers,
    addUser,
    editUser,
    removeUser,
  }
}
