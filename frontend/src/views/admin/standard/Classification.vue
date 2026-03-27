<template>
  <div class="admin-page">
    <div class="page-header"><h2>분류 등록</h2><p class="page-desc">데이터 분류 체계를 등록하고 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">분류 체계 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '분류_체계')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 분류 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.code + ' 분류 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">분류 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">대분류</span><span class="info-value">{{ detailData.category1 }}</span></div>
          <div class="modal-info-item"><span class="info-label">중분류</span><span class="info-value">{{ detailData.category2 }}</span></div>
          <div class="modal-info-item"><span class="info-label">소분류</span><span class="info-value">{{ detailData.category3 }}</span></div>
          <div class="modal-info-item"><span class="info-label">코드</span><span class="info-value">{{ detailData.code }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터셋 수</span><span class="info-value">{{ detailData.count }}개</span></div>
          <div class="modal-info-item"><span class="info-label">등록일</span><span class="info-value">{{ detailData.regDate }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 분류 등록 팝업 -->
    <AdminModal :visible="showRegister" title="분류 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">대분류</label><select><option>수자원</option><option>환경</option><option>시설</option><option>경영</option></select></div>
          <div class="modal-form-group"><label class="required">중분류</label><input placeholder="중분류 입력" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소분류</label><input placeholder="소분류 입력" /></div>
          <div class="modal-form-group"><label class="required">코드</label><input placeholder="코드 (예: WR-DAM-LV)" /></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="분류 설명"></textarea></div>
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
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { classificationApi } from '../../../api/standard.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '대분류', field: 'category1', flex: 1 },
  { headerName: '중분류', field: 'category2', flex: 1 },
  { headerName: '소분류', field: 'category3', flex: 1 },
  { headerName: '코드', field: 'code', width: 110 },
  { headerName: '데이터셋 수', field: 'count', width: 90 },
  { headerName: '등록일', field: 'regDate', width: 110 },
]
const rows = ref([
  { category1: '수자원', category2: '댐', category3: '수위', code: 'WR-DAM-LV', count: 15, regDate: '2026-01-10' },
  { category1: '수자원', category2: '댐', category3: '유량', code: 'WR-DAM-FL', count: 12, regDate: '2026-01-10' },
  { category1: '수자원', category2: '하천', category3: '수위', code: 'WR-RIV-LV', count: 24, regDate: '2026-01-12' },
  { category1: '환경', category2: '수질', category3: 'IoT센서', code: 'EN-WQ-IOT', count: 8, regDate: '2026-01-15' },
  { category1: '환경', category2: '수질', category3: '검사결과', code: 'EN-WQ-TST', count: 6, regDate: '2026-01-15' },
  { category1: '시설', category2: '관로', category3: 'GIS', code: 'FA-PP-GIS', count: 3, regDate: '2026-02-01' },
])

onMounted(async () => {
  try {
    const res = await classificationApi.list()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        category1: r.name || '', category2: '', category3: '',
        code: r.code || '', count: r.dataset_count || 0, regDate: '',
      }))
    }
  } catch (e) {
    console.warn('Classification: API call failed, using mock data', e)
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
