<template>
  <div class="admin-layout">
    <!-- Admin GNB Header -->
    <header class="admin-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/admin" class="logo">
            <SettingOutlined class="logo-icon" />
            <span class="logo-text">데이터허브포털관리</span>
          </router-link>
        </div>
        <nav class="admin-gnb">
          <template v-for="menu in gnbMenus" :key="menu.path">
            <router-link
              v-if="isMenuAccessible(menu.key)"
              :to="menu.path"
              class="gnb-item"
              :class="{ active: isGnbActive(menu.path) }"
            >
              {{ menu.label }}
            </router-link>
          </template>
        </nav>
        <div class="header-right">
          <span class="user-info">
            <span class="user-role">{{ authStore.roleLabel }}</span>
            <span class="user-name">{{ authStore.user?.name }}</span>
          </span>
          <button class="portal-link" @click="goBackToPortal">사용자포털</button>
          <button class="logout-btn" @click="handleLogout"><LogoutOutlined /></button>
        </div>
      </div>
    </header>

    <!-- Body: Sidebar + Content -->
    <div class="admin-body">
      <!-- Sidebar -->
      <aside class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <MenuUnfoldOutlined v-if="sidebarCollapsed" />
          <MenuFoldOutlined v-else />
        </div>
        <nav class="sidebar-nav" v-show="!sidebarCollapsed">
          <div
            v-for="group in currentSidebarMenus"
            :key="group.label"
            class="menu-group"
          >
            <div
              class="menu-group-header"
              :class="{ expanded: group.expanded }"
              @click="toggleGroup(group)"
            >
              <span>{{ group.label }}</span>
              <DownOutlined v-if="group.expanded" class="arrow" />
              <RightOutlined v-else class="arrow" />
            </div>
            <ul class="menu-items" v-show="group.expanded">
              <li
                v-for="item in group.children"
                :key="item.path"
                class="menu-item"
                :class="{ active: $route.path === item.path }"
              >
                <router-link :to="item.path">{{ item.label }}</router-link>
              </li>
            </ul>
          </div>
        </nav>
      </aside>

      <!-- Content Area -->
      <main class="admin-content">
        <!-- Breadcrumb -->
        <div class="breadcrumb">
          <span>홈</span>
          <span class="sep">></span>
          <span v-for="(crumb, i) in breadcrumbs" :key="i">
            <span :class="{ current: i === breadcrumbs.length - 1 }">{{ crumb }}</span>
            <span class="sep" v-if="i < breadcrumbs.length - 1">></span>
          </span>
        </div>

        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
  RightOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const sidebarCollapsed = ref(false)

const gnbMenus = [
  { label: '시스템관리', path: '/admin/system', key: 'system' },
  { label: '사용자관리', path: '/admin/user', key: 'user' },
  { label: '데이터표준', path: '/admin/standard', key: 'standard' },
  { label: '데이터수집', path: '/admin/collection', key: 'collection' },
  { label: '데이터정제', path: '/admin/cleansing', key: 'cleansing' },
  { label: '데이터저장', path: '/admin/storage', key: 'storage' },
  { label: '데이터유통', path: '/admin/distribution', key: 'distribution' },
  { label: '운영관리', path: '/admin/operation', key: 'operation' },
]

function isMenuAccessible(key: string): boolean {
  const access = authStore.adminMenuAccess as Record<string, boolean>
  return access[key] !== false
}

function handleLogout() {
  authStore.logout()
  router.push('/portal/login')
}

function goBackToPortal() {
  // 관리자 포털 팝업 닫기 (사용자포털 팝업은 별도로 열려 있음)
  window.close()
}

interface MenuItem {
  label: string
  path: string
}

interface MenuGroup {
  label: string
  expanded: boolean
  children: MenuItem[]
}

const sidebarConfig: Record<string, MenuGroup[]> = {
  '/admin/system': reactive([
    {
      label: '인프라관리', expanded: true,
      children: [
        { label: '에코시스템 총괄', path: '/admin/system' },
        { label: '클라우드 구성', path: '/admin/system/cloud' },
        { label: 'DR/백업 관리', path: '/admin/system/dr' },
        { label: '패키지 검증', path: '/admin/system/package' },
      ]
    },
    {
      label: '연계관리', expanded: false,
      children: [
        { label: '표준 인터페이스', path: '/admin/system/interface' },
        { label: '이기종 통합', path: '/admin/system/integration' },
        { label: 'DMZ 연계', path: '/admin/system/dmz' },
      ]
    },
  ]),
  '/admin/user': reactive([
    {
      label: '계정관리', expanded: true,
      children: [
        { label: '내부 사용자', path: '/admin/user' },
        { label: '외부 사용자', path: '/admin/user/external' },
        { label: '사용자 공통', path: '/admin/user/common' },
      ]
    },
    {
      label: '권한관리', expanded: false,
      children: [
        { label: '역할 관리', path: '/admin/user/roles' },
        { label: '데이터 접근제어', path: '/admin/user/access' },
      ]
    },
  ]),
  '/admin/standard': reactive([
    {
      label: '표준관리', expanded: true,
      children: [
        { label: '표준 준수', path: '/admin/standard' },
        { label: '분류 등록', path: '/admin/standard/classification' },
      ]
    },
    {
      label: '표준사전', expanded: false,
      children: [
        { label: '단어사전', path: '/admin/standard/words' },
        { label: '도메인사전', path: '/admin/standard/domains' },
        { label: '용어사전', path: '/admin/standard/terms' },
        { label: '코드사전', path: '/admin/standard/codes' },
      ]
    },
    {
      label: '품질관리', expanded: false,
      children: [
        { label: '분류체계 연동', path: '/admin/standard/quality-link' },
        { label: '품질 검증', path: '/admin/standard/quality-check' },
      ]
    },
    {
      label: '등급관리', expanded: false,
      children: [
        { label: '등급 분류', path: '/admin/standard/grade' },
      ]
    },
  ]),
  '/admin/collection': reactive([
    {
      label: '수집관리', expanded: true,
      children: [
        { label: '수집 전략', path: '/admin/collection' },
        { label: '데이터셋 구성', path: '/admin/collection/dataset' },
        { label: '수집 UI', path: '/admin/collection/ui' },
        { label: '경량 수집', path: '/admin/collection/lightweight' },
      ]
    },
    {
      label: 'DB복제', expanded: false,
      children: [
        { label: '원본DB 설정', path: '/admin/collection/db-source' },
        { label: '마이그레이션', path: '/admin/collection/migration' },
      ]
    },
    {
      label: '외부연계', expanded: false,
      children: [
        { label: '기관 연계', path: '/admin/collection/external' },
        { label: '공간정보 수집', path: '/admin/collection/spatial' },
      ]
    },
  ]),
  '/admin/cleansing': reactive([
    {
      label: '정제관리', expanded: true,
      children: [
        { label: '정제 UI', path: '/admin/cleansing' },
        { label: '비식별화', path: '/admin/cleansing/anonymize' },
        { label: '기술 검토', path: '/admin/cleansing/review' },
      ]
    },
    {
      label: '모델링', expanded: false,
      children: [
        { label: '변환 관리', path: '/admin/cleansing/transform' },
      ]
    },
  ]),
  '/admin/storage': reactive([
    {
      label: '저장소관리', expanded: true,
      children: [
        { label: '저장소 구분', path: '/admin/storage' },
        { label: '고속처리 DB', path: '/admin/storage/highspeed' },
        { label: '비정형 저장소', path: '/admin/storage/unstructured' },
      ]
    },
  ]),
  '/admin/distribution': reactive([
    {
      label: '유통관리', expanded: true,
      children: [
        { label: '유통 구성', path: '/admin/distribution' },
        { label: '표준화 관리', path: '/admin/distribution/standard' },
        { label: '유통 포맷', path: '/admin/distribution/format' },
        { label: '유통 UI', path: '/admin/distribution/ui' },
      ]
    },
    {
      label: '융합/API', expanded: false,
      children: [
        { label: '융합 모델', path: '/admin/distribution/fusion' },
        { label: '표준 API', path: '/admin/distribution/api' },
        { label: 'MCP 연동', path: '/admin/distribution/mcp' },
      ]
    },
    {
      label: '통계', expanded: false,
      children: [
        { label: '유통 통계', path: '/admin/distribution/stats' },
      ]
    },
  ]),
  '/admin/operation': reactive([
    {
      label: '통계/리포트', expanded: true,
      children: [
        { label: '허브 통계', path: '/admin/operation' },
      ]
    },
    {
      label: 'AI모니터링', expanded: false,
      children: [
        { label: 'AI 현황', path: '/admin/operation/ai' },
      ]
    },
    {
      label: '관리최적화', expanded: false,
      children: [
        { label: '기능 검토', path: '/admin/operation/optimize' },
      ]
    },
  ]),
}

const currentSidebarMenus = computed(() => {
  return sidebarConfig['/admin/' + (route.path.split('/')[2] || 'system')] || sidebarConfig['/admin/system']
})

const breadcrumbs = computed(() => {
  const labels: string[] = []
  const gnb = gnbMenus.find(m => route.path.startsWith(m.path))
  if (gnb) labels.push(gnb.label)

  const sidebar = currentSidebarMenus.value
  for (const group of sidebar) {
    for (const item of group.children) {
      if (item.path === route.path) {
        labels.push(group.label)
        labels.push(item.label)
        return labels
      }
    }
  }
  return labels
})

function isGnbActive(path: string): boolean {
  return route.path.startsWith(path)
}

function toggleGroup(group: MenuGroup) {
  group.expanded = !group.expanded
}
</script>

<style lang="scss" scoped>
@use '../styles/variables' as *;

.admin-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

// ===== Header =====
.admin-header {
  background: $admin-header-bg;
  height: $admin-header-height;
  flex-shrink: 0;
  z-index: 100;
}

.header-inner {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 $spacing-lg;
}

.header-left {
  .logo {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    text-decoration: none;
    color: $white;
    font-weight: 700;
    font-size: $font-size-md;
    white-space: nowrap;

    .logo-icon { font-size: 20px; }
  }
}

.admin-gnb {
  display: flex;
  align-items: center;
  margin-left: $spacing-xl;
  gap: 1px;
  flex: 1;
}

.gnb-item {
  padding: 6px 14px;
  color: rgba($white, 0.7);
  font-size: $font-size-sm;
  text-decoration: none;
  border-radius: $radius-sm;
  transition: all $transition-fast;
  white-space: nowrap;

  &:hover {
    color: $white;
    background: rgba($white, 0.1);
    text-decoration: none;
  }

  &.active {
    color: $white;
    background: rgba($white, 0.2);
    font-weight: 600;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  white-space: nowrap;

  .user-info {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    color: rgba($white, 0.8);
    font-size: $font-size-sm;
  }

  .user-role {
    background: rgba($white, 0.15);
    padding: 2px 8px;
    border-radius: 10px;
    font-size: $font-size-xs;
  }

  .portal-link {
    font-size: $font-size-xs;
    color: $white;
    background: $primary;
    padding: 4px 10px;
    border-radius: $radius-sm;
    text-decoration: none;
    &:hover {
      background: lighten($primary, 8%);
      text-decoration: none;
    }
  }

  .logout-btn {
    background: none;
    color: rgba($white, 0.6);
    font-size: 16px;
    padding: 4px;
    border-radius: $radius-sm;
    transition: color $transition-fast;
    &:hover { color: $white; }
  }
}

// ===== Body =====
.admin-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// ===== Sidebar =====
.admin-sidebar {
  width: $sidebar-width;
  background: $sidebar-bg;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width $transition-normal;
  overflow-y: auto;

  &.collapsed {
    width: 28px;
  }
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  cursor: pointer;
  color: $text-muted;
  font-size: 11px;
  border-bottom: 1px solid $border-color;
  flex-shrink: 0;

  &:hover { background: $sidebar-item-hover; }
}

.sidebar-nav {
  padding: $spacing-sm 0;
}

.menu-group {
  margin-bottom: 2px;
}

.menu-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px $spacing-lg;
  background: $sidebar-header-bg;
  color: $white;
  font-size: $font-size-sm;
  font-weight: 600;
  cursor: pointer;
  transition: background $transition-fast;

  &:hover { background: $sidebar-header-hover; }

  .arrow {
    font-size: 11px;
  }
}

.menu-items {
  background: $sidebar-sub-bg;
}

.menu-item {
  a {
    display: block;
    padding: 8px $spacing-lg 8px $spacing-xl;
    font-size: $font-size-sm;
    color: $text-secondary;
    text-decoration: none;
    transition: all $transition-fast;

    &:hover {
      background: $sidebar-item-hover;
      color: $primary;
    }
  }

  &.active a {
    background: $sidebar-item-active;
    color: $primary;
    font-weight: 600;
  }
}

// ===== Content =====
.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-lg $spacing-xl;
  background: $bg-light;
}

.breadcrumb {
  font-size: $font-size-xs;
  color: $text-muted;
  margin-bottom: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-xs;

  .sep { color: #ccc; }
  .current { color: $text-primary; font-weight: 600; }
}

// ===== 반응형: 태블릿 =====
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .admin-sidebar {
    width: 180px;
  }

  .gnb-item {
    padding: 6px 8px;
    font-size: $font-size-xs;
  }

  .admin-content {
    padding: $spacing-md $spacing-lg;
  }

  .header-left .logo .logo-text {
    font-size: $font-size-sm;
  }
}
</style>
