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
  first_name: string | null
  last_name: string | null
  email: string
  display_name: string | null
  avatar_url: string | null
  is_admin: boolean
  status: string
  is_active: boolean
  is_email_verified: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}
