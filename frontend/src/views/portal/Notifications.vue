<template>
  <div class="notif-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">알림 설정</span>
    </nav>

    <div class="page-header"><h2>알림 설정</h2><p>데이터 변경, 품질, 시스템 알림 구독을 관리합니다.</p></div>
    <div class="notif-sections">
      <div class="notif-card" v-for="section in sections" :key="section.title">
        <div class="notif-card-header"><component :is="section.icon" /> {{ section.title }}</div>
        <div class="notif-items">
          <div v-for="item in section.items" :key="item.label" class="notif-item">
            <div class="notif-info"><span class="notif-label">{{ item.label }}</span><span class="notif-desc">{{ item.desc }}</span></div>
            <label class="toggle"><input type="checkbox" :checked="item.enabled" /><span class="slider"></span></label>
          </div>
        </div>
      </div>
    </div>
    <div class="notif-footer"><button class="btn btn-primary" @click="saveSettings"><SaveOutlined /> 설정 저장</button></div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { DatabaseOutlined, SafetyOutlined, BellOutlined, SettingOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { userApi } from '../../api/portal.api'

// Icon mapping for sections from API
const iconMap: Record<string, Component> = {
  'data': DatabaseOutlined,
  'quality': SafetyOutlined,
  'system': SettingOutlined,
  'channel': BellOutlined,
}

// Fallback mock data
const defaultSections: { title: string; icon: Component; items: { label: string; desc: string; enabled: boolean }[] }[] = [
  { title: '데이터 변경 알림', icon: DatabaseOutlined, items: [
    { label: '즐겨찾기 데이터 업데이트', desc: '즐겨찾기에 등록한 데이터셋이 갱신되면 알림', enabled: true },
    { label: '신규 데이터셋 등록', desc: '관심 분류에 새 데이터셋이 등록되면 알림', enabled: true },
    { label: '데이터 스키마 변경', desc: '이용 중인 데이터셋의 컬럼 구조가 변경되면 알림', enabled: false },
  ]},
  { title: '품질 알림', icon: SafetyOutlined, items: [
    { label: '품질 진단 결과', desc: '정기 품질 진단 결과 알림', enabled: true },
    { label: '이상값 탐지', desc: '이용 데이터에서 이상값이 탐지되면 알림', enabled: false },
    { label: '수집 오류', desc: '구독 중인 파이프라인에 수집 오류 발생 시 알림', enabled: true },
  ]},
  { title: '시스템 알림', icon: SettingOutlined, items: [
    { label: '시스템 점검 공지', desc: '정기/비정기 시스템 점검 사전 알림', enabled: true },
    { label: '신청 승인/반려', desc: '데이터 이용 신청 처리 결과 알림', enabled: true },
    { label: '권한 만료 예정', desc: '데이터 이용 권한 만료 7일 전 알림', enabled: true },
  ]},
  { title: '알림 수신 방식', icon: BellOutlined, items: [
    { label: '포털 내 알림', desc: '포털 상단 알림 아이콘으로 수신', enabled: true },
    { label: '이메일 알림', desc: '등록된 이메일로 알림 발송', enabled: false },
  ]},
]

const sections = ref(defaultSections)

onMounted(async () => {
  try {
    const res = await userApi.notificationSettings()
    if (res.data?.data) {
      sections.value = res.data.data.map((s: any) => ({
        ...s,
        icon: iconMap[s.iconKey] || DatabaseOutlined,
      }))
    }
  } catch (e) {
    console.error('알림 설정 조회 실패:', e)
  }
})

async function saveSettings() {
  try {
    await userApi.updateNotificationSettings(sections.value)
  } catch (e) {
    console.error('알림 설정 저장 실패:', e)
  }
}
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.notif-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.notif-sections { display: flex; flex-direction: column; gap: $spacing-lg; }
.notif-card { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden; }
.notif-card-header { padding: $spacing-md $spacing-lg; background: #4a6a8a; color: $white; font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: $spacing-sm; }
.notif-items { padding: $spacing-sm 0; }
.notif-item { display: flex; align-items: center; justify-content: space-between; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $bg-light; &:last-child { border-bottom: none; } }
.notif-info { display: flex; flex-direction: column; gap: 2px; }
.notif-label { font-size: $font-size-sm; font-weight: 500; color: $text-primary; }
.notif-desc { font-size: $font-size-xs; color: $text-muted; }
.toggle { position: relative; width: 44px; height: 24px; flex-shrink: 0;
  input { display: none; &:checked + .slider { background: $primary; &::before { transform: translateX(20px); } } }
  .slider { position: absolute; inset: 0; background: #ccc; border-radius: 24px; transition: 0.3s; cursor: pointer;
    &::before { content: ''; position: absolute; width: 18px; height: 18px; background: $white; border-radius: 50%; left: 3px; top: 3px; transition: 0.3s; }
  }
}
.notif-footer { display: flex; justify-content: flex-end; }
</style>
