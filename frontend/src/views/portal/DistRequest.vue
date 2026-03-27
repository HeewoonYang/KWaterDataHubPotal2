<template>
  <div class="request-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">데이터 신청</span>
    </nav>

    <div class="page-header">
      <h2>데이터 신청</h2>
      <p>데이터셋 이용을 신청하고 승인 현황을 확인합니다.</p>
    </div>
    <div class="request-tabs">
      <button :class="{ active: tab === 'new' }" @click="tab = 'new'"><FormOutlined /> 신규 신청</button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'"><HistoryOutlined /> 신청 이력</button>
    </div>

    <!-- 신규 신청 -->
    <div v-if="tab === 'new'" class="new-request">
      <div class="form-card">
        <div class="form-group"><label>데이터셋 선택</label><select><option>댐 수위 관측 데이터</option><option>수질 모니터링 센서 데이터</option><option>상수도 관로 GIS 데이터</option><option>하천 유량 관측 데이터</option></select></div>
        <div class="form-group"><label>신청 사유</label><textarea rows="3" placeholder="데이터 이용 목적을 입력하세요"></textarea></div>
        <div class="form-row">
          <div class="form-group"><label>이용 기간 (시작)</label><input type="date" value="2026-03-25" /></div>
          <div class="form-group"><label>이용 기간 (종료)</label><input type="date" value="2026-06-25" /></div>
        </div>
        <div class="form-group"><label>이용 포맷</label>
          <div class="format-options">
            <label class="radio-label"><input type="radio" name="format" value="csv" checked /> CSV</label>
            <label class="radio-label"><input type="radio" name="format" value="json" /> JSON</label>
            <label class="radio-label"><input type="radio" name="format" value="api" /> API</label>
          </div>
        </div>
        <div class="form-actions"><button class="btn btn-primary" @click="showConfirm = true"><SendOutlined /> 신청</button><button class="btn btn-outline">취소</button></div>
      </div>
    </div>

    <!-- 신청 이력 -->
    <div v-if="tab === 'history'" class="request-history">
      <div class="table-section">
        <div class="table-header"><span class="table-count">전체 <strong>{{ history.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, history, '유통_신청_이력')"><FileExcelOutlined /></button></div></div>
        <div class="ag-grid-wrapper">
          <AgGridVue class="ag-theme-alpine" :rowData="history" :columnDefs="cols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" />
        </div>
      </div>
    </div>

    <!-- 신청 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="'신청 상세 - ' + detailData.dataset" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">신청 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋</span><span class="info-value">{{ detailData.dataset }}</span></div>
          <div class="modal-info-item"><span class="info-label">신청일</span><span class="info-value">{{ detailData.requestDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">이용기간</span><span class="info-value">{{ detailData.period }}</span></div>
          <div class="modal-info-item"><span class="info-label">포맷</span><span class="info-value">{{ detailData.format }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '승인' ? 'badge-success' : detailData.status === '검토중' ? 'badge-warning' : 'badge-danger'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 신청 확인 팝업 -->
    <AdminModal :visible="showConfirm" title="데이터 신청 확인" size="sm" @close="showConfirm = false">
      <div style="text-align: center; padding: 16px 0;">
        <p style="font-size: 14px; color: #555; margin-bottom: 8px;">선택한 데이터셋의 이용을 신청하시겠습니까?</p>
        <p style="font-size: 12px; color: #999;">신청 후 관리자 승인 절차가 진행됩니다.</p>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="submitRequest"><CheckCircleOutlined /> 신청</button>
        <button class="btn btn-outline" @click="showConfirm = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../utils/exportExcel'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { FormOutlined, HistoryOutlined, SendOutlined, FileExcelOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../components/AdminModal.vue'
import { distributionApi } from '../../api/portal.api'
ModuleRegistry.registerModules([AllCommunityModule])

const tab = ref('new')
const showDetail = ref(false), showConfirm = ref(false)
const detailData = ref<any>({})

// Form fields for new request
const requestForm = ref({
  dataset: '댐 수위 관측 데이터',
  reason: '',
  startDate: '2026-03-25',
  endDate: '2026-06-25',
  format: 'csv',
})

const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋', field: 'dataset', flex: 2, minWidth: 180 },
  { headerName: '신청일', field: 'requestDate', width: 110, maxWidth: 110, flex: 0 },
  { headerName: '이용기간', field: 'period', flex: 1, minWidth: 150 },
  { headerName: '포맷', field: 'format', width: 65, maxWidth: 65, flex: 0 },
  { headerName: '상태', field: 'status', width: 75, maxWidth: 75, flex: 0 },
]

// Fallback mock data
const defaultHistory = [
  { dataset: '댐 수위 관측 데이터', requestDate: '2026-03-20', period: '2026-03-20 ~ 2026-06-20', format: 'CSV', status: '승인' },
  { dataset: '수질 모니터링 센서 데이터', requestDate: '2026-03-18', period: '2026-03-18 ~ 2026-09-18', format: 'API', status: '승인' },
  { dataset: '상수도 관로 GIS 데이터', requestDate: '2026-03-15', period: '2026-03-15 ~ 2026-06-15', format: 'JSON', status: '검토중' },
  { dataset: '환경영향평가 보고서', requestDate: '2026-03-10', period: '2026-03-10 ~ 2026-04-10', format: 'CSV', status: '반려' },
]

const history = ref(defaultHistory)

async function fetchHistory() {
  try {
    const res = await distributionApi.requests({ page: 1, page_size: 20 })
    if (res.data?.items?.length) {
      history.value = res.data.items.map((item: any) => ({
        id: item.id,
        dataset: item.purpose || '데이터 신청',
        requestDate: item.created_at ? item.created_at.substring(0, 10) : '',
        period: item.created_at ? `${item.created_at.substring(0, 10)} ~` : '',
        format: item.requested_format || '',
        status: item.status === 'APPROVED' ? '승인' : item.status === 'REJECTED' ? '반려' : item.status === 'PENDING' ? '검토중' : item.status,
      }))
    }
  } catch (e) {
    console.error('신청 이력 조회 실패:', e)
  }
}

async function submitRequest() {
  try {
    await distributionApi.createRequest({
      dataset: requestForm.value.dataset,
      reason: requestForm.value.reason,
      startDate: requestForm.value.startDate,
      endDate: requestForm.value.endDate,
      format: requestForm.value.format,
    })
    showConfirm.value = false
    await fetchHistory()
    tab.value = 'history'
  } catch (e) {
    console.error('데이터 신청 실패:', e)
    showConfirm.value = false
  }
}

onMounted(() => { fetchHistory() })

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.request-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.request-tabs { display: flex; gap: $spacing-sm;
  button { padding: 8px 18px; border: 1px solid $border-color; border-radius: $radius-md; background: $white; font-size: $font-size-sm; color: $text-secondary; display: flex; align-items: center; gap: 6px; cursor: pointer;
    &:hover { border-color: $primary; color: $primary; }
    &.active { background: $primary; color: $white; border-color: $primary; }
  }
}
.form-card { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-xl; box-shadow: $shadow-sm; display: flex; flex-direction: column; gap: $spacing-lg; }
.form-group { display: flex; flex-direction: column; gap: $spacing-xs;
  label { font-size: $font-size-sm; font-weight: 600; color: $text-secondary; }
  select, input, textarea { padding: 8px 12px; border: 1px solid $border-color; border-radius: $radius-md; font-size: $font-size-sm; font-family: inherit; outline: none; &:focus { border-color: $primary; } }
}
.form-row { display: flex; gap: $spacing-lg; .form-group { flex: 1; } }
.format-options { display: flex; gap: $spacing-lg; }
.radio-label { font-size: $font-size-sm; color: $text-secondary; display: flex; align-items: center; gap: $spacing-xs; cursor: pointer; }
.form-actions { display: flex; gap: $spacing-sm; }
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.table-actions { display: flex; align-items: center; gap: $spacing-sm; }
.btn-excel { background: none; border: 1px solid #2e7d32; color: #2e7d32; width: 32px; height: 32px; border-radius: $radius-md; font-size: 18px; display: flex; align-items: center; justify-content: center; &:hover { background: #2e7d32; color: $white; } }
.ag-grid-wrapper { :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; font-family: $font-family; } :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; } :deep(.ag-header-cell) { color: #fff; } :deep(.ag-row) { cursor: pointer; } }
</style>
