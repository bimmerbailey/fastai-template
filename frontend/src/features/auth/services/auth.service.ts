import { api } from "@/lib/api"
import type { AuthResponse, AuthUser, LoginPayload } from "../types/auth.types"

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    return api<AuthResponse>("/auth/login", {
      method: "POST",
      body: payload,
    })
  },

  async getMe(): Promise<AuthUser> {
    return api<AuthUser>("/auth/me")
  },
}
