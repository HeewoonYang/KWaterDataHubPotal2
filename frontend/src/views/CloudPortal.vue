<template>
  <div class="cloud-portal">
    <!-- Header -->
    <header class="cloud-header">
      <div class="header-inner">
        <div class="header-left">
          <CloudServerOutlined class="logo-icon" />
          <span class="logo-text">K-water 클라우드 포털</span>
        </div>
        <div class="header-right">
          <BellOutlined class="header-action" />
          <span class="user-name">홍길동 님</span>
        </div>
      </div>
    </header>

    <!-- 대시보드 본문 -->
    <main class="cloud-content">
      <!-- 서비스 카드 -->
      <section class="service-section">
        <h2>클라우드 서비스</h2>
        <div class="service-cards">
          <div v-for="svc in services" :key="svc.label" class="service-card" :class="{ highlight: svc.highlight }" @click="svc.action?.()">
            <div class="svc-icon" :style="{ background: svc.color }">
              <component :is="svc.icon" />
            </div>
            <div class="svc-info">
              <h3>{{ svc.label }}</h3>
              <p>{{ svc.desc }}</p>
            </div>
            <RightOutlined class="svc-arrow" />
          </div>
        </div>
      </section>

      <!-- 하단 요약 -->
      <section class="summary-section">
        <div class="summary-cards">
          <div v-for="item in summaryItems" :key="item.label" class="summary-card">
            <component :is="item.icon" class="sum-icon" :style="{ color: item.color }" />
            <span class="sum-value">{{ item.value }}</span>
            <span class="sum-label">{{ item.label }}</span>
          </div>
        </div>
      </section>

      <!-- 최근 활동 -->
      <section class="activity-section">
        <h2>최근 활동</h2>
        <div class="activity-list">
          <div v-for="act in activities" :key="act.id" class="activity-item">
            <ClockCircleOutlined class="act-time-icon" />
            <span class="act-text">{{ act.text }}</span>
            <span class="act-time">{{ act.time }}</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { type Component } from 'vue'
import {
  CloudServerOutlined,
  BellOutlined,
  RightOutlined,
  DatabaseOutlined,
  DesktopOutlined,
  SafetyOutlined,
  ApiOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  CloudOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'

function openDataHubPortal() {
  const w = Math.round(window.screen.width * 0.8)
  const h = Math.round(window.screen.height * 0.8)
  const left = Math.round((window.screen.width - w) / 2)
  const top = Math.round((window.screen.height - h) / 2)
  window.open(
    '/portal/login',
    'datahub-portal',
    `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
  )
}

const services: { icon: Component; label: string; desc: string; color: string; highlight?: boolean; action?: () => void }[] = [
  { icon: DatabaseOutlined, label: '데이터허브포털', desc: '통합 데이터 검색/활용/유통', color: '#0066CC', highlight: true, action: openDataHubPortal },
  { icon: DesktopOutlined, label: '인프라 관리', desc: '클라우드 인프라 모니터링', color: '#28A745' },
  { icon: SafetyOutlined, label: '보안 센터', desc: '접근 통제 및 감사 관리', color: '#DC3545' },
  { icon: ApiOutlined, label: 'API 게이트웨이', desc: 'REST/SOAP API 관리', color: '#9b59b6' },
  { icon: AppstoreOutlined, label: '서비스 카탈로그', desc: '클라우드 서비스 목록', color: '#FFC107' },
  { icon: ThunderboltOutlined, label: 'AI/ML 플랫폼', desc: '머신러닝 모델 관리', color: '#17a2b8' },
]

const summaryItems: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: CloudOutlined, label: '클라우드 서비스', value: '12', color: '#0066CC' },
  { icon: DatabaseOutlined, label: '데이터셋', value: '1,247', color: '#28A745' },
  { icon: TeamOutlined, label: '활성 사용자', value: '156', color: '#9b59b6' },
  { icon: ApiOutlined, label: 'API 호출 (일)', value: '48,320', color: '#FFC107' },
]

const activities = [
  { id: 1, text: '데이터허브 - 댐 수위 관측 데이터 갱신 완료', time: '10분 전' },
  { id: 2, text: '인프라 - Kafka Cluster CPU 사용률 경고 (78%)', time: '25분 전' },
  { id: 3, text: '데이터허브 - 수질 모니터링 센서 데이터 수집 완료', time: '1시간 전' },
  { id: 4, text: 'API 게이트웨이 - 강수량 예측 API v2.1 배포', time: '2시간 전' },
  { id: 5, text: '보안 - 외부 사용자 계정 3건 승인 처리', time: '3시간 전' },
]
</script>

<style lang="scss" scoped>
@use '../styles/variables' as *;

.cloud-portal {
  min-height: 100vh;
  background: #f0f2f5;
}

.cloud-header {
  background: #001529;
  height: 56px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-xl;
}
.header-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  color: $white;
  .logo-icon { font-size: 22px; }
  .logo-text { font-size: $font-size-lg; font-weight: 700; }
}
.header-right {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  color: rgba($white, 0.8);
  .header-action { font-size: 18px; cursor: pointer; &:hover { color: $white; } }
  .user-name { font-size: $font-size-sm; }
}

.cloud-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  gap: $spacing-xl;
}

h2 {
  font-size: $font-size-lg;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: $spacing-lg;
}

// ===== Service Cards =====
.service-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-lg;
}
.service-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  cursor: pointer;
  transition: all $transition-fast;
  box-shadow: $shadow-sm;

  &:hover { box-shadow: $shadow-md; transform: translateY(-2px); }
  &.highlight { border-color: $primary; border-width: 2px; }
}
.svc-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: $white;
  flex-shrink: 0;
}
.svc-info {
  flex: 1;
  h3 { font-size: $font-size-md; font-weight: 600; margin-bottom: 2px; }
  p { font-size: $font-size-xs; color: $text-muted; }
}
.svc-arrow { color: $text-muted; font-size: 14px; }

// ===== Summary =====
.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-lg;
}
.summary-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  box-shadow: $shadow-sm;

  .sum-icon { font-size: 28px; }
  .sum-value { font-size: 22px; font-weight: 700; color: $text-primary; }
  .sum-label { font-size: $font-size-xs; color: $text-muted; }
}

// ===== Activity =====
.activity-section {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: $spacing-xl;
  box-shadow: $shadow-sm;

  h2 { margin-bottom: $spacing-md; }
}
.activity-list {
  display: flex;
  flex-direction: column;
}
.activity-item {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md 0;
  border-bottom: 1px solid $bg-light;
  &:last-child { border-bottom: none; }

  .act-time-icon { color: $text-muted; font-size: 14px; }
  .act-text { flex: 1; font-size: $font-size-sm; color: $text-primary; }
  .act-time { font-size: $font-size-xs; color: $text-muted; white-space: nowrap; }
}

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .service-cards { grid-template-columns: repeat(2, 1fr); }
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
