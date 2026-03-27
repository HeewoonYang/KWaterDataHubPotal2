<template>
  <div class="admin-page">
    <div class="page-header"><h2>표준화 관리</h2><p class="page-desc">데이터 유통 표준화 규칙 및 적용 현황을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">표준화 규칙 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 규칙 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '유통_표준화')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 표준화 규칙 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">표준화 규칙 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">규칙명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">적용 대상</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">표준 포맷</span><span class="info-value">{{ detailData.format }}</span></div>
          <div class="modal-info-item"><span class="info-label">적용률</span><span class="info-value">{{ detailData.rate }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 규칙 추가 팝업 -->
    <AdminModal :visible="showRegister" title="규칙 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">규칙명</label><input placeholder="규칙명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">적용 대상</label><input placeholder="적용 대상" /></div>
          <div class="modal-form-group"><label class="required">표준 포맷</label><input placeholder="표준 포맷" /></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="규칙 설명"></textarea></div>
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
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '규칙명', field: 'name', flex: 2 },
  { headerName: '적용 대상', field: 'target', flex: 1 },
  { headerName: '표준 포맷', field: 'format', width: 100 },
  { headerName: '적용률', field: 'rate', width: 80 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '날짜/시간 ISO 8601 표준화', target: '전체 데이터셋', format: 'ISO 8601', rate: '98%', status: '활성' },
  { name: '코드값 표준코드 매핑', target: '코드 포함 데이터', format: 'K-water 표준코드', rate: '95%', status: '활성' },
  { name: '좌표계 WGS84 통일', target: 'GIS 데이터셋', format: 'EPSG:4326', rate: '100%', status: '활성' },
  { name: '단위 SI 단위 통일', target: '계측 데이터', format: 'SI 단위계', rate: '92%', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.configs()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.config_name || r.name || '',
        target: r.target || '-',
        format: r.column_change_policy || r.format || '',
        rate: r.rate || '-',
        status: r.status === 'ACTIVE' ? '활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DistStandard: API call failed, using mock data', e)
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
