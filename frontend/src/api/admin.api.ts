import apiClient from './client'
import type { PageResponse, APIResponse } from '../types/common'

// ── 시스템관리 ──
export const adminSystemApi = {
  infrastructure: () => apiClient.get<APIResponse<any[]>>('/admin/system/infrastructure'),
  cloud: () => apiClient.get<APIResponse<any[]>>('/admin/system/cloud'),
  drBackup: () => apiClient.get<APIResponse<any[]>>('/admin/system/dr-backup'),
  packages: () => apiClient.get<APIResponse<any[]>>('/admin/system/packages'),
  interfaces: () => apiClient.get<APIResponse<any[]>>('/admin/system/interfaces'),
  integrations: () => apiClient.get<APIResponse<any[]>>('/admin/system/integrations'),
  dmzLinks: () => apiClient.get<APIResponse<any[]>>('/admin/system/dmz-links'),
}

// ── 사용자관리 ──
export const adminUserApi = {
  users: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/user/users', { params }),
  createUser: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/users', data),
  roles: () => apiClient.get<APIResponse<any[]>>('/admin/user/roles'),
  accessPolicies: () => apiClient.get<APIResponse<any[]>>('/admin/user/access-policies'),
}

// ── 데이터수집 ──
export const adminCollectionApi = {
  strategies: () => apiClient.get<APIResponse<any[]>>('/admin/collection/strategies'),
  dataSources: () => apiClient.get<APIResponse<any[]>>('/admin/collection/data-sources'),
  datasetConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/collection/dataset-configs'),
  jobs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/collection/jobs', { params }),
  migrations: () => apiClient.get<APIResponse<any[]>>('/admin/collection/migrations'),
  externalAgencies: () => apiClient.get<APIResponse<any[]>>('/admin/collection/external-agencies'),
  spatialConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/collection/spatial-configs'),
}

// ── 데이터정제 ──
export const adminCleansingApi = {
  rules: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/rules'),
  jobs: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/jobs'),
  anonymization: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/anonymization'),
  transforms: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/transforms'),
}

// ── 데이터저장 ──
export const adminStorageApi = {
  zones: () => apiClient.get<APIResponse<any[]>>('/admin/storage/zones'),
  highspeed: () => apiClient.get<APIResponse<any[]>>('/admin/storage/highspeed'),
  unstructured: () => apiClient.get<APIResponse<any[]>>('/admin/storage/unstructured'),
}

// ── 데이터유통 ──
export const adminDistributionApi = {
  configs: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/configs'),
  formats: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/formats'),
  apiEndpoints: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/api-endpoints'),
  mcpConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/mcp-configs'),
  fusionModels: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/fusion-models'),
  stats: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/distribution/stats', { params }),
}

// ── 운영관리 ──
export const adminOperationApi = {
  hubStats: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/hub-stats', { params }),
  aiLogs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/ai-logs', { params }),
  aiModels: () => apiClient.get<APIResponse<any[]>>('/admin/operation/ai-models'),
  systemEvents: () => apiClient.get<APIResponse<any[]>>('/admin/operation/system-events'),
}
