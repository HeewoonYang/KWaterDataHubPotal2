import apiClient from './client'

export interface SsoProvider {
  provider_type: string
  provider_name: string
  display_name: string
}

export const ssoApi = {
  exchangeCode: (code: string) =>
    apiClient.post('/sso/exchange', { code }),

  getProviders: () =>
    apiClient.get<{ success: boolean; data: SsoProvider[] }>('/sso/providers'),
}

// 관리자용 SSO 제공자 CRUD
export const adminSsoApi = {
  list: () => apiClient.get('/admin/system/sso-providers'),
  create: (data: any) => apiClient.post('/admin/system/sso-providers', data),
  update: (id: string, data: any) => apiClient.put(`/admin/system/sso-providers/${id}`, data),
  delete: (id: string) => apiClient.delete(`/admin/system/sso-providers/${id}`),
}
