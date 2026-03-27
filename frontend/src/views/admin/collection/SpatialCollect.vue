<template>
  <div class="admin-page">
    <div class="page-header"><h2>공간정보 수집</h2><p class="page-desc">GIS/공간정보 데이터 수집 설정을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">공간정보 소스 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 소스 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '공간정보_수집')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 소스 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">공간정보 소스 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">소스명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">좌표계</span><span class="info-value">{{ detailData.crs }}</span></div>
          <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol }}</span></div>
          <div class="modal-info-item"><span class="info-label">레이어 수</span><span class="info-value">{{ detailData.layers }}개</span></div>
          <div class="modal-info-item"><span class="info-label">최근 수집</span><span class="info-value">{{ detailData.lastSync }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 소스 추가 팝업 -->
    <AdminModal :visible="showRegister" title="소스 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">소스명</label><input placeholder="소스명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">좌표계</label><select><option>EPSG:5186</option><option>EPSG:4326</option><option>EPSG:5179</option></select></div>
          <div class="modal-form-group"><label class="required">프로토콜</label><select><option>WFS 2.0</option><option>WMS 1.3</option><option>GeoJSON</option></select></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="소스 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '소스명', field: 'name', flex: 2 },
  { headerName: '좌표계', field: 'crs', width: 110 },
  { headerName: '프로토콜', field: 'protocol', width: 100 },
  { headerName: '레이어 수', field: 'layers', width: 85 },
  { headerName: '최근 수집', field: 'lastSync', width: 120 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '상수도 관로 네트워크', crs: 'EPSG:5186', protocol: 'WFS 2.0', layers: 5, lastSync: '2026-03-25 01:00', status: '활성' },
  { name: '댐/저수지 위치', crs: 'EPSG:4326', protocol: 'WMS 1.3', layers: 3, lastSync: '2026-03-24 01:00', status: '활성' },
  { name: '하천 유역 경계', crs: 'EPSG:5186', protocol: 'WFS 2.0', layers: 2, lastSync: '2026-03-23 01:00', status: '활성' },
  { name: '수질 관측소 위치', crs: 'EPSG:4326', protocol: 'GeoJSON', layers: 1, lastSync: '2026-03-25 06:00', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.spatialConfigs()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.config_name || r.name || '',
        crs: r.coordinate_system || r.crs || '',
        protocol: r.spatial_data_type || r.protocol || '',
        layers: r.layers || '-',
        lastSync: r.lastSync || '-',
        status: r.status === 'ACTIVE' ? '활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('SpatialCollect: API call failed, using mock data', e)
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
