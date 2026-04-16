<template>
  <div class="admin-page">
    <div class="page-header"><h2>등급 분류</h2><p class="page-desc">데이터 보안 등급 분류 기준 및 등급별 정책을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">등급 체계 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '등급_관리')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 등급 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">등급 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">등급</span><span class="info-value">{{ detailData.grade }}</span></div>
          <div class="modal-info-item"><span class="info-label">등급명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">설명</span><span class="info-value">{{ detailData.desc }}</span></div>
          <div class="modal-info-item"><span class="info-label">접근 대상</span><span class="info-value">{{ detailData.access }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터셋 수</span><span class="info-value">{{ detailData.count }}개</span></div>
          <div class="modal-info-item"><span class="info-label">비식별화</span><span class="info-value">{{ detailData.anonymize }}</span></div>
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
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { gradeApi } from '../../../api/standard.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: '등급', field: 'grade', width: 90 },
  { headerName: '등급명', field: 'name', width: 110 },
  { headerName: '설명', field: 'desc', flex: 2 },
  { headerName: '접근 대상', field: 'access', flex: 1 },
  { headerName: '데이터셋 수', field: 'count', width: 100 },
  { headerName: '비식별화', field: 'anonymize', width: 90 },
])
const rows = ref([
  { grade: 'L1', name: '비공개', desc: '개인정보, 보안데이터 등 접근 제한', access: '시스템 관리자만', count: 45, anonymize: '필수' },
  { grade: 'L2', name: '내부공유', desc: 'K-water 내부 직원 공유 데이터', access: '내부 사용자 이상', count: 320, anonymize: '선택' },
  { grade: 'L3', name: '공개', desc: '외부 공개 가능 데이터', access: '전체 사용자', count: 580, anonymize: '불필요' },
])

onMounted(async () => {
  try {
    const res = await gradeApi.list()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        grade: r.grade_code, name: r.grade_name, desc: r.description || '',
        access: r.access_scope || '', count: r.dataset_count || 0, anonymize: r.anonymize_required || '',
      }))
    }
  } catch (e) {
    console.warn('GradeManage: API call failed, using mock data', e)
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
