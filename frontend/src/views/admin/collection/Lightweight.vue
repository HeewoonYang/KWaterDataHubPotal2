<template>
  <div class="admin-page">
    <div class="page-header"><h2>경량 수집</h2><p class="page-desc">경량 에이전트 기반 소규모 데이터 수집을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">경량 수집 에이전트 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 에이전트 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '경량_에이전트')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 에이전트 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">에이전트 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">에이전트명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 시스템</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">수집 방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 실행</span><span class="info-value">{{ detailData.lastRun }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 에이전트 등록 팝업 -->
    <AdminModal :visible="showRegister" title="에이전트 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">에이전트명</label><input placeholder="에이전트명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">대상 시스템</label><input placeholder="대상 시스템" /></div>
          <div class="modal-form-group"><label class="required">수집 방식</label><select><option>HTTP POST</option><option>File Upload</option><option>SFTP</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">주기</label><select><option>수동</option><option>일 1회</option><option>주 1회</option></select></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="에이전트 설명"></textarea></div>
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
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '에이전트명', field: 'name', flex: 2 },
  { headerName: '대상 시스템', field: 'target', flex: 1 },
  { headerName: '수집 방식', field: 'method', width: 100 },
  { headerName: '주기', field: 'schedule', width: 80 },
  { headerName: '최근 실행', field: 'lastRun', width: 120 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '현장 수질측정 Agent', target: '현장 태블릿', method: 'HTTP POST', schedule: '수동', lastRun: '2026-03-25 09:15', status: '활성' },
  { name: '엑셀 업로드 Agent', target: '관리자 PC', method: 'File Upload', schedule: '수동', lastRun: '2026-03-24 15:30', status: '활성' },
  { name: '외부 CSV 수집', target: 'FTP Server', method: 'SFTP', schedule: '일 1회', lastRun: '2026-03-25 06:00', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.jobs({ status: 'RUNNING' })
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.dataset_name || r.name || '',
        target: r.target || '-',
        method: r.method || '-',
        schedule: r.schedule || '-',
        lastRun: r.started_at ? String(r.started_at).replace('T', ' ').substring(0, 16) : (r.lastRun || '-'),
        status: r.job_status === 'RUNNING' ? '활성' : r.job_status === 'COMPLETED' ? '완료' : (r.status || r.job_status || '-'),
      }))
    }
  } catch (e) {
    console.warn('Lightweight: API call failed, using mock data', e)
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
