<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>MindsDB 연동*</h2>
      <p class="page-desc">MindsDB를 활용한 데이터 패브릭 및 예측 모델을 관리합니다.</p>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">MindsDB 모델 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 모델 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'MindsDB_모델')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.modelName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">MindsDB 모델 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">모델명</span><span class="info-value">{{ detailData.modelName }}</span></div>
          <div class="modal-info-item"><span class="info-label">예측대상</span><span class="info-value">{{ detailData.predTarget }}</span></div>
          <div class="modal-info-item"><span class="info-label">학습데이터셋</span><span class="info-value">{{ detailData.trainDataset }}</span></div>
          <div class="modal-info-item"><span class="info-label">정확도</span><span class="info-value">{{ detailData.accuracy }}</span></div>
          <div class="modal-info-item"><span class="info-label">최종학습</span><span class="info-value">{{ detailData.lastTrained }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 등록 팝업 -->
    <AdminModal :visible="showRegister" title="MindsDB 모델 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">모델명</label><input v-model="regForm.modelName" placeholder="모델명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">예측대상</label><input v-model="regForm.predTarget" placeholder="예측 대상 입력" /></div>
          <div class="modal-form-group"><label class="required">학습데이터셋</label><input v-model="regForm.trainDataset" placeholder="학습 데이터셋명" /></div>
        </div>
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
import { ref, reactive } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }

const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '모델명', field: 'modelName', flex: 1.2, minWidth: 120 },
  { headerName: '예측대상', field: 'predTarget', flex: 1, minWidth: 120 },
  { headerName: '학습데이터셋', field: 'trainDataset', flex: 1.2, minWidth: 140 },
  { headerName: '정확도', field: 'accuracy', flex: 0.6, minWidth: 70 },
  { headerName: '최종학습', field: 'lastTrained', flex: 0.8, minWidth: 100 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { modelName: '수질이상 탐지', predTarget: 'pH/DO 이상치', trainDataset: '수질 측정 이력 (3년)', accuracy: '96.2%', lastTrained: '2026-04-01', status: '활성' },
  { modelName: '댐 수위 예측', predTarget: '24시간 수위 예측', trainDataset: '댐 수위 일별 통계', accuracy: '93.8%', lastTrained: '2026-04-03', status: '활성' },
  { modelName: '관망 누수 예측', predTarget: '누수 확률', trainDataset: '관망 누수 분석', accuracy: '91.5%', lastTrained: '2026-03-28', status: '활성' },
  { modelName: '자산 교체 시기', predTarget: '교체 필요 시점', trainDataset: '자산 노후화 예측', accuracy: '88.3%', lastTrained: '2026-03-25', status: '학습중' },
])

const regForm = reactive({ modelName: '', predTarget: '', trainDataset: '' })

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

function handleRegister() {
  if (!regForm.modelName || !regForm.predTarget) { message.warning('필수 항목을 입력하세요.'); return }
  rows.value.push({ ...regForm, accuracy: '-', lastTrained: '-', status: '대기' })
  message.success('등록되었습니다.')
  showRegister.value = false
  Object.assign(regForm, { modelName: '', predTarget: '', trainDataset: '' })
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
