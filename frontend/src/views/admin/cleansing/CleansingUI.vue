<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>정제 UI</h2>
      <p class="page-desc">데이터 정제 규칙을 설정하고 정제 결과를 관리합니다.</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ rowData.length }}</strong>건</span>
        <div class="table-actions"><button class="btn btn-success"><PlusOutlined /> 정제 규칙 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '정제_규칙')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="defaultColDef" :pagination="true" :paginationPageSize="10" :rowSelection="'multiple'" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 정제 규칙 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">정제 규칙 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">규칙명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 테이블</span><span class="info-value">{{ detailData.table }}</span></div>
          <div class="modal-info-item"><span class="info-label">정제 유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">적용 건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">성공률</span><span class="info-value">{{ detailData.rate }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 실행</span><span class="info-value">{{ detailData.lastRun }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '완료' ? 'badge-success' : detailData.status === '오류' ? 'badge-danger' : 'badge-warning'">{{ detailData.status }}</span></span></div>
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
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { ClearOutlined, CheckCircleOutlined, SyncOutlined, ExclamationCircleOutlined, PlusOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCleansingApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: ClearOutlined, label: '전체 정제 규칙', value: '58', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '정제 완료', value: '45', color: '#28A745' },
  { icon: SyncOutlined, label: '정제중', value: '8', color: '#FFC107' },
  { icon: ExclamationCircleOutlined, label: '오류', value: '5', color: '#DC3545' },
]
const defaultColDef = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, minWidth: 36, flex: 0, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '규칙명', field: 'name', flex: 2, minWidth: 180 },
  { headerName: '대상 테이블', field: 'table', flex: 1, minWidth: 130 },
  { headerName: '정제 유형', field: 'type', flex: 0.7, minWidth: 80 },
  { headerName: '적용 건수', field: 'count', flex: 0.7, minWidth: 80 },
  { headerName: '성공률', field: 'rate', flex: 0.5, minWidth: 65 },
  { headerName: '최근 실행', field: 'lastRun', flex: 1, minWidth: 130 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rowData = ref([
  { name: '수위 데이터 이상값 제거', table: 'TB_DAM_LEVEL', type: '이상값', count: '12,500건', rate: '99.2%', lastRun: '2026-03-25 12:00', status: '완료' },
  { name: '수질 NULL 값 보정', table: 'TB_WATER_QUALITY', type: 'NULL 처리', count: '8,200건', rate: '97.8%', lastRun: '2026-03-25 11:30', status: '완료' },
  { name: '관로 좌표 정규화', table: 'TB_PIPE_GIS', type: '정규화', count: '320만건', rate: '95.1%', lastRun: '2026-03-25 10:00', status: '진행중' },
  { name: '전력량 단위 통일', table: 'TB_POWER_USAGE', type: '변환', count: '15,600건', rate: '100%', lastRun: '2026-03-24 18:00', status: '완료' },
  { name: '개인정보 비식별화', table: 'TB_USER_LOG', type: '비식별화', count: '42,000건', rate: '100%', lastRun: '2026-03-24 06:00', status: '완료' },
  { name: '중복 데이터 제거', table: 'TB_SENSOR_RAW', type: '중복제거', count: '1,800건', rate: '88.5%', lastRun: '2026-03-25 13:00', status: '오류' },
])

onMounted(async () => {
  try {
    const res = await adminCleansingApi.jobs()
    const items = res.data.data
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        name: r.job_name || r.name || '',
        table: r.table || '-',
        type: r.type || '-',
        count: r.total_rows != null ? r.total_rows.toLocaleString() + '건' : (r.count || '-'),
        rate: r.total_rows && r.cleansed_rows != null ? Math.round((r.cleansed_rows / r.total_rows) * 100) + '%' : (r.rate || '-'),
        lastRun: r.started_at ? String(r.started_at).replace('T', ' ').substring(0, 16) : (r.lastRun || '-'),
        status: r.job_status === 'COMPLETED' ? '완료' : r.job_status === 'RUNNING' ? '진행중' : r.job_status === 'FAILED' ? '오류' : (r.status || r.job_status || '-'),
      }))
    }
  } catch (e) {
    console.warn('CleansingUI: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
