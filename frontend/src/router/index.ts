import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 클라우드 포털 (메인 진입점, 인증 불필요)
    {
      path: '/',
      name: 'CloudPortal',
      component: () => import('../views/CloudPortal.vue'),
      meta: { requiresAuth: false },
    },

    // 데이터허브 로그인 (팝업으로 열림)
    {
      path: '/portal/login',
      name: 'Login',
      component: () => import('../views/auth/Login.vue'),
      meta: { requiresAuth: false, isPortal: true },
    },

    // SSO 콜백
    {
      path: '/portal/sso-callback',
      name: 'SsoCallback',
      component: () => import('../views/auth/SsoCallback.vue'),
      meta: { requiresAuth: false, isPortal: true },
    },

    // 데이터허브 사용자 포털 (팝업 내)
    {
      path: '/portal',
      component: () => import('../layouts/PortalLayout.vue'),
      meta: { requiresAuth: true, isPortal: true },
      children: [
        { path: '', name: 'Dashboard', component: () => import('../views/portal/Dashboard.vue') },
        { path: 'widget-settings', name: 'WidgetSettings', component: () => import('../views/portal/WidgetSettings.vue') },
        { path: 'gallery', name: 'Gallery', component: () => import('../views/portal/Gallery.vue') },
        { path: 'widget-manage', name: 'WidgetManage', component: () => import('../views/portal/WidgetManage.vue') },
        { path: 'gallery-content', name: 'GalleryContent', component: () => import('../views/portal/GalleryContent.vue') },
        // 실시간 모니터링
        { path: 'monitoring', name: 'MonitoringRWIS', component: () => import('../views/portal/RealtimeMeasureDB.vue') },
        { path: 'monitoring/rwis', redirect: '/portal/monitoring' },
        { path: 'monitoring/rwis/office', name: 'MonitoringRWISOffice', component: () => import('../views/portal/MeasureOffice.vue') },
        { path: 'monitoring/rwis/site', name: 'MonitoringRWISSite', component: () => import('../views/portal/MeasureSite.vue') },
        { path: 'monitoring/hdaps', name: 'MonitoringHDAPS', component: () => import('../views/portal/MonitoringHDAPS.vue') },
        { path: 'monitoring/gios', name: 'MonitoringGIOS', component: () => import('../views/portal/MonitoringGIOS.vue') },
        { path: 'monitoring/smart-metering', name: 'MonitoringSmartMetering', component: () => import('../views/portal/MonitoringSmartMetering.vue') },
        { path: 'monitoring/gis', name: 'GisMap', component: () => import('../views/portal/GisMap.vue') },
        // 카탈로그
        { path: 'catalog', name: 'Catalog', component: () => import('../views/portal/Catalog.vue') },
        { path: 'catalog/search', name: 'CatalogSearch', component: () => import('../views/portal/CatalogSearch.vue') },
        { path: 'catalog/knowledge-graph', name: 'KnowledgeGraph', component: () => import('../views/portal/KnowledgeGraph.vue') },
        { path: 'catalog/ontology', name: 'OntologyManage', component: () => import('../views/portal/OntologyManage.vue') },
        { path: 'catalog/lineage', name: 'DataLineage', component: () => import('../views/portal/DataLineage.vue') },
        // 시각화
        { path: 'visualization', name: 'Visualization', component: () => import('../views/portal/Visualization.vue'), meta: { requiresInternal: true } },
        { path: 'visualization/gallery', redirect: '/portal/gallery-content' },
        // 유통
        { path: 'distribution', name: 'Distribution', component: () => import('../views/portal/Distribution.vue') },
        { path: 'distribution/request', name: 'DistRequest', component: () => import('../views/portal/DistRequest.vue') },
        { path: 'distribution/download', name: 'DistDownload', component: () => import('../views/portal/DistDownload.vue') },
        // 장바구니
        { path: 'cart', name: 'DataCart', component: () => import('../views/portal/DataCart.vue') },
        // AI 검색
        { path: 'ai-search', name: 'AISearch', component: () => import('../views/portal/AISearch.vue'), meta: { requiresInternal: true } },
        // 마이페이지
        { path: 'mypage', name: 'MyPage', component: () => import('../views/portal/MyPage.vue') },
        { path: 'mypage/data', name: 'MyData', component: () => import('../views/portal/MyData.vue') },
        { path: 'mypage/notifications', name: 'Notifications', component: () => import('../views/portal/Notifications.vue') },
        { path: 'change-password', name: 'ChangePassword', component: () => import('../views/portal/ChangePassword.vue') },
        // 게시판
        { path: 'board/notices', name: 'BoardNotice', component: () => import('../views/portal/BoardNotice.vue') },
        { path: 'board/qna', name: 'BoardQna', component: () => import('../views/portal/BoardQna.vue') },
        { path: 'board/faq', name: 'BoardFaq', component: () => import('../views/portal/BoardFaq.vue') },
        // 사이트맵
        { path: 'sitemap', name: 'SiteMap', component: () => import('../views/portal/SiteMap.vue') },
      ],
    },

    // 데이터허브 관리자 포털 (별도 팝업)
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, isPortal: true },
      children: [
        { path: '', redirect: '/admin/system' },
        // 시스템관리
        { path: 'system', name: 'AdminSystem', component: () => import('../views/admin/AdminDashboard.vue'), meta: { adminMenu: 'system' } },

        { path: 'system/dr', name: 'AdminSystemDr', component: () => import('../views/admin/system/DrBackup.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_DR' } },
        { path: 'system/dr-dashboard', name: 'AdminSystemDrDashboard', component: () => import('../views/admin/system/DrRestoreDashboard.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_DR_DB' } },
        { path: 'system/package', name: 'AdminSystemPackage', component: () => import('../views/admin/system/PackageVerify.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_PKG' } },
        { path: 'system/interface', name: 'AdminSystemInterface', component: () => import('../views/admin/system/InterfaceStd.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_INTF' } },
        { path: 'system/integration', name: 'AdminSystemIntegration', component: () => import('../views/admin/system/Integration.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_INTG' } },
        { path: 'system/dmz', name: 'AdminSystemDmz', component: () => import('../views/admin/system/DmzLink.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_DMZ' } },
        { path: 'system/sso', name: 'AdminSystemSso', component: () => import('../views/admin/system/SsoSettings.vue'), meta: { adminMenu: 'system', screenCode: 'SYS_SSO' } },
        // 사용자관리
        { path: 'user', name: 'AdminUser', component: () => import('../views/admin/user/UserList.vue'), meta: { adminMenu: 'user', screenCode: 'USR_LIST' } },
        { path: 'user/external', name: 'AdminUserExternal', component: () => import('../views/admin/user/ExternalUser.vue'), meta: { adminMenu: 'user', screenCode: 'USR_EXT' } },
        { path: 'user/common', name: 'AdminUserCommon', component: () => import('../views/admin/user/UserCommon.vue'), meta: { adminMenu: 'user', screenCode: 'USR_COMMON' } },
        { path: 'user/org-sync', name: 'AdminUserOrgSync', component: () => import('../views/admin/user/OrgUserSync.vue'), meta: { adminMenu: 'user', screenCode: 'USR_SYNC' } },
        { path: 'user/roles', name: 'AdminUserRoles', component: () => import('../views/admin/user/RoleManage.vue'), meta: { adminMenu: 'user', screenCode: 'USR_ROLES' } },
        { path: 'user/access', name: 'AdminUserAccess', component: () => import('../views/admin/user/AccessControl.vue'), meta: { adminMenu: 'user', screenCode: 'USR_ACCESS' } },
        // 데이터표준
        { path: 'standard', name: 'AdminStandard', component: () => import('../views/admin/standard/StandardCompliance.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/classification', name: 'AdminStandardClass', component: () => import('../views/admin/standard/Classification.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/quality-link', name: 'AdminStandardQLink', component: () => import('../views/admin/standard/QualityLink.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/quality-check', name: 'AdminStandardQCheck', component: () => import('../views/admin/standard/QualityCheck.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/quality-dashboard', name: 'AdminStandardQDashboard', component: () => import('../views/admin/standard/QualityDashboard.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/grade', name: 'AdminStandardGrade', component: () => import('../views/admin/standard/GradeManage.vue'), meta: { adminMenu: 'standard' } },
        // 표준사전 관리
        { path: 'standard/words', name: 'AdminStdWords', component: () => import('../views/admin/standard/WordDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/domains', name: 'AdminStdDomains', component: () => import('../views/admin/standard/DomainDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/terms', name: 'AdminStdTerms', component: () => import('../views/admin/standard/TermDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/codes', name: 'AdminStdCodes', component: () => import('../views/admin/standard/CodeDictionary.vue'), meta: { adminMenu: 'standard' } },
        // 데이터수집
        { path: 'collection', name: 'AdminCollection', component: () => import('../views/admin/collection/CollectionDashboard.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/strategy', name: 'AdminCollectionStrategy', component: () => import('../views/admin/collection/CollectionStrategy.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/profiling', name: 'AdminCollectionProfiling', component: () => import('../views/admin/collection/DataProfiling.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/quality-gate', name: 'AdminCollectionQualityGate', component: () => import('../views/admin/collection/QualityGate.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/dataset', name: 'AdminCollectionDataset', component: () => import('../views/admin/collection/DatasetConfig.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/ui', name: 'AdminCollectionUI', component: () => import('../views/admin/collection/CollectionUI.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/lightweight', name: 'AdminCollectionLight', component: () => import('../views/admin/collection/Lightweight.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/db-source', name: 'AdminCollectionDbSrc', component: () => import('../views/admin/collection/DbSource.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/db-explorer', name: 'AdminCollectionDbExplorer', component: () => import('../views/admin/collection/DbExplorer.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/migration', name: 'AdminCollectionMigration', component: () => import('../views/admin/collection/Migration.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/migration-results', name: 'AdminCollectionMigrationResults', component: () => import('../views/admin/collection/MigrationResults.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/external', name: 'AdminCollectionExternal', component: () => import('../views/admin/collection/ExternalLink.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/spatial', name: 'AdminCollectionSpatial', component: () => import('../views/admin/collection/SpatialCollect.vue'), meta: { adminMenu: 'collection' } },

        { path: 'collection/domain-detail', name: 'AdminCollectionDomainDetail', component: () => import('../views/admin/collection/DomainCollectionDetail.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/unstructured-data', name: 'AdminCollectionUnstructuredData', component: () => import('../views/admin/collection/UnstructuredData.vue'), meta: { adminMenu: 'collection' } },
        // 데이터정제
        { path: 'cleansing', name: 'AdminCleansing', component: () => import('../views/admin/cleansing/CleansingUI.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/anonymize', name: 'AdminCleansingAnon', component: () => import('../views/admin/cleansing/Anonymize.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/review', name: 'AdminCleansingReview', component: () => import('../views/admin/cleansing/TechReview.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/transform', name: 'AdminCleansingTransform', component: () => import('../views/admin/cleansing/TransformManage.vue'), meta: { adminMenu: 'cleansing' } },
        // 데이터저장
        { path: 'storage', name: 'AdminStorage', component: () => import('../views/admin/storage/StorageManage.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/highspeed', name: 'AdminStorageHighspeed', component: () => import('../views/admin/storage/HighspeedDb.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/unstructured', name: 'AdminStorageUnstruct', component: () => import('../views/admin/storage/Unstructured.vue'), meta: { adminMenu: 'storage' } },
        // 데이터패브릭 (저장 하위)
        { path: 'storage/fabric', name: 'AdminStorageFabric', component: () => import('../views/admin/storage/FabricDashboard.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/llm-config', name: 'AdminStorageLlm', component: () => import('../views/admin/storage/LlmConfig.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/gpu-datasets', name: 'AdminStorageGpu', component: () => import('../views/admin/storage/GpuDatasetManage.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/mindsdb', name: 'AdminStorageMindsdb', component: () => import('../views/admin/storage/MindsDbConfig.vue'), meta: { adminMenu: 'storage' } },
        // 분석DB (저장 하위)
        { path: 'storage/analysis-datasets', name: 'AdminStorageAnalysis', component: () => import('../views/admin/storage/AnalysisDatasets.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/lifecycle-policy', name: 'AdminStorageLifecycle', component: () => import('../views/admin/storage/LifecyclePolicy.vue'), meta: { adminMenu: 'storage' } },
        // 데이터유통
        { path: 'distribution', name: 'AdminDistribution', component: () => import('../views/admin/distribution/DistributionConfig.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/standard', name: 'AdminDistStandard', component: () => import('../views/admin/distribution/DistStandard.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/format', name: 'AdminDistFormat', component: () => import('../views/admin/distribution/DistFormat.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/ui', name: 'AdminDistUI', component: () => import('../views/admin/distribution/DistUI.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/fusion', name: 'AdminDistFusion', component: () => import('../views/admin/distribution/FusionModel.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/api', name: 'AdminDistApi', component: () => import('../views/admin/distribution/StandardApi.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/mcp', name: 'AdminDistMcp', component: () => import('../views/admin/distribution/McpLink.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/stats', name: 'AdminDistStats', component: () => import('../views/admin/distribution/DistStats.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/usage', name: 'AdminDistUsage', component: () => import('../views/admin/distribution/UsageDashboard.vue'), meta: { adminMenu: 'distribution' } },
        // 온톨로지
        { path: 'ontology', name: 'AdminOntologyGraph', component: () => import('../views/portal/KnowledgeGraph.vue'), meta: { adminMenu: 'ontology' } },
        { path: 'ontology/manage', name: 'AdminOntologyManage', component: () => import('../views/portal/OntologyManage.vue'), meta: { adminMenu: 'ontology' } },
        { path: 'ontology/augmentation', name: 'AdminOntologyAug', component: () => import('../views/admin/ontology/OntologyAugmentation.vue'), meta: { adminMenu: 'ontology' } },
        { path: 'ontology/doc-ingestion', name: 'AdminOntologyDoc', component: () => import('../views/admin/ontology/OntologyDocIngestion.vue'), meta: { adminMenu: 'ontology' } },
        // 운영관리
        { path: 'operation', name: 'AdminOperation', component: () => import('../views/admin/operation/HubStats.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/ai', name: 'AdminOperationAi', component: () => import('../views/admin/operation/AiMonitor.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/optimize', name: 'AdminOperationOptimize', component: () => import('../views/admin/operation/Optimize.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/integration', name: 'AdminIntegrationMonitor', component: () => import('../views/admin/operation/IntegrationMonitor.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/apm', name: 'AdminApmDashboard', component: () => import('../views/admin/operation/ApmDashboard.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/security', name: 'AdminSecurityMonitor', component: () => import('../views/admin/operation/SecurityMonitor.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/events', name: 'AdminDataEvents', component: () => import('../views/admin/operation/DataEventMonitor.vue'), meta: { adminMenu: 'operation' } },
      ],
    },

    // 404 → 클라우드 포털
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// 라우터 가드
router.beforeEach((to: RouteLocationNormalized) => {
  const authStore = useAuthStore()

  // 인증 불필요 페이지
  if (to.meta.requiresAuth === false) {
    // 로그인 페이지에서 이미 인증된 경우 → 사용자 포털로
    if (to.name === 'Login' && authStore.isAuthenticated) {
      return '/portal'
    }
    return true
  }

  // 인증 필요 페이지 - 미로그인 시 로그인으로
  if (!authStore.isAuthenticated) {
    return '/portal/login'
  }

  // 임시/초기 비밀번호 상태이면 변경 페이지로 강제 이동 (예외: 변경 페이지 자체, 로그아웃 경로)
  if (authStore.mustChangePassword && to.name !== 'ChangePassword') {
    return { path: '/portal/change-password', query: { forced: '1' } }
  }

  // 관리자 포털 접근 체크
  if (to.meta.requiresAdmin && !authStore.canAccessAdmin) {
    return '/portal'
  }

  // 내부 사용자 전용 페이지 체크
  if (to.meta.requiresInternal && authStore.isExternal) {
    return '/portal'
  }

  // 관리자 메뉴별 세부 권한 체크
  if (to.meta.adminMenu) {
    const menuKey = to.meta.adminMenu as string
    const access = authStore.adminMenuAccess as Record<string, boolean>
    if (access[menuKey] === false) {
      const firstAllowed = Object.entries(access).find(([, v]) => v)
      if (firstAllowed) return `/admin/${firstAllowed[0]}`
      return '/portal'
    }
  }

  return true
})

export default router
