import http from './http'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: {
    id: number
    username: string
    email: string
  }
}

export interface UserInfo {
  id: number
  username: string
  email: string
  created_at: string
}

/** Register a new user account */
export function register(data: RegisterPayload) {
  return http.post<TokenResponse>('/auth/register', data)
}

/** Login with email and password */
export function login(data: LoginPayload) {
  return http.post<TokenResponse>('/auth/login', data)
}

/** Get current user info from token */
export function getMe() {
  return http.get<UserInfo>('/auth/me')
}
