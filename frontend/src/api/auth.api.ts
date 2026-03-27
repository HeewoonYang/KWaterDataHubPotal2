import apiClient from './client'

export interface LoginRequest {
  login_id: string
  password: string
}

export interface UserProfile {
  id: string
  login_id: string
  name: string
  email: string | null
  department_name: string | null
  position: string | null
  user_type: string
  role_code: string
  role_name: string
  data_grades: number[]
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserProfile
}

export interface APIResponse<T> {
  success: boolean
  message: string
  data: T | null
}

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data),

  logout: () =>
    apiClient.post<APIResponse<null>>('/auth/logout'),

  getMe: () =>
    apiClient.get<APIResponse<UserProfile>>('/auth/me'),
}
