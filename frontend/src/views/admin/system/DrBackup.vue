<template>
  <div class="admin-page">
    <div class="page-header"><h2>DR/백업 관리</h2><p class="page-desc">재해복구(DR) 설정 및 백업 이력을 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">백업 이력 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '백업_이력')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 백업 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.target + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">백업 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">백업 대상</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">시작 시간</span><span class="info-value">{{ detailData.startTime }}</span></div>
          <div class="modal-info-item"><span class="info-label">소요 시간</span><span class="info-value">{{ detailData.duration }}</span></div>
          <div class="modal-info-item"><span class="info-label">용량</span><span class="info-value">{{ detailData.size }}</span></div>
          <div class="modal-info-item"><span class="info-label">결과</span><span class="info-value"><span class="badge" :class="detailData.result === '성공' ? 'badge-success' : 'badge-warning'">{{ detailData.result }}</span></span></div>
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
import { SaveOutlined, SyncOutlined, CheckCircleOutlined, DatabaseOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: SaveOutlined, label: '최근 백업', value: '03-25 02:00', color: '#0066CC' },
  { icon: SyncOutlined, label: 'DR 동기화', value: '정상', color: '#28A745' },
  { icon: CheckCircleOutlined, label: '복구 테스트', value: '03-20', color: '#9b59b6' },
  { icon: DatabaseOutlined, label: '백업 용량', value: '2.3 TB', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '백업 대상', field: 'target', flex: 2 },
  { headerName: '유형', field: 'type', width: 90 },
  { headerName: '시작 시간', field: 'startTime', flex: 1 },
  { headerName: '소요 시간', field: 'duration', width: 90 },
  { headerName: '용량', field: 'size', width: 90 },
  { headerName: '결과', field: 'result', width: 70 },
]
const rows = ref([
  { target: 'PostgreSQL Master DB', type: '전체백업', startTime: '2026-03-25 02:00', duration: '45분', size: '850 GB', result: '성공' },
  { target: 'OpenMetadata DB', type: '증분백업', startTime: '2026-03-25 02:00', duration: '12분', size: '120 GB', result: '성공' },
  { target: 'Redis Cache', type: 'RDB 스냅샷', startTime: '2026-03-25 03:00', duration: '3분', size: '8 GB', result: '성공' },
  { target: 'NFS 스토리지', type: '증분백업', startTime: '2026-03-25 04:00', duration: '90분', size: '1.2 TB', result: '성공' },
  { target: 'PostgreSQL Master DB', type: '전체백업', startTime: '2026-03-24 02:00', duration: '43분', size: '848 GB', result: '성공' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.drBackup()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        target: r.backup_name || r.target_system || r.target || '',
        type: r.backup_type || r.type || '',
        startTime: r.last_backup_at ? String(r.last_backup_at).replace('T', ' ').substring(0, 16) : (r.startTime || '-'),
        duration: r.duration || '-',
        size: r.size || '-',
        result: r.last_backup_status === 'SUCCESS' ? '성공' : r.last_backup_status === 'FAILED' ? '실패' : (r.last_backup_status || r.result || '-'),
      }))
    }
  } catch (e) {
    console.warn('DrBackup: API call failed, using mock data', e)
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
