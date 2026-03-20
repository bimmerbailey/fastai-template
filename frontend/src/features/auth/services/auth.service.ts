import type { AuthResponse, LoginPayload } from '../types/auth.types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(error.detail ?? 'Login failed')
    }

    return response.json()
  },
}
