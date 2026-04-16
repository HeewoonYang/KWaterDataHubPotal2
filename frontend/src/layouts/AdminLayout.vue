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
        <!-- Tab Bar -->
        <div class="admin-tabs" v-if="tabStore.tabs.length > 0">
          <button
            v-show="canScrollLeft"
            class="tabs-nav-btn tabs-nav-left"
            title="왼쪽으로 스크롤"
            @click="scrollTabs(-1)"
          ><LeftOutlined /></button>
          <div
            class="tabs-scroll"
            ref="tabsScrollRef"
            :class="{ 'fade-left': canScrollLeft, 'fade-right': canScrollRight }"
            @wheel="onTabsWheel"
          >
            <div
              v-for="tab in tabStore.tabs"
              :key="tab.path"
              class="tab-item"
              :class="{ active: tab.path === route.path }"
              :ref="(el) => setTabRef(tab.path, el)"
              @click="onTabClick(tab.path)"
            >
              <span class="tab-label">{{ tab.label }}</span>
              <span
                v-if="tab.closable"
                class="tab-close"
                @click.stop="onTabClose(tab.path)"
              ><CloseOutlined /></span>
            </div>
          </div>
          <button
            v-show="canScrollRight"
            class="tabs-nav-btn tabs-nav-right"
            title="오른쪽으로 스크롤"
            @click="scrollTabs(1)"
          ><RightOutlined /></button>
          <div class="tabs-actions">
            <button class="tabs-action-btn" title="다른 탭 모두 닫기" @click="onCloseOthers"><MinusOutlined /></button>
          </div>
        </div>

        <!-- Breadcrumb -->
        <div class="breadcrumb">
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
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
  RightOutlined,
  LeftOutlined,
  LogoutOutlined,
  CloseOutlined,
  MinusOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useAdminTabsStore } from '../stores/adminTabs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const tabStore = useAdminTabsStore()
const sidebarCollapsed = ref(false)

const gnbMenus = [
  { label: '시스템관리', path: '/admin/system', key: 'system' },
  { label: '사용자관리', path: '/admin/user', key: 'user' },
  { label: '데이터표준', path: '/admin/standard', key: 'standard' },
  { label: '데이터수집', path: '/admin/collection', key: 'collection' },
  { label: '온톨로지', path: '/admin/ontology', key: 'ontology' },
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
  if (window.opener && !window.opener.closed) {
    // 팝업으로 열린 경우: 원래 사용자 포탈 창 포커스 후 팝업 닫기
    window.opener.focus()
    window.close()
  } else {
    // 직접 접속(/admin URL 직접 진입)인 경우: 같은 창에서 사용자 포탈로 이동
    router.push('/portal/dashboard')
  }
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
        { label: 'DR/백업 관리', path: '/admin/system/dr' },
        { label: '복구·PIT 대시보드', path: '/admin/system/dr-dashboard' },
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
        { label: '조직/사용자 관리', path: '/admin/user' },
        { label: '외부 사용자', path: '/admin/user/external' },
        { label: '조직사용자 동기화', path: '/admin/user/org-sync' },
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
        { label: '품질 대시보드', path: '/admin/standard/quality-dashboard' },
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
      label: '수집현황', expanded: true,
      children: [
        { label: '수집 대시보드', path: '/admin/collection' },
        { label: '도메인 수집현황', path: '/admin/collection/domain-detail' },
        { label: '수집 전략', path: '/admin/collection/strategy' },
        { label: '데이터셋 구성', path: '/admin/collection/dataset' },
      ]
    },
    {
      label: '데이터 품질/프로파일', expanded: false,
      children: [
        { label: '프로파일링/태깅', path: '/admin/collection/profiling' },
        { label: '품질 게이트웨이', path: '/admin/collection/quality-gate' },
      ]
    },
    {
      label: '수집 도구', expanded: false,
      children: [
        { label: '수집 UI', path: '/admin/collection/ui' },
        { label: '경량 수집', path: '/admin/collection/lightweight' },
      ]
    },
    {
      label: 'DB복제', expanded: false,
      children: [
        { label: '원본DB 설정', path: '/admin/collection/db-source' },
        { label: 'DB 탐색기', path: '/admin/collection/db-explorer' },
        { label: '마이그레이션', path: '/admin/collection/migration' },
        { label: '마이그레이션 결과·로그', path: '/admin/collection/migration-results' },
      ]
    },
    {
      label: '외부연계', expanded: false,
      children: [
        { label: '기관 연계', path: '/admin/collection/external' },
        { label: '공간정보 수집', path: '/admin/collection/spatial' },
      ]
    },
    {
      label: '비정형데이터', expanded: false,
      children: [
        { label: '비정형데이터관리', path: '/admin/collection/unstructured-data' },
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
    {
      label: '데이터패브릭', expanded: false,
      children: [
        { label: '패브릭 현황', path: '/admin/storage/fabric' },
        { label: 'LLM/T2SQL 설정', path: '/admin/storage/llm-config' },
        { label: 'GPU DB 데이터셋', path: '/admin/storage/gpu-datasets' },
        { label: 'MindsDB 연동', path: '/admin/storage/mindsdb' },
      ]
    },
    {
      label: '분석DB', expanded: false,
      children: [
        { label: '분석DB 데이터셋', path: '/admin/storage/analysis-datasets' },
        { label: '라이프사이클 정책', path: '/admin/storage/lifecycle-policy' },
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
      label: '통계/활용', expanded: false,
      children: [
        { label: '유통 통계', path: '/admin/distribution/stats' },
        { label: '활용도 대시보드', path: '/admin/distribution/usage' },
      ]
    },
  ]),
  '/admin/ontology': reactive([
    {
      label: '온톨로지 관리', expanded: true,
      children: [
        { label: '지식그래프/온톨로지', path: '/admin/ontology' },
        { label: '온톨로지 관리', path: '/admin/ontology/manage' },
      ]
    },
    {
      label: '메타 증강', expanded: false,
      children: [
        { label: '온톨로지 메타 증강', path: '/admin/ontology/augmentation' },
        { label: '비정형 문서 인제스트', path: '/admin/ontology/doc-ingestion' },
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
      label: '연계/모니터링', expanded: false,
      children: [
        { label: '연계 서비스', path: '/admin/operation/integration' },
        { label: 'App 모니터링', path: '/admin/operation/apm' },
        { label: '보안 모니터링', path: '/admin/operation/security' },
        { label: 'Data Event', path: '/admin/operation/events' },
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

// ===== 탭 네비게이션 =====
function getPageLabel(path: string): string {
  // sidebarConfig에서 라벨 찾기
  for (const key of Object.keys(sidebarConfig)) {
    for (const group of sidebarConfig[key]) {
      for (const item of group.children) {
        if (item.path === path) return item.label
      }
    }
  }
  // GNB에서 찾기 (대메뉴 기본 페이지)
  const gnb = gnbMenus.find(m => m.path === path)
  if (gnb) return gnb.label
  return '관리'
}

function onTabClick(path: string) {
  if (path !== route.path) {
    router.push(path)
  }
}

function onTabClose(path: string) {
  const nextPath = tabStore.removeTab(path)
  if (nextPath && nextPath !== route.path) {
    router.push(nextPath)
  }
}

function onCloseOthers() {
  const nextPath = tabStore.removeOthers(route.path)
  if (nextPath !== route.path) {
    router.push(nextPath)
  }
}

// 경로 변경 시 탭 자동 추가
watch(() => route.path, (newPath) => {
  if (newPath.startsWith('/admin')) {
    const label = getPageLabel(newPath)
    tabStore.addTab(newPath, label)
  }
}, { immediate: false })

// 초기화: 스토어 복원 + 현재 경로 탭 추가
onMounted(() => {
  tabStore.init()
  if (route.path.startsWith('/admin')) {
    const label = getPageLabel(route.path)
    tabStore.addTab(route.path, label)
  }
  nextTick(() => {
    attachScrollObserver()
    updateScrollState()
    scrollActiveTabIntoView()
  })
})

// ===== 탭바 가로 스크롤 처리 =====
const tabsScrollRef = ref<HTMLElement | null>(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const tabRefs = new Map<string, HTMLElement>()
let resizeObs: ResizeObserver | null = null

function setTabRef(path: string, el: any) {
  if (el) tabRefs.set(path, el as HTMLElement)
  else tabRefs.delete(path)
}

function updateScrollState() {
  const el = tabsScrollRef.value
  if (!el) {
    canScrollLeft.value = false
    canScrollRight.value = false
    return
  }
  const { scrollLeft, scrollWidth, clientWidth } = el
  canScrollLeft.value = scrollLeft > 1
  canScrollRight.value = scrollLeft + clientWidth < scrollWidth - 1
}

function scrollTabs(dir: number) {
  const el = tabsScrollRef.value
  if (!el) return
  el.scrollBy({ left: dir * Math.max(160, el.clientWidth * 0.6), behavior: 'smooth' })
}

function onTabsWheel(e: WheelEvent) {
  // 세로 휠을 가로 스크롤로 변환 (trackpad 가로 휠은 deltaX 로 그대로 처리)
  const el = tabsScrollRef.value
  if (!el) return
  if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
    el.scrollLeft += e.deltaY
    e.preventDefault()
  }
}

function scrollActiveTabIntoView() {
  const el = tabsScrollRef.value
  if (!el) return
  const tab = tabRefs.get(route.path)
  if (!tab) return
  const tabLeft = tab.offsetLeft
  const tabRight = tabLeft + tab.offsetWidth
  const viewLeft = el.scrollLeft
  const viewRight = viewLeft + el.clientWidth
  if (tabLeft < viewLeft) {
    el.scrollTo({ left: Math.max(0, tabLeft - 12), behavior: 'smooth' })
  } else if (tabRight > viewRight) {
    el.scrollTo({ left: tabRight - el.clientWidth + 12, behavior: 'smooth' })
  }
}

function attachScrollObserver() {
  const el = tabsScrollRef.value
  if (!el) return
  el.addEventListener('scroll', updateScrollState, { passive: true })
  if (typeof ResizeObserver !== 'undefined') {
    resizeObs = new ResizeObserver(() => updateScrollState())
    resizeObs.observe(el)
  }
  window.addEventListener('resize', updateScrollState)
}

onBeforeUnmount(() => {
  const el = tabsScrollRef.value
  if (el) el.removeEventListener('scroll', updateScrollState)
  resizeObs?.disconnect()
  window.removeEventListener('resize', updateScrollState)
})

// 탭 개수 변경 시 스크롤 상태 재계산
watch(() => tabStore.tabs.length, () => {
  nextTick(() => {
    updateScrollState()
    scrollActiveTabIntoView()
  })
})

// 라우트 변경 시 활성 탭을 가시 영역으로
watch(() => route.path, () => {
  nextTick(() => {
    updateScrollState()
    scrollActiveTabIntoView()
  })
})
</script>

<style lang="scss" scoped>
@use '../styles/variables' as *;

.admin-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
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

// ===== Tabs =====
.admin-tabs {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid $border-color;
  margin: (-$spacing-lg) (-$spacing-xl) $spacing-md;
  padding: 0 $spacing-md;
  height: 36px;
  flex-shrink: 0;
  position: sticky;
  top: -#{$spacing-lg};
  z-index: 10;
}

.tabs-scroll {
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  // flex 자식의 기본 min-width:auto 가 콘텐츠 크기로 결정돼 overflow-x가 동작하지 않는 문제 회피
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  gap: 2px;
  position: relative;
  // 좌우 끝 fade 마스크 — 가려진 탭이 더 있음을 시각적으로 암시
  &.fade-left {
    mask-image: linear-gradient(90deg, transparent 0, #000 24px);
    -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 24px);
  }
  &.fade-right {
    mask-image: linear-gradient(90deg, #000 calc(100% - 24px), transparent);
    -webkit-mask-image: linear-gradient(90deg, #000 calc(100% - 24px), transparent);
  }
  &.fade-left.fade-right {
    mask-image: linear-gradient(90deg, transparent 0, #000 24px, #000 calc(100% - 24px), transparent);
    -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 24px, #000 calc(100% - 24px), transparent);
  }

  &::-webkit-scrollbar {
    height: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: #c7c7c7;
    border-radius: 3px;

    &:hover { background: #a8a8a8; }
  }
}

.tabs-nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 26px;
  flex-shrink: 0;
  font-size: 11px;
  color: $text-secondary;
  background: #fafafa;
  border: 1px solid $border-color;
  border-radius: $radius-sm;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    color: $primary;
    border-color: $primary;
    background: #fff;
  }

  &.tabs-nav-left { margin-right: 4px; }
  &.tabs-nav-right { margin-left: 4px; }
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: $font-size-xs;
  color: $text-secondary;
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid transparent;
  border-bottom: 2px solid transparent;
  border-radius: $radius-sm $radius-sm 0 0;
  transition: all $transition-fast;
  position: relative;

  &:hover {
    color: $primary;
    background: rgba($primary, 0.04);
  }

  &.active {
    color: $primary;
    font-weight: 600;
    background: #fff;
    border-color: $border-color $border-color transparent;
    border-bottom-color: $primary;
  }
}

.tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  transition: all $transition-fast;
  color: #bbb;

  &:hover {
    background: #fde8e8;
    color: #DC3545;
  }
}

.tabs-actions {
  display: flex;
  align-items: center;
  margin-left: 4px;
  flex-shrink: 0;
}

.tabs-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: $radius-sm;
  font-size: 10px;
  color: $text-muted;
  background: none;
  border: 1px solid $border-color;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    color: $primary;
    border-color: $primary;
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
