<template>
  <div class="admin-page">
    <div class="page-header"><h2>App 모니터링 (APM)</h2><p class="page-desc">API 호출량, 응답시간, 에러율을 모니터링합니다.</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-value">{{ data.today_calls?.toLocaleString() }}</div><div class="stat-label">오늘 API 호출</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#DC3545">{{ data.today_errors }}</div><div class="stat-label">오늘 에러</div></div>
      <div class="stat-card"><div class="stat-value" :style="{ color: data.error_rate > 5 ? '#DC3545' : '#28A745' }">{{ data.error_rate }}%</div><div class="stat-label">에러율</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#0066CC">{{ data.avg_response_ms }}ms</div><div class="stat-label">평균 응답시간</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><div class="card-title">7일 트렌드</div>
        <table class="data-table"><thead><tr><th>날짜</th><th>호출</th><th>에러</th></tr></thead>
          <tbody><tr v-for="t in data.trend || []" :key="t.date"><td>{{ t.date }}</td><td>{{ t.calls }}</td><td :style="{ color: t.errors > 0 ? '#DC3545' : '#28A745', fontWeight: 600 }">{{ t.errors }}</td></tr></tbody>
        </table>
      </div>
      <div class="card"><div class="card-title">상위 에러 경로</div>
        <div v-if="(data.top_errors||[]).length === 0" style="padding:20px;text-align:center;color:#999;">에러 없음</div>
        <table v-else class="data-table"><thead><tr><th>경로</th><th>건수</th></tr></thead>
          <tbody><tr v-for="e in data.top_errors || []" :key="e.path"><td style="font-family:monospace;font-size:11px;">{{ e.path }}</td><td style="color:#DC3545;font-weight:700;">{{ e.count }}</td></tr></tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminOperationApi } from '../../../api/admin.api'
const data = ref<any>({})
onMounted(async () => { try { const r = await adminOperationApi.apmDashboard(); if (r.data?.data) data.value = r.data.data } catch {} })
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .stat-value { font-size: 28px; font-weight: 800; } .stat-label { font-size: 12px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; } }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } }
</style>
