<template>
  <div class="admin-page">
    <div class="page-header"><h2>패키지 검증</h2><p class="page-desc">설치된 패키지 버전 및 호환성을 검증합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">패키지 목록 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm"><SyncOutlined /> 전체 검증</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '패키지_검증')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 패키지 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">패키지 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">패키지명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">현재 버전</span><span class="info-value">{{ detailData.current }}</span></div>
          <div class="modal-info-item"><span class="info-label">권장 버전</span><span class="info-value">{{ detailData.recommended }}</span></div>
          <div class="modal-info-item"><span class="info-label">분류</span><span class="info-value">{{ detailData.category }}</span></div>
          <div class="modal-info-item"><span class="info-label">호환성</span><span class="info-value"><span class="badge" :class="detailData.status === '적합' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">검증일</span><span class="info-value">{{ detailData.checkedAt }}</span></div>
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
import { SyncOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '패키지명', field: 'name', flex: 2 },
  { headerName: '현재 버전', field: 'current', width: 100 },
  { headerName: '권장 버전', field: 'recommended', width: 100 },
  { headerName: '분류', field: 'category', width: 100 },
  { headerName: '호환성', field: 'status', width: 80 },
  { headerName: '검증일', field: 'checkedAt', width: 110 },
]
const rows = ref([
  { name: 'Vue.js', current: '3.4.21', recommended: '3.4.21', category: 'Frontend', status: '적합', checkedAt: '2026-03-25' },
  { name: 'FastAPI', current: '0.110.0', recommended: '0.110.0', category: 'Backend', status: '적합', checkedAt: '2026-03-25' },
  { name: 'PostgreSQL', current: '16.2', recommended: '16.2', category: 'DB', status: '적합', checkedAt: '2026-03-25' },
  { name: 'AG Grid', current: '33.0.4', recommended: '33.0.4', category: 'Frontend', status: '적합', checkedAt: '2026-03-25' },
  { name: 'Redis', current: '7.2.4', recommended: '7.2.4', category: 'Cache', status: '적합', checkedAt: '2026-03-25' },
  { name: 'Kafka', current: '3.6.1', recommended: '3.7.0', category: 'Messaging', status: '업데이트 권고', checkedAt: '2026-03-24' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.packages()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.package_name || r.name || '',
        current: r.package_version || r.current || '',
        recommended: r.recommended || r.package_version || '',
        category: r.vendor || r.license_type || r.category || '',
        status: r.poc_status === 'PASS' ? '적합' : r.poc_status === 'WARN' ? '업데이트 권고' : r.poc_status || (r.status || '-'),
        checkedAt: r.license_expiry || r.checkedAt || '-',
      }))
    }
  } catch (e) {
    console.warn('PackageVerify: API call failed, using mock data', e)
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
