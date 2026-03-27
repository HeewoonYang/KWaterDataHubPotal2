<template>
  <div class="admin-page">
    <div class="page-header"><h2>유통 포맷</h2><p class="page-desc">데이터 유통 포맷(CSV, JSON, API 등) 설정을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">유통 포맷 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '유통_포맷')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 유통 포맷 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">유통 포맷 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">포맷명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">MIME Type</span><span class="info-value">{{ detailData.mime }}</span></div>
          <div class="modal-info-item"><span class="info-label">인코딩</span><span class="info-value">{{ detailData.encoding }}</span></div>
          <div class="modal-info-item"><span class="info-label">최대 용량</span><span class="info-value">{{ detailData.maxSize }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용 데이터셋</span><span class="info-value">{{ detailData.datasets }}개</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
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
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '포맷명', field: 'name', flex: 1 },
  { headerName: 'MIME Type', field: 'mime', flex: 1 },
  { headerName: '인코딩', field: 'encoding', width: 90 },
  { headerName: '최대 용량', field: 'maxSize', width: 90 },
  { headerName: '사용 데이터셋', field: 'datasets', width: 100 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: 'CSV', mime: 'text/csv', encoding: 'UTF-8', maxSize: '500 MB', datasets: 42, status: '활성' },
  { name: 'JSON', mime: 'application/json', encoding: 'UTF-8', maxSize: '200 MB', datasets: 35, status: '활성' },
  { name: 'Excel', mime: 'application/vnd.openxmlformats', encoding: '-', maxSize: '100 MB', datasets: 18, status: '활성' },
  { name: 'GeoJSON', mime: 'application/geo+json', encoding: 'UTF-8', maxSize: '300 MB', datasets: 8, status: '활성' },
  { name: 'XML', mime: 'application/xml', encoding: 'UTF-8', maxSize: '200 MB', datasets: 5, status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.formats()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.format_name || r.name || '',
        mime: r.mime_type || r.mime || '',
        encoding: r.encoding || 'UTF-8',
        maxSize: r.maxSize || '-',
        datasets: r.datasets || '-',
        status: r.is_active === true ? '활성' : r.is_active === false ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DistFormat: API call failed, using mock data', e)
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
