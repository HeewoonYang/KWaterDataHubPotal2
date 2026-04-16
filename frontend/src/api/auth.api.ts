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
  role_group: string
  data_grades: number[]
  screen_permissions: Record<string, { create: boolean; update: boolean; delete: boolean }>
  must_change_password?: boolean
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

export interface FindIdRequestPayload {
  name: string
  phone: string
}

export interface FindIdRequestData {
  request_id: string
  masked_phone: string
}

export interface FindIdVerifyPayload {
  request_id: string
  code: string
}

export interface FindIdVerifyData {
  login_id_masked: string
}

export interface ResetPasswordPayload {
  login_id: string
  name: string
  phone: string
}

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data),

  logout: () =>
    apiClient.post<APIResponse<null>>('/auth/logout'),

  getMe: () =>
    apiClient.get<APIResponse<UserProfile>>('/auth/me'),

  changePassword: (old_password: string, new_password: string) =>
    apiClient.put<APIResponse<null>>('/auth/change-password', { old_password, new_password }),

  // 아이디 찾기
  findIdRequest: (data: FindIdRequestPayload) =>
    apiClient.post<APIResponse<FindIdRequestData>>('/auth/recovery/find-id/request', data),
  findIdVerify: (data: FindIdVerifyPayload) =>
    apiClient.post<APIResponse<FindIdVerifyData>>('/auth/recovery/find-id/verify', data),

  // 비밀번호 찾기(임시 비밀번호 SMS 발송)
  resetPassword: (data: ResetPasswordPayload) =>
    apiClient.post<APIResponse<null>>('/auth/recovery/reset-password', data),
}
