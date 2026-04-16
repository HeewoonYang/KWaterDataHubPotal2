<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <h2>에코시스템 총괄</h2>
      <p class="page-desc">K-water 클라우드 데이터 에코시스템 인프라를 총괄 관리합니다.</p>
    </div>

    <!-- 상태 요약 카드 (클릭 시 상세 팝업) -->
    <div class="status-cards">
      <div v-for="card in statusCards" :key="card.label" class="status-card clickable" @click="openStatusDetail(card)">
        <div class="status-icon" :style="{ background: card.color }">
          <component :is="card.icon" />
        </div>
        <div class="status-info">
          <span class="status-value">{{ card.value }}</span>
          <span class="status-label">{{ card.label }}</span>
        </div>
        <span class="status-badge" :class="card.status">{{ card.statusText }}</span>
      </div>
    </div>

    <!-- 검색/필터 영역 -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>시스템 유형</label><select v-model="filterType"><option value="">전체</option><option value="db">데이터베이스</option><option value="app">애플리케이션</option><option value="infra">인프라</option></select></div>
        <div class="filter-group"><label>상태</label><select v-model="filterStatus"><option value="">전체</option><option value="active">정상</option><option value="warning">주의</option><option value="error">오류</option></select></div>
        <div class="filter-group"><label>검색</label><input type="text" v-model="searchText" placeholder="시스템명 검색" /></div>
        <div class="filter-actions"><button class="btn btn-primary" @click="onSearch">조회</button><button class="btn btn-outline" @click="onReset">초기화</button></div>
      </div>
    </div>

    <!-- AG Grid 데이터 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ tableData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-success" @click="showRegister = true">등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, tableData, '대시보드_데이터')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="tableData" :columnDefs="columnDefs" :defaultColDef="defaultColDef" :pagination="true" :paginationPageSize="10" :rowSelection="'multiple'" :animateRows="true" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- ====== 상세 팝업 (첨부 디자인 참조) ====== -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="xl" @close="showDetail = false">
      <!-- 요약 카드 -->
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">CPU</div><div class="stat-number">{{ detailData.cpu }}%</div></div>
        <div class="modal-stat-card success"><div class="stat-title">메모리</div><div class="stat-number">{{ detailData.memory }}%</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">디스크</div><div class="stat-number">{{ detailData.disk }}%</div></div>
        <div class="modal-stat-card" :class="detailData.status === 'active' ? 'success' : detailData.status === 'warning' ? 'warning' : 'danger'"><div class="stat-title">상태</div><div class="stat-number">{{ detailData.statusLabel }}</div></div>
      </div>
      <!-- 차트 영역 -->
      <div class="modal-chart-row">
        <div class="chart-panel"><div class="chart-title">리소스 사용률</div><div class="chart-placeholder"><BarChartOutlined style="font-size:32px;opacity:0.3" /> &nbsp; 12개월 리소스 추이</div></div>
        <div class="chart-panel"><div class="chart-title">상태 분포</div><div class="chart-placeholder"><PieChartOutlined style="font-size:32px;opacity:0.3" /> &nbsp; 정상/주의/장애 비율</div></div>
      </div>
      <!-- 상세 정보 -->
      <div class="modal-section">
        <div class="modal-section-title">시스템 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">시스템명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.typeLabel }}</span></div>
          <div class="modal-info-item"><span class="info-label">호스트</span><span class="info-value">{{ detailData.host }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 점검</span><span class="info-value">{{ detailData.lastCheck }}</span></div>
        </div>
      </div>
      <!-- 이력 테이블 -->
      <div class="modal-section">
        <div class="modal-section-title">점검 이력</div>
        <table class="modal-table">
          <thead><tr><th>번호</th><th>점검 일시</th><th>CPU</th><th>메모리</th><th>디스크</th><th>결과</th></tr></thead>
          <tbody>
            <tr v-for="(h, i) in checkHistory" :key="i"><td class="text-center">{{ i + 1 }}</td><td>{{ h.date }}</td><td class="text-right">{{ h.cpu }}%</td><td class="text-right">{{ h.mem }}%</td><td class="text-right">{{ h.disk }}%</td><td class="text-center"><span class="badge" :class="h.status === '정상' ? 'badge-success' : 'badge-warning'">{{ h.status }}</span></td></tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- ====== 등록 팝업 ====== -->
    <AdminModal :visible="showRegister" title="시스템 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">시스템명</label><input placeholder="시스템명을 입력하세요" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">유형</label><select><option>데이터베이스</option><option>애플리케이션</option><option>인프라</option></select></div>
          <div class="modal-form-group"><label class="required">호스트</label><input placeholder="IP 주소" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>포트</label><input placeholder="포트 번호" /></div>
          <div class="modal-form-group"><label>점검 주기</label><select><option>5분</option><option>10분</option><option>30분</option><option>1시간</option></select></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea rows="3" placeholder="시스템 설명 (선택)"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>

    <!-- ====== 상태 카드 클릭 상세 팝업 ====== -->
    <AdminModal :visible="showStatusModal" :title="statusModalTitle" size="lg" @close="showStatusModal = false">
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">전체</div><div class="stat-number">24</div></div>
        <div class="modal-stat-card success"><div class="stat-title">우수 (95%↑)</div><div class="stat-number">21</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">보통 (90%↑)</div><div class="stat-number">2</div></div>
        <div class="modal-stat-card danger"><div class="stat-title">미흡 (0%↑)</div><div class="stat-number">1</div></div>
      </div>
      <div class="modal-chart-row">
        <div class="chart-panel"><div class="chart-title">평가 등급</div><div class="chart-placeholder"><PieChartOutlined style="font-size:32px;opacity:0.3" /> &nbsp; 우수 87.5% / 보통 8.3% / 미흡 4.2%</div></div>
        <div class="chart-panel">
          <div class="chart-title">시스템별 가동률</div>
          <table class="modal-table">
            <thead><tr><th>번호</th><th>시스템명</th><th>가동률</th><th>등급</th></tr></thead>
            <tbody>
              <tr><td class="text-center">1</td><td>PostgreSQL Master</td><td class="text-right">99.99%</td><td class="text-center"><span class="badge badge-success">우수</span></td></tr>
              <tr><td class="text-center">2</td><td>OpenMetadata</td><td class="text-right">99.8%</td><td class="text-center"><span class="badge badge-success">우수</span></td></tr>
              <tr><td class="text-center">3</td><td>Kafka Cluster</td><td class="text-right">92.5%</td><td class="text-center"><span class="badge badge-warning">보통</span></td></tr>
              <tr><td class="text-center">4</td><td>Nginx LB</td><td class="text-right">85.0%</td><td class="text-center"><span class="badge badge-danger">미흡</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="modal-section">
        <div class="chart-title">시스템 12개월 추이</div>
        <div class="chart-placeholder" style="height:120px"><BarChartOutlined style="font-size:32px;opacity:0.3" /> &nbsp; 월별 가동률 추이 차트</div>
      </div>
      <template #footer><button class="btn btn-outline" @click="showStatusModal = false">닫기</button></template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../utils/gridHelper'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { DesktopOutlined, CheckCircleOutlined, WarningOutlined, CloseCircleOutlined, FileExcelOutlined, SaveOutlined, BarChartOutlined, PieChartOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../components/AdminModal.vue'
import { adminSystemApi } from '../../api/admin.api'

ModuleRegistry.registerModules([AllCommunityModule])

const filterType = ref(''), filterStatus = ref(''), searchText = ref('')
const showDetail = ref(false), showRegister = ref(false), showStatusModal = ref(false)
const statusModalTitle = ref('')
const detailData = ref<any>({})

const checkHistory = [
  { date: '2026-03-25 09:00', cpu: 45, mem: 62, disk: 38, status: '정상' },
  { date: '2026-03-25 08:00', cpu: 42, mem: 60, disk: 38, status: '정상' },
  { date: '2026-03-25 07:00', cpu: 48, mem: 64, disk: 38, status: '정상' },
  { date: '2026-03-25 06:00', cpu: 38, mem: 55, disk: 37, status: '정상' },
  { date: '2026-03-25 05:00', cpu: 35, mem: 52, disk: 37, status: '정상' },
]

const statusCards: { icon: Component; label: string; value: string; color: string; status: string; statusText: string }[] = [
  { icon: DesktopOutlined, label: '전체 시스템', value: '24', color: '#0066CC', status: 'normal', statusText: '정상' },
  { icon: CheckCircleOutlined, label: '정상 가동', value: '21', color: '#28A745', status: 'normal', statusText: '87.5%' },
  { icon: WarningOutlined, label: '주의', value: '2', color: '#FFC107', status: 'warning', statusText: '경고' },
  { icon: CloseCircleOutlined, label: '장애', value: '1', color: '#DC3545', status: 'error', statusText: '점검 중' },
]

const tableData = ref([
  { id: 1, name: 'PostgreSQL (Master)', type: 'db', typeLabel: 'DB', host: '10.0.1.10', status: 'active', statusLabel: '정상', cpu: 45, memory: 62, disk: 38, lastCheck: '2026-03-25 09:00' },
  { id: 2, name: 'PostgreSQL (Replica)', type: 'db', typeLabel: 'DB', host: '10.0.1.11', status: 'active', statusLabel: '정상', cpu: 32, memory: 55, disk: 38, lastCheck: '2026-03-25 09:00' },
  { id: 3, name: 'OpenMetadata Server', type: 'app', typeLabel: 'APP', host: '10.0.2.10', status: 'active', statusLabel: '정상', cpu: 28, memory: 48, disk: 22, lastCheck: '2026-03-25 09:00' },
  { id: 4, name: 'FastAPI Gateway', type: 'app', typeLabel: 'APP', host: '10.0.2.20', status: 'active', statusLabel: '정상', cpu: 15, memory: 30, disk: 12, lastCheck: '2026-03-25 09:00' },
  { id: 5, name: 'Kafka Cluster', type: 'infra', typeLabel: 'INFRA', host: '10.0.3.10-12', status: 'warning', statusLabel: '주의', cpu: 78, memory: 85, disk: 65, lastCheck: '2026-03-25 08:55' },
  { id: 6, name: 'Redis Sentinel', type: 'infra', typeLabel: 'INFRA', host: '10.0.3.20', status: 'active', statusLabel: '정상', cpu: 12, memory: 20, disk: 8, lastCheck: '2026-03-25 09:00' },
  { id: 7, name: 'Celery Worker Pool', type: 'app', typeLabel: 'APP', host: '10.0.4.10-13', status: 'active', statusLabel: '정상', cpu: 55, memory: 60, disk: 15, lastCheck: '2026-03-25 09:00' },
  { id: 8, name: 'Nginx LB', type: 'infra', typeLabel: 'INFRA', host: '10.0.0.10', status: 'error', statusLabel: '장애', cpu: 0, memory: 0, disk: 42, lastCheck: '2026-03-25 08:30' },
  { id: 9, name: 'MinIO Storage', type: 'infra', typeLabel: 'INFRA', host: '10.0.5.10', status: 'active', statusLabel: '정상', cpu: 20, memory: 35, disk: 72, lastCheck: '2026-03-25 09:00' },
  { id: 10, name: 'Airflow Scheduler', type: 'app', typeLabel: 'APP', host: '10.0.4.20', status: 'active', statusLabel: '정상', cpu: 35, memory: 42, disk: 18, lastCheck: '2026-03-25 09:00' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.infrastructure()
    const items = res.data.data
    if (items && items.length > 0) {
      tableData.value = items.map((item: any) => ({
        ...item,
        name: item.infra_name ?? item.name,
        type: item.infra_type ?? item.type,
        typeLabel: item.infra_type_label ?? item.typeLabel,
        host: item.host_address ?? item.host,
        statusLabel: item.status_label ?? item.statusLabel,
        lastCheck: item.last_check_at ?? item.lastCheck,
      }))
    }
  } catch (e) {
    console.warn('AdminDashboard: API 호출 실패, mock 데이터 사용', e)
  }
})

const defaultColDef = { ...baseDefaultColDef }
const columnDefs: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, flex: 0, width: 40, minWidth: 40, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '시스템명', field: 'name', flex: 2, minWidth: 180 },
  { headerName: '유형', field: 'typeLabel', flex: 0.5, minWidth: 65, cellClass: (p: any) => `type-cell type-${p.data.type}` },
  { headerName: '호스트', field: 'host', flex: 1.5, minWidth: 130, cellStyle: { fontFamily: "'JetBrains Mono', 'D2Coding', monospace", fontSize: '12px', color: '#666' } },
  { headerName: '상태', field: 'statusLabel', flex: 0.5, minWidth: 60, cellClass: (p: any) => `status-cell status-${p.data.status}` },
  { headerName: 'CPU', field: 'cpu', flex: 0.5, minWidth: 60, valueFormatter: (p: any) => `${p.value}%` },
  { headerName: '메모리', field: 'memory', flex: 0.5, minWidth: 65, valueFormatter: (p: any) => `${p.value}%` },
  { headerName: '디스크', field: 'disk', flex: 0.5, minWidth: 65, valueFormatter: (p: any) => `${p.value}%` },
  { headerName: '최근 점검', field: 'lastCheck', flex: 1.2, minWidth: 150 },
  { headerName: '상세', flex: 0.5, minWidth: 55, sortable: false,
    cellRenderer: () => '<button style="background:#0066CC;color:#fff;border:none;border-radius:4px;padding:2px 10px;font-size:11px;cursor:pointer;">상세</button>' },
])

function onRowClick(event: any) {
  if (event.column?.colId === '10') return // 상세 버튼 클릭은 별도
  detailData.value = event.data
  showDetail.value = true
}

function openStatusDetail(card: any) {
  statusModalTitle.value = card.label + ' 현황'
  showStatusModal.value = true
}

function onSearch() { console.log('조회:', filterType.value, filterStatus.value, searchText.value) }
function onReset() { filterType.value = ''; filterStatus.value = ''; searchText.value = '' }
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.admin-dashboard { display: flex; flex-direction: column; gap: $spacing-lg; }
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; color: $text-primary; margin-bottom: $spacing-xs; } .page-desc { font-size: $font-size-sm; color: $text-muted; } }
.status-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: $spacing-md; }
.status-card { background: $white; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; display: flex; align-items: center; gap: $spacing-md; box-shadow: $shadow-sm; &.clickable { cursor: pointer; transition: all 0.2s; &:hover { box-shadow: $shadow-md; border-color: $primary; transform: translateY(-2px); } } }
.status-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; color: #fff; }
.status-info { flex: 1; display: flex; flex-direction: column; }
.status-value { font-size: $font-size-xl; font-weight: 700; }
.status-label { font-size: $font-size-xs; color: $text-muted; }
.status-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; &.normal { background: #e8f5e9; color: #2e7d32; } &.warning { background: #fff3e0; color: #e65100; } &.error { background: #fce4ec; color: #c62828; } }
.search-filter { background: #f5f7fa; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; }
.filter-row { display: flex; align-items: flex-end; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: $spacing-xs; label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; } select, input { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 150px; background: $white; outline: none; &:focus { border-color: $primary; } } }
.filter-actions { display: flex; gap: $spacing-sm; }
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.table-actions { display: flex; align-items: center; gap: $spacing-sm; }
.btn-excel { background: none; border: 1px solid #2e7d32; color: #2e7d32; width: 32px; height: 32px; border-radius: $radius-md; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all $transition-fast; &:hover { background: #2e7d32; color: $white; } }
.ag-grid-wrapper { :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; --ag-row-border-color: #f0f0f0; --ag-selected-row-background-color: #e8f0fe; font-family: $font-family; } :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; } :deep(.ag-header-cell) { color: #fff; } :deep(.ag-header-select-all) { color: #fff; } :deep(.ag-paging-panel) { justify-content: center; font-size: 12px; } :deep(.type-cell) { font-size: 10px; font-weight: 600; &.type-db { color: #1565c0; } &.type-app { color: #7b1fa2; } &.type-infra { color: #00695c; } } :deep(.status-cell) { font-weight: 500; &.status-active { color: #2e7d32; } &.status-warning { color: #e65100; } &.status-error { color: #c62828; } } :deep(.ag-row) { cursor: pointer; } }
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) { .status-cards { grid-template-columns: repeat(2, 1fr); } .filter-row { flex-direction: column; align-items: stretch; } }
</style>
