<template>
  <div class="admin-page">
    <div class="page-header"><h2>변환 관리</h2><p class="page-desc">데이터 모델링/변환 규칙 및 파이프라인을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">변환 규칙 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 규칙 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '변환_규칙')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 변환 규칙 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">변환 규칙 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">변환 규칙명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스 스키마</span><span class="info-value">{{ detailData.source }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 스키마</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">변환 유형</span><span class="info-value">{{ detailData.type }}</span></div>
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
        <div class="modal-form-group"><label class="required">변환 규칙명</label><input placeholder="규칙명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소스 스키마</label><input placeholder="소스 스키마" /></div>
          <div class="modal-form-group"><label class="required">대상 스키마</label><input placeholder="대상 스키마" /></div>
        </div>
        <div class="modal-form-group"><label class="required">변환 유형</label><select><option>단위변환</option><option>포맷변환</option><option>좌표변환</option><option>코드매핑</option></select></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCleansingApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '변환 규칙명', field: 'name', flex: 2 },
  { headerName: '소스 스키마', field: 'source', flex: 1 },
  { headerName: '대상 스키마', field: 'target', flex: 1 },
  { headerName: '변환 유형', field: 'type', flex: 0.8, minWidth: 80 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { name: '수위 데이터 단위 통일', source: 'cm/m 혼재', target: 'm 통일', type: '단위변환', status: '활성' },
  { name: '날짜 포맷 표준화', source: 'YYYYMMDD 외', target: 'ISO 8601', type: '포맷변환', status: '활성' },
  { name: '좌표계 변환', source: 'EPSG:5186', target: 'EPSG:4326', type: '좌표변환', status: '활성' },
  { name: '코드값 매핑', source: '기관별 코드', target: 'K-water 표준코드', type: '코드매핑', status: '활성' },
])


onMounted(async () => {
  try {
    const res = await adminCleansingApi.transforms()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.model_name || r.name || '',
        source: r.source || '-',
        target: r.target || '-',
        type: r.transform_type || r.type || '',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'INACTIVE' ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('TransformManage: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
function handleRegister() { message.success("등록되었습니다."); showRegister.value = false }
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
