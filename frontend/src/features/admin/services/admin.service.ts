import { adminApi } from "@/lib/api"
import type { UserRead, UserCreate, UserUpdate, UserListParams } from "../types/admin.types"

export const adminService = {
  async getUsers(params?: UserListParams): Promise<UserRead[]> {
    return adminApi<UserRead[]>("/users", { params })
  },

  async getUser(id: string): Promise<UserRead> {
    return adminApi<UserRead>(`/users/${id}`)
  },

  async createUser(payload: UserCreate): Promise<UserRead> {
    return adminApi<UserRead>("/users", { method: "POST", body: payload })
  },

  async updateUser(id: string, payload: UserUpdate): Promise<UserRead> {
    return adminApi<UserRead>(`/users/${id}`, { method: "PATCH", body: payload })
  },

  async deleteUser(id: string): Promise<void> {
    await adminApi(`/users/${id}`, { method: "DELETE" })
  },
}
