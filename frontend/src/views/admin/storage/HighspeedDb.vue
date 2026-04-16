<template>
  <div class="admin-page">
    <div class="page-header"><h2>고속처리 DB</h2><p class="page-desc">실시간/대용량 고속 처리 데이터베이스를 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">고속DB 인스턴스 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '고속DB_인스턴스')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 인스턴스 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">고속DB 인스턴스 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">인스턴스명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">DB엔진</span><span class="info-value">{{ detailData.engine }}</span></div>
          <div class="modal-info-item"><span class="info-label">용량</span><span class="info-value">{{ detailData.storage }}</span></div>
          <div class="modal-info-item"><span class="info-label">CPU 사용률</span><span class="info-value">{{ detailData.cpu }}</span></div>
          <div class="modal-info-item"><span class="info-label">메모리</span><span class="info-value">{{ detailData.memory }}</span></div>
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
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { ThunderboltOutlined, HddOutlined, DashboardOutlined, DatabaseOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminStorageApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: ThunderboltOutlined, label: '초당 쿼리', value: '12,500', color: '#0066CC' },
  { icon: HddOutlined, label: '사용 용량', value: '3.2 TB', color: '#28A745' },
  { icon: DashboardOutlined, label: '평균 응답', value: '2.3ms', color: '#9b59b6' },
  { icon: DatabaseOutlined, label: '활성 연결', value: '245', color: '#FFC107' },
]
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '인스턴스명', field: 'name', flex: 2 },
  { headerName: 'DB엔진', field: 'engine', width: 110 },
  { headerName: '용량', field: 'storage', width: 80 },
  { headerName: 'CPU 사용률', field: 'cpu', width: 90 },
  { headerName: '메모리', field: 'memory', width: 90 },
  { headerName: '상태', field: 'status', width: 70 },
])
const rows = ref([
  { name: 'timescale-realtime-01', engine: 'TimescaleDB', storage: '1.2 TB', cpu: '45%', memory: '62%', status: '정상' },
  { name: 'redis-cache-01', engine: 'Redis 7.2', storage: '8 GB', cpu: '15%', memory: '48%', status: '정상' },
  { name: 'clickhouse-analytics', engine: 'ClickHouse', storage: '2.0 TB', cpu: '35%', memory: '55%', status: '정상' },
  { name: 'gpu-db-cluster-01', engine: 'GPU DB', storage: '512 GB', cpu: '62%', memory: '78%', status: '정상' },
  { name: 'gpu-db-cluster-02', engine: 'GPU DB', storage: '512 GB', cpu: '55%', memory: '71%', status: '정상' },
])

onMounted(async () => {
  try {
    const res = await adminStorageApi.highspeed()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.db_name || r.name || '',
        engine: r.db_type || r.engine || '',
        storage: r.storage || '-',
        cpu: r.cpu || '-',
        memory: r.max_memory_gb != null ? r.max_memory_gb + ' GB' : (r.memory || '-'),
        status: r.status === 'ACTIVE' ? '정상' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('HighspeedDb: API call failed, using mock data', e)
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
