<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>유통 구성</h2>
      <p class="page-desc">데이터 유통 DB를 등록하고 연결 상태를 관리합니다.</p>
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
        <div class="table-actions"><button class="btn btn-success"><PlusOutlined /> 유통 DB 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '유통DB_설정')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 유통 채널 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">유통 채널 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">유통 채널명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 시스템</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">포맷</span><span class="info-value">{{ detailData.format }}</span></div>
          <div class="modal-info-item"><span class="info-label">유통 건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 유통</span><span class="info-value">{{ detailData.lastSync }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '정상' ? 'badge-success' : 'badge-danger'">{{ detailData.status }}</span></span></div>
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
import { SwapOutlined, ApiOutlined, LinkOutlined, DisconnectOutlined, PlusOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: SwapOutlined, label: '전체 유통 채널', value: '15', color: '#0066CC' },
  { icon: ApiOutlined, label: 'REST API', value: '8', color: '#28A745' },
  { icon: LinkOutlined, label: '연결 정상', value: '13', color: '#9b59b6' },
  { icon: DisconnectOutlined, label: '연결 오류', value: '2', color: '#DC3545' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '유통 채널명', field: 'name', flex: 2, minWidth: 170 },
  { headerName: '유형', field: 'type', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '대상 시스템', field: 'target', flex: 1, minWidth: 120 },
  { headerName: '포맷', field: 'format', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '유통 건수', field: 'count', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '최근 유통', field: 'lastSync', flex: 1, minWidth: 130 },
  { headerName: '상태', field: 'status', width: 70, maxWidth: 70, flex: 0 },
]
const rowData = ref([
  { name: '수자원 공개 API', type: 'REST API', target: '공공데이터포털', format: 'JSON', count: '1.2억건', lastSync: '2026-03-25 13:00', status: '정상' },
  { name: '수도 관리 연계', type: 'DB Link', target: '수도관리시스템', format: 'DB', count: '320만건', lastSync: '2026-03-25 12:30', status: '정상' },
  { name: '환경 데이터 피드', type: 'REST API', target: '환경부', format: 'JSON', count: '85만건', lastSync: '2026-03-25 11:00', status: '정상' },
  { name: '기상 데이터 수신', type: 'REST API', target: '기상청', format: 'XML', count: '24건/일', lastSync: '2026-03-25 13:00', status: '정상' },
  { name: 'GIS 데이터 연계', type: 'File (SFTP)', target: '공간정보시스템', format: 'SHP', count: '120건', lastSync: '2026-03-24 22:00', status: '오류' },
  { name: 'ERP 경영 데이터', type: 'DB Link', target: 'SAP ERP', format: 'DB', count: '9억건', lastSync: '2026-03-25 06:00', status: '정상' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.configs()
    const items = res.data.data
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        name: r.config_name || r.name || '',
        type: r.column_change_policy || r.type || '',
        target: r.target || '-',
        format: r.format || '-',
        count: r.count || '-',
        lastSync: r.lastSync || '-',
        status: r.status === 'ACTIVE' ? '정상' : r.status === 'ERROR' ? '오류' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DistributionConfig: API call failed, using mock data', e)
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
