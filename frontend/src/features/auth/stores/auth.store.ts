import { computed, ref } from "vue"
import { defineStore } from "pinia"
import { useRouter } from "vue-router"
import { authService } from "../services/auth.service"
import type { AuthUser, LoginPayload } from "../types/auth.types"

export const useAuthStore = defineStore("auth", () => {
  const router = useRouter()

  const token = ref<string | null>(localStorage.getItem("auth_token"))
  const user = ref<AuthUser | null>(null)
  const isAuthenticated = computed(() => !!token.value)

  async function login(payload: LoginPayload): Promise<void> {
    const response = await authService.login(payload)
    token.value = response.access_token
    localStorage.setItem("auth_token", response.access_token)
    await router.push({ name: "dashboard" })
  }

  function logout(): void {
    token.value = null
    user.value = null
    localStorage.removeItem("auth_token")
    router.push({ name: "login" })
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
  }
})
