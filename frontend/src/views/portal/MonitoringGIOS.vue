<template>
  <div class="monitoring-page">
    <nav class="breadcrumb"><router-link to="/portal/monitoring">실시간모니터링</router-link><span class="separator">&gt;</span><span class="current">GIOS</span></nav>
    <div class="page-header"><h2>GIOS 지하수정보 모니터링*</h2><p>지하수정보관리시스템(GIOS) 실시간 관측 현황</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-icon" style="background:#e6f7ff;color:#0066CC"><EnvironmentOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.totalWells }}</div><div class="stat-label">관측공</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f6ffed;color:#28A745"><CheckCircleOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.activeWells }}</div><div class="stat-label">정상 관측</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#fff7e6;color:#fa8c16"><ExperimentOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.avgLevel }}</div><div class="stat-label">평균 수위(m)</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#fff1f0;color:#DC3545"><WarningOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.alerts }}</div><div class="stat-label">이상 관측</div></div></div>
    </div>
    <div class="table-section">
      <div class="section-title">관측공별 현황</div>
      <table class="data-table">
        <thead><tr><th>관측공명</th><th>지역</th><th>수위(m)</th><th>수온(C)</th><th>EC(uS/cm)</th><th>최종 관측</th><th>상태</th></tr></thead>
        <tbody>
          <tr v-for="w in wells" :key="w.name"><td>{{ w.name }}</td><td>{{ w.region }}</td>
            <td>{{ w.level }}</td><td>{{ w.temp }}</td><td>{{ w.ec }}</td><td>{{ w.lastObs }}</td>
            <td><span class="status-badge" :class="w.status">{{ w.statusLabel }}</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { EnvironmentOutlined, CheckCircleOutlined, ExperimentOutlined, WarningOutlined } from '@ant-design/icons-vue'
const stats = ref({ totalWells: 156, activeWells: 148, avgLevel: '-12.4', alerts: 3 })
const wells = ref([
  { name: 'GW-서울-001', region: '서울 강남', level: -8.2, temp: 15.3, ec: 342, lastObs: '10분 전', status: 'normal', statusLabel: '정상' },
  { name: 'GW-경기-012', region: '경기 수원', level: -11.5, temp: 14.8, ec: 289, lastObs: '10분 전', status: 'normal', statusLabel: '정상' },
  { name: 'GW-강원-008', region: '강원 춘천', level: -15.7, temp: 13.2, ec: 198, lastObs: '10분 전', status: 'normal', statusLabel: '정상' },
  { name: 'GW-충남-003', region: '충남 대전', level: -6.8, temp: 16.1, ec: 412, lastObs: '30분 전', status: 'warning', statusLabel: '지연' },
  { name: 'GW-전남-015', region: '전남 광주', level: -19.3, temp: 14.5, ec: 267, lastObs: '10분 전', status: 'normal', statusLabel: '정상' },
  { name: 'GW-경북-007', region: '경북 대구', level: -22.1, temp: 15.8, ec: 523, lastObs: '1시간 전', status: 'error', statusLabel: '통신 장애' },
  { name: 'GW-부산-002', region: '부산 해운대', level: -4.3, temp: 17.2, ec: 1850, lastObs: '10분 전', status: 'warning', statusLabel: '염수침투' },
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
