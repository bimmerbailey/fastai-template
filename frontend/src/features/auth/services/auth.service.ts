import { api } from '@/lib/api'
import type { AuthResponse, LoginPayload } from '../types/auth.types'

export const authService = {
  async login(payload: LoginPayload): Promise<AuthResponse> {

    return api<AuthResponse>('/auth/login', {
      method: 'POST',
      body: payload,
    })
  },
}
