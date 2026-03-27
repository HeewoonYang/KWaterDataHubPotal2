<template>
  <div class="sitemap-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">사이트맵</span>
    </nav>

    <div class="page-header"><h2>사이트맵</h2><p>데이터허브 포털 전체 메뉴를 한눈에 확인합니다.</p></div>
    <div class="sitemap-grid">
      <div v-for="group in sitemapData" :key="group.title" class="sitemap-group">
        <div class="group-header" :style="{ background: group.color }"><component :is="group.icon" /> {{ group.title }}</div>
        <ul class="group-items">
          <li v-for="item in group.items" :key="item.label">
            <router-link :to="item.path">{{ item.label }}</router-link>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { type Component } from 'vue'
import { HomeOutlined, DatabaseOutlined, BarChartOutlined, SwapOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
const authStore = useAuthStore()
const allSitemap: { title: string; icon: Component; color: string; roles: string[]; items: { label: string; path: string }[] }[] = [
  { title: '대시보드', icon: HomeOutlined, color: '#0066CC', roles: ['ADMIN','MANAGER','INTERNAL','EXTERNAL'], items: [
    { label: '대시보드', path: '/portal' },
    { label: '위젯 설정', path: '/portal/widget-settings' },
    { label: '시각화 갤러리 설정', path: '/portal/gallery' },
    { label: '위젯 관리', path: '/portal/widget-manage' },
    { label: '갤러리 콘텐츠 관리', path: '/portal/gallery-content' },
  ]},
  { title: '데이터 카탈로그', icon: DatabaseOutlined, color: '#28A745', roles: ['ADMIN','MANAGER','INTERNAL','EXTERNAL'], items: [
    { label: '카탈로그 탐색', path: '/portal/catalog' },
    { label: '데이터 검색', path: '/portal/catalog/search' },
  ]},
  { title: '데이터 시각화', icon: BarChartOutlined, color: '#9b59b6', roles: ['ADMIN','MANAGER','INTERNAL'], items: [
    { label: 'D&D 시각화', path: '/portal/visualization' },
    { label: '차트 갤러리', path: '/portal/visualization/gallery' },
  ]},
  { title: '데이터 유통', icon: SwapOutlined, color: '#FFC107', roles: ['ADMIN','MANAGER','INTERNAL','EXTERNAL'], items: [
    { label: '유통 데이터 목록', path: '/portal/distribution' },
    { label: '데이터 신청', path: '/portal/distribution/request' },
    { label: '데이터 다운로드', path: '/portal/distribution/download' },
  ]},
  { title: 'AI 검색', icon: RobotOutlined, color: '#17a2b8', roles: ['ADMIN','MANAGER','INTERNAL'], items: [
    { label: 'AI 자연어 검색', path: '/portal/ai-search' },
  ]},
  { title: '마이페이지', icon: UserOutlined, color: '#DC3545', roles: ['ADMIN','MANAGER','INTERNAL','EXTERNAL'], items: [
    { label: '내 프로필', path: '/portal/mypage' },
    { label: '내 데이터', path: '/portal/mypage/data' },
    { label: '알림 설정', path: '/portal/mypage/notifications' },
  ]},
]
const sitemapData = allSitemap.filter(g => authStore.userRole && g.roles.includes(authStore.userRole))
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.sitemap-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.sitemap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: $spacing-lg; }
.sitemap-group { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; overflow: hidden; box-shadow: $shadow-sm; }
.group-header { padding: $spacing-md $spacing-lg; color: $white; font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: $spacing-sm; }
.group-items { padding: $spacing-md 0;
  li { padding: 6px $spacing-xl;
    a { font-size: $font-size-sm; color: $text-secondary; text-decoration: none; display: block; padding: 4px 0; &:hover { color: $primary; } }
  }
}
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) { .sitemap-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
