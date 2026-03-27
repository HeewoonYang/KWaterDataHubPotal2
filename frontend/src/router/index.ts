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
        // 실시간 계측DB
        { path: 'realtime-measure', name: 'RealtimeMeasureDB', component: () => import('../views/portal/RealtimeMeasureDB.vue') },
        { path: 'realtime-measure/office', name: 'MeasureOffice', component: () => import('../views/portal/MeasureOffice.vue') },
        { path: 'realtime-measure/site', name: 'MeasureSite', component: () => import('../views/portal/MeasureSite.vue') },
        // 카탈로그
        { path: 'catalog', name: 'Catalog', component: () => import('../views/portal/Catalog.vue') },
        { path: 'catalog/search', name: 'CatalogSearch', component: () => import('../views/portal/CatalogSearch.vue') },
        // 시각화
        { path: 'visualization', name: 'Visualization', component: () => import('../views/portal/Visualization.vue'), meta: { requiresInternal: true } },
        { path: 'visualization/gallery', redirect: '/portal/gallery-content' },
        // 유통
        { path: 'distribution', name: 'Distribution', component: () => import('../views/portal/Distribution.vue') },
        { path: 'distribution/request', name: 'DistRequest', component: () => import('../views/portal/DistRequest.vue') },
        { path: 'distribution/download', name: 'DistDownload', component: () => import('../views/portal/DistDownload.vue') },
        // AI 검색
        { path: 'ai-search', name: 'AISearch', component: () => import('../views/portal/AISearch.vue'), meta: { requiresInternal: true } },
        // 마이페이지
        { path: 'mypage', name: 'MyPage', component: () => import('../views/portal/MyPage.vue') },
        { path: 'mypage/data', name: 'MyData', component: () => import('../views/portal/MyData.vue') },
        { path: 'mypage/notifications', name: 'Notifications', component: () => import('../views/portal/Notifications.vue') },
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
        { path: 'system/cloud', name: 'AdminSystemCloud', component: () => import('../views/admin/system/CloudConfig.vue'), meta: { adminMenu: 'system' } },
        { path: 'system/dr', name: 'AdminSystemDr', component: () => import('../views/admin/system/DrBackup.vue'), meta: { adminMenu: 'system' } },
        { path: 'system/package', name: 'AdminSystemPackage', component: () => import('../views/admin/system/PackageVerify.vue'), meta: { adminMenu: 'system' } },
        { path: 'system/interface', name: 'AdminSystemInterface', component: () => import('../views/admin/system/InterfaceStd.vue'), meta: { adminMenu: 'system' } },
        { path: 'system/integration', name: 'AdminSystemIntegration', component: () => import('../views/admin/system/Integration.vue'), meta: { adminMenu: 'system' } },
        { path: 'system/dmz', name: 'AdminSystemDmz', component: () => import('../views/admin/system/DmzLink.vue'), meta: { adminMenu: 'system' } },
        // 사용자관리
        { path: 'user', name: 'AdminUser', component: () => import('../views/admin/user/UserList.vue'), meta: { adminMenu: 'user' } },
        { path: 'user/external', name: 'AdminUserExternal', component: () => import('../views/admin/user/ExternalUser.vue'), meta: { adminMenu: 'user' } },
        { path: 'user/common', name: 'AdminUserCommon', component: () => import('../views/admin/user/UserCommon.vue'), meta: { adminMenu: 'user' } },
        { path: 'user/roles', name: 'AdminUserRoles', component: () => import('../views/admin/user/RoleManage.vue'), meta: { adminMenu: 'user' } },
        { path: 'user/access', name: 'AdminUserAccess', component: () => import('../views/admin/user/AccessControl.vue'), meta: { adminMenu: 'user' } },
        // 데이터표준
        { path: 'standard', name: 'AdminStandard', component: () => import('../views/admin/standard/StandardCompliance.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/classification', name: 'AdminStandardClass', component: () => import('../views/admin/standard/Classification.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/quality-link', name: 'AdminStandardQLink', component: () => import('../views/admin/standard/QualityLink.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/quality-check', name: 'AdminStandardQCheck', component: () => import('../views/admin/standard/QualityCheck.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/grade', name: 'AdminStandardGrade', component: () => import('../views/admin/standard/GradeManage.vue'), meta: { adminMenu: 'standard' } },
        // 표준사전 관리
        { path: 'standard/words', name: 'AdminStdWords', component: () => import('../views/admin/standard/WordDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/domains', name: 'AdminStdDomains', component: () => import('../views/admin/standard/DomainDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/terms', name: 'AdminStdTerms', component: () => import('../views/admin/standard/TermDictionary.vue'), meta: { adminMenu: 'standard' } },
        { path: 'standard/codes', name: 'AdminStdCodes', component: () => import('../views/admin/standard/CodeDictionary.vue'), meta: { adminMenu: 'standard' } },
        // 데이터수집
        { path: 'collection', name: 'AdminCollection', component: () => import('../views/admin/collection/CollectionStrategy.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/dataset', name: 'AdminCollectionDataset', component: () => import('../views/admin/collection/DatasetConfig.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/ui', name: 'AdminCollectionUI', component: () => import('../views/admin/collection/CollectionUI.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/lightweight', name: 'AdminCollectionLight', component: () => import('../views/admin/collection/Lightweight.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/db-source', name: 'AdminCollectionDbSrc', component: () => import('../views/admin/collection/DbSource.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/migration', name: 'AdminCollectionMigration', component: () => import('../views/admin/collection/Migration.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/external', name: 'AdminCollectionExternal', component: () => import('../views/admin/collection/ExternalLink.vue'), meta: { adminMenu: 'collection' } },
        { path: 'collection/spatial', name: 'AdminCollectionSpatial', component: () => import('../views/admin/collection/SpatialCollect.vue'), meta: { adminMenu: 'collection' } },
        // 데이터정제
        { path: 'cleansing', name: 'AdminCleansing', component: () => import('../views/admin/cleansing/CleansingUI.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/anonymize', name: 'AdminCleansingAnon', component: () => import('../views/admin/cleansing/Anonymize.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/review', name: 'AdminCleansingReview', component: () => import('../views/admin/cleansing/TechReview.vue'), meta: { adminMenu: 'cleansing' } },
        { path: 'cleansing/transform', name: 'AdminCleansingTransform', component: () => import('../views/admin/cleansing/TransformManage.vue'), meta: { adminMenu: 'cleansing' } },
        // 데이터저장
        { path: 'storage', name: 'AdminStorage', component: () => import('../views/admin/storage/StorageManage.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/highspeed', name: 'AdminStorageHighspeed', component: () => import('../views/admin/storage/HighspeedDb.vue'), meta: { adminMenu: 'storage' } },
        { path: 'storage/unstructured', name: 'AdminStorageUnstruct', component: () => import('../views/admin/storage/Unstructured.vue'), meta: { adminMenu: 'storage' } },
        // 데이터유통
        { path: 'distribution', name: 'AdminDistribution', component: () => import('../views/admin/distribution/DistributionConfig.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/standard', name: 'AdminDistStandard', component: () => import('../views/admin/distribution/DistStandard.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/format', name: 'AdminDistFormat', component: () => import('../views/admin/distribution/DistFormat.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/ui', name: 'AdminDistUI', component: () => import('../views/admin/distribution/DistUI.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/fusion', name: 'AdminDistFusion', component: () => import('../views/admin/distribution/FusionModel.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/api', name: 'AdminDistApi', component: () => import('../views/admin/distribution/StandardApi.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/mcp', name: 'AdminDistMcp', component: () => import('../views/admin/distribution/McpLink.vue'), meta: { adminMenu: 'distribution' } },
        { path: 'distribution/stats', name: 'AdminDistStats', component: () => import('../views/admin/distribution/DistStats.vue'), meta: { adminMenu: 'distribution' } },
        // 운영관리
        { path: 'operation', name: 'AdminOperation', component: () => import('../views/admin/operation/HubStats.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/ai', name: 'AdminOperationAi', component: () => import('../views/admin/operation/AiMonitor.vue'), meta: { adminMenu: 'operation' } },
        { path: 'operation/optimize', name: 'AdminOperationOptimize', component: () => import('../views/admin/operation/Optimize.vue'), meta: { adminMenu: 'operation' } },
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

  // 관리자 포털 접근 체크
  if (to.meta.requiresAdmin && !authStore.canAccessAdmin) {
    return '/portal'
  }

  // 내부 사용자 전용 페이지 체크
  if (to.meta.requiresInternal && authStore.userRole === 'EXTERNAL') {
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
