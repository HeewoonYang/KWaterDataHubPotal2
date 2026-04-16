<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>표준 준수</h2>
      <p class="page-desc">데이터 표준 준수 현황을 관리하고 모니터링합니다.</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>분류</label><select v-model="f1"><option value="">전체</option><option>단어</option><option>용어</option><option>도메인</option><option>코드</option></select></div>
        <div class="filter-group"><label>준수율</label><select v-model="f2"><option value="">전체</option><option>90% 이상</option><option>70~90%</option><option>70% 미만</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="f3" placeholder="표준명 검색" /></div>
        <div class="filter-actions"><button class="btn btn-primary"><SearchOutlined /> 조회</button></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ rowData.length }}</strong>건</span>
        <div class="table-actions"><button class="btn btn-success" @click="runCheck"><CheckCircleOutlined /> 점검 실행</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '표준_준수')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" :rowSelection="'multiple'" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 표준 준수 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="md" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">준수 현황</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">표준명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">분류</span><span class="info-value">{{ detailData.category }}</span></div>
          <div class="modal-info-item"><span class="info-label">총 항목</span><span class="info-value">{{ detailData.total }}</span></div>
          <div class="modal-info-item"><span class="info-label">준수</span><span class="info-value">{{ detailData.passed }}</span></div>
          <div class="modal-info-item"><span class="info-label">미준수</span><span class="info-value">{{ detailData.failed }}</span></div>
          <div class="modal-info-item"><span class="info-label">준수율</span><span class="info-value">{{ detailData.rate }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 검사</span><span class="info-value">{{ detailData.lastCheck }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { CheckCircleOutlined, WarningOutlined, FileTextOutlined, AuditOutlined, SearchOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
ModuleRegistry.registerModules([AllCommunityModule])
import { qualityApi } from '../../../api/standard.api'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
const f1 = ref(''), f2 = ref(''), f3 = ref('')
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: AuditOutlined, label: '전체 표준', value: '1,842', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '준수', value: '1,680', color: '#28A745' },
  { icon: WarningOutlined, label: '미준수', value: '162', color: '#DC3545' },
  { icon: FileTextOutlined, label: '평균 준수율', value: '91.2%', color: '#FFC107' },
]
const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, flex: 0, minWidth: 36, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '표준명', field: 'name', flex: 2, minWidth: 180 },
  { headerName: '분류', field: 'category', flex: 0.6, minWidth: 70 },
  { headerName: '총 항목', field: 'total', flex: 0.6, minWidth: 65 },
  { headerName: '준수', field: 'passed', flex: 0.5, minWidth: 60 },
  { headerName: '미준수', field: 'failed', flex: 0.5, minWidth: 65 },
  { headerName: '준수율', field: 'rate', flex: 0.6, minWidth: 65 },
  { headerName: '최근 검사', field: 'lastCheck', flex: 1, minWidth: 120 },
])
const rowData = ref([
  { name: '표준단어사전', category: '단어', total: 520, passed: 498, failed: 22, rate: '95.8%', lastCheck: '2026-03-25' },
  { name: '표준용어사전', category: '용어', total: 380, passed: 352, failed: 28, rate: '92.6%', lastCheck: '2026-03-25' },
  { name: '표준도메인사전', category: '도메인', total: 245, passed: 230, failed: 15, rate: '93.9%', lastCheck: '2026-03-24' },
  { name: '표준코드사전', category: '코드', total: 412, passed: 365, failed: 47, rate: '88.6%', lastCheck: '2026-03-24' },
  { name: '컬럼명 표준', category: '용어', total: 185, passed: 145, failed: 40, rate: '78.4%', lastCheck: '2026-03-23' },
  { name: '테이블명 표준', category: '용어', total: 100, passed: 90, failed: 10, rate: '90.0%', lastCheck: '2026-03-23' },
])

const showDetail = ref(false)
const detailData = ref<any>({})

async function loadData() {
  try {
    const res = await qualityApi.listCompliance()
    const items = res.data.data
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        name: r.standard_name || '', category: r.category || '',
        total: r.total_items || 0, passed: r.passed_items || 0, failed: r.failed_items || 0,
        rate: r.compliance_rate ? `${r.compliance_rate}%` : '0%',
        lastCheck: r.checked_at?.substring(0, 10) || '',
      }))
    }
  } catch (e) {
    console.warn('StandardCompliance: API call failed, using mock data', e)
  }
}

async function runCheck() {
  try {
    await qualityApi.runComplianceCheck()
    message.success('표준 준수 점검이 완료되었습니다.')
    await loadData()
  } catch (e) {
    message.error('점검 실행에 실패했습니다.')
  }
}

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

onMounted(() => loadData())
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
