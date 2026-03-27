<template>
  <div class="admin-page">
    <div class="page-header"><h2>융합 모델</h2><p class="page-desc">다중 데이터셋 융합 모델을 정의하고 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">융합 모델 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 모델 생성</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '융합_모델')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 융합 모델 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">융합 모델 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">모델명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스 데이터셋</span><span class="info-value">{{ detailData.sources }}</span></div>
          <div class="modal-info-item"><span class="info-label">융합 방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">갱신 주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 모델 생성 팝업 -->
    <AdminModal :visible="showRegister" title="모델 생성" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">모델명</label><input placeholder="모델명 입력" /></div>
        <div class="modal-form-group"><label class="required">소스 데이터셋</label><input placeholder="소스 데이터셋 (콤마 구분)" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">융합 방식</label><select><option>JOIN</option><option>UNION+보정</option><option>공간JOIN</option></select></div>
          <div class="modal-form-group"><label class="required">갱신 주기</label><select><option>10분</option><option>1시간</option><option>일 1회</option></select></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 생성</button>
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
  { headerName: '모델명', field: 'name', flex: 2 },
  { headerName: '소스 데이터셋', field: 'sources', flex: 1 },
  { headerName: '융합 방식', field: 'method', width: 110 },
  { headerName: '갱신 주기', field: 'schedule', width: 90 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '댐 종합 현황', sources: '수위+유량+기상', method: 'JOIN', schedule: '10분', status: '활성' },
  { name: '수질 통합 분석', sources: '수질센서+검사결과', method: 'UNION+보정', schedule: '1시간', status: '활성' },
  { name: '관로-수질 연계', sources: 'GIS관로+수질관측', method: '공간JOIN', schedule: '일 1회', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.fusionModels()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.model_name || r.name || '',
        sources: r.fusion_type || r.sources || '',
        method: r.method || '-',
        schedule: r.schedule || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.poc_status || (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('FusionModel: API call failed, using mock data', e)
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
