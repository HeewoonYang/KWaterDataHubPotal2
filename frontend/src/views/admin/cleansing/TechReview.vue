<template>
  <div class="admin-page">
    <div class="page-header"><h2>기술 검토</h2><p class="page-desc">데이터 정제 기술 적용 현황 및 검토 결과를 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">기술 검토 항목 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '기술_검토')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 검토 항목 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.item + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">기술 검토 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">검토 항목</span><span class="info-value">{{ detailData.item }}</span></div>
          <div class="modal-info-item"><span class="info-label">적용 기술</span><span class="info-value">{{ detailData.tech }}</span></div>
          <div class="modal-info-item"><span class="info-label">검토 결과</span><span class="info-value"><span class="badge" :class="detailData.result === '적합' ? 'badge-success' : 'badge-warning'">{{ detailData.result }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">검토자</span><span class="info-value">{{ detailData.reviewer }}</span></div>
          <div class="modal-info-item"><span class="info-label">검토일</span><span class="info-value">{{ detailData.date }}</span></div>
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
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCleansingApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '검토 항목', field: 'item', flex: 2 },
  { headerName: '적용 기술', field: 'tech', flex: 1 },
  { headerName: '검토 결과', field: 'result', flex: 0.7, minWidth: 80 },
  { headerName: '검토자', field: 'reviewer', flex: 0.7, minWidth: 80 },
  { headerName: '검토일', field: 'date', flex: 0.8, minWidth: 100 },
])
const rows = ref([
  { item: '결측값 보간 알고리즘', tech: '선형보간 / KNN', result: '적합', reviewer: '김매니저', date: '2026-03-20' },
  { item: '이상값 탐지 모델', tech: 'IQR / Z-Score', result: '적합', reviewer: '김매니저', date: '2026-03-18' },
  { item: '중복 제거 전략', tech: 'Hash 기반 중복 탐지', result: '적합', reviewer: '관리자', date: '2026-03-15' },
  { item: '데이터 타입 변환', tech: 'Schema Evolution', result: '보완필요', reviewer: '관리자', date: '2026-03-12' },
  { item: '인코딩 통일', tech: 'UTF-8 자동 변환', result: '적합', reviewer: '김매니저', date: '2026-03-10' },
])

onMounted(async () => {
  try {
    const res = await adminCleansingApi.rules()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        item: r.rule_name || r.item || '',
        tech: r.rule_type || r.tech || '',
        result: r.is_active === true ? '적합' : r.is_active === false ? '보완필요' : (r.result || '-'),
        reviewer: r.reviewer || '-',
        date: r.date || '-',
      }))
    }
  } catch (e) {
    console.warn('TechReview: API call failed, using mock data', e)
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
