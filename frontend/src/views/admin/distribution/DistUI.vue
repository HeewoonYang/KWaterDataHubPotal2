<template>
  <div class="admin-page">
    <div class="page-header"><h2>유통 UI</h2><p class="page-desc">데이터 유통 프로세스 실행 및 모니터링 화면입니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">유통 이력 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '유통_이력')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 유통 이력 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.dataset + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">유통 이력 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋</span><span class="info-value">{{ detailData.dataset }}</span></div>
          <div class="modal-info-item"><span class="info-label">유통 방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">요청자</span><span class="info-value">{{ detailData.requester }}</span></div>
          <div class="modal-info-item"><span class="info-label">요청 시간</span><span class="info-value">{{ detailData.time }}</span></div>
          <div class="modal-info-item"><span class="info-label">결과</span><span class="info-value"><span class="badge" :class="detailData.result === '성공' ? 'badge-success' : 'badge-danger'">{{ detailData.result }}</span></span></div>
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
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { SwapOutlined, DownloadOutlined, ApiOutlined, CheckCircleOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: SwapOutlined, label: '금일 유통 건수', value: '1,250', color: '#0066CC' },
  { icon: DownloadOutlined, label: '금일 다운로드', value: '340', color: '#28A745' },
  { icon: ApiOutlined, label: 'API 호출', value: '45,200', color: '#9b59b6' },
  { icon: CheckCircleOutlined, label: '성공률', value: '99.8%', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋', field: 'dataset', flex: 2 },
  { headerName: '유통 방식', field: 'method', width: 100 },
  { headerName: '요청자', field: 'requester', width: 90 },
  { headerName: '요청 시간', field: 'time', width: 140 },
  { headerName: '결과', field: 'result', width: 70 },
]
const rows = ref([
  { dataset: '댐 수위 관측 데이터', method: 'API', requester: '홍길동', time: '2026-03-25 09:30', result: '성공' },
  { dataset: '수질 모니터링 센서', method: 'CSV 다운로드', requester: '이외부', time: '2026-03-25 09:25', result: '성공' },
  { dataset: '전력 사용량 통계', method: 'Excel 다운로드', requester: '박기상', time: '2026-03-25 09:15', result: '성공' },
  { dataset: '상수도 관로 GIS', method: 'GeoJSON API', requester: '홍길동', time: '2026-03-25 09:00', result: '성공' },
  { dataset: '하천 유량 관측', method: 'API', requester: '김매니저', time: '2026-03-25 08:45', result: '실패' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.stats()
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        dataset: r.stat_type || r.dataset || '',
        method: r.method || '-',
        requester: r.requester || '-',
        time: r.stat_date || r.time || '',
        result: r.result || '-',
      }))
    }
  } catch (e) {
    console.warn('DistUI: API call failed, using mock data', e)
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
