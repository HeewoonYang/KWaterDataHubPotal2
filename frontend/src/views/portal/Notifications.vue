<template>
  <div class="notif-page">
    <nav class="breadcrumb">
      <router-link to="/portal/mypage">마이페이지</router-link>
      <span class="separator">&gt;</span>
      <span class="current">알림 수신</span>
    </nav>

    <div class="page-header">
      <div class="header-left">
        <h2>알림 수신</h2>
        <p>시스템, 데이터, 승인 관련 알림을 확인합니다.</p>
      </div>
      <div class="header-right">
        <button class="btn btn-sm btn-outline" @click="markAllRead" v-if="unreadCount > 0">
          <CheckOutlined /> 모두 읽음
        </button>
        <button class="btn btn-sm btn-icon" @click="showSettings = true" title="알림 설정">
          <SettingOutlined />
        </button>
      </div>
    </div>

    <!-- 탭 -->
    <div class="notif-tabs">
      <button :class="{ active: tab === 'all' }" @click="tab = 'all'">전체 ({{ notifications.length }})</button>
      <button :class="{ active: tab === 'unread' }" @click="tab = 'unread'">읽지 않음 ({{ unreadCount }})</button>
      <button :class="{ active: tab === 'system' }" @click="tab = 'system'">시스템</button>
      <button :class="{ active: tab === 'data' }" @click="tab = 'data'">데이터</button>
      <button :class="{ active: tab === 'approval' }" @click="tab = 'approval'">승인</button>
    </div>

    <!-- 알림 목록 -->
    <div class="notif-list">
      <div v-for="n in filteredNotifications" :key="n.id" class="notif-item" :class="{ unread: !n.is_read }" @click="readNotification(n)">
        <div class="notif-icon" :class="n.notification_type.toLowerCase()">
          <BellOutlined v-if="n.notification_type === 'SYSTEM'" />
          <DatabaseOutlined v-else-if="n.notification_type === 'DATA_CHANGE'" />
          <DownloadOutlined v-else-if="n.notification_type === 'DOWNLOAD'" />
          <CheckCircleOutlined v-else-if="n.notification_type === 'APPROVAL'" />
          <AlertOutlined v-else />
        </div>
        <div class="notif-body">
          <div class="notif-title">{{ n.title }}</div>
          <div class="notif-message" v-if="n.message">{{ n.message }}</div>
          <div class="notif-time">{{ formatTime(n.created_at) }}</div>
        </div>
        <div class="notif-badge" v-if="!n.is_read"></div>
      </div>
      <div v-if="filteredNotifications.length === 0" class="notif-empty">
        <BellOutlined class="empty-icon" />
        <p>알림이 없습니다.</p>
      </div>
    </div>

    <!-- 알림 설정 팝업 -->
    <AdminModal :visible="showSettings" title="알림 설정" size="md" @close="showSettings = false">
      <div class="settings-sections">
        <div class="settings-card" v-for="section in settingSections" :key="section.title">
          <div class="settings-card-header"><component :is="section.icon" /> {{ section.title }}</div>
          <div class="settings-items">
            <div v-for="item in section.items" :key="item.label" class="settings-item">
              <div class="settings-info">
                <span class="settings-label">{{ item.label }}</span>
                <span class="settings-desc">{{ item.desc }}</span>
              </div>
              <label class="toggle"><input type="checkbox" v-model="item.enabled" /><span class="slider"></span></label>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="saveSettings"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showSettings = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import {
  BellOutlined, SettingOutlined, CheckOutlined, SaveOutlined,
  DatabaseOutlined, DownloadOutlined, CheckCircleOutlined, AlertOutlined, SafetyOutlined,
} from '@ant-design/icons-vue'
import AdminModal from '../../components/AdminModal.vue'
import { message } from '../../utils/message'
import { userApi } from '../../api/portal.api'

const tab = ref('all')
const showSettings = ref(false)
const notifications = ref<any[]>([])

// 기본 알림 (API fallback)
const defaultNotifications = [
  { id: '1', notification_type: 'SYSTEM', title: '시스템 점검 안내 (03/28 02:00~06:00)', message: '정기 시스템 점검이 예정되어 있습니다.', is_read: false, created_at: '2026-03-25T14:00:00' },
  { id: '2', notification_type: 'DOWNLOAD', title: '다운로드가 완료되었습니다', message: '댐 수위 관측 데이터 CSV 파일이 준비되었습니다.', is_read: true, created_at: '2026-03-24T22:00:00' },
  { id: '3', notification_type: 'SYSTEM', title: '데이터허브 포털 오픈 안내', message: '데이터허브 포털이 정식 오픈되었습니다.', is_read: true, created_at: '2026-03-23T10:00:00' },
  { id: '4', notification_type: 'APPROVAL', title: '데이터 신청이 승인되었습니다', message: 'RWIS 도로기상 관측 데이터 CSV 다운로드가 승인되었습니다.', is_read: false, created_at: '2026-03-22T16:30:00' },
  { id: '5', notification_type: 'DATA_CHANGE', title: '즐겨찾기 데이터 업데이트', message: '수질 모니터링 센서 데이터가 갱신되었습니다.', is_read: false, created_at: '2026-03-22T09:00:00' },
  { id: '6', notification_type: 'APPROVAL', title: '데이터 신청이 반려되었습니다', message: '하천 유량 관측 API 접근 신청이 반려되었습니다. 사유: 접근 권한 등급 미달', is_read: true, created_at: '2026-03-20T11:00:00' },
]

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

const filteredNotifications = computed(() => {
  let list = notifications.value
  if (tab.value === 'unread') list = list.filter(n => !n.is_read)
  else if (tab.value === 'system') list = list.filter(n => n.notification_type === 'SYSTEM')
  else if (tab.value === 'data') list = list.filter(n => n.notification_type === 'DATA_CHANGE' || n.notification_type === 'DOWNLOAD')
  else if (tab.value === 'approval') list = list.filter(n => n.notification_type === 'APPROVAL')
  return list
})

function formatTime(dt: string): string {
  if (!dt) return ''
  const d = new Date(dt)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 3600) return Math.floor(diff / 60) + '분 전'
  if (diff < 86400) return Math.floor(diff / 3600) + '시간 전'
  if (diff < 604800) return Math.floor(diff / 86400) + '일 전'
  return dt.substring(0, 10)
}

async function readNotification(n: any) {
  if (!n.is_read) {
    n.is_read = true
    try { await userApi.markRead(n.id) } catch { /* ignore */ }
  }
}

async function markAllRead() {
  for (const n of notifications.value) {
    if (!n.is_read) {
      n.is_read = true
      try { await userApi.markRead(n.id) } catch { /* ignore */ }
    }
  }
}

// ── 알림 설정 ──
const settingSections = ref<{ title: string; icon: Component; items: { label: string; desc: string; enabled: boolean }[] }[]>([
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
])

async function saveSettings() {
  try {
    const settings: { notification_type: string; is_enabled: boolean; channel: string }[] = []
    const notiTypes = ['DATA_CHANGE', 'QUALITY', 'SYSTEM']
    for (let si = 0; si < 3; si++) {
      for (const item of settingSections.value[si].items) {
        settings.push({ notification_type: notiTypes[si], is_enabled: item.enabled, channel: 'WEB' })
      }
    }
    if (settingSections.value[3]) {
      settings.push({ notification_type: 'WEB', is_enabled: settingSections.value[3].items[0]?.enabled ?? true, channel: 'WEB' })
      settings.push({ notification_type: 'EMAIL', is_enabled: settingSections.value[3].items[1]?.enabled ?? false, channel: 'EMAIL' })
    }
    await userApi.updateNotificationSettings({ settings })
    message.success('알림 설정이 저장되었습니다.')
    showSettings.value = false
  } catch (e) {
    console.error('알림 설정 저장 실패:', e)
  }
}

onMounted(async () => {
  // 알림 목록 로드
  try {
    const res = await userApi.notifications({ page: 1, page_size: 50 })
    if (res.data?.items?.length) notifications.value = res.data.items
    else notifications.value = defaultNotifications
  } catch {
    notifications.value = defaultNotifications
  }

  // 알림 설정 로드
  try {
    const res = await userApi.notificationSettings()
    const settings = res.data?.data ?? res.data
    if (Array.isArray(settings) && settings.length > 0) {
      const typeToItem: Record<string, { section: number; item: number }> = {
        'DATA_CHANGE': { section: 0, item: 0 }, 'QUALITY': { section: 1, item: 0 }, 'SYSTEM': { section: 2, item: 0 },
        'WEB': { section: 3, item: 0 }, 'EMAIL': { section: 3, item: 1 },
      }
      for (const s of settings) {
        const m = typeToItem[s.notification_type]
        if (m && settingSections.value[m.section]?.items[m.item]) {
          settingSections.value[m.section].items[m.item].enabled = s.is_enabled
        }
      }
    }
  } catch { /* use defaults */ }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.notif-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb { font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; a { color: #999; text-decoration: none; &:hover { color: #0066CC; } } .separator { color: #ddd; } .current { color: #333; font-weight: 600; } }
.page-header { display: flex; justify-content: space-between; align-items: flex-start;
  .header-left { h2 { font-size: $font-size-xl; font-weight: 700; margin: 0 0 4px; } p { font-size: $font-size-sm; color: $text-muted; margin: 0; } }
  .header-right { display: flex; gap: 8px; }
}
.btn-icon { padding: 6px 8px; border: 1px solid $border-color; border-radius: $radius-md; background: #fff; cursor: pointer; font-size: 16px; color: #666; &:hover { border-color: $primary; color: $primary; } }

.notif-tabs { display: flex; gap: 4px; border-bottom: 2px solid #e8e8e8; padding-bottom: 0;
  button { padding: 8px 16px; border: none; background: none; font-size: 13px; color: #666; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px;
    &.active { color: $primary; border-bottom-color: $primary; font-weight: 600; }
    &:hover { color: $primary; }
  }
}

.notif-list { display: flex; flex-direction: column; }
.notif-item {
  display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; border-bottom: 1px solid #f0f0f0;
  cursor: pointer; transition: background 0.15s; border-radius: 4px;
  &:hover { background: #f9f9f9; }
  &.unread { background: #f0f7ff; &:hover { background: #e6f0fa; } }
}
.notif-icon {
  width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
  &.system { background: #e6f7ff; color: #0066CC; }
  &.data_change { background: #f6ffed; color: #28A745; }
  &.download { background: #fff7e6; color: #fa8c16; }
  &.approval { background: #f9f0ff; color: #9b59b6; }
}
.notif-body { flex: 1; min-width: 0;
  .notif-title { font-size: 13px; font-weight: 600; color: #333; margin-bottom: 2px; }
  .notif-message { font-size: 12px; color: #666; margin-bottom: 4px; }
  .notif-time { font-size: 11px; color: #bbb; }
}
.notif-badge { width: 8px; height: 8px; border-radius: 50%; background: $primary; flex-shrink: 0; margin-top: 6px; }
.notif-empty { text-align: center; padding: 60px 20px; color: #ccc; .empty-icon { font-size: 36px; margin-bottom: 8px; display: block; } p { font-size: 13px; } }

// 설정 팝업
.settings-sections { display: flex; flex-direction: column; gap: 12px; }
.settings-card { border: 1px solid #e8e8e8; border-radius: 6px; overflow: hidden; }
.settings-card-header { padding: 8px 14px; background: #4a6a8a; color: #fff; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.settings-items { padding: 4px 0; }
.settings-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; border-bottom: 1px solid #fafafa; &:last-child { border-bottom: none; } }
.settings-info { display: flex; flex-direction: column; gap: 1px; .settings-label { font-size: 12px; font-weight: 500; } .settings-desc { font-size: 11px; color: #999; } }
.toggle { position: relative; width: 40px; height: 22px; flex-shrink: 0;
  input { display: none; &:checked + .slider { background: $primary; &::before { transform: translateX(18px); } } }
  .slider { position: absolute; inset: 0; background: #ccc; border-radius: 22px; transition: 0.3s; cursor: pointer;
    &::before { content: ''; position: absolute; width: 16px; height: 16px; background: #fff; border-radius: 50%; left: 3px; top: 3px; transition: 0.3s; }
  }
}
</style>
