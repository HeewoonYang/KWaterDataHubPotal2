<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>분석DB 데이터셋*</h2>
      <p class="page-desc">모든 수집 데이터가 분석DB로 이동하지 않습니다. GPU DB에서 <strong>중요도가 높거나 조회 빈도가 많은 데이터셋만</strong> 데이터 패브릭을 통해 승격된 데이터셋을 관리합니다.</p>
    </div>
    <div class="kpi-row">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <div class="kpi-icon" :style="{ background: k.color }"><component :is="k.icon" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">분석DB 데이터셋 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '분석DB_데이터셋')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.datasetName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">분석DB 데이터셋 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.datasetName }}</span></div>
          <div class="modal-info-item"><span class="info-label">원본 NL쿼리</span><span class="info-value">{{ detailData.originalQuery }}</span></div>
          <div class="modal-info-item"><span class="info-label">승격일</span><span class="info-value">{{ detailData.promotedAt }}</span></div>
          <div class="modal-info-item"><span class="info-label">승격사유</span><span class="info-value">{{ detailData.reason }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용횟수</span><span class="info-value">{{ detailData.usageCount }}</span></div>
          <div class="modal-info-item"><span class="info-label">크기</span><span class="info-value">{{ detailData.size }}</span></div>
          <div class="modal-info-item"><span class="info-label">마지막접근</span><span class="info-value">{{ detailData.lastAccess }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { DatabaseOutlined, HddOutlined, ArrowUpOutlined, ThunderboltOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }

const kpis: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: DatabaseOutlined, label: '총 데이터셋', value: '15', color: '#0066CC' },
  { icon: HddOutlined, label: '총 용량', value: '256 GB', color: '#28A745' },
  { icon: ArrowUpOutlined, label: '이번달 승격', value: '3', color: '#fa8c16' },
  { icon: ThunderboltOutlined, label: '캐시 히트율', value: '78.5%', color: '#9b59b6' },
]

const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '데이터셋명', field: 'datasetName', flex: 1.2, minWidth: 130 },
  { headerName: '원본 NL쿼리', field: 'originalQuery', flex: 1.8, minWidth: 200 },
  { headerName: '승격일', field: 'promotedAt', flex: 0.7, minWidth: 90 },
  { headerName: '승격사유', field: 'reason', flex: 0.6, minWidth: 70 },
  { headerName: '사용횟수', field: 'usageCount', flex: 0.6, minWidth: 70 },
  { headerName: '크기', field: 'size', flex: 0.6, minWidth: 70 },
  { headerName: '마지막접근', field: 'lastAccess', flex: 0.7, minWidth: 90 },
])
const rows = ref([
  { datasetName: '댐 수위 일별 통계', originalQuery: '댐별 일일 평균 수위를 조회해줘', promotedAt: '2026-03-15', reason: '고사용', usageCount: '1,245', size: '12.5 GB', lastAccess: '2026-04-07' },
  { datasetName: '수질 월별 리포트', originalQuery: '각 정수장 월별 수질 현황 보여줘', promotedAt: '2026-03-20', reason: '고사용', usageCount: '890', size: '8.3 GB', lastAccess: '2026-04-06' },
  { datasetName: '관망 GIS 매핑', originalQuery: '관망 노후도 GIS 매핑 데이터', promotedAt: '2026-04-01', reason: '수동승격', usageCount: '156', size: '25.1 GB', lastAccess: '2026-04-05' },
  { datasetName: '자산관리 종합현황', originalQuery: 'ERP 자산 노후도 및 교체이력', promotedAt: '2026-04-03', reason: '중요도', usageCount: '78', size: '5.2 GB', lastAccess: '2026-04-04' },
])

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
</style>
