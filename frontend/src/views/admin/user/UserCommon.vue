<template>
  <div class="admin-page">
    <div class="page-header"><h2>사용자 공통</h2><p class="page-desc">비밀번호 정책, 세션 관리 등 사용자 공통 설정을 관리합니다.</p></div>
    <div class="settings-cards">
      <div class="setting-card" v-for="s in settings" :key="s.title">
        <div class="setting-header"><component :is="s.icon" /> {{ s.title }}</div>
        <div class="setting-items">
          <div v-for="item in s.items" :key="item.label" class="setting-item">
            <span class="setting-label">{{ item.label }}</span>
            <span class="setting-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { LockOutlined, ClockCircleOutlined, SafetyOutlined, MailOutlined } from '@ant-design/icons-vue'
import { adminUserApi } from '../../../api/admin.api'

const settings = ref<{ title: string; icon: Component; items: { label: string; value: string }[] }[]>([
  { title: '비밀번호 정책', icon: LockOutlined, items: [
    { label: '최소 길이', value: '8자 이상' },
    { label: '복잡도', value: '대/소문자+숫자+특수문자' },
    { label: '변경 주기', value: '90일' },
    { label: '재사용 제한', value: '최근 5개' },
  ]},
  { title: '세션 관리', icon: ClockCircleOutlined, items: [
    { label: '세션 타임아웃', value: '30분' },
    { label: '동시 접속', value: '3개 디바이스' },
    { label: '자동 로그아웃', value: '활성' },
  ]},
  { title: '보안 설정', icon: SafetyOutlined, items: [
    { label: '로그인 실패 잠금', value: '5회 시 30분 잠금' },
    { label: 'IP 접근 제어', value: '활성' },
    { label: '2단계 인증', value: '선택적' },
  ]},
  { title: '알림 설정', icon: MailOutlined, items: [
    { label: '가입 승인 알림', value: '이메일+포털' },
    { label: '비밀번호 만료 알림', value: '7일 전' },
    { label: '계정 만료 알림', value: '14일 전' },
  ]},
])

onMounted(async () => {
  try {
    await adminUserApi.users()
    // 사용자 공통 설정은 정적 설정 화면, API 연동은 추후 확장
  } catch (e) {
    console.warn('UserCommon: API call failed, using mock data', e)
  }
})
</script>
<style lang="scss" scoped>
@use '../../../styles/variables' as *;
.admin-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } .page-desc { font-size: $font-size-sm; color: $text-muted; } }
.settings-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: $spacing-lg; }
.setting-card { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden; }
.setting-header { padding: $spacing-md $spacing-lg; background: #4a6a8a; color: $white; font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: $spacing-sm; }
.setting-items { padding: $spacing-sm 0; }
.setting-item { display: flex; justify-content: space-between; padding: $spacing-sm $spacing-lg; border-bottom: 1px solid #f5f5f5; &:last-child { border-bottom: none; } }
.setting-label { font-size: $font-size-sm; color: $text-secondary; }
.setting-value { font-size: $font-size-sm; font-weight: 600; color: $text-primary; }
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) { .settings-cards { grid-template-columns: 1fr; } }
</style>
