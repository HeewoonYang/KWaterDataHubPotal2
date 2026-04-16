<template>
  <div class="admin-page">
    <div class="page-header"><h2>Data Event 모니터링</h2><p class="page-desc">데이터 이벤트 감시, 알람 현황 및 SOP 연동 상태를 관리합니다.</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-value">{{ summary.total }}</div><div class="stat-label">전체 이벤트</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#fa8c16">{{ summary.active }}</div><div class="stat-label">미해결</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#DC3545">{{ summary.critical }}</div><div class="stat-label">긴급</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#28A745">{{ summary.resolved }}</div><div class="stat-label">해결</div></div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">최근 데이터 이벤트</div>
        <div v-for="evt in events" :key="evt.id" class="event-item" :class="{ resolved: evt.is_resolved }">
          <span class="evt-severity" :class="(evt.severity||'INFO').toLowerCase()">{{ evt.severity }}</span>
          <div class="evt-body">
            <div class="evt-title">{{ evt.title }}</div>
            <div class="evt-desc">{{ evt.description || '-' }}</div>
            <div class="evt-time">{{ evt.occurred_at }} {{ evt.is_resolved ? '(해결: ' + evt.resolved_at + ')' : '' }}</div>
          </div>
        </div>
        <div v-if="events.length === 0" style="padding:20px;text-align:center;color:#999;">이벤트 없음</div>
      </div>
      <div class="card">
        <div class="card-title">SOP 연동 현황</div>
        <table class="data-table">
          <thead><tr><th>SOP명</th><th>상태</th><th>최종 트리거</th></tr></thead>
          <tbody>
            <tr v-for="sop in sopList" :key="sop.name">
              <td><strong>{{ sop.name }}</strong></td>
              <td><span class="status-badge" :class="sop.status === '정상' ? 'active' : 'standby'">{{ sop.status }}</span></td>
              <td>{{ sop.last_triggered }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminOperationApi } from '../../../api/admin.api'
const events = ref<any[]>([])
const sopList = ref<any[]>([])
const summary = ref<any>({ total: 0, active: 0, critical: 0, resolved: 0 })
onMounted(async () => {
  try {
    const r = await adminOperationApi.dataEvents()
    if (r.data?.data) { events.value = r.data.data.events; summary.value = r.data.data.summary; sopList.value = r.data.data.sop_status }
  } catch {}
})
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .stat-value { font-size: 28px; font-weight: 800; } .stat-label { font-size: 12px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; } }
.event-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; &.resolved { opacity: 0.5; } }
.evt-severity { padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 700; white-space: nowrap; height: fit-content;
  &.critical { background: #fff1f0; color: #DC3545; } &.high { background: #fff7e6; color: #fa8c16; } &.medium { background: #e6f7ff; color: #0066CC; } &.info { background: #f6ffed; color: #28A745; } &.low { background: #f5f5f5; color: #999; }
}
.evt-body { .evt-title { font-size: 12px; font-weight: 600; } .evt-desc { font-size: 11px; color: #666; } .evt-time { font-size: 10px; color: #999; margin-top: 2px; } }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.standby { background: #f0f5ff; color: #0066CC; } }
</style>
