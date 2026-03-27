export type AccountStatus = "active" | "suspended" | "locked" | "pending_verification"

export interface UserRead {
  id: string
  first_name: string | null
  last_name: string | null
  email: string
  display_name: string | null
  avatar_url: string | null
  is_admin: boolean
  status: AccountStatus
  is_active: boolean
  is_email_verified: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface UserCreate {
  first_name?: string
  last_name?: string
  email: string
  password: string
  display_name?: string
  avatar_url?: string
  is_admin?: boolean
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  email?: string
  password?: string
  display_name?: string
  avatar_url?: string
  is_admin?: boolean
  status?: AccountStatus
}

export interface UserListParams {
  offset?: number
  limit?: number
}
