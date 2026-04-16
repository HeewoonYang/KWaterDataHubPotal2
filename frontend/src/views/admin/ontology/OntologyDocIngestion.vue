<template>
  <div class="admin-page">
    <div class="page-header"><h2>비정형 문서 인제스트*</h2><p class="page-desc">매뉴얼, 절차서, 연보, 지침 등 비정형 문서를 인제스트하여 온톨로지 그래프에 통합합니다.</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-icon" style="background:#e6f7ff;color:#0066CC"><FileTextOutlined /></div><div class="kpi-body"><div class="kpi-value">42</div><div class="kpi-label">총 문서</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f6ffed;color:#28A745"><CheckCircleOutlined /></div><div class="kpi-body"><div class="kpi-value">35</div><div class="kpi-label">처리완료</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff7e6;color:#fa8c16"><SyncOutlined /></div><div class="kpi-body"><div class="kpi-value">4</div><div class="kpi-label">처리중</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f5f5f5;color:#999"><ClockCircleOutlined /></div><div class="kpi-body"><div class="kpi-value">3</div><div class="kpi-label">대기</div></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">전체 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 문서 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '비정형문서인제스트')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.docName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">문서 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">문서명</span><span class="info-value">{{ detailData.docName }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.docType }}</span></div>
          <div class="modal-info-item"><span class="info-label">파일크기</span><span class="info-value">{{ detailData.fileSize }}</span></div>
          <div class="modal-info-item"><span class="info-label">업로드일</span><span class="info-value">{{ detailData.uploadDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">처리상태</span><span class="info-value">{{ detailData.processStatus }}</span></div>
          <div class="modal-info-item"><span class="info-label">추출엔티티</span><span class="info-value">{{ detailData.entityCount }}</span></div>
          <div class="modal-info-item"><span class="info-label">그래프통합</span><span class="info-value">{{ detailData.graphStatus }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 등록 팝업 -->
    <AdminModal :visible="showRegister" title="문서 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">문서명</label><input v-model="regForm.docName" placeholder="문서명 입력" /></div>
        <div class="modal-form-group"><label class="required">유형</label><select v-model="regForm.docType"><option value="">선택</option><option>매뉴얼</option><option>절차서</option><option>연보</option><option>지침</option></select></div>
        <div class="modal-form-group"><label class="required">파일 업로드</label><input type="file" /></div>
        <div class="modal-form-group"><label>설명</label><textarea v-model="regForm.description" placeholder="문서에 대한 설명을 입력하세요" rows="3"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
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
import { FileTextOutlined, CheckCircleOutlined, SyncOutlined, ClockCircleOutlined, PlusOutlined, FileExcelOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const regForm = ref({ docName: '', docType: '', description: '' })
const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 45 },
  { headerName: '문서명', field: 'docName', flex: 1.3, minWidth: 160 },
  { headerName: '유형', field: 'docType', flex: 0.5, minWidth: 65 },
  { headerName: '파일크기', field: 'fileSize', flex: 0.6, minWidth: 75 },
  { headerName: '업로드일', field: 'uploadDate', flex: 0.7, minWidth: 90 },
  { headerName: '처리상태', field: 'processStatus', flex: 0.5, minWidth: 65 },
  { headerName: '추출엔티티', field: 'entityCount', flex: 0.6, minWidth: 75 },
  { headerName: '그래프통합', field: 'graphStatus', flex: 0.6, minWidth: 75 },
])
const rows = ref([
  { docName: '수자원관리 매뉴얼 v3.2', docType: '매뉴얼', fileSize: '12.5 MB', uploadDate: '2026-03-28', processStatus: '완료', entityCount: '1,560', graphStatus: '통합완료' },
  { docName: '정수장 운영 절차서', docType: '절차서', fileSize: '8.3 MB', uploadDate: '2026-03-29', processStatus: '완료', entityCount: '980', graphStatus: '통합완료' },
  { docName: '2025년 수자원 연보', docType: '연보', fileSize: '45.2 MB', uploadDate: '2026-04-01', processStatus: '완료', entityCount: '3,200', graphStatus: '통합완료' },
  { docName: '댐 안전관리 지침 개정', docType: '지침', fileSize: '5.1 MB', uploadDate: '2026-04-03', processStatus: '처리중', entityCount: '420', graphStatus: '진행중' },
  { docName: '관망 유지보수 매뉴얼', docType: '매뉴얼', fileSize: '15.8 MB', uploadDate: '2026-04-05', processStatus: '대기', entityCount: '0', graphStatus: '-' },
])

onMounted(() => {})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
function handleRegister() { message.success('등록되었습니다.'); showRegister.value = false; regForm.value = { docName: '', docType: '', description: '' } }
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
:deep(.ag-row) { cursor: pointer; }
</style>
