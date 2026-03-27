<template>
  <div class="admin-page">
    <div class="page-header"><h2>이기종 통합</h2><p class="page-desc">이기종 시스템 간 데이터 통합 연계 현황을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">연계 현황 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '연계_현황')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 연계 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.source + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">연계 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">소스 시스템</span><span class="info-value">{{ detailData.source }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 시스템</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">연계 방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터 건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 연계</span><span class="info-value">{{ detailData.lastSync }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '정상' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
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
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '소스 시스템', field: 'source', flex: 1 },
  { headerName: '대상 시스템', field: 'target', flex: 1 },
  { headerName: '연계 방식', field: 'method', width: 100 },
  { headerName: '데이터 건수', field: 'count', width: 100 },
  { headerName: '최근 연계', field: 'lastSync', width: 120 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { source: 'Oracle (수자원)', target: 'PostgreSQL (데이터허브)', method: 'CDC', count: '2,450만', lastSync: '2026-03-25 08:00', status: '정상' },
  { source: 'MySQL (경영)', target: 'PostgreSQL (데이터허브)', method: 'ETL', count: '580만', lastSync: '2026-03-25 06:00', status: '정상' },
  { source: 'MSSQL (환경)', target: 'PostgreSQL (데이터허브)', method: 'ETL', count: '1,200만', lastSync: '2026-03-25 07:00', status: '정상' },
  { source: 'MongoDB (IoT)', target: 'PostgreSQL (데이터허브)', method: 'Kafka', count: '8,500만', lastSync: '2026-03-25 09:00', status: '지연' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.integrations()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        source: r.integration_name || r.source || '',
        target: r.source_db_type || r.target || '',
        method: r.sync_direction || r.method || '',
        count: r.count || '-',
        lastSync: r.last_sync_at ? String(r.last_sync_at).replace('T', ' ').substring(0, 16) : (r.lastSync || '-'),
        status: r.sync_status === 'SYNCED' ? '정상' : r.sync_status === 'DELAYED' ? '지연' : (r.sync_status || r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('Integration: API call failed, using mock data', e)
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
