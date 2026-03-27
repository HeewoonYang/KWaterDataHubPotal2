import apiClient from './client'
import type { PageRequest, PageResponse, APIResponse } from '@/types/common'
import type {
  StdWord, StdDomain, StdTerm, StdCode, StdRequest,
  Classification, DataGrade, QualityRule, QualityCheckResult, ComplianceResult,
  MetaModel,
} from '@/types/standard'

// ── 단어사전 ──
export const wordApi = {
  list: (params?: PageRequest) => apiClient.get<PageResponse<StdWord>>('/standards/words', { params }),
  get: (id: number) => apiClient.get<APIResponse<StdWord>>(`/standards/words/${id}`),
  create: (data: Partial<StdWord>) => apiClient.post<APIResponse<StdWord>>('/standards/words', data),
  update: (id: number, data: Partial<StdWord>) => apiClient.put<APIResponse<StdWord>>(`/standards/words/${id}`, data),
  delete: (id: number) => apiClient.delete<APIResponse>(`/standards/words/${id}`),
}

// ── 도메인사전 ──
export const domainApi = {
  list: (params?: PageRequest) => apiClient.get<PageResponse<StdDomain>>('/standards/domains', { params }),
  get: (id: number) => apiClient.get<APIResponse<StdDomain>>(`/standards/domains/${id}`),
  create: (data: Partial<StdDomain>) => apiClient.post<APIResponse<StdDomain>>('/standards/domains', data),
  update: (id: number, data: Partial<StdDomain>) => apiClient.put<APIResponse<StdDomain>>(`/standards/domains/${id}`, data),
  delete: (id: number) => apiClient.delete<APIResponse>(`/standards/domains/${id}`),
}

// ── 용어사전 ──
export const termApi = {
  list: (params?: PageRequest) => apiClient.get<PageResponse<StdTerm>>('/standards/terms', { params }),
  get: (id: number) => apiClient.get<APIResponse<StdTerm>>(`/standards/terms/${id}`),
  create: (data: Partial<StdTerm>) => apiClient.post<APIResponse<StdTerm>>('/standards/terms', data),
  update: (id: number, data: Partial<StdTerm>) => apiClient.put<APIResponse<StdTerm>>(`/standards/terms/${id}`, data),
  delete: (id: number) => apiClient.delete<APIResponse>(`/standards/terms/${id}`),
}

// ── 코드사전 ──
export const codeApi = {
  list: (params?: PageRequest) => apiClient.get<PageResponse<StdCode>>('/standards/codes', { params }),
  get: (id: number) => apiClient.get<APIResponse<StdCode>>(`/standards/codes/${id}`),
  create: (data: Partial<StdCode>) => apiClient.post<APIResponse<StdCode>>('/standards/codes', data),
  update: (id: number, data: Partial<StdCode>) => apiClient.put<APIResponse<StdCode>>(`/standards/codes/${id}`, data),
  delete: (id: number) => apiClient.delete<APIResponse>(`/standards/codes/${id}`),
}

// ── 임포트/익스포트 ──
export const importExportApi = {
  importExcel: (file: File, dictType: string) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<APIResponse>(`/standards/import?dict_type=${dictType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportExcel: (dictType: string) =>
    apiClient.get(`/standards/export?dict_type=${dictType}`, { responseType: 'blob' }),
}

// ── 표준 신청 ──
export const requestApi = {
  list: (params?: PageRequest) => apiClient.get<PageResponse<StdRequest>>('/standards/requests', { params }),
  create: (data: { request_type: string; action_type: string; request_data: Record<string, any> }) =>
    apiClient.post<APIResponse<StdRequest>>('/standards/requests', data),
  approve: (id: number, comment?: string) =>
    apiClient.put<APIResponse<StdRequest>>(`/standards/requests/${id}/approve`, null, { params: { comment } }),
  reject: (id: number, comment?: string) =>
    apiClient.put<APIResponse<StdRequest>>(`/standards/requests/${id}/reject`, null, { params: { comment } }),
}

// ── 분류체계 ──
export const classificationApi = {
  list: (format: 'flat' | 'tree' = 'flat') => apiClient.get<APIResponse<Classification[]>>('/classifications', { params: { format } }),
  get: (id: number) => apiClient.get<APIResponse<Classification>>(`/classifications/${id}`),
  create: (data: Partial<Classification>) => apiClient.post<APIResponse<Classification>>('/classifications', data),
  update: (id: number, data: Partial<Classification>) => apiClient.put<APIResponse<Classification>>(`/classifications/${id}`, data),
  delete: (id: number) => apiClient.delete<APIResponse>(`/classifications/${id}`),
  triggerSync: () => apiClient.post<APIResponse>('/classifications/sync'),
  getSyncStatus: () => apiClient.get<APIResponse>('/classifications/sync-status'),
}

// ── 등급 ──
export const gradeApi = {
  list: () => apiClient.get<APIResponse<DataGrade[]>>('/classifications/grades'),
  update: (id: number, data: Partial<DataGrade>) => apiClient.put<APIResponse<DataGrade>>(`/classifications/grades/${id}`, data),
}

// ── 품질 ──
export const qualityApi = {
  listRules: () => apiClient.get<APIResponse<QualityRule[]>>('/quality/rules'),
  createRule: (data: Partial<QualityRule>) => apiClient.post<APIResponse<QualityRule>>('/quality/rules', data),
  executeCheck: () => apiClient.post<APIResponse>('/quality/execute'),
  listResults: (params?: PageRequest) => apiClient.get<PageResponse<QualityCheckResult>>('/quality/results', { params }),
  getResult: (id: number) => apiClient.get<APIResponse<QualityCheckResult>>(`/quality/results/${id}`),
  listCompliance: () => apiClient.get<APIResponse<ComplianceResult[]>>('/quality/compliance'),
  runComplianceCheck: () => apiClient.post<APIResponse>('/quality/compliance/check'),
}

// ── 메타모델 ──
export const modelApi = {
  list: () => apiClient.get<APIResponse<MetaModel[]>>('/models'),
  get: (id: number) => apiClient.get<APIResponse<MetaModel>>(`/models/${id}`),
  create: (data: Partial<MetaModel>) => apiClient.post<APIResponse<MetaModel>>('/models', data),
  update: (id: number, data: Partial<MetaModel>) => apiClient.put<APIResponse<MetaModel>>(`/models/${id}`, data),
}
