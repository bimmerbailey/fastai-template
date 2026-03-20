import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.store'
import type { LoginPayload } from '../types/auth.types'

export function useLogin() {
  const authStore = useAuthStore()
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function login(payload: LoginPayload): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      await authStore.login(payload)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'An unexpected error occurred'
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    login,
  }
}
