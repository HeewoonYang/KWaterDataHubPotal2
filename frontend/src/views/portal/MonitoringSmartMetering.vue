<template>
  <div class="monitoring-page">
    <nav class="breadcrumb"><router-link to="/portal/monitoring">실시간모니터링</router-link><span class="separator">&gt;</span><span class="current">Smart Metering</span></nav>
    <div class="page-header"><h2>스마트미터링 모니터링*</h2><p>광역/지방 상수도 스마트미터링 실시간 계측 현황</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-icon" style="background:#e6f7ff;color:#0066CC"><NodeIndexOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.totalMeters }}</div><div class="stat-label">계측기</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f6ffed;color:#28A745"><CheckCircleOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.online }}</div><div class="stat-label">온라인</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#fff7e6;color:#fa8c16"><BarChartOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.todayUsage }}</div><div class="stat-label">금일 사용량(m3)</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f9f0ff;color:#9b59b6"><AlertOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.anomaly }}</div><div class="stat-label">이상 감지</div></div></div>
    </div>
    <div class="table-section">
      <div class="section-title">계측기별 실시간 현황</div>
      <table class="data-table">
        <thead><tr><th>미터ID</th><th>지역</th><th>유량(m3/h)</th><th>압력(kPa)</th><th>전력(kWh)</th><th>온도(C)</th><th>최종 수신</th><th>상태</th></tr></thead>
        <tbody>
          <tr v-for="m in meters" :key="m.id"><td><strong>{{ m.id }}</strong></td><td>{{ m.region }}</td>
            <td>{{ m.flow }}</td><td>{{ m.pressure }}</td><td>{{ m.power }}</td><td>{{ m.temp }}</td><td>{{ m.lastRecv }}</td>
            <td><span class="status-badge" :class="m.status">{{ m.statusLabel }}</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { NodeIndexOutlined, CheckCircleOutlined, BarChartOutlined, AlertOutlined } from '@ant-design/icons-vue'
const stats = ref({ totalMeters: 463, online: 451, todayUsage: '128,450', anomaly: 2 })
const meters = ref([
  { id: 'MTR-G81-001', region: '시흥정수장', flow: 3.42, pressure: 385, power: 12.5, temp: 18.2, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
  { id: 'MTR-G81-002', region: '시흥정수장', flow: 2.87, pressure: 392, power: 11.8, temp: 17.9, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
  { id: 'MTR-SH-001', region: '반월정수장', flow: 4.15, pressure: 378, power: 15.2, temp: 19.1, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
  { id: 'MTR-BW-001', region: '반월배수지', flow: 1.23, pressure: 295, power: 8.7, temp: 16.5, lastRecv: '5분 전', status: 'warning', statusLabel: '저압력' },
  { id: 'MTR-AY-001', region: '안양가압장', flow: 5.61, pressure: 412, power: 22.3, temp: 20.4, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
  { id: 'MTR-IC-003', region: '인천취수장', flow: 0.12, pressure: 180, power: 3.1, temp: 15.8, lastRecv: '30분 전', status: 'error', statusLabel: '통신 장애' },
  { id: 'MTR-SW-007', region: '수원배수지', flow: 3.98, pressure: 401, power: 14.6, temp: 18.7, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
  { id: 'MTR-DJ-002', region: '대전정수장', flow: 2.45, pressure: 365, power: 10.9, temp: 17.3, lastRecv: '1분 전', status: 'normal', statusLabel: '정상' },
])
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.monitoring-page { padding-bottom: 20px; }
.breadcrumb { font-size: 12px; color: #999; margin-bottom: 12px; a { color: $primary; text-decoration: none; } }
.page-header { margin-bottom: 16px; h2 { margin: 0 0 4px; font-size: 20px; } p { margin: 0; color: #666; font-size: 13px; } }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.stat-body { .stat-value { font-size: 22px; font-weight: 700; color: #333; } .stat-label { font-size: 12px; color: #999; } }
.table-section { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; }
.section-title { font-weight: 600; font-size: 14px; margin-bottom: 12px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px;
  th { background: #f5f7fa; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
  tr:hover td { background: #fafafa; }
}
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;
  &.normal { background: #f6ffed; color: #28A745; } &.warning { background: #fff7e6; color: #fa8c16; } &.error { background: #fff1f0; color: #DC3545; }
}
</style>
