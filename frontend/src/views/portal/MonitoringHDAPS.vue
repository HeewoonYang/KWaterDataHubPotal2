<template>
  <div class="monitoring-page">
    <nav class="breadcrumb"><router-link to="/portal/monitoring">실시간모니터링</router-link><span class="separator">&gt;</span><span class="current">HDAPS</span></nav>
    <div class="page-header"><h2>HDAPS 수력발전 모니터링*</h2><p>수력발전 관리시스템(HDAPS) 실시간 운영 현황</p></div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-icon" style="background:#e6f7ff;color:#0066CC"><ThunderboltOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.totalPlants }}</div><div class="stat-label">발전소</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#f6ffed;color:#28A745"><DashboardOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.activeTurbines }}</div><div class="stat-label">가동 터빈</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#fff7e6;color:#fa8c16"><FireOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.totalOutput }}</div><div class="stat-label">총 발전량(MW)</div></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#fff1f0;color:#DC3545"><AlertOutlined /></div><div class="stat-body"><div class="stat-value">{{ stats.alerts }}</div><div class="stat-label">경보</div></div></div>
    </div>
    <div class="table-section">
      <div class="section-title">발전소별 현황</div>
      <table class="data-table">
        <thead><tr><th>발전소</th><th>터빈 수</th><th>가동</th><th>발전량(MW)</th><th>수위(EL.m)</th><th>유입량(m3/s)</th><th>상태</th></tr></thead>
        <tbody>
          <tr v-for="p in plants" :key="p.name"><td>{{ p.name }}</td><td>{{ p.turbines }}</td><td>{{ p.active }}</td>
            <td>{{ p.output }}</td><td>{{ p.waterLevel }}</td><td>{{ p.inflow }}</td>
            <td><span class="status-badge" :class="p.status">{{ p.statusLabel }}</span></td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { ThunderboltOutlined, DashboardOutlined, FireOutlined, AlertOutlined } from '@ant-design/icons-vue'
const stats = ref({ totalPlants: 7, activeTurbines: 18, totalOutput: '1,247', alerts: 0 })
const plants = ref([
  { name: '소양강', turbines: 4, active: 3, output: 352, waterLevel: 183.5, inflow: 42.3, status: 'normal', statusLabel: '정상' },
  { name: '충주', turbines: 4, active: 4, output: 412, waterLevel: 138.2, inflow: 65.1, status: 'normal', statusLabel: '정상' },
  { name: '합천', turbines: 2, active: 2, output: 186, waterLevel: 169.8, inflow: 23.5, status: 'normal', statusLabel: '정상' },
  { name: '대청', turbines: 2, active: 2, output: 148, waterLevel: 72.1, inflow: 18.9, status: 'normal', statusLabel: '정상' },
  { name: '안동', turbines: 2, active: 1, output: 67, waterLevel: 156.3, inflow: 11.2, status: 'warning', statusLabel: '점검중' },
  { name: '임하', turbines: 2, active: 2, output: 54, waterLevel: 159.7, inflow: 8.7, status: 'normal', statusLabel: '정상' },
  { name: '횡성', turbines: 2, active: 2, output: 28, waterLevel: 178.4, inflow: 5.4, status: 'normal', statusLabel: '정상' },
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
