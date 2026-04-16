<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>데이터패브릭 현황*</h2>
      <p class="page-desc">자연어질의(T2SQL), MindsDB, GPU DB 현황을 종합 모니터링합니다.</p>
    </div>
    <div class="kpi-row">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <div class="kpi-icon" :style="{ background: k.color }"><component :is="k.icon" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
      </div>
    </div>

    <div class="fabric-note"><InfoCircleOutlined /> 수집DB의 모든 데이터가 분석DB로 이동하지 않습니다. 자연어질의(T2SQL) 또는 MindsDB를 통해 생성된 데이터셋 중 <strong>중요도가 높거나 조회 빈도가 많은 데이터셋만</strong> GPU DB를 거쳐 분석DB로 승격됩니다.</div>

    <div class="grid-2">
      <div class="table-section">
        <div class="table-header">
          <span class="table-count">7일 NL 쿼리 트렌드 <strong>{{ trendRows.length }}</strong>건</span>
          <div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(trendCols, trendRows, 'NL쿼리_트렌드')"><FileExcelOutlined /></button></div>
        </div>
        <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="trendRows" :columnDefs="trendCols" :defaultColDef="defCol" :pagination="false" domLayout="autoHeight" /></div>
      </div>
      <div class="table-section">
        <div class="table-header">
          <span class="table-count">상위 조회 데이터셋 <strong>{{ topRows.length }}</strong>건</span>
          <div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(topCols, topRows, '상위_조회_데이터셋')"><FileExcelOutlined /></button></div>
        </div>
        <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="topRows" :columnDefs="topCols" :defaultColDef="defCol" :pagination="false" domLayout="autoHeight" /></div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { SearchOutlined, CheckCircleOutlined, DatabaseOutlined, RobotOutlined, FileExcelOutlined, InfoCircleOutlined } from '@ant-design/icons-vue'
ModuleRegistry.registerModules([AllCommunityModule])

const kpis: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: SearchOutlined, label: '오늘 NL쿼리', value: '156', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: 'T2SQL 성공률', value: '94.2%', color: '#28A745' },
  { icon: DatabaseOutlined, label: 'GPU DB 데이터셋', value: '23', color: '#9b59b6' },
  { icon: RobotOutlined, label: 'MindsDB 활성모델', value: '8', color: '#fa8c16' },
]
const defCol = { ...baseDefaultColDef }

const trendCols = withHeaderTooltips([
  { headerName: '날짜', field: 'date', flex: 1, minWidth: 100 },
  { headerName: '쿼리수', field: 'queryCount', flex: 0.7, minWidth: 70 },
  { headerName: '성공', field: 'success', flex: 0.7, minWidth: 70 },
  { headerName: '실패', field: 'fail', flex: 0.7, minWidth: 70 },
])
const trendRows = ref([
  { date: '2026-04-07', queryCount: '156', success: '147', fail: '9' },
  { date: '2026-04-06', queryCount: '142', success: '134', fail: '8' },
  { date: '2026-04-05', queryCount: '98', success: '91', fail: '7' },
  { date: '2026-04-04', queryCount: '168', success: '159', fail: '9' },
  { date: '2026-04-03', queryCount: '175', success: '165', fail: '10' },
  { date: '2026-04-02', queryCount: '130', success: '122', fail: '8' },
  { date: '2026-04-01', queryCount: '145', success: '137', fail: '8' },
])

const topCols = withHeaderTooltips([
  { headerName: '데이터셋명', field: 'datasetName', flex: 2, minWidth: 150 },
  { headerName: '조회수', field: 'viewCount', flex: 0.7, minWidth: 70 },
  { headerName: '서빙소스', field: 'source', flex: 1, minWidth: 90 },
])
const topRows = ref([
  { datasetName: '댐 수위 일별 통계', viewCount: '1,245', source: 'GPU DB' },
  { datasetName: '수질 측정 이력', viewCount: '890', source: '분석DB' },
  { datasetName: '관망 압력 데이터', viewCount: '567', source: 'GPU DB' },
  { datasetName: '실시간 유량 현황', viewCount: '423', source: '실시간' },
  { datasetName: '자산 노후화 지표', viewCount: '312', source: '분석DB' },
])
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.fabric-note { margin-bottom: 16px; padding: 10px 14px; background: #f0f7ff; border: 1px solid #91caff; border-radius: 6px; font-size: 12px; color: #0958d9; display: flex; align-items: flex-start; gap: 6px; line-height: 1.6; }
</style>
