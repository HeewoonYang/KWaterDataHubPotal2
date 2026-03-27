<template>
  <div class="admin-page">
    <div class="page-header"><h2>마이그레이션</h2><p class="page-desc">레거시 DB 데이터 마이그레이션 작업을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">마이그레이션 작업 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 작업 생성</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '마이그레이션')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 마이그레이션 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">작업 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">작업명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스</span><span class="info-value">{{ detailData.source }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">진행률</span><span class="info-value">{{ detailData.progress }}</span></div>
          <div class="modal-info-item"><span class="info-label">이관 건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '완료' ? 'badge-success' : detailData.status === '진행 중' ? 'badge-info' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 작업 생성 팝업 -->
    <AdminModal :visible="showRegister" title="작업 생성" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">작업명</label><input placeholder="작업명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소스</label><input placeholder="소스 DB" /></div>
          <div class="modal-form-group"><label class="required">대상</label><input placeholder="대상 DB" /></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="작업 설명"></textarea></div>
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
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '작업명', field: 'name', flex: 2 },
  { headerName: '소스', field: 'source', flex: 1 },
  { headerName: '대상', field: 'target', flex: 1 },
  { headerName: '진행률', field: 'progress', width: 80 },
  { headerName: '이관 건수', field: 'count', width: 100 },
  { headerName: '상태', field: 'status', width: 80 },
]
const rows = ref([
  { name: '수자원DB 전체 이관', source: 'Oracle (수자원)', target: 'PostgreSQL', progress: '100%', count: '2,450만', status: '완료' },
  { name: '경영정보 이관', source: 'MySQL (경영)', target: 'PostgreSQL', progress: '85%', count: '493만', status: '진행 중' },
  { name: '환경데이터 이관', source: 'MSSQL (환경)', target: 'PostgreSQL', progress: '45%', count: '540만', status: '진행 중' },
  { name: 'IoT 이력 이관', source: 'MongoDB (IoT)', target: 'PostgreSQL', progress: '0%', count: '-', status: '대기' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.migrations()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.migration_name || r.name || '',
        source: r.migration_type || r.source || '',
        target: r.target || 'PostgreSQL',
        progress: r.total_tables && r.completed_tables != null ? Math.round((r.completed_tables / r.total_tables) * 100) + '%' : (r.progress || '-'),
        count: r.total_tables ? r.total_tables + '테이블' : (r.count || '-'),
        status: r.status === 'COMPLETED' ? '완료' : r.status === 'RUNNING' ? '진행 중' : r.status === 'PENDING' ? '대기' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('Migration: API call failed, using mock data', e)
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
