<template>
  <div class="admin-page">
    <div class="page-header"><h2>데이터셋 구성</h2><p class="page-desc">수집 대상 데이터셋을 정의하고 구성합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">데이터셋 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 데이터셋 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '데이터셋_설정')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 데이터셋 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">데이터셋 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스 유형</span><span class="info-value">{{ detailData.sourceType }}</span></div>
          <div class="modal-info-item"><span class="info-label">테이블/토픽</span><span class="info-value">{{ detailData.table }}</span></div>
          <div class="modal-info-item"><span class="info-label">컬럼 수</span><span class="info-value">{{ detailData.columns }}개</span></div>
          <div class="modal-info-item"><span class="info-label">수집 주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 데이터셋 추가 팝업 -->
    <AdminModal :visible="showRegister" title="데이터셋 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">데이터셋명</label><input placeholder="데이터셋명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소스 유형</label><select><option>Oracle DB</option><option>Kafka</option><option>GIS API</option><option>CSV</option><option>REST API</option></select></div>
          <div class="modal-form-group"><label class="required">수집 주기</label><select><option>실시간</option><option>10분</option><option>1시간</option><option>일 1회</option><option>월 1회</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">테이블/토픽</label><input placeholder="테이블명 또는 토픽명" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="데이터셋 설명"></textarea></div>
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
  { headerName: '데이터셋명', field: 'name', flex: 2 },
  { headerName: '소스 유형', field: 'sourceType', width: 100 },
  { headerName: '테이블/토픽', field: 'table', flex: 1 },
  { headerName: '컬럼 수', field: 'columns', width: 75 },
  { headerName: '수집 주기', field: 'schedule', width: 90 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '댐 수위 관측 데이터', sourceType: 'Oracle DB', table: 'TM_DAM_LEVEL', columns: 12, schedule: '10분', status: '활성' },
  { name: '수질 모니터링 센서', sourceType: 'Kafka', table: 'iot.water-quality', columns: 18, schedule: '실시간', status: '활성' },
  { name: '상수도 관로 GIS', sourceType: 'GIS API', table: '/wfs/pipeline', columns: 24, schedule: '일 1회', status: '활성' },
  { name: '전력 사용량 통계', sourceType: 'CSV', table: '/data/power/*.csv', columns: 8, schedule: '월 1회', status: '활성' },
  { name: '하천 유량 관측', sourceType: 'REST API', table: '/api/river/flow', columns: 10, schedule: '1시간', status: '일시정지' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.datasetConfigs()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.dataset_name || r.name || '',
        sourceType: r.source_name || r.sourceType || '',
        table: r.source_table || r.table || '',
        columns: r.columns || '-',
        schedule: r.schedule || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'PAUSED' ? '일시정지' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DatasetConfig: API call failed, using mock data', e)
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
