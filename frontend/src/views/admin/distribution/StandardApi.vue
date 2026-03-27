<template>
  <div class="admin-page">
    <div class="page-header"><h2>표준 API</h2><p class="page-desc">데이터허브 표준 REST API 관리 및 모니터링합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">API 목록 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> API 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '표준_API')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- API 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">API 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">API명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">Method</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">Endpoint</span><span class="info-value">{{ detailData.endpoint }}</span></div>
          <div class="modal-info-item"><span class="info-label">버전</span><span class="info-value">{{ detailData.version }}</span></div>
          <div class="modal-info-item"><span class="info-label">일 호출</span><span class="info-value">{{ detailData.calls }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge badge-success">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- API 등록 팝업 -->
    <AdminModal :visible="showRegister" title="API 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">API명</label><input placeholder="API명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">Method</label><select><option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option></select></div>
          <div class="modal-form-group"><label class="required">버전</label><select><option>v1</option><option>v2</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">Endpoint</label><input placeholder="/api/v1/..." /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="API 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { ApiOutlined, CheckCircleOutlined, DashboardOutlined, ThunderboltOutlined, PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: ApiOutlined, label: '등록 API', value: '32', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '활성', value: '28', color: '#28A745' },
  { icon: DashboardOutlined, label: '평균 응답', value: '125ms', color: '#9b59b6' },
  { icon: ThunderboltOutlined, label: '일 호출량', value: '1.45M', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: 'API명', field: 'name', flex: 2 },
  { headerName: 'Method', field: 'method', width: 75 },
  { headerName: 'Endpoint', field: 'endpoint', flex: 2 },
  { headerName: '버전', field: 'version', width: 65 },
  { headerName: '일 호출', field: 'calls', width: 80 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '데이터셋 목록 조회', method: 'GET', endpoint: '/api/v1/datasets', version: 'v1', calls: '45,200', status: '활성' },
  { name: '데이터셋 상세 조회', method: 'GET', endpoint: '/api/v1/datasets/{id}', version: 'v1', calls: '32,100', status: '활성' },
  { name: '수위 데이터 조회', method: 'GET', endpoint: '/api/v1/dam/levels', version: 'v1', calls: '128,500', status: '활성' },
  { name: '수질 데이터 조회', method: 'GET', endpoint: '/api/v1/water-quality', version: 'v1', calls: '85,300', status: '활성' },
  { name: '데이터 다운로드', method: 'POST', endpoint: '/api/v1/downloads', version: 'v1', calls: '2,340', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.apiEndpoints()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.api_name || r.name || '',
        method: r.http_method || r.method || '',
        endpoint: r.api_path || r.endpoint || '',
        version: r.version || 'v1',
        calls: r.rate_limit_per_min != null ? r.rate_limit_per_min + '/분' : (r.calls || '-'),
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'INACTIVE' ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('StandardApi: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
