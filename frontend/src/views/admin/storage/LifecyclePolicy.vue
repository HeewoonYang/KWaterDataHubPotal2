<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>라이프사이클 정책*</h2>
      <p class="page-desc">GPU DB와 분석DB 간 데이터 보관/승격/삭제 정책을 관리합니다.</p>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">라이프사이클 정책 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 정책 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '라이프사이클_정책')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 라이프사이클 플로우 -->
    <div class="table-section" style="margin-top: 16px;">
      <div class="table-header"><span class="table-count">데이터 라이프사이클 플로우</span></div>
      <div class="flow-card">
        <pre class="flow-text">원천DB → 수집DB(PG) → 데이터 패브릭(T2SQL/MindsDB) → GPU DB (단기 보관: 1주~1월)
  │
  ├─ [조건 충족] 중요도 높음 OR 조회 빈도 많음 → 분석DB 승격 (이력 보관)
  ├─ [조건 미충족] 저사용 + 보관기간 초과 → 삭제 (이력만 분석DB에 보관)
  └─ 자연어질의 시 → 분석DB 우선 검색 → 없으면 GPU DB에서 신규 생성

  ※ 모든 수집 데이터가 분석DB로 이동하지 않습니다.
     중요도가 높거나 조회 빈도가 많은 데이터셋만 승격됩니다.</pre>
      </div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.policyName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">라이프사이클 정책 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">정책명</span><span class="info-value">{{ detailData.policyName }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">조건</span><span class="info-value">{{ detailData.criteria }}</span></div>
          <div class="modal-info-item"><span class="info-label">액션</span><span class="info-value">{{ detailData.action }}</span></div>
          <div class="modal-info-item"><span class="info-label">스케줄</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">마지막실행</span><span class="info-value">{{ detailData.lastRun }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 등록 팝업 -->
    <AdminModal :visible="showRegister" title="라이프사이클 정책 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">정책명</label><input v-model="regForm.policyName" placeholder="정책명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">대상</label><select v-model="regForm.target"><option>GPU DB</option><option>분석DB</option></select></div>
          <div class="modal-form-group"><label class="required">액션</label><select v-model="regForm.action"><option>분석DB 승격</option><option>삭제 (이력보관)</option><option>아카이브</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">조건</label><input v-model="regForm.criteria" placeholder="사용횟수 ≥ 100 AND 7일 이내 접근" /></div>
        <div class="modal-form-group"><label class="required">스케줄</label><input v-model="regForm.schedule" placeholder="매일 02:00" /></div>
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
  { headerName: '정책명', field: 'policyName', flex: 1.2, minWidth: 130 },
  { headerName: '대상', field: 'target', flex: 0.6, minWidth: 70 },
  { headerName: '조건', field: 'criteria', flex: 2, minWidth: 220 },
  { headerName: '액션', field: 'action', flex: 0.8, minWidth: 100 },
  { headerName: '스케줄', field: 'schedule', flex: 0.8, minWidth: 100 },
  { headerName: '마지막실행', field: 'lastRun', flex: 1, minWidth: 130 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { policyName: '고사용 자동승격', target: 'GPU DB', criteria: '사용횟수 ≥ 100 AND 7일 이내 접근', action: '분석DB 승격', schedule: '매일 02:00', lastRun: '2026-04-07 02:00', status: '활성' },
  { policyName: '저사용 만료삭제', target: 'GPU DB', criteria: '사용횟수 < 5 AND 보관기간 초과', action: '삭제 (이력보관)', schedule: '매일 03:00', lastRun: '2026-04-07 03:00', status: '활성' },
  { policyName: '중요도 기반 보관', target: 'GPU DB', criteria: '중요도등급 = A', action: '분석DB 승격', schedule: '매주 월 04:00', lastRun: '2026-04-07 04:00', status: '활성' },
  { policyName: '분석DB 아카이브', target: '분석DB', criteria: '마지막접근 > 90일', action: '아카이브', schedule: '매월 1일 05:00', lastRun: '2026-04-01 05:00', status: '활성' },
])

const regForm = reactive({ policyName: '', target: 'GPU DB', action: '분석DB 승격', criteria: '', schedule: '' })

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

function handleRegister() {
  if (!regForm.policyName || !regForm.criteria || !regForm.schedule) { message.warning('필수 항목을 입력하세요.'); return }
  rows.value.push({ ...regForm, lastRun: '-', status: '활성' })
  message.success('등록되었습니다.')
  showRegister.value = false
  Object.assign(regForm, { policyName: '', target: 'GPU DB', action: '분석DB 승격', criteria: '', schedule: '' })
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.flow-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 20px; }
.flow-text { background: #f8f9fa; padding: 16px 20px; border-radius: 6px; font-size: 13px; line-height: 1.8; margin: 0; font-family: 'D2Coding', 'Consolas', monospace; color: #333; white-space: pre; }
</style>
