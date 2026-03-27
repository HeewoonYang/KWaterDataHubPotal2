<template>
  <div class="admin-page">
    <div class="page-header"><h2>AI 현황</h2><p class="page-desc">AI 기반 데이터 분석 및 이상 탐지 현황을 모니터링합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">AI 모델 실행 현황 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'AI_모니터링')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- AI 모델 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">AI 모델 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">AI 모델명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 데이터</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">금일 실행</span><span class="info-value">{{ detailData.runs }}</span></div>
          <div class="modal-info-item"><span class="info-label">정확도</span><span class="info-value">{{ detailData.accuracy }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
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
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { RobotOutlined, ExperimentOutlined, AlertOutlined, CheckCircleOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminOperationApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: RobotOutlined, label: '활성 모델', value: '5', color: '#0066CC' },
  { icon: ExperimentOutlined, label: '금일 추론', value: '12,500', color: '#28A745' },
  { icon: AlertOutlined, label: '이상 탐지', value: '23', color: '#DC3545' },
  { icon: CheckCircleOutlined, label: '정확도', value: '96.5%', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: 'AI 모델명', field: 'name', flex: 2 },
  { headerName: '유형', field: 'type', width: 110 },
  { headerName: '대상 데이터', field: 'target', flex: 1 },
  { headerName: '금일 실행', field: 'runs', width: 90 },
  { headerName: '정확도', field: 'accuracy', width: 80 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '수질 이상값 탐지', type: '이상탐지', target: '수질 센서 데이터', runs: '4,200', accuracy: '97.2%', status: '활성' },
  { name: '수위 예측 모델', type: '시계열 예측', target: '댐 수위 데이터', runs: '2,880', accuracy: '95.8%', status: '활성' },
  { name: '관로 누수 예측', type: '분류', target: 'GIS+유량 데이터', runs: '720', accuracy: '94.5%', status: '활성' },
  { name: '자연어 검색 (NLP)', type: 'NLP', target: '카탈로그 메타데이터', runs: '3,500', accuracy: '96.8%', status: '활성' },
  { name: '전력 소비 예측', type: '시계열 예측', target: '전력 사용량', runs: '1,200', accuracy: '93.2%', status: '학습 중' },
])

onMounted(async () => {
  try {
    const res = await adminOperationApi.aiLogs()
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.model_name || r.name || '',
        type: r.query_type || r.type || '',
        target: r.target || '-',
        runs: r.token_count != null ? r.token_count.toLocaleString() : (r.runs || '-'),
        accuracy: r.satisfaction_rating != null ? r.satisfaction_rating + '%' : (r.accuracy || '-'),
        status: r.status || '활성',
      }))
    }
  } catch (e) {
    console.warn('AiMonitor: API call failed, using mock data', e)
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
