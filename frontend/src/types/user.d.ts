export interface User {
  id: number
  username: string
  email: string
  avatar_url: string
  status: number
  created_at: string
}

export interface TokenData {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  email: string
}
