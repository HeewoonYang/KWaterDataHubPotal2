import apiClient from './client'
import type { PageResponse, APIResponse } from '../types/common'

// ── 대시보드 ──
export const dashboardApi = {
  summary: () => apiClient.get<APIResponse<any>>('/portal/dashboard/summary'),
  collectionTrend: () => apiClient.get<APIResponse<any[]>>('/portal/dashboard/collection-trend'),
  categoryStats: () => apiClient.get<APIResponse<any[]>>('/portal/dashboard/category-stats'),
  recentData: () => apiClient.get<APIResponse<any[]>>('/portal/dashboard/recent-data'),
  notices: () => apiClient.get<APIResponse<any[]>>('/portal/dashboard/notices'),
}

// ── 위젯/갤러리 관리 ──
export const widgetApi = {
  getUserDashboard: () => apiClient.get<APIResponse<any>>('/portal/widget/user-dashboard'),
  saveUserDashboard: (data: any) => apiClient.put<APIResponse<any>>('/portal/widget/user-dashboard', data),
  widgets: () => apiClient.get<APIResponse<any[]>>('/portal/widget/widgets'),
  templates: () => apiClient.get<APIResponse<any[]>>('/portal/widget/templates'),
  galleryCharts: (params?: Record<string, any>) => apiClient.get<any>('/portal/widget/gallery-charts', { params }),
  chartTemplates: () => apiClient.get<APIResponse<any[]>>('/portal/widget/chart-templates'),
}

// ── 게시판 ──
export const boardApi = {
  diskUsage: () => apiClient.get<APIResponse<any>>('/portal/board/disk-usage'),
  // 공지사항
  notices: (params?: Record<string, any>) => apiClient.get<any>('/portal/board/notices', { params }),
  getNotice: (id: string) => apiClient.get<APIResponse<any>>(`/portal/board/notices/${id}`),
  createNotice: (data: FormData) => apiClient.post<APIResponse<any>>('/portal/board/notices', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateNotice: (id: string, data: FormData) => apiClient.put<APIResponse<any>>(`/portal/board/notices/${id}`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteNotice: (id: string) => apiClient.delete<APIResponse<any>>(`/portal/board/notices/${id}`),
  // 질의응답
  qnaList: (params?: Record<string, any>) => apiClient.get<any>('/portal/board/qna', { params }),
  getQna: (id: string) => apiClient.get<APIResponse<any>>(`/portal/board/qna/${id}`),
  createQna: (data: FormData) => apiClient.post<APIResponse<any>>('/portal/board/qna', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  answerQna: (id: string, data: FormData) => apiClient.put<APIResponse<any>>(`/portal/board/qna/${id}/answer`, data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  // FAQ
  faqList: (params?: Record<string, any>) => apiClient.get<APIResponse<any>>('/portal/board/faq', { params }),
  createFaq: (data: FormData) => apiClient.post<APIResponse<any>>('/portal/board/faq', data, { headers: { 'Content-Type': 'multipart/form-data' } }),
  // 첨부파일 다운로드
  downloadAttachment: (id: string) => apiClient.get(`/portal/board/attachments/${id}/download`, { responseType: 'blob' }),
}

// ── 카탈로그 ──
export const catalogApi = {
  list: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/catalog/datasets', { params }),
  get: (id: string) =>
    apiClient.get<APIResponse<any>>(`/portal/catalog/datasets/${id}`),
  categories: () =>
    apiClient.get<APIResponse<any[]>>('/portal/catalog/categories'),
  search: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/catalog/search', { params }),
  lineage: () =>
    apiClient.get<APIResponse<any>>('/portal/catalog/lineage'),
}

// ── 유통 ──
export const distributionApi = {
  datasets: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/distribution/datasets', { params }),
  createRequest: (data: any) =>
    apiClient.post<APIResponse<any>>('/portal/distribution/requests', data),
  requests: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/distribution/requests', { params }),
  downloads: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/distribution/downloads', { params }),
  downloadFile: (datasetId: string, format: string = 'CSV') =>
    apiClient.get(`/portal/distribution/download/${datasetId}?format=${format}`, { responseType: 'blob' }),
  // API 키 관리
  issueApiKey: (requestId: string) =>
    apiClient.post<APIResponse<any>>(`/portal/distribution/requests/${requestId}/api-key`),
  getApiKeyInfo: (requestId: string) =>
    apiClient.get<APIResponse<any>>(`/portal/distribution/requests/${requestId}/api-key`),
  regenerateApiKey: (requestId: string) =>
    apiClient.post<APIResponse<any>>(`/portal/distribution/requests/${requestId}/api-key/regenerate`),
  revokeApiKey: (requestId: string, apiKeyId: string) =>
    apiClient.delete<APIResponse<any>>(`/portal/distribution/requests/${requestId}/api-key`, { params: { api_key_id: apiKeyId } }),
}

// ── 시각화 ──
export const visualizationApi = {
  dataSources: () =>
    apiClient.get<APIResponse<any[]>>('/portal/visualization/data-sources'),
  columns: (datasetId: string) =>
    apiClient.get<APIResponse<any[]>>(`/portal/visualization/datasets/${datasetId}/columns`),
  listCharts: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/visualization/charts', { params }),
  getChart: (id: string) =>
    apiClient.get<APIResponse<any>>(`/portal/visualization/charts/${id}`),
  createChart: (data: any) =>
    apiClient.post<APIResponse<any>>('/portal/visualization/charts', data),
  updateChart: (id: string, data: any) =>
    apiClient.put<APIResponse<any>>(`/portal/visualization/charts/${id}`, data),
  deleteChart: (id: string) =>
    apiClient.delete<APIResponse<any>>(`/portal/visualization/charts/${id}`),
  cloneChart: (id: string) =>
    apiClient.post<APIResponse<any>>(`/portal/visualization/charts/${id}/clone`),
}

// ── 사용자 ──
export const userApi = {
  profile: () =>
    apiClient.get<APIResponse<any>>('/portal/user/profile'),
  updateProfile: (data: any) =>
    apiClient.put<APIResponse<any>>('/portal/user/profile', data),
  favorites: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/user/favorites', { params }),
  addFavorite: (data: any) =>
    apiClient.post<APIResponse<any>>('/portal/user/favorites', data),
  removeFavorite: (id: string) =>
    apiClient.delete<APIResponse<any>>(`/portal/user/favorites/${id}`),
  recentViews: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/user/recent-views', { params }),
  downloadHistory: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/user/downloads', { params }),
  notifications: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/portal/user/notifications', { params }),
  markRead: (id: string) =>
    apiClient.put<APIResponse<any>>(`/portal/user/notifications/${id}/read`),
  notificationSettings: () =>
    apiClient.get<APIResponse<any[]>>('/portal/user/notification-settings'),
  updateNotificationSettings: (data: any) =>
    apiClient.put<APIResponse<any>>('/portal/user/notification-settings', data),
}

// ── 실시간 계측DB ──
export const measurementApi = {
  summary: () => apiClient.get<APIResponse<any>>('/portal/measurement/summary'),
  regions: () => apiClient.get<APIResponse<any>>('/portal/measurement/regions'),
  offices: (region?: string) => apiClient.get<APIResponse<any>>('/portal/measurement/offices', { params: { region } }),
  sites: (site?: string) => apiClient.get<APIResponse<any>>('/portal/measurement/sites', { params: { site } }),
  tags: (site?: string) => apiClient.get<APIResponse<any>>('/portal/measurement/tags', { params: { site } }),
}

// ── AI 검색 ──
export const aiApi = {
  search: (query: string) =>
    apiClient.post<APIResponse<any>>('/portal/ai/search', { query }),
  suggestions: () =>
    apiClient.get<APIResponse<string[]>>('/portal/ai/suggestions'),
}

// ── 장바구니 ──
export const cartApi = {
  list: () =>
    apiClient.get<APIResponse<any[]>>('/portal/cart'),
  add: (data: any) =>
    apiClient.post<APIResponse<any>>('/portal/cart', data),
  remove: (itemId: string) =>
    apiClient.delete<APIResponse<any>>(`/portal/cart/${itemId}`),
  clear: () =>
    apiClient.delete<APIResponse<any>>('/portal/cart'),
  update: (itemId: string, data: any) =>
    apiClient.put<APIResponse<any>>(`/portal/cart/${itemId}`, data),
}
