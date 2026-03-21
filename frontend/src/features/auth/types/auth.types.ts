export interface LoginPayload {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface AuthUser {
  id: string
  email: string
  is_admin: boolean
}

export interface AuthState {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
}
