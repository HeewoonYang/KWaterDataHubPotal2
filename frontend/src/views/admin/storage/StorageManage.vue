<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>저장소 구분</h2>
      <p class="page-desc">데이터 저장소를 구분하고 용량을 관리합니다.</p>
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
        <div class="table-actions"><button class="btn btn-success"><PlusOutlined /> 저장소 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '저장소_관리')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 저장소 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">저장소 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">저장소명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">호스트</span><span class="info-value">{{ detailData.host }}</span></div>
          <div class="modal-info-item"><span class="info-label">전체 용량</span><span class="info-value">{{ detailData.totalSize }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용 용량</span><span class="info-value">{{ detailData.usedSize }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용률</span><span class="info-value">{{ detailData.usage }}</span></div>
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
import { HddOutlined, DatabaseOutlined, CloudOutlined, FileOutlined, PlusOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminStorageApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: HddOutlined, label: '전체 저장소', value: '8', color: '#0066CC' },
  { icon: DatabaseOutlined, label: 'RDB 저장소', value: '3', color: '#28A745' },
  { icon: CloudOutlined, label: '오브젝트 저장소', value: '2', color: '#9b59b6' },
  { icon: FileOutlined, label: '파일 저장소', value: '3', color: '#FFC107' },
]
const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '저장소명', field: 'name', flex: 2, minWidth: 160 },
  { headerName: '유형', field: 'type', flex: 0.7, minWidth: 90 },
  { headerName: '호스트', field: 'host', flex: 1, minWidth: 120 },
  { headerName: '전체 용량', field: 'totalSize', flex: 0.7, minWidth: 80 },
  { headerName: '사용 용량', field: 'usedSize', flex: 0.7, minWidth: 80 },
  { headerName: '사용률', field: 'usage', flex: 0.6, minWidth: 65 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rowData = ref([
  { name: 'PostgreSQL Master', type: 'RDB', host: '10.0.1.10', totalSize: '2 TB', usedSize: '1.2 TB', usage: '60%', status: '정상' },
  { name: 'PostgreSQL Replica', type: 'RDB', host: '10.0.1.11', totalSize: '2 TB', usedSize: '1.2 TB', usage: '60%', status: '정상' },
  { name: 'TimescaleDB', type: 'RDB (시계열)', host: '10.0.1.20', totalSize: '4 TB', usedSize: '2.8 TB', usage: '70%', status: '정상' },
  { name: 'MinIO Cluster', type: '오브젝트', host: '10.0.5.10-12', totalSize: '10 TB', usedSize: '3.5 TB', usage: '35%', status: '정상' },
  { name: 'Elasticsearch', type: '검색엔진', host: '10.0.6.10-12', totalSize: '3 TB', usedSize: '1.8 TB', usage: '60%', status: '정상' },
  { name: 'NFS 파일서버', type: '파일', host: '10.0.7.10', totalSize: '5 TB', usedSize: '2.1 TB', usage: '42%', status: '정상' },
  { name: 'HDFS Cluster', type: '분산파일', host: '10.0.8.10-13', totalSize: '20 TB', usedSize: '8.4 TB', usage: '42%', status: '정상' },
  { name: 'Redis Sentinel', type: '캐시', host: '10.0.3.20', totalSize: '64 GB', usedSize: '12 GB', usage: '19%', status: '정상' },
  { name: 'GPU DB Cluster', type: 'GPU가속', host: '10.0.9.10-12', totalSize: '1 TB', usedSize: '128 GB', usage: '12%', status: '정상' },
  { name: '분석 PostgreSQL', type: 'RDB (분석)', host: '10.0.1.30', totalSize: '4 TB', usedSize: '256 GB', usage: '6%', status: '정상' },
])

onMounted(async () => {
  try {
    const res = await adminStorageApi.zones()
    const items = res.data.data
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        name: r.zone_name || r.name || '',
        type: r.zone_type || r.storage_type || r.type || '',
        host: r.host || '-',
        totalSize: r.max_capacity_gb != null ? r.max_capacity_gb + ' GB' : (r.totalSize || '-'),
        usedSize: r.used_capacity_gb != null ? r.used_capacity_gb + ' GB' : (r.usedSize || '-'),
        usage: r.max_capacity_gb && r.used_capacity_gb != null ? Math.round((r.used_capacity_gb / r.max_capacity_gb) * 100) + '%' : (r.usage || '-'),
        status: r.status === 'ACTIVE' ? '정상' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('StorageManage: API call failed, using mock data', e)
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
