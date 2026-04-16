<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>GPU DB 데이터셋*</h2>
      <p class="page-desc">GPU DB에 저장된 데이터셋의 라이프사이클을 관리합니다. 중요도가 높거나 조회 빈도가 많은 데이터셋만 분석DB로 승격됩니다.</p>
    </div>
    <div class="kpi-row">
      <div class="kpi-card" v-for="k in kpis" :key="k.label">
        <div class="kpi-icon" :style="{ background: k.color }"><component :is="k.icon" /></div>
        <div class="kpi-body"><div class="kpi-value">{{ k.value }}</div><div class="kpi-label">{{ k.label }}</div></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">GPU DB 데이터셋 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'GPU_DB_데이터셋')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.datasetName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">GPU DB 데이터셋 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.datasetName }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스쿼리</span><span class="info-value">{{ detailData.sourceQuery }}</span></div>
          <div class="modal-info-item"><span class="info-label">보관기간</span><span class="info-value">{{ detailData.retention }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용횟수</span><span class="info-value">{{ detailData.usageCount }}</span></div>
          <div class="modal-info-item"><span class="info-label">크기</span><span class="info-value">{{ detailData.size }}</span></div>
          <div class="modal-info-item"><span class="info-label">마지막접근</span><span class="info-value">{{ detailData.lastAccess }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handlePromote"><ArrowUpOutlined /> 분석DB 승격</button>
        <button class="btn btn-danger" @click="handleDelete"><DeleteOutlined /> 삭제</button>
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
import { DatabaseOutlined, HddOutlined, ClockCircleOutlined, RiseOutlined, FileExcelOutlined, ArrowUpOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }

const kpis: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: DatabaseOutlined, label: '총 데이터셋', value: '23', color: '#0066CC' },
  { icon: HddOutlined, label: '총 용량', value: '128 GB', color: '#28A745' },
  { icon: ClockCircleOutlined, label: '만료 예정', value: '5', color: '#fa8c16' },
  { icon: RiseOutlined, label: '고사용 데이터셋', value: '8', color: '#9b59b6' },
]

const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '데이터셋명', field: 'datasetName', flex: 1.5, minWidth: 150 },
  { headerName: '소스쿼리', field: 'sourceQuery', flex: 2, minWidth: 200 },
  { headerName: '보관기간', field: 'retention', flex: 0.6, minWidth: 70 },
  { headerName: '사용횟수', field: 'usageCount', flex: 0.6, minWidth: 70 },
  { headerName: '크기', field: 'size', flex: 0.6, minWidth: 70 },
  { headerName: '마지막접근', field: 'lastAccess', flex: 0.8, minWidth: 100 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 70 },
])
const rows = ref([
  { datasetName: '댐 수위 일별 통계', sourceQuery: 'SELECT ... FROM water_level GROUP BY day', retention: '1개월', usageCount: '245', size: '12.5 GB', lastAccess: '2026-04-07', status: 'ACTIVE' },
  { datasetName: '수질 측정 이력 (3년)', sourceQuery: 'SELECT ... FROM water_quality WHERE ...', retention: '1주', usageCount: '182', size: '8.3 GB', lastAccess: '2026-04-06', status: 'ACTIVE' },
  { datasetName: '관망 누수 분석', sourceQuery: 'SELECT ... FROM pipe_leak_analysis', retention: '1개월', usageCount: '67', size: '5.1 GB', lastAccess: '2026-04-05', status: 'ACTIVE' },
  { datasetName: '자산 노후화 예측', sourceQuery: 'SELECT ... FROM asset_aging_predict', retention: '1주', usageCount: '12', size: '3.2 GB', lastAccess: '2026-03-28', status: 'EXPIRING' },
  { datasetName: '시설 유지보수 이력', sourceQuery: 'SELECT ... FROM facility_maintenance', retention: '1주', usageCount: '3', size: '1.8 GB', lastAccess: '2026-03-20', status: 'EXPIRING' },
])

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

function handlePromote() {
  message.success(`'${detailData.value.datasetName}'이(가) 분석DB로 승격되었습니다.`)
  showDetail.value = false
}

function handleDelete() {
  message.success(`'${detailData.value.datasetName}'이(가) 삭제되었습니다.`)
  rows.value = rows.value.filter((r: any) => r.datasetName !== detailData.value.datasetName)
  showDetail.value = false
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
</style>
