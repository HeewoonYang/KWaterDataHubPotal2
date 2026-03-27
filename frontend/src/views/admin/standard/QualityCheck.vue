<template>
  <div class="admin-page">
    <div class="page-header"><h2>품질 검증</h2><p class="page-desc">데이터 품질 진단 규칙 및 검증 결과를 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">품질 진단 결과 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm"><ThunderboltOutlined /> 진단 실행</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '품질_진단')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 품질 진단 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.dataset + ' 품질 진단 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">진단 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋</span><span class="info-value">{{ detailData.dataset }}</span></div>
          <div class="modal-info-item"><span class="info-label">진단 항목</span><span class="info-value">{{ detailData.checkType }}</span></div>
          <div class="modal-info-item"><span class="info-label">전체 건수</span><span class="info-value">{{ detailData.total }}</span></div>
          <div class="modal-info-item"><span class="info-label">오류 건수</span><span class="info-value">{{ detailData.errors }}</span></div>
          <div class="modal-info-item"><span class="info-label">품질 점수</span><span class="info-value"><span class="badge" :class="detailData.score === '100%' ? 'badge-success' : 'badge-info'">{{ detailData.score }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">진단일</span><span class="info-value">{{ detailData.date }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { ThunderboltOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { qualityApi } from '../../../api/standard.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋', field: 'dataset', flex: 2 },
  { headerName: '진단 항목', field: 'checkType', flex: 1 },
  { headerName: '전체 건수', field: 'total', width: 90 },
  { headerName: '오류 건수', field: 'errors', width: 90 },
  { headerName: '품질 점수', field: 'score', width: 90 },
  { headerName: '진단일', field: 'date', width: 110 },
]
const rows = ref([
  { dataset: '댐 수위 관측 데이터', checkType: '완전성', total: '1,200만', errors: '152', score: '99.99%', date: '2026-03-25' },
  { dataset: '댐 수위 관측 데이터', checkType: '유효성', total: '1,200만', errors: '2,340', score: '99.98%', date: '2026-03-25' },
  { dataset: '수질 모니터링 센서', checkType: '완전성', total: '850만', errors: '8,500', score: '99.90%', date: '2026-03-25' },
  { dataset: '상수도 관로 GIS', checkType: '정확성', total: '320만', errors: '450', score: '99.99%', date: '2026-03-24' },
  { dataset: '전력 사용량 통계', checkType: '일관성', total: '15,600', errors: '0', score: '100%', date: '2026-03-24' },
])

onMounted(async () => {
  try {
    const res = await qualityApi.listResults()
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        dataset: r.dataset_name || '', checkType: r.check_type || '',
        total: r.total_count?.toLocaleString() || '0', errors: r.error_count?.toLocaleString() || '0',
        score: r.score ? `${r.score}%` : '0%', date: r.executed_at?.substring(0, 10) || '',
      }))
    }
  } catch (e) {
    console.warn('QualityCheck: API call failed, using mock data', e)
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
