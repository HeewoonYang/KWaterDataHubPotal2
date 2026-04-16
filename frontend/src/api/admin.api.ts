import apiClient from './client'
import type { PageResponse, APIResponse } from '../types/common'

// ── 시스템관리 ──
export const adminSystemApi = {
  infrastructure: () => apiClient.get<APIResponse<any[]>>('/admin/system/infrastructure'),
  createInfrastructure: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/system/infrastructure', null, { params }),
  updateInfrastructure: (id: string, params: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/system/infrastructure/${id}`, null, { params }),
  cloud: () => apiClient.get<APIResponse<any[]>>('/admin/system/cloud'),
  drBackup: () => apiClient.get<APIResponse<any[]>>('/admin/system/dr-backup'),
  createDrBackup: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/system/dr-backup', null, { params }),
  deleteDrBackup: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/system/dr-backup/${id}`),
  executeBackup: (id: string) => apiClient.post<APIResponse<any>>(`/admin/system/dr-backup/${id}/execute`),
  restoreBackup: (id: string) => apiClient.post<APIResponse<any>>(`/admin/system/dr-backup/${id}/restore`),
  healthCheck: () => apiClient.get<APIResponse<any>>('/admin/system/health-check'),
  packages: () => apiClient.get<APIResponse<any[]>>('/admin/system/packages'),
  // 표준 인터페이스
  interfaces: () => apiClient.get<APIResponse<any[]>>('/admin/system/interfaces'),
  getInterface: (id: string) => apiClient.get<APIResponse<any>>(`/admin/system/interfaces/${id}`),
  createInterface: (data: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/system/interfaces', data),
  updateInterface: (id: string, data: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/system/interfaces/${id}`, data),
  deleteInterface: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/system/interfaces/${id}`),
  testInterface: (id: string) => apiClient.post<APIResponse<any>>(`/admin/system/interfaces/${id}/test`),
  interfaceLogs: (id: string, params?: Record<string, any>) => apiClient.get<any>(`/admin/system/interfaces/${id}/logs`, { params }),
  // 이기종 통합
  integrations: () => apiClient.get<APIResponse<any[]>>('/admin/system/integrations'),
  getIntegration: (id: string) => apiClient.get<APIResponse<any>>(`/admin/system/integrations/${id}`),
  createIntegration: (data: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/system/integrations', data),
  updateIntegration: (id: string, data: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/system/integrations/${id}`, data),
  deleteIntegration: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/system/integrations/${id}`),
  testIntegration: (id: string) => apiClient.post<APIResponse<any>>(`/admin/system/integrations/${id}/test`),
  syncIntegration: (id: string) => apiClient.post<APIResponse<any>>(`/admin/system/integrations/${id}/sync`),
  integrationLogs: (id: string, params?: Record<string, any>) => apiClient.get<any>(`/admin/system/integrations/${id}/logs`, { params }),
  // DMZ 연계
  dmzLinks: () => apiClient.get<APIResponse<any[]>>('/admin/system/dmz-links'),
  getDmzLink: (id: string) => apiClient.get<APIResponse<any>>(`/admin/system/dmz-links/${id}`),
  createDmzLink: (data: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/system/dmz-links', data),
  updateDmzLink: (id: string, data: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/system/dmz-links/${id}`, data),
  deleteDmzLink: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/system/dmz-links/${id}`),
}

// ── 사용자관리 ──
export const adminUserApi = {
  users: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/user/users', { params }),
  getUser: (userId: string) => apiClient.get<APIResponse<any>>(`/admin/user/users/${userId}`),
  createUser: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/users', data),
  updateUser: (userId: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/user/users/${userId}`, data),
  deleteUser: (userId: string) => apiClient.delete<APIResponse<any>>(`/admin/user/users/${userId}`),
  resetPassword: (userId: string) => apiClient.post<APIResponse<any>>(`/admin/user/users/${userId}/reset-password`),
  sendInitialPassword: (userId: string) => apiClient.post<APIResponse<any>>(`/admin/user/users/${userId}/send-initial-password`),
  roles: () => apiClient.get<APIResponse<any[]>>('/admin/user/roles'),
  createRole: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/roles', data),
  updateRole: (roleId: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/user/roles/${roleId}`, data),
  deleteRole: (roleId: string) => apiClient.delete<APIResponse<any>>(`/admin/user/roles/${roleId}`),
  // 화면별 권한
  screenCodes: () => apiClient.get<APIResponse<any[]>>('/admin/user/screen-codes'),
  screenPermissions: (roleId: string) => apiClient.get<APIResponse<any[]>>(`/admin/user/roles/${roleId}/screen-permissions`),
  updateScreenPermissions: (roleId: string, data: { permissions: any[] }) => apiClient.put<APIResponse<any>>(`/admin/user/roles/${roleId}/screen-permissions`, data),
  accessPolicies: () => apiClient.get<APIResponse<any[]>>('/admin/user/access-policies'),
  createAccessPolicy: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/access-policies', data),
  updateAccessPolicy: (policyId: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/user/access-policies/${policyId}`, data),
  deleteAccessPolicy: (policyId: string) => apiClient.delete<APIResponse<any>>(`/admin/user/access-policies/${policyId}`),
  accessRequests: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/user/access-requests', { params }),
  approveAccessRequest: (requestId: string) => apiClient.put<APIResponse<any>>(`/admin/user/access-requests/${requestId}/approve`),
  rejectAccessRequest: (requestId: string) => apiClient.put<APIResponse<any>>(`/admin/user/access-requests/${requestId}/reject`),
  orgTree: () => apiClient.get<APIResponse<any[]>>('/admin/user/org-tree'),
  runOrgSync: (dryRun?: boolean) => apiClient.post<APIResponse<any>>(`/admin/user/org-sync?dry_run=${dryRun || false}`),
  orgSyncHistory: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/user/org-sync/history', { params }),
  orgSyncDetail: (syncId: string) => apiClient.get<APIResponse<any>>(`/admin/user/org-sync/history/${syncId}`),
  commonSettings: () => apiClient.get<APIResponse<any>>('/admin/user/common-settings'),
  updateCommonSettings: (data: { settings: Record<string, string> }) => apiClient.put<APIResponse<any>>('/admin/user/common-settings', data),
  // 보안 규칙
  createSecurityRule: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/security-rules', data),
  updateSecurityRule: (ruleId: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/user/security-rules/${ruleId}`, data),
  deleteSecurityRule: (ruleId: string) => apiClient.delete<APIResponse<any>>(`/admin/user/security-rules/${ruleId}`),
  // 커스텀 카테고리
  createCustomCategory: (data: { category_name: string }) => apiClient.post<APIResponse<any>>('/admin/user/custom-categories', data),
  deleteCustomCategory: (categoryKey: string) => apiClient.delete<APIResponse<any>>(`/admin/user/custom-categories/${categoryKey}`),
  createCustomSetting: (data: any) => apiClient.post<APIResponse<any>>('/admin/user/custom-settings', data),
  deleteCustomSetting: (settingId: string) => apiClient.delete<APIResponse<any>>(`/admin/user/custom-settings/${settingId}`),
}

// ── 데이터수집 ──
export const adminCollectionApi = {
  // 전략 CRUD
  strategies: () => apiClient.get<APIResponse<any[]>>('/admin/collection/strategies'),
  createStrategy: (data: any) => apiClient.post<APIResponse<any>>('/admin/collection/strategies', data),
  updateStrategy: (id: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/collection/strategies/${id}`, data),
  deleteStrategy: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/strategies/${id}`),
  // 데이터 소스 CRUD + 테스트
  dataSources: () => apiClient.get<APIResponse<any[]>>('/admin/collection/data-sources'),
  createDataSource: (data: any) => apiClient.post<APIResponse<any>>('/admin/collection/data-sources', data),
  updateDataSource: (id: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/collection/data-sources/${id}`, data),
  deleteDataSource: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/data-sources/${id}`),
  testDataSource: (id: string) => apiClient.post<APIResponse<any>>(`/admin/collection/data-sources/${id}/test`),
  // 데이터셋 구성 CRUD
  datasetConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/collection/dataset-configs'),
  createDatasetConfig: (data: any) => apiClient.post<APIResponse<any>>('/admin/collection/dataset-configs', data),
  updateDatasetConfig: (id: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/collection/dataset-configs/${id}`, data),
  deleteDatasetConfig: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/dataset-configs/${id}`),
  // 수집 작업
  jobs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/collection/jobs', { params }),
  getJob: (id: string) => apiClient.get<APIResponse<any>>(`/admin/collection/jobs/${id}`),
  executeCollection: (configId?: string) => apiClient.post<APIResponse<any>>(`/admin/collection/jobs/execute${configId ? '?dataset_config_id=' + configId : ''}`),
  registerCatalog: (jobId: string) => apiClient.post<APIResponse<any>>(`/admin/collection/jobs/${jobId}/register-catalog`),
  // 스케줄
  schedules: () => apiClient.get<APIResponse<any[]>>('/admin/collection/schedules'),
  createSchedule: (data: any) => apiClient.post<APIResponse<any>>('/admin/collection/schedules', data),
  // 모니터링
  monitoringSummary: () => apiClient.get<APIResponse<any>>('/admin/collection/monitoring/summary'),
  failureAnalysis: (days: number = 7) => apiClient.get<APIResponse<any>>('/admin/collection/monitoring/failure-analysis', { params: { days } }),
  // 알람 설정 (REQ-DHUB-005-002-003)
  alerts: () => apiClient.get<APIResponse<any[]>>('/admin/collection/alerts'),
  upsertAlert: (data: any) => apiClient.post<APIResponse<any>>('/admin/collection/alerts', data),
  deleteAlert: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/alerts/${id}`),
  testAlert: (id: string) => apiClient.post<APIResponse<any>>(`/admin/collection/alerts/${id}/test`),
  dispatchAlertsNow: () => apiClient.post<APIResponse<any>>('/admin/collection/alerts/dispatch-now'),
  // 마이그레이션 (REQ-DHUB-005-004-007)
  migrations: () => apiClient.get<APIResponse<any[]>>('/admin/collection/migrations'),
  createMigration: (data?: any) => apiClient.post<APIResponse<any>>('/admin/collection/migrations', data || {}),
  getMigration: (id: string) => apiClient.get<APIResponse<any>>(`/admin/collection/migrations/${id}`),
  executeMigration: (id: string) => apiClient.post<APIResponse<any>>(`/admin/collection/migrations/${id}/execute`),
  executeMigrationSync: (id: string) => apiClient.post<APIResponse<any>>(`/admin/collection/migrations/${id}/execute-sync`),
  updateMigration: (id: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/collection/migrations/${id}`, data),
  deleteMigration: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/migrations/${id}`),
  // REQ-DHUB-005-004-008 결과·세부로그 대시보드
  migrationResultsSummary: (days = 30) =>
    apiClient.get<APIResponse<any>>('/admin/collection/migrations/results/summary', { params: { days } }),
  migrationAllAuditLogs: (params?: Record<string, any>) =>
    apiClient.get<PageResponse<any>>('/admin/collection/migrations/results/audit-logs', { params }),
  // 단일 테이블 매핑 (REQ-DHUB-005-004-004 연계 테이블 추가/삭제/수정)
  addMigrationTable: (mid: string, t: any) => apiClient.post<APIResponse<any>>(`/admin/collection/migrations/${mid}/tables`, t),
  updateMigrationTable: (mid: string, key: string, t: any) =>
    apiClient.put<APIResponse<any>>(`/admin/collection/migrations/${mid}/tables/${encodeURIComponent(key)}`, t),
  deleteMigrationTable: (mid: string, key: string) =>
    apiClient.delete<APIResponse<any>>(`/admin/collection/migrations/${mid}/tables/${encodeURIComponent(key)}`),
  // 외부기관 연계 (REQ-DHUB-005-005-001)
  externalAgencies: (params?: Record<string, any>) => apiClient.get<APIResponse<any[]>>('/admin/collection/external-agencies', { params }),
  getExternalAgency: (id: string) => apiClient.get<APIResponse<any>>(`/admin/collection/external-agencies/${id}`),
  createExternalAgency: (data: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/collection/external-agencies', data),
  updateExternalAgency: (id: string, data: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/collection/external-agencies/${id}`, data),
  deleteExternalAgency: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/external-agencies/${id}`),
  externalAgencyStats: () => apiClient.get<APIResponse<any>>('/admin/collection/external-agencies/stats'),
  externalAgencyHealthCheck: (id: string) => apiClient.post<APIResponse<any>>(`/admin/collection/external-agencies/${id}/health-check`),
  externalAgencyHealthCheckAll: () => apiClient.post<APIResponse<any>>('/admin/collection/external-agencies/health-check-all'),
  externalAgencyHealthLogs: (id: string, params?: Record<string, any>) => apiClient.get<any>(`/admin/collection/external-agencies/${id}/health-logs`, { params }),
  externalAgencyTxLogs: (id: string, params?: Record<string, any>) => apiClient.get<any>(`/admin/collection/external-agencies/${id}/tx-logs`, { params }),
  externalAgencyFailover: (id: string, data: { activate: boolean; reason?: string }) =>
    apiClient.post<APIResponse<any>>(`/admin/collection/external-agencies/${id}/failover`, data),
  // 공간정보
  spatialConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/collection/spatial-configs'),
  spatialConfigDetail: (id: string) =>
    apiClient.get<APIResponse<any>>(`/admin/collection/spatial-configs/${id}`),
  createSpatialConfig: (data: Record<string, any>) =>
    apiClient.post<APIResponse<any>>('/admin/collection/spatial-configs', data),
  updateSpatialConfig: (id: string, data: Record<string, any>) =>
    apiClient.put<APIResponse<any>>(`/admin/collection/spatial-configs/${id}`, data),
  deleteSpatialConfig: (id: string) =>
    apiClient.delete<APIResponse<any>>(`/admin/collection/spatial-configs/${id}`),
  testSpatialConnection: (id: string) =>
    apiClient.post<APIResponse<any>>(`/admin/collection/spatial-configs/${id}/test-connection`),
  discoverSpatialLayers: (id: string) =>
    apiClient.post<APIResponse<any>>(`/admin/collection/spatial-configs/${id}/discover-layers`),
  runSpatialCollection: (id: string) =>
    apiClient.post<APIResponse<any>>(`/admin/collection/spatial-configs/${id}/run`),
  spatialConfigHistory: (id: string, limit = 20) =>
    apiClient.get<APIResponse<any[]>>(`/admin/collection/spatial-configs/${id}/history`, { params: { limit } }),
  // 비정형데이터관리
  unstructuredDocs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/collection/unstructured-docs', { params }),
  unstructuredDocSummary: () => apiClient.get<APIResponse<any>>('/admin/collection/unstructured-docs/summary'),
  getUnstructuredDoc: (id: string) => apiClient.get<APIResponse<any>>(`/admin/collection/unstructured-docs/${id}`),
  createUnstructuredDoc: (formData: FormData) => apiClient.post<APIResponse<any>>('/admin/collection/unstructured-docs', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  updateUnstructuredDoc: (id: string, formData: FormData) => apiClient.put<APIResponse<any>>(`/admin/collection/unstructured-docs/${id}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  deleteUnstructuredDoc: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/collection/unstructured-docs/${id}`),
  downloadUnstructuredDoc: (id: string) => apiClient.get(`/admin/collection/unstructured-docs/${id}/download`, { responseType: 'blob' }),
  unstructuredDocOntologyUsage: (id: string) => apiClient.get<APIResponse<any>>(`/admin/collection/unstructured-docs/${id}/ontology-usage`),
  approveOntologyUsage: (docId: string, usageId: string, comment?: string) => apiClient.put<APIResponse<any>>(`/admin/collection/unstructured-docs/${docId}/ontology-usage/${usageId}/approve`, null, { params: { comment } }),
  rejectOntologyUsage: (docId: string, usageId: string, comment?: string) => apiClient.put<APIResponse<any>>(`/admin/collection/unstructured-docs/${docId}/ontology-usage/${usageId}/reject`, null, { params: { comment } }),
}

// ══════════════════════════════════════
// REQ-DHUB-005-003: DR / PIT / 이관감사 / OpenMetadata
// ══════════════════════════════════════
export const adminDrApi = {
  // 커넥터
  connectors: () => apiClient.get<APIResponse<any[]>>('/admin/dr/connectors'),
  testConnector: (sourceId: string) => apiClient.post<APIResponse<any>>('/admin/dr/connectors/test', { data_source_id: sourceId }),
  // 저장 없이 입력값으로 즉시 테스트 (등록 모달에서 사용)
  testConnectorConfig: (config: any) => apiClient.post<APIResponse<any>>('/admin/dr/connectors/test-config', config),
  listTables: (sourceId: string, schema: string) =>
    apiClient.get<APIResponse<string[]>>(`/admin/dr/data-sources/${sourceId}/schemas/${encodeURIComponent(schema)}/tables`),
  // DB 탐색기 (REQ-DHUB-005-004-003 확장)
  describeColumns: (sourceId: string, schema: string, table: string) =>
    apiClient.get<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/schemas/${encodeURIComponent(schema)}/tables/${encodeURIComponent(table)}/columns`),
  getTableDdl: (sourceId: string, schema: string, table: string) =>
    apiClient.get<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/schemas/${encodeURIComponent(schema)}/tables/${encodeURIComponent(table)}/ddl`),
  runQuery: (sourceId: string, sql: string, limit = 500) =>
    apiClient.post<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/query`, { sql, limit }),
  listSchemas: (sourceId: string) => apiClient.get<APIResponse<string[]>>(`/admin/dr/data-sources/${sourceId}/schemas`),
  listAccounts: (sourceId: string) => apiClient.get<APIResponse<any[]>>(`/admin/dr/data-sources/${sourceId}/accounts`),
  // 계정·권한 관리 (REQ-DHUB-005-004-002)
  createAccount: (sourceId: string, data: { account_name: string; password: string; note?: string }) =>
    apiClient.post<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/accounts`, data),
  dropAccount: (sourceId: string, accountName: string) =>
    apiClient.delete<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/accounts/${encodeURIComponent(accountName)}`),
  changeAccountPassword: (sourceId: string, accountName: string, data: { new_password: string; note?: string }) =>
    apiClient.post<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/accounts/${encodeURIComponent(accountName)}/password`, data),
  grantPrivileges: (sourceId: string, accountName: string, data: { privileges: string[]; schema?: string; table?: string; note?: string }) =>
    apiClient.post<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/accounts/${encodeURIComponent(accountName)}/grant`, data),
  revokePrivileges: (sourceId: string, accountName: string, data: { privileges: string[]; schema?: string; table?: string; note?: string }) =>
    apiClient.post<APIResponse<any>>(`/admin/dr/data-sources/${sourceId}/accounts/${encodeURIComponent(accountName)}/revoke`, data),

  // 백업
  backups: () => apiClient.get<APIResponse<any[]>>('/admin/dr/backups'),
  upsertBackup: (data: any) => apiClient.post<APIResponse<any>>('/admin/dr/backups', data),
  executeBackup: (id: string) => apiClient.post<APIResponse<any>>(`/admin/dr/backups/${id}/execute`),
  deleteBackup: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/dr/backups/${id}`),

  // PIT 복구
  pitList: () => apiClient.get<APIResponse<any[]>>('/admin/dr/pit-recoveries'),
  pitUpsert: (data: any) => apiClient.post<APIResponse<any>>('/admin/dr/pit-recoveries', data),
  pitSimulate: (id: string) => apiClient.post<APIResponse<any>>(`/admin/dr/pit-recoveries/${id}/simulate`),
  pitApprove: (id: string) => apiClient.post<APIResponse<any>>(`/admin/dr/pit-recoveries/${id}/approve`),
  pitExecute: (id: string) => apiClient.post<APIResponse<any>>(`/admin/dr/pit-recoveries/${id}/execute`),

  // 복구 이력/대시보드
  restoreLogs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/dr/restore-logs', { params }),
  restoreDashboard: (days: number = 30) => apiClient.get<APIResponse<any>>('/admin/dr/restore-dashboard', { params: { days } }),

  // 계정 이력
  accountHistory: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/dr/account-history', { params }),
  accountSnapshot: (sourceId: string) => apiClient.post<APIResponse<any>>('/admin/dr/account-history/snapshot', { source_id: sourceId }),

  // 이관 감사/검증
  migrationAuditLogs: (migrationId: string) => apiClient.get<APIResponse<any[]>>(`/admin/dr/migrations/${migrationId}/audit-logs`),
  migrationValidation: (migrationId: string) => apiClient.get<APIResponse<any>>(`/admin/dr/migrations/${migrationId}/validation`),
  migrationValidate: (migrationId: string, data: any) => apiClient.post<APIResponse<any>>(`/admin/dr/migrations/${migrationId}/validate`, data),

  // OpenMetadata
  omStatus: () => apiClient.get<APIResponse<any>>('/admin/dr/openmetadata/status'),
  omLogs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/dr/openmetadata/sync-logs', { params }),
  omSyncDataset: (datasetId: string) => apiClient.post<APIResponse<any>>(`/admin/dr/openmetadata/sync-dataset/${datasetId}`),
  omSyncPending: () => apiClient.post<APIResponse<any>>('/admin/dr/openmetadata/sync-pending'),
  omDashboard: (days: number = 7) => apiClient.get<APIResponse<any>>('/admin/dr/openmetadata/dashboard', { params: { days } }),
}

// ── 데이터정제 ──
export const adminCleansingApi = {
  rules: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/rules'),
  jobs: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/jobs'),
  anonymization: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/anonymization'),
  createAnonymization: (data: any) => apiClient.post<APIResponse<any>>('/admin/cleansing/anonymization', data),
  updateAnonymization: (id: string, data: any) => apiClient.put<APIResponse<any>>(`/admin/cleansing/anonymization/${id}`, data),
  deleteAnonymization: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/cleansing/anonymization/${id}`),
  executeAnonymization: (id: string) => apiClient.post<APIResponse<any>>(`/admin/cleansing/anonymization/${id}/execute`),
  transforms: () => apiClient.get<APIResponse<any[]>>('/admin/cleansing/transforms'),
}

// ── 데이터저장 ──
export const adminStorageApi = {
  zones: () => apiClient.get<APIResponse<any[]>>('/admin/storage/zones'),
  createZone: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/storage/zones', null, { params }),
  deleteZone: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/storage/zones/${id}`),
  highspeed: () => apiClient.get<APIResponse<any[]>>('/admin/storage/highspeed'),
  createHighspeed: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/storage/highspeed', null, { params }),
  deleteHighspeed: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/storage/highspeed/${id}`),
  unstructured: () => apiClient.get<APIResponse<any[]>>('/admin/storage/unstructured'),
  createUnstructured: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/storage/unstructured', null, { params }),
  deleteUnstructured: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/storage/unstructured/${id}`),
  summary: () => apiClient.get<APIResponse<any>>('/admin/storage/summary'),
}

// ── 데이터유통 ──
export const adminDistributionApi = {
  requests: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/distribution/requests', { params }),
  approveRequest: (requestId: string) => apiClient.put<APIResponse<any>>(`/admin/distribution/requests/${requestId}/approve`),
  rejectRequest: (requestId: string) => apiClient.put<APIResponse<any>>(`/admin/distribution/requests/${requestId}/reject`),
  configs: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/configs'),
  formats: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/formats'),
  apiEndpoints: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/api-endpoints'),
  mcpConfigs: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/mcp-configs'),
  fusionModels: () => apiClient.get<APIResponse<any[]>>('/admin/distribution/fusion-models'),
  createFusionModel: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/distribution/fusion-models', null, { params }),
  updateFusionModel: (id: string, params: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/distribution/fusion-models/${id}`, null, { params }),
  deleteFusionModel: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/distribution/fusion-models/${id}`),
  createMcpConfig: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/distribution/mcp-configs', null, { params }),
  updateMcpConfig: (id: string, params: Record<string, any>) => apiClient.put<APIResponse<any>>(`/admin/distribution/mcp-configs/${id}`, null, { params }),
  deleteMcpConfig: (id: string) => apiClient.delete<APIResponse<any>>(`/admin/distribution/mcp-configs/${id}`),
  stats: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/distribution/stats', { params }),
}

// ── 운영관리 ──
export const adminOperationApi = {
  integrationStatus: () => apiClient.get<APIResponse<any>>('/admin/operation/integration-status'),
  apmDashboard: () => apiClient.get<APIResponse<any>>('/admin/operation/apm-dashboard'),
  securityDashboard: () => apiClient.get<APIResponse<any>>('/admin/operation/security-dashboard'),
  dataEvents: () => apiClient.get<APIResponse<any>>('/admin/operation/data-events'),
  accessLogs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/access-logs', { params }),
  accessLogSummary: (days?: number) => apiClient.get<APIResponse<any>>(`/admin/operation/access-logs/summary?days=${days || 7}`),
  changeLog: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/change-log', { params }),
  createSystemEvent: (params: Record<string, any>) => apiClient.post<APIResponse<any>>('/admin/operation/system-events', null, { params }),
  hubStats: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/hub-stats', { params }),
  aiLogs: (params?: Record<string, any>) => apiClient.get<PageResponse<any>>('/admin/operation/ai-logs', { params }),
  aiModels: () => apiClient.get<APIResponse<any[]>>('/admin/operation/ai-models'),
  systemEvents: () => apiClient.get<APIResponse<any[]>>('/admin/operation/system-events'),
  // 로그 보관정책
  logRetention: () => apiClient.get<APIResponse<any>>('/admin/operation/log-retention'),
  updateLogRetention: (logType: string, retentionDays: number) => apiClient.put<APIResponse<any>>(`/admin/operation/log-retention?log_type=${logType}&retention_days=${retentionDays}`),
  cleanupLogs: (logType: string) => apiClient.delete<APIResponse<any>>(`/admin/operation/log-cleanup?log_type=${logType}`),
}
