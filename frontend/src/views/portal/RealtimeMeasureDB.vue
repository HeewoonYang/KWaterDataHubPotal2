<template>
  <div class="measure-page">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/portal/monitoring">실시간모니터링</router-link>
      <span class="separator">&gt;</span>
      <span class="current">RWIS</span>
    </nav>

    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <div class="title-wrap">
          <div style="display:flex;align-items:center;gap:10px;">
            <h2>RWIS 모니터링*</h2>
            <span class="badge-realtime"><ThunderboltOutlined /> 실시간</span>
          </div>
          <p class="page-desc">실시간 수자원정보시스템(RWIS) 수위·유량·수질 계측 현황</p>
        </div>
      </div>
      <div class="header-right">
        <CalendarOutlined />
        <input type="date" v-model="dateFrom" class="date-input" />
        <span class="date-sep">~</span>
        <input type="date" v-model="dateTo" class="date-input" />
      </div>
    </div>

    <!-- Tab bar -->
    <div class="measure-tabs">
      <router-link to="/portal/monitoring" class="active">전체</router-link>
      <router-link to="/portal/monitoring/rwis/office">사무소 대시보드</router-link>
      <router-link to="/portal/monitoring/rwis/site">사업장 대시보드</router-link>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-row">
      <div class="kpi-card kpi-blue">
        <div class="kpi-body">
          <div class="kpi-label">전체 태그 수</div>
          <div class="kpi-value">71,612</div>
        </div>
        <div class="kpi-sub">7개 유역/지사 &middot; 463개 사업장</div>
      </div>
      <div class="kpi-card kpi-green">
        <div class="kpi-body">
          <div class="kpi-label">데이터 건수(15분)</div>
          <div class="kpi-value">284,530</div>
        </div>
        <div class="kpi-sub">최근 15분 수집 건수</div>
      </div>
      <div class="kpi-card kpi-purple">
        <div class="kpi-body">
          <div class="kpi-label">데이터 건수(1시간)</div>
          <div class="kpi-value">2.3억</div>
        </div>
        <div class="kpi-sub">최근 1시간 누적</div>
      </div>
      <div class="kpi-card kpi-orange">
        <div class="kpi-body">
          <div class="kpi-label">유역/지사</div>
          <div class="kpi-value">7</div>
        </div>
        <div class="kpi-sub">전국 유역본부/지역지사</div>
      </div>
      <div class="kpi-card kpi-teal">
        <div class="kpi-body">
          <div class="kpi-label">사업장</div>
          <div class="kpi-value">463</div>
        </div>
        <div class="kpi-sub">전체 사업장 수</div>
      </div>
    </div>

    <!-- Charts Row 1 -->
    <div class="chart-row">
      <!-- Donut: 유역별 태그 분포 -->
      <div class="chart-card">
        <div class="chart-title">유역별 태그 분포</div>
        <div class="donut-container">
          <svg viewBox="0 0 200 200" class="donut-svg">
            <circle v-for="(seg, idx) in donutSegments" :key="idx"
              cx="100" cy="100" r="70" fill="none"
              :stroke="seg.color" stroke-width="30"
              :stroke-dasharray="seg.dashArray"
              :stroke-dashoffset="seg.dashOffset"
              :transform="'rotate(-90 100 100)'"
            />
            <text x="100" y="95" text-anchor="middle" class="donut-total">71,612</text>
            <text x="100" y="112" text-anchor="middle" class="donut-label-center">전체 태그</text>
          </svg>
          <div class="donut-legend">
            <div v-for="(item, idx) in regionDistribution" :key="idx" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-value">{{ item.tags.toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Line Chart: 데이터 유입 추이 -->
      <div class="chart-card">
        <div class="chart-title">데이터 유입 추이 (15분)</div>
        <svg viewBox="0 0 560 260" class="line-chart-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#0066CC" stop-opacity="0.3" />
              <stop offset="100%" stop-color="#0066CC" stop-opacity="0.02" />
            </linearGradient>
          </defs>
          <!-- Grid lines -->
          <line v-for="i in 5" :key="'gl'+i" :x1="50" :x2="540" :y1="30 + (i-1)*50" :y2="30 + (i-1)*50" stroke="#eee" stroke-width="1" />
          <!-- Y axis labels -->
          <text v-for="(lbl, i) in lineYLabels" :key="'yl'+i" :x="45" :y="35 + i*50" text-anchor="end" class="axis-text">{{ lbl }}</text>
          <!-- X axis labels -->
          <text v-for="(lbl, i) in lineXLabels" :key="'xl'+i" :x="50 + i * (490/11)" :y="252" text-anchor="middle" class="axis-text">{{ lbl }}</text>
          <!-- Area fill -->
          <polygon :points="areaPoints" fill="url(#areaGrad)" />
          <!-- Line -->
          <polyline :points="linePoints" fill="none" stroke="#0066CC" stroke-width="2" stroke-linejoin="round" />
          <!-- Dots -->
          <circle v-for="(pt, i) in lineDataPoints" :key="'dot'+i" :cx="pt.x" :cy="pt.y" r="3" fill="#0066CC" />
          <!-- Legend -->
          <rect x="430" y="8" width="10" height="10" rx="2" fill="#0066CC" />
          <text x="444" y="17" class="legend-text">15분 데이터</text>
        </svg>
      </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="chart-row">
      <!-- Horizontal Bars: 권역별 태그 수 -->
      <div class="chart-card">
        <div class="chart-title">권역별 태그 수</div>
        <svg viewBox="0 0 520 300" class="hbar-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient v-for="(item, idx) in regionDistribution" :key="'hg'+idx" :id="'hbarGrad'+idx" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" :stop-color="item.color" stop-opacity="0.85" />
              <stop offset="100%" :stop-color="item.color" stop-opacity="1" />
            </linearGradient>
          </defs>
          <g v-for="(item, idx) in regionDistribution" :key="'hb'+idx">
            <!-- Bar background -->
            <rect :x="160" :y="15 + idx * 40" width="320" height="24" rx="4" fill="#f0f0f0" />
            <!-- Bar fill -->
            <rect :x="160" :y="15 + idx * 40" :width="320 * (item.tags / maxTags)" height="24" rx="4" :fill="'url(#hbarGrad'+idx+')'" />
            <!-- Label left -->
            <text :x="155" :y="31 + idx * 40" text-anchor="end" class="hbar-label">{{ item.name }}</text>
            <!-- Value inside bar -->
            <text :x="165 + 320 * (item.tags / maxTags) - 8" :y="31 + idx * 40" text-anchor="end" fill="#fff" font-size="11" font-weight="600">
              {{ item.tags.toLocaleString() }}
            </text>
          </g>
        </svg>
      </div>

      <!-- Gauges: 권역별 수집률 -->
      <div class="chart-card">
        <div class="chart-title">권역별 수집률</div>
        <div class="gauge-grid">
          <div v-for="(item, idx) in gaugeData" :key="'gauge'+idx" class="gauge-item">
            <svg viewBox="0 0 120 80" class="gauge-svg">
              <!-- Background arc -->
              <path :d="gaugeArcPath(50)" fill="none" stroke="#e8e8e8" stroke-width="10" stroke-linecap="round" />
              <!-- Value arc -->
              <path :d="gaugeArcPath(50)" fill="none" :stroke="gaugeColor(item.rate)" stroke-width="10" stroke-linecap="round"
                :stroke-dasharray="gaugeCircum" :stroke-dashoffset="gaugeCircum - (gaugeCircum * item.rate / 100)" />
              <text x="60" y="62" text-anchor="middle" font-size="16" font-weight="700" :fill="gaugeColor(item.rate)">{{ item.rate }}%</text>
              <text x="60" y="76" text-anchor="middle" font-size="9" fill="#999">{{ item.name }}</text>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- AG Grid -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">유역/지사별 현황 <strong>{{ gridData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, gridData, '실시간_계측DB_전체')">
            <FileExcelOutlined />
          </button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="gridData"
          :columnDefs="columnDefs"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="10"
          domLayout="autoHeight"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  FileExcelOutlined,
  ThunderboltOutlined,
  CalendarOutlined,
} from '@ant-design/icons-vue'
import { exportGridToExcel } from '../../utils/exportExcel'

ModuleRegistry.registerModules([AllCommunityModule])

const router = useRouter()

const today = new Date()
const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
const dateTo = ref(today.toISOString().substring(0, 10))
const dateFrom = ref(weekAgo.toISOString().substring(0, 10))

// Region distribution data
const regionDistribution = ref([
  { name: '한강권역본부', tags: 15546, color: '#3b82f6' },
  { name: '강원지역지사', tags: 4457, color: '#22c55e' },
  { name: '충청지역지사', tags: 16206, color: '#eab308' },
  { name: '금영섬권역본부', tags: 7128, color: '#f97316' },
  { name: '광주전남지역지사', tags: 6847, color: '#a855f7' },
  { name: '낙동강권역본부', tags: 9108, color: '#14b8a6' },
  { name: '경남부산지역지사', tags: 12320, color: '#ef4444' },
])

const totalTags = 71612
const maxTags = computed(() => Math.max(...regionDistribution.value.map(r => r.tags)))

// Donut chart segments
const donutSegments = computed(() => {
  const circumference = 2 * Math.PI * 70
  let offset = 0
  return regionDistribution.value.map(item => {
    const pct = item.tags / totalTags
    const dashLen = circumference * pct
    const seg = {
      color: item.color,
      dashArray: `${dashLen} ${circumference - dashLen}`,
      dashOffset: `${-offset}`,
    }
    offset += dashLen
    return seg
  })
})

// Line chart data (15min intervals)
const lineRawData = [280, 310, 295, 340, 320, 285, 360, 390, 350, 310, 284, 300]
const lineXLabels = ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00']
const lineYLabels = ['400K', '300K', '200K', '100K', '0']

const lineDataPoints = computed(() => {
  const minY = 30
  const maxY = 230
  const maxVal = 400
  return lineRawData.map((val, i) => ({
    x: 50 + i * (490 / 11),
    y: minY + (maxY - minY) * (1 - val / maxVal),
  }))
})

const linePoints = computed(() =>
  lineDataPoints.value.map(p => `${p.x},${p.y}`).join(' ')
)

const areaPoints = computed(() => {
  const pts = lineDataPoints.value
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `${first.x},230 ${linePoints.value} ${last.x},230`
})

// Gauge data
const gaugeData = ref([
  { name: '한강권역', rate: 89 },
  { name: '강원지역', rate: 91 },
  { name: '충청지역', rate: 92 },
  { name: '금영섬권역', rate: 78 },
  { name: '광주전남', rate: 83 },
  { name: '낙동강권역', rate: 88 },
])

const gaugeCircum = Math.PI * 50 // half circle circumference

function gaugeArcPath(r: number): string {
  return `M ${60 - r} 60 A ${r} ${r} 0 0 1 ${60 + r} 60`
}

function gaugeColor(rate: number): string {
  if (rate >= 90) return '#28A745'
  if (rate >= 80) return '#0066CC'
  return '#DC3545'
}

// Grid data
const gridData = ref([
  { region: '한강권역본부', offices: 11, sites: 68, tags: 15546, ratio: 21.7, collectRate: 89, dataCount: '4,820만' },
  { region: '강원지역지사', offices: 2, sites: 24, tags: 4457, ratio: 6.2, collectRate: 91, dataCount: '1,380만' },
  { region: '충청지역지사', offices: 12, sites: 85, tags: 16206, ratio: 22.6, collectRate: 92, dataCount: '5,030만' },
  { region: '금영섬권역본부', offices: 7, sites: 52, tags: 7128, ratio: 10.0, collectRate: 78, dataCount: '2,210만' },
  { region: '광주전남지역지사', offices: 10, sites: 71, tags: 6847, ratio: 9.6, collectRate: 83, dataCount: '2,120만' },
  { region: '낙동강권역본부', offices: 8, sites: 63, tags: 9108, ratio: 12.7, collectRate: 88, dataCount: '2,830만' },
  { region: '경남부산지역지사', offices: 11, sites: 100, tags: 12320, ratio: 17.2, collectRate: 85, dataCount: '3,820만' },
])

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }

function navigateToOffice(region: string) {
  router.push({ path: '/portal/monitoring/rwis/office', query: { region } })
}

const columnDefs: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 55, resizable: false },
  {
    headerName: '유역/지사',
    field: 'region',
    flex: 2,
    minWidth: 160,
    cellRenderer: (params: any) => {
      const link = document.createElement('a')
      link.href = '#'
      link.textContent = params.value
      link.style.color = '#0066CC'
      link.style.textDecoration = 'none'
      link.style.fontWeight = '600'
      link.addEventListener('click', (e: Event) => {
        e.preventDefault()
        navigateToOffice(params.value)
      })
      return link
    },
  },
  { headerName: '사무소', field: 'offices', width: 100, type: 'numericColumn' },
  { headerName: '사업장', field: 'sites', width: 100, type: 'numericColumn' },
  {
    headerName: '태그 수',
    field: 'tags',
    width: 110,
    maxWidth: 110,
    flex: 0,
    type: 'numericColumn',
    valueFormatter: (params: any) => params.value?.toLocaleString(),
  },
  {
    headerName: '비율',
    field: 'ratio',
    flex: 1,
    minWidth: 150,
    cellRenderer: (params: any) => {
      const wrapper = document.createElement('div')
      wrapper.style.display = 'flex'
      wrapper.style.alignItems = 'center'
      wrapper.style.gap = '8px'
      wrapper.style.width = '100%'

      const bar = document.createElement('div')
      bar.style.flex = '1'
      bar.style.height = '8px'
      bar.style.background = '#e9ecef'
      bar.style.borderRadius = '4px'
      bar.style.overflow = 'hidden'

      const fill = document.createElement('div')
      fill.style.width = `${params.value}%`
      fill.style.height = '100%'
      fill.style.background = '#0066CC'
      fill.style.borderRadius = '4px'
      bar.appendChild(fill)

      const text = document.createElement('span')
      text.textContent = `${params.value}%`
      text.style.fontSize = '12px'
      text.style.color = '#666'
      text.style.minWidth = '40px'
      text.style.textAlign = 'right'

      wrapper.appendChild(bar)
      wrapper.appendChild(text)
      return wrapper
    },
  },
  {
    headerName: '수집률',
    field: 'collectRate',
    width: 90,
    maxWidth: 90,
    flex: 0,
    cellRenderer: (params: any) => {
      const span = document.createElement('span')
      span.textContent = `${params.value}%`
      span.style.fontWeight = '600'
      if (params.value >= 90) {
        span.style.color = '#28A745'
      } else if (params.value >= 80) {
        span.style.color = '#0066CC'
      } else {
        span.style.color = '#DC3545'
      }
      return span
    },
  },
  { headerName: '데이터 건수', field: 'dataCount', width: 130 },
]
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.measure-page {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

/* Breadcrumb */
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    h2 {
      font-size: $font-size-xl;
      font-weight: 700;
      margin: 0;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: $font-size-sm;
    color: $text-secondary;

    .date-input {
      padding: 4px 8px;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      font-size: 12px;
      color: #333;
      &:focus { outline: none; border-color: $primary; }
    }
    .date-sep { color: #999; font-size: 12px; }
  }
}

.badge-realtime {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba($success, 0.1);
  color: $success;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
}

/* Tab bar */
.measure-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid $border-color;

  a {
    padding: 10px 20px;
    font-size: $font-size-md;
    color: $text-secondary;
    text-decoration: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    transition: all $transition-fast;

    &:hover {
      color: $primary;
    }

    &.active {
      color: $primary;
      border-bottom-color: $primary;
      font-weight: 600;
    }
  }
}

/* KPI Cards */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: $spacing-md;
}

.kpi-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  border-left: 3px solid transparent;

  .kpi-body {
    .kpi-label {
      font-size: $font-size-xs;
      color: $text-muted;
      margin-bottom: 4px;
    }
    .kpi-value {
      font-size: 22px;
      font-weight: 700;
      color: $text-primary;
    }
  }

  .kpi-sub {
    margin-top: 6px;
    font-size: 10px;
    color: $text-muted;
  }

  &.kpi-blue { border-left-color: #3b82f6; }
  &.kpi-green { border-left-color: #22c55e; }
  &.kpi-purple { border-left-color: #a855f7; }
  &.kpi-orange { border-left-color: #f97316; }
  &.kpi-teal { border-left-color: #14b8a6; }
}

/* Chart layout */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
}

.chart-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
}

.chart-title {
  font-size: $font-size-md;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $spacing-md;
  padding-bottom: $spacing-sm;
  border-bottom: 1px solid #f0f0f0;
}

/* Donut */
.donut-container {
  display: flex;
  align-items: center;
  gap: $spacing-xl;
}

.donut-svg {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.donut-total {
  font-size: 20px;
  font-weight: 700;
  fill: $text-primary;
}

.donut-label-center {
  font-size: 11px;
  fill: $text-muted;
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: $font-size-sm;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  color: $text-secondary;
}

.legend-value {
  font-weight: 600;
  color: $text-primary;
}

/* Line chart */
.line-chart-svg {
  width: 100%;
  height: auto;
}

.axis-text {
  font-size: 10px;
  fill: #999;
}

.legend-text {
  font-size: 10px;
  fill: $text-secondary;
}

/* Horizontal bars */
.hbar-svg {
  width: 100%;
  height: auto;
}

.hbar-label {
  font-size: 11px;
  fill: $text-secondary;
}

/* Gauges */
.gauge-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-md;
}

.gauge-item {
  display: flex;
  justify-content: center;
}

.gauge-svg {
  width: 120px;
  height: 80px;
}

/* AG Grid Table */
.table-section {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md $spacing-lg;
  border-bottom: 1px solid $border-color;
}

.table-count {
  font-size: $font-size-sm;
  color: $text-secondary;
  strong { color: $primary; }
}

.table-actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.btn-excel {
  background: none;
  border: 1px solid #2e7d32;
  color: #2e7d32;
  width: 32px;
  height: 32px;
  border-radius: $radius-md;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all $transition-fast;
  cursor: pointer;
  &:hover { background: #2e7d32; color: $white; }
}

.ag-grid-wrapper {
  :deep(.ag-theme-alpine) {
    --ag-header-background-color: #4a6a8a;
    --ag-header-foreground-color: #fff;
    --ag-header-height: 38px;
    --ag-row-height: 40px;
    --ag-font-size: 13px;
    --ag-borders: none;
    --ag-row-border-color: #f0f0f0;
    --ag-selected-row-background-color: #e8f0fe;
    font-family: $font-family;
  }
  :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; }
  :deep(.ag-header-cell) { color: #fff; }
}

/* Responsive */
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .kpi-row {
    grid-template-columns: repeat(3, 1fr);
  }
  .chart-row {
    grid-template-columns: 1fr;
  }
  .donut-container {
    flex-direction: column;
    align-items: flex-start;
  }
  .gauge-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
