<template>
  <div class="admin-page migration-results">
    <div class="page-header">
      <h2>마이그레이션 결과 · 세부로그</h2>
      <p class="page-desc">
        전 마이그레이션 작업의 결과 요약, 일자별 추이, TOP 실패, 감사로그를 통합 조회합니다.
      </p>
    </div>

    <!-- 기간 필터 -->
    <div class="period-filter">
      <label>조회 기간:</label>
      <button v-for="d in PERIODS" :key="d" class="chip" :class="{ active: period === d }" @click="setPeriod(d)">
        {{ d }}일
      </button>
      <button class="btn btn-outline btn-sm" @click="loadAll" :disabled="loading">
        <ReloadOutlined /> 새로고침
      </button>
    </div>

    <!-- KPI 카드 -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">총 작업</div>
        <div class="kpi-value">{{ summary.total || 0 }}</div>
      </div>
      <div class="kpi-card success">
        <div class="kpi-label">성공률 (최근 {{ period }}일)</div>
        <div class="kpi-value">{{ summary.success_rate || 0 }}%</div>
        <div class="kpi-sub">성공 {{ summary.success || 0 }} / 실패 {{ summary.failed || 0 }}</div>
      </div>
      <div class="kpi-card info">
        <div class="kpi-label">평균 소요</div>
        <div class="kpi-value">{{ avgDurationLabel }}</div>
      </div>
      <div class="kpi-card warn">
        <div class="kpi-label">누적 이관 행수</div>
        <div class="kpi-value">{{ (summary.total_rows || 0).toLocaleString() }}</div>
        <div class="kpi-sub">{{ summary.total_tables || 0 }} 테이블</div>
      </div>
    </div>

    <!-- 차트 3분할 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">일자별 성공/실패 추이</div>
        <div ref="chartTrendRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">상태 분포</div>
        <div ref="chartStatusRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">TOP 실패 (테이블 x 단계)</div>
        <div ref="chartFailureRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 통합 감사로그 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <div class="filters">
          <input v-model="logFilters.q" placeholder="작업명 검색..." class="filter-input" @keyup.enter="loadLogs(1)" />
          <input v-model="logFilters.table_name" placeholder="테이블명..." class="filter-input" @keyup.enter="loadLogs(1)" />
          <select v-model="logFilters.action">
            <option value="">전체 행위</option>
            <option v-for="a in ACTIONS" :key="a" :value="a">{{ a }}</option>
          </select>
          <select v-model="logFilters.severity">
            <option value="">전체 심각도</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
          </select>
          <select v-model="logFilters.phase">
            <option value="">전체 단계</option>
            <option v-for="p in PHASES" :key="p" :value="p">{{ p }}</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="loadLogs(1)"><SearchOutlined /> 조회</button>
          <button class="btn btn-outline btn-sm" @click="resetLogFilters"><ClearOutlined /> 초기화</button>
        </div>
        <div class="table-actions">
          <span class="muted">{{ logTotal.toLocaleString() }}건</span>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportLogs"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine"
                   :rowData="logRows"
                   :columnDefs="logCols"
                   :defaultColDef="defCol"
                   :pagination="true"
                   :paginationPageSize="logPageSize"
                   :suppressPaginationPanel="true"
                   domLayout="autoHeight" />
      </div>
      <!-- 커스텀 페이지네이션 (서버 사이드) -->
      <div class="server-pager">
        <button class="btn btn-outline btn-xs" :disabled="logPage <= 1" @click="loadLogs(1)">«</button>
        <button class="btn btn-outline btn-xs" :disabled="logPage <= 1" @click="loadLogs(logPage - 1)">‹</button>
        <span class="muted">{{ logPage }} / {{ logTotalPages || 1 }}</span>
        <button class="btn btn-outline btn-xs" :disabled="logPage >= logTotalPages" @click="loadLogs(logPage + 1)">›</button>
        <button class="btn btn-outline btn-xs" :disabled="logPage >= logTotalPages" @click="loadLogs(logTotalPages)">»</button>
        <select v-model.number="logPageSize" @change="loadLogs(1)">
          <option :value="30">30/page</option>
          <option :value="50">50/page</option>
          <option :value="100">100/page</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { ReloadOutlined, FileExcelOutlined, SearchOutlined, ClearOutlined } from '@ant-design/icons-vue'
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { message } from '../../../utils/message'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const PERIODS = [7, 30, 90]
const ACTIONS = ['START', 'COMPLETE', 'FAIL', 'VALIDATE', 'TABLE_ADD', 'TABLE_REMOVE', 'TABLE_MODIFY', 'PAUSE', 'RESUME', 'ROLLBACK']
const PHASES = ['INIT', 'SCHEMA_COPY', 'DATA_COPY', 'VALIDATION', 'CUTOVER', 'INDEX_REBUILD', 'MAPPING']

const period = ref(30)
const loading = ref(false)
const summary = ref<any>({})

const chartTrendRef = ref<HTMLElement | null>(null)
const chartStatusRef = ref<HTMLElement | null>(null)
const chartFailureRef = ref<HTMLElement | null>(null)
let chartTrend: any, chartStatus: any, chartFailure: any

const avgDurationLabel = computed(() => {
  const s = summary.value.avg_duration_sec || 0
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`
})

function setPeriod(d: number) {
  period.value = d
  loadAll()
}

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadSummary(), loadLogs(1)])
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  try {
    const r = await adminCollectionApi.migrationResultsSummary(period.value)
    summary.value = r.data.data || {}
    await nextTick()
    renderCharts()
  } catch (e: any) {
    message.error('요약 조회 실패')
  }
}

function renderCharts() {
  renderTrendChart()
  renderStatusChart()
  renderFailureChart()
}

function renderTrendChart() {
  if (!chartTrendRef.value) return
  chartTrend = chartTrend || echarts.init(chartTrendRef.value)
  const data = summary.value.by_date || []
  chartTrend.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['성공', '실패'], right: 10, top: 0, textStyle: { fontSize: 11 } },
    grid: { top: 30, right: 20, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: data.map((d: any) => d.date.slice(5)), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '성공', type: 'bar', stack: 's', data: data.map((d: any) => d.success), itemStyle: { color: '#52c41a' } },
      { name: '실패', type: 'bar', stack: 's', data: data.map((d: any) => d.failed), itemStyle: { color: '#ff4d4f' } },
    ],
  }, true)
}

function renderStatusChart() {
  if (!chartStatusRef.value) return
  chartStatus = chartStatus || echarts.init(chartStatusRef.value)
  const data = (summary.value.by_status || []).map((s: any) => ({
    name: statusLabel(s.status), value: s.count,
    itemStyle: { color: statusColor(s.status) },
  }))
  chartStatus.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 5, top: 'center', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['38%', '50%'],
      label: { show: true, formatter: '{b}\n{c}', fontSize: 11 },
      data,
    }],
  }, true)
}

function renderFailureChart() {
  if (!chartFailureRef.value) return
  chartFailure = chartFailure || echarts.init(chartFailureRef.value)
  const data = summary.value.top_failures || []
  chartFailure.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 10, right: 20, bottom: 30, left: 140 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: {
      type: 'category',
      data: data.map((f: any) => `${f.table}\n[${f.phase}]`).reverse(),
      axisLabel: { fontSize: 10 },
    },
    series: [{
      type: 'bar',
      data: data.map((f: any) => f.count).reverse(),
      itemStyle: { color: '#ff4d4f' },
      label: { show: true, position: 'right', fontSize: 10 },
    }],
  }, true)
}

function statusLabel(s: string) {
  return { COMPLETED: '완료', RUNNING: '실행중', PENDING: '대기', FAILED: '실패' }[s] || s
}
function statusColor(s: string) {
  return { COMPLETED: '#52c41a', RUNNING: '#1677ff', PENDING: '#8c8c8c', FAILED: '#ff4d4f' }[s] || '#d9d9d9'
}

// 감사로그 (서버사이드 페이징·필터)
const logRows = ref<any[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(30)
const logTotalPages = computed(() => Math.ceil(logTotal.value / logPageSize.value))
const logFilters = reactive<any>({
  q: '', table_name: '', action: '', severity: '', phase: '',
})
const defCol = { ...baseDefaultColDef }
const logCols: ColDef[] = withHeaderTooltips([
  { headerName: '시각', field: 'created_at', width: 165,
    valueFormatter: (p: any) => p.value ? new Date(p.value).toLocaleString('ko-KR') : '-' },
  { headerName: '작업명', field: 'migration_name', flex: 1.5, minWidth: 160,
    cellRenderer: (p: any) => p.value ? `<b>${p.value}</b>` : '<span style="color:#bbb">-</span>' },
  { headerName: '행위', field: 'action', width: 120,
    cellRenderer: (p: any) => `<span class="mode-tag ${(p.value || '').toLowerCase()}">${p.value || ''}</span>` },
  { headerName: '단계', field: 'phase', width: 110 },
  { headerName: '테이블', field: 'table_name', flex: 1.2, minWidth: 140,
    cellRenderer: (p: any) => p.value ? `<code>${p.value}</code>` : '-' },
  { headerName: '행수', field: 'row_count', width: 100,
    valueFormatter: (p: any) => p.value != null ? p.value.toLocaleString() : '-' },
  { headerName: '소요', field: 'duration_ms', width: 85,
    valueFormatter: (p: any) => p.value ? `${p.value}ms` : '-' },
  { headerName: '심각도', field: 'severity', width: 85,
    cellRenderer: (p: any) => `<span class="sev ${(p.value || '').toLowerCase()}">${p.value || ''}</span>` },
])

async function loadLogs(page: number) {
  logPage.value = page
  try {
    const params: any = {
      page, page_size: logPageSize.value,
      days: period.value,
    }
    for (const k of ['q', 'table_name', 'action', 'severity', 'phase']) {
      if (logFilters[k]) params[k] = logFilters[k]
    }
    const r = await adminCollectionApi.migrationAllAuditLogs(params)
    logRows.value = r.data.items || []
    logTotal.value = r.data.total || 0
  } catch (e: any) {
    message.error('로그 조회 실패')
  }
}

function resetLogFilters() {
  Object.keys(logFilters).forEach(k => logFilters[k] = '')
  loadLogs(1)
}

function exportLogs() {
  exportGridToExcel(logCols, logRows.value, `마이그레이션로그_${period.value}일`)
}

watch(() => period.value, () => loadLogs(1))

function onResize() {
  chartTrend?.resize()
  chartStatus?.resize()
  chartFailure?.resize()
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chartTrend?.dispose(); chartStatus?.dispose(); chartFailure?.dispose()
})
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';

.migration-results { display: flex; flex-direction: column; gap: 12px; }

.period-filter { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #fff; border: 1px solid #eee; border-radius: 6px; }
.period-filter label { font-size: 13px; font-weight: 600; color: #595959; }
.chip {
  padding: 4px 12px; font-size: 12px; border: 1px solid #d9d9d9; background: #fff;
  border-radius: 14px; cursor: pointer; transition: all 0.15s;
  &:hover { border-color: #1677ff; color: #1677ff; }
  &.active { background: #1677ff; color: #fff; border-color: #1677ff; }
}

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.kpi-card {
  background: #fff; border: 1px solid #eee; border-radius: 6px; padding: 14px 16px;
  border-left: 4px solid #1677ff;
  &.success { border-left-color: #52c41a; }
  &.info { border-left-color: #13c2c2; }
  &.warn { border-left-color: #faad14; }
}
.kpi-label { font-size: 12px; color: #888; }
.kpi-value { font-size: 24px; font-weight: 700; color: #262626; margin-top: 3px; }
.kpi-sub { font-size: 11px; color: #888; margin-top: 3px; }

.chart-row { display: grid; grid-template-columns: 1.4fr 1fr 1.2fr; gap: 10px; }
.chart-card {
  background: #fff; border: 1px solid #eee; border-radius: 6px; padding: 10px 12px;
}
.chart-title { font-size: 13px; font-weight: 600; color: #262626; margin-bottom: 6px; }
.chart-body { width: 100%; height: 240px; }

/* 필터 */
.filters { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.filter-input { padding: 5px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; min-width: 150px; }
.filters select { padding: 5px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; }
.server-pager {
  display: flex; align-items: center; gap: 6px; justify-content: flex-end;
  padding: 8px 4px; font-size: 12px;
}
.server-pager select { padding: 3px 6px; border: 1px solid #d9d9d9; border-radius: 3px; font-size: 11px; }
.btn-xs { padding: 2px 8px; font-size: 11px; }

/* 심각도/행위 태그 */
:deep(.mode-tag) {
  display: inline-block; padding: 1px 6px; border-radius: 3px;
  font-size: 10px; font-weight: 600; background: #f0f2f5; color: #595959;
  &.start { background: #e6f4ff; color: #003a8c; }
  &.complete { background: #f6ffed; color: #135200; }
  &.fail { background: #fff2f0; color: #820014; }
  &.validate { background: #fff7e6; color: #874d00; }
  &.table_add { background: #e6fffb; color: #006d75; }
  &.table_remove { background: #fff1f0; color: #cf1322; }
  &.table_modify { background: #f9f0ff; color: #531dab; }
}
:deep(.sev) {
  display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.info { background: #e6f4ff; color: #003a8c; }
  &.warning { background: #fff7e6; color: #874d00; }
  &.error { background: #fff2f0; color: #820014; }
}
:deep(code) { background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 11px; }
</style>
