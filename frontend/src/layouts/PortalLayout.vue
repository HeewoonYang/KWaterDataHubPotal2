<template>
  <div class="portal-layout">
    <!-- GNB Header -->
    <header class="portal-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/portal" class="logo">
            <CloudOutlined class="logo-icon" />
            <span class="logo-text">K-water 데이터허브포털</span>
          </router-link>
        </div>
        <nav class="gnb">
          <router-link
            v-for="menu in mainMenus"
            :key="menu.path"
            :to="menu.path"
            class="gnb-item"
            :class="{ active: isActive(menu.path) }"
          >
            {{ menu.label }}
          </router-link>
        </nav>
        <div class="header-right">
          <span class="role-badge">{{ authStore.roleLabel }}</span>
          <span class="user-name">{{ authStore.user?.name }} 님</span>
          <button v-if="authStore.canAccessAdmin" class="admin-link" @click="openAdminPortal">관리자포털</button>
          <button class="logout-btn" @click="handleLogout"><LogoutOutlined /></button>
        </div>
      </div>
    </header>

    <!-- Sub Navigation -->
    <div class="sub-nav" v-if="currentSubMenus.length > 0">
      <div class="sub-nav-inner">
        <router-link
          v-for="sub in currentSubMenus"
          :key="sub.path"
          :to="sub.path"
          class="sub-nav-item"
          :class="{ active: $route.path === sub.path }"
        >
          {{ sub.label }}
        </router-link>
      </div>
    </div>

    <!-- Content -->
    <main class="portal-content">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="portal-footer">
      <div class="footer-inner">
        <span>© 2026 K-water 한국수자원공사. All rights reserved.</span>
        <span class="footer-links">
          <a href="#">개인정보처리방침</a>
          <a href="#">이용약관</a>
          <router-link to="/portal/sitemap">사이트맵</router-link>
        </span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CloudOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 브라우저 탭/창 닫힐 때 로그아웃 처리
// sessionStorage는 탭 닫으면 자동 삭제됨 → 다음 접속 시 세션 키가 없으면 로그아웃 상태
onMounted(() => {
  const sessionKey = sessionStorage.getItem('datahub_session_active')
  if (!sessionKey && authStore.isAuthenticated) {
    // 이전 탭이 닫혀서 sessionStorage가 없는 경우 → localStorage 정리 후 로그인으로
    authStore.logout()
    router.push('/portal/login')
    return
  }
  sessionStorage.setItem('datahub_session_active', '1')
})

const allMenus = [
  { label: '대시보드', path: '/portal', roles: ['ADMIN', 'MANAGER', 'INTERNAL', 'EXTERNAL'] },
  { label: '데이터카탈로그', path: '/portal/catalog', roles: ['ADMIN', 'MANAGER', 'INTERNAL', 'EXTERNAL'] },
  { label: '데이터유통', path: '/portal/distribution', roles: ['ADMIN', 'MANAGER', 'INTERNAL', 'EXTERNAL'] },
  { label: 'AI검색', path: '/portal/ai-search', roles: ['ADMIN', 'MANAGER', 'INTERNAL'] },
  { label: '마이페이지', path: '/portal/mypage', roles: ['ADMIN', 'MANAGER', 'INTERNAL', 'EXTERNAL'] },
]

const mainMenus = computed(() =>
  allMenus.filter(m => authStore.userRole && m.roles.includes(authStore.userRole))
)

function handleLogout() {
  authStore.logout()
  router.push('/portal/login')
}

function openAdminPortal() {
  const w = Math.round(window.screen.width * 0.8)
  const h = Math.round(window.screen.height * 0.8)
  const left = Math.round((window.screen.width - w) / 2)
  const top = Math.round((window.screen.height - h) / 2)
  window.open(
    '/admin',
    'admin-portal',
    `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
  )
}

const subMenuMap: Record<string, { label: string; path: string }[]> = {
  '/portal': [
    { label: '대시보드', path: '/portal' },
    { label: '위젯 설정', path: '/portal/widget-settings' },
    { label: '시각화 갤러리 설정', path: '/portal/gallery' },
    { label: '위젯 관리', path: '/portal/widget-manage' },
    { label: '갤러리 콘텐츠 관리', path: '/portal/gallery-content' },
    { label: '실시간 계측DB', path: '/portal/realtime-measure' },
  ],
  '/portal/catalog': [
    { label: '카탈로그 탐색', path: '/portal/catalog' },
    { label: '데이터 검색', path: '/portal/catalog/search' },
  ],
  '/portal/distribution': [
    { label: '유통 데이터 목록', path: '/portal/distribution' },
    { label: '데이터 신청', path: '/portal/distribution/request' },
    { label: '데이터 다운로드', path: '/portal/distribution/download' },
  ],
  '/portal/mypage': [
    { label: '내 프로필', path: '/portal/mypage' },
    { label: '내 데이터', path: '/portal/mypage/data' },
    { label: '알림 설정', path: '/portal/mypage/notifications' },
  ],
}

// 대시보드 하위 경로 목록 (서브메뉴 유지용)
const dashboardPaths = ['/portal', '/portal/widget-settings', '/portal/widget-manage', '/portal/gallery', '/portal/gallery-content', '/portal/visualization', '/portal/visualization/gallery', '/portal/realtime-measure', '/portal/realtime-measure/office', '/portal/realtime-measure/site']

const currentSubMenus = computed(() => {
  const p = route.path.replace(/\/$/, '')
  // 대시보드 하위 경로인 경우 항상 /portal 서브메뉴 표시
  if (dashboardPaths.includes(p)) return subMenuMap['/portal'] || []
  const parts = p.split('/')
  const basePath = '/portal/' + (parts[2] || '')
  return subMenuMap[basePath] || []
})

function isActive(path: string): boolean {
  if (path === '/portal') return route.path === '/portal'
  return route.path.startsWith(path)
}
</script>

<style lang="scss" scoped>
@use '../styles/variables' as *;

.portal-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

// ===== Header =====
.portal-header {
  background: $white;
  border-bottom: 1px solid $border-color;
  height: $gnb-height;
  box-shadow: $shadow-sm;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 $spacing-xl;
}

.header-left {
  .logo {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    text-decoration: none;
    color: $primary;
    font-weight: 700;
    font-size: $font-size-lg;
    white-space: nowrap;

    .logo-icon {
      font-size: 22px;
    }
  }
}

.gnb {
  display: flex;
  align-items: center;
  margin-left: $spacing-xxl;
  gap: 2px;
  flex: 1;
}

.gnb-item {
  padding: 8px 16px;
  color: $text-secondary;
  font-size: $font-size-md;
  font-weight: 500;
  text-decoration: none;
  border-radius: $radius-md;
  transition: all $transition-fast;
  white-space: nowrap;

  &:hover {
    color: $primary;
    background: rgba($primary, 0.06);
    text-decoration: none;
  }

  &.active {
    color: $white;
    background: $gnb-active;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  white-space: nowrap;

  .user-name {
    font-size: $font-size-sm;
    color: $text-secondary;
  }

  .role-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba($primary, 0.1);
    color: $primary;
  }

  .admin-link {
    font-size: $font-size-sm;
    color: $white;
    background: $primary;
    padding: 5px 12px;
    border-radius: $radius-md;
    text-decoration: none;
    font-weight: 500;
    transition: background $transition-fast;

    &:hover {
      background: darken($primary, 10%);
      text-decoration: none;
    }
  }

  .logout-btn {
    background: none;
    color: $text-muted;
    font-size: 16px;
    padding: 4px;
    border-radius: $radius-sm;
    transition: color $transition-fast;
    &:hover { color: $error; }
  }
}

// ===== Sub Navigation =====
.sub-nav {
  background: $subnav-bg;
  height: $subnav-height;
}

.sub-nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 $spacing-xl;
  gap: 2px;
}

.sub-nav-item {
  padding: 6px 18px;
  color: rgba($white, 0.85);
  font-size: $font-size-sm;
  text-decoration: none;
  border-radius: $radius-sm;
  transition: all $transition-fast;

  &:hover {
    background: rgba($white, 0.15);
    color: $white;
    text-decoration: none;
  }

  &.active {
    background: $subnav-active;
    color: $white;
    font-weight: 600;
  }
}

// ===== Content =====
.portal-content {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: $spacing-xl;
}

// ===== Footer =====
.portal-footer {
  background: $secondary;
  color: rgba($white, 0.7);
  padding: $spacing-lg $spacing-xl;
  font-size: $font-size-xs;
  margin-top: auto;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-links {
  display: flex;
  gap: $spacing-lg;

  a {
    color: rgba($white, 0.7);
    text-decoration: none;
    &:hover { color: $white; }
  }
}

// ===== 반응형: 태블릿 =====
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .header-inner {
    padding: 0 $spacing-lg;
  }

  .gnb {
    margin-left: $spacing-lg;
    gap: 0;
  }

  .gnb-item {
    padding: 8px 10px;
    font-size: $font-size-sm;
  }

  .portal-content {
    padding: $spacing-lg;
  }

  .header-left .logo .logo-text {
    font-size: $font-size-md;
  }
}
</style>
