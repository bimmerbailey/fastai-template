import { ref } from "vue"
import { defineStore } from "pinia"
import { adminService } from "../services/admin.service"
import type { UserRead, UserCreate, UserUpdate, UserListParams } from "../types/admin.types"

export const useAdminStore = defineStore("admin", () => {
  const users = ref<UserRead[]>([])
  const selectedUser = ref<UserRead | null>(null)

  async function fetchUsers(params?: UserListParams): Promise<void> {
    users.value = await adminService.getUsers(params)
  }

  async function fetchUser(id: string): Promise<void> {
    selectedUser.value = await adminService.getUser(id)
  }

  async function addUser(payload: UserCreate): Promise<UserRead> {
    const user = await adminService.createUser(payload)
    users.value.push(user)
    return user
  }

  async function editUser(id: string, payload: UserUpdate): Promise<UserRead> {
    const user = await adminService.updateUser(id, payload)
    const index = users.value.findIndex((u) => u.id === id)
    if (index !== -1) users.value[index] = user
    if (selectedUser.value?.id === id) selectedUser.value = user
    return user
  }

  async function removeUser(id: string): Promise<void> {
    await adminService.deleteUser(id)
    users.value = users.value.filter((u) => u.id !== id)
    if (selectedUser.value?.id === id) selectedUser.value = null
  }

  return {
    users,
    selectedUser,
    fetchUsers,
    fetchUser,
    addUser,
    editUser,
    removeUser,
  }
})
