<template>
  <div class="admin-page">
    <div class="page-header"><h2>연계 서비스 모니터링</h2><p class="page-desc">AI API, MCP, DT API, A2A 등 연계 서비스 현황을 모니터링합니다.</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-value">{{ summary.total }}</div><div class="stat-label">전체 서비스</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#28A745">{{ summary.active }}</div><div class="stat-label">활성</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#0066CC">{{ summary.api_calls_7d }}</div><div class="stat-label">7일 API 호출</div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">연계 서비스 <strong>{{ services.length }}</strong>건</span></div>
      <table class="data-table">
        <thead><tr><th>서비스명</th><th>유형</th><th>전체</th><th>활성</th><th>상태</th><th>7일 호출</th></tr></thead>
        <tbody>
          <tr v-for="s in services" :key="s.name">
            <td><strong>{{ s.name }}</strong></td><td>{{ s.type }}</td><td>{{ s.total }}</td><td>{{ s.active }}</td>
            <td><span class="status-badge" :class="s.status === '정상' ? 'active' : 'inactive'">{{ s.status }}</span></td>
            <td>{{ s.calls_7d?.toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminOperationApi } from '../../../api/admin.api'
const services = ref<any[]>([])
const summary = ref<any>({ total: 0, active: 0, api_calls_7d: 0 })
onMounted(async () => {
  try {
    const res = await adminOperationApi.integrationStatus()
    if (res.data?.data) { services.value = res.data.data.services; summary.value = res.data.data.summary }
  } catch { /* fallback */ }
})
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .stat-value { font-size: 28px; font-weight: 800; } .stat-label { font-size: 12px; color: #999; } }
.table-section { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; }
.table-header { padding: 12px 16px; border-bottom: 1px solid #e8e8e8; .table-count { font-size: 13px; strong { color: $primary; } } }
.data-table { width: 100%; font-size: 13px; border-collapse: collapse; th { background: #f5f7fa; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; } }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.inactive { background: #f5f5f5; color: #999; } }
</style>
