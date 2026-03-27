<template>
  <div class="admin-page">
    <div class="page-header"><h2>비식별화</h2><p class="page-desc">개인정보 비식별화 정책 및 처리 현황을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">비식별화 규칙 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 규칙 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '비식별화_규칙')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 비식별화 규칙 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">비식별화 규칙 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">규칙명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 컬럼</span><span class="info-value">{{ detailData.column }}</span></div>
          <div class="modal-info-item"><span class="info-label">처리 방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">적용 데이터셋</span><span class="info-value">{{ detailData.datasets }}개</span></div>
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
          <div class="modal-form-group"><label class="required">대상 컬럼</label><input placeholder="컬럼명" /></div>
          <div class="modal-form-group"><label class="required">처리 방식</label><select><option>부분 마스킹</option><option>가명처리</option><option>범주화</option><option>총계처리</option><option>데이터 삭제</option></select></div>
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
import { adminCleansingApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '규칙명', field: 'name', flex: 2 },
  { headerName: '대상 컬럼', field: 'column', flex: 1 },
  { headerName: '처리 방식', field: 'method', width: 110 },
  { headerName: '적용 데이터셋', field: 'datasets', width: 100 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '주민등록번호 마스킹', column: 'SSN / 주민번호', method: '부분 마스킹', datasets: 3, status: '활성' },
  { name: '이름 가명처리', column: 'NAME / 성명', method: '가명처리', datasets: 5, status: '활성' },
  { name: '전화번호 일반화', column: 'PHONE / 전화번호', method: '범주화', datasets: 4, status: '활성' },
  { name: '주소 총계처리', column: 'ADDRESS / 주소', method: '총계처리', datasets: 2, status: '활성' },
  { name: 'IP주소 삭제', column: 'IP_ADDR', method: '데이터 삭제', datasets: 1, status: '비활성' },
])

onMounted(async () => {
  try {
    const res = await adminCleansingApi.anonymization()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.config_name || r.name || '',
        column: r.column || '-',
        method: r.method || '',
        datasets: r.datasets || '-',
        status: r.is_active === true ? '활성' : r.is_active === false ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('Anonymize: API call failed, using mock data', e)
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
