<template>
  <div class="admin-page">
    <div class="page-header"><h2>수집 UI</h2><p class="page-desc">데이터 수집 파이프라인 실행 및 모니터링 화면입니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">파이프라인 실행 이력 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '수집_이력')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 실행 이력 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.pipeline + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">실행 이력 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">파이프라인</span><span class="info-value">{{ detailData.pipeline }}</span></div>
          <div class="modal-info-item"><span class="info-label">시작 시간</span><span class="info-value">{{ detailData.startTime }}</span></div>
          <div class="modal-info-item"><span class="info-label">소요 시간</span><span class="info-value">{{ detailData.duration }}</span></div>
          <div class="modal-info-item"><span class="info-label">수집 건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">결과</span><span class="info-value"><span class="badge" :class="detailData.result === '성공' ? 'badge-success' : detailData.result === '실행 중' ? 'badge-info' : 'badge-warning'">{{ detailData.result }}</span></span></div>
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
import { PlayCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: PlayCircleOutlined, label: '실행 중', value: '3', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '금일 성공', value: '28', color: '#28A745' },
  { icon: CloseCircleOutlined, label: '금일 실패', value: '1', color: '#DC3545' },
  { icon: SyncOutlined, label: '금일 수집량', value: '1.2M건', color: '#FFC107' },
]
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '파이프라인', field: 'pipeline', flex: 1.5, minWidth: 150 },
  { headerName: '시작 시간', field: 'startTime', flex: 1, minWidth: 120 },
  { headerName: '소요 시간', field: 'duration', flex: 0.6, minWidth: 70 },
  { headerName: '수집 건수', field: 'count', flex: 0.7, minWidth: 80 },
  { headerName: '결과', field: 'result', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { pipeline: '댐 수위 관측 (실시간)', startTime: '2026-03-25 09:00', duration: '2초', count: '15,240', result: '성공' },
  { pipeline: '수질 센서 데이터 (Kafka)', startTime: '2026-03-25 09:00', duration: '실시간', count: '892,300', result: '실행 중' },
  { pipeline: '하천 유량 관측 (API)', startTime: '2026-03-25 08:00', duration: '15초', count: '3,200', result: '성공' },
  { pipeline: '관로 GIS 일배치', startTime: '2026-03-25 01:00', duration: '25분', count: '45,000', result: '성공' },
  { pipeline: '전력통계 월배치', startTime: '2026-03-01 00:00', duration: '5분', count: '1,300', result: '성공' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.jobs()
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        pipeline: r.dataset_name || r.pipeline || '',
        startTime: r.started_at ? String(r.started_at).replace('T', ' ').substring(0, 16) : (r.startTime || '-'),
        duration: r.started_at && r.finished_at ? (() => { const ms = new Date(r.finished_at).getTime() - new Date(r.started_at).getTime(); return ms < 60000 ? Math.round(ms/1000) + '초' : Math.round(ms/60000) + '분'; })() : (r.duration || '-'),
        count: r.total_rows != null ? r.total_rows.toLocaleString() : (r.count || '-'),
        result: r.job_status === 'COMPLETED' ? '성공' : r.job_status === 'RUNNING' ? '실행 중' : r.job_status === 'FAILED' ? '실패' : (r.result || r.job_status || '-'),
      }))
    }
  } catch (e) {
    console.warn('CollectionUI: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
