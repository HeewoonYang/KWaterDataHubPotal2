<template>
  <div class="measure-page">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <router-link to="/portal/realtime-measure">실시간 계측DB</router-link>
      <span class="separator">/</span>
      <span class="current">사무소 대시보드</span>
    </nav>

    <!-- Header -->
    <div class="page-header">
      <h2>사무소 대시보드 ({{ selectedRegion }} &gt; {{ selectedOffice }})</h2>
    </div>

    <!-- Tab bar -->
    <div class="measure-tabs">
      <router-link to="/portal/realtime-measure">전체</router-link>
      <router-link to="/portal/realtime-measure/office" class="active">사무소 대시보드</router-link>
      <router-link to="/portal/realtime-measure/site">사업장 대시보드</router-link>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>권역</label>
        <select v-model="selectedRegion" class="filter-select">
          <option v-for="r in regionOptions" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>사무소</label>
        <select v-model="selectedOffice" class="filter-select">
          <option v-for="o in officeOptions" :key="o" :value="o">{{ o }}</option>
        </select>
      </div>
      <button class="btn-search" @click="handleSearch">
        <SearchOutlined /> 조회
      </button>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-row">
      <div class="kpi-card kpi-blue">
        <div class="kpi-label">사업장수</div>
        <div class="kpi-value">7</div>
      </div>
      <div class="kpi-card kpi-green">
        <div class="kpi-label">태그합계</div>
        <div class="kpi-value">3,857</div>
      </div>
      <div class="kpi-card kpi-purple">
        <div class="kpi-label">전체데이터</div>
        <div class="kpi-value">1.7억</div>
      </div>
      <div class="kpi-card kpi-orange">
        <div class="kpi-label">데이터기간</div>
        <div class="kpi-value">2024.01~</div>
      </div>
    </div>

    <!-- AG Grid: 사업장별 현황 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">사업장별 현황 <strong>{{ gridData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, gridData, selectedOffice + '_사업장')">
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

    <!-- Charts Row -->
    <div class="chart-row">
      <!-- Horizontal Bars: 사업장별 태그 분포 -->
      <div class="chart-card">
        <div class="chart-title">사업장별 태그 분포</div>
        <svg viewBox="0 0 520 300" class="hbar-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient v-for="(item, idx) in siteDistribution" :key="'sg'+idx" :id="'siteGrad'+idx" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" :stop-color="item.color" stop-opacity="0.85" />
              <stop offset="100%" :stop-color="item.color" stop-opacity="1" />
            </linearGradient>
          </defs>
          <g v-for="(item, idx) in siteDistribution" :key="'sb'+idx">
            <rect :x="120" :y="15 + idx * 38" width="360" height="24" rx="4" fill="#f0f0f0" />
            <rect :x="120" :y="15 + idx * 38" :width="360 * (item.tags / siteMaxTags)" height="24" rx="4" :fill="'url(#siteGrad'+idx+')'" />
            <text :x="115" :y="31 + idx * 38" text-anchor="end" class="hbar-label">{{ item.name }}</text>
            <text :x="125 + 360 * (item.tags / siteMaxTags) - 8" :y="31 + idx * 38" text-anchor="end" fill="#fff" font-size="11" font-weight="600">
              {{ item.tags.toLocaleString() }}
            </text>
          </g>
        </svg>
      </div>

      <!-- Area Line Chart: 일별 데이터 유입 추이 -->
      <div class="chart-card">
        <div class="chart-title">일별 데이터 유입 추이</div>
        <svg viewBox="0 0 560 260" class="line-chart-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="officeAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#22c55e" stop-opacity="0.3" />
              <stop offset="100%" stop-color="#22c55e" stop-opacity="0.02" />
            </linearGradient>
          </defs>
          <!-- Grid lines -->
          <line v-for="i in 5" :key="'ogl'+i" :x1="50" :x2="540" :y1="30 + (i-1)*50" :y2="30 + (i-1)*50" stroke="#eee" stroke-width="1" />
          <!-- Y axis labels -->
          <text v-for="(lbl, i) in officeYLabels" :key="'oyl'+i" :x="45" :y="35 + i*50" text-anchor="end" class="axis-text">{{ lbl }}</text>
          <!-- X axis labels -->
          <text v-for="(lbl, i) in officeXLabels" :key="'oxl'+i" :x="50 + i * (490 / (officeXLabels.length - 1))" :y="252" text-anchor="middle" class="axis-text">{{ lbl }}</text>
          <!-- Area fill -->
          <polygon :points="officeAreaPoints" fill="url(#officeAreaGrad)" />
          <!-- Line -->
          <polyline :points="officeLinePoints" fill="none" stroke="#22c55e" stroke-width="2" stroke-linejoin="round" />
          <!-- Dots -->
          <circle v-for="(pt, i) in officeDataPoints" :key="'odot'+i" :cx="pt.x" :cy="pt.y" r="3" fill="#22c55e" />
          <!-- Legend -->
          <rect x="450" y="8" width="10" height="10" rx="2" fill="#22c55e" />
          <text x="464" y="17" class="legend-text">일별 유입</text>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  FileExcelOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue'
import { exportGridToExcel } from '../../utils/exportExcel'

ModuleRegistry.registerModules([AllCommunityModule])

const route = useRoute()
const router = useRouter()

const regionOptions = ref(['수도권', '한강권역', '강원지역', '충청지역', '금영섬권역', '광주전남', '낙동강권역', '경남부산'])
const officeOptions = ref(['과천관리단', '시흥관리단', '안산관리단', '수원관리단'])

const selectedRegion = ref((route.query.region as string) || '수도권')
const selectedOffice = ref('과천관리단')

function handleSearch() {
  // In real app, fetch data based on selected filters
}

// Site distribution for horizontal bars
const siteDistribution = ref([
  { name: 'G81', tags: 2149, color: '#3b82f6' },
  { name: '시흥정수장', tags: 379, color: '#22c55e' },
  { name: '반월정수장', tags: 201, color: '#eab308' },
  { name: '거점가압장', tags: 132, color: '#f97316' },
  { name: '안산가압장', tags: 104, color: '#a855f7' },
  { name: '구천암', tags: 68, color: '#14b8a6' },
  { name: '경인가압장', tags: 94, color: '#ef4444' },
])

const siteMaxTags = computed(() => Math.max(...siteDistribution.value.map(s => s.tags)))

// Line chart data
const officeRawData = [120, 135, 128, 142, 155, 148, 160, 172, 165, 158, 170, 168, 175, 180]
const officeXLabels = ['03/14', '03/16', '03/18', '03/20', '03/22', '03/24', '03/26']
const officeYLabels = ['200만', '150만', '100만', '50만', '0']

const officeDataPoints = computed(() => {
  const minY = 30
  const maxY = 230
  const maxVal = 200
  const len = officeRawData.length
  return officeRawData.map((val, i) => ({
    x: 50 + i * (490 / (len - 1)),
    y: minY + (maxY - minY) * (1 - val / maxVal),
  }))
})

const officeLinePoints = computed(() =>
  officeDataPoints.value.map(p => `${p.x},${p.y}`).join(' ')
)

const officeAreaPoints = computed(() => {
  const pts = officeDataPoints.value
  const first = pts[0]
  const last = pts[pts.length - 1]
  return `${first.x},230 ${officeLinePoints.value} ${last.x},230`
})

// Grid data
const gridData = ref([
  { name: 'G81', tags: 2149, collectRate: 38.6, collectTags: 830, uncollect: 1319, dataCount: '8,400만', status: '경고' },
  { name: '시흥정수장', tags: 379, collectRate: 97.8, collectTags: 371, uncollect: 8, dataCount: '1,480만', status: '정상' },
  { name: '반월정수장', tags: 201, collectRate: 97.5, collectTags: 196, uncollect: 5, dataCount: '780만', status: '정상' },
  { name: '거점가압장', tags: 132, collectRate: 83.4, collectTags: 110, uncollect: 22, dataCount: '520만', status: '정상' },
  { name: '안산가압장', tags: 104, collectRate: 100, collectTags: 104, uncollect: 0, dataCount: '410만', status: '정상' },
  { name: '구천암', tags: 68, collectRate: 100, collectTags: 68, uncollect: 0, dataCount: '270만', status: '정상' },
  { name: '경인가압장', tags: 94, collectRate: 90.3, collectTags: 85, uncollect: 9, dataCount: '370만', status: '정상' },
])

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }

function navigateToSite(siteName: string) {
  router.push({ path: '/portal/realtime-measure/site', query: { region: selectedRegion.value, office: selectedOffice.value, site: siteName } })
}

const columnDefs: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  {
    headerName: '사업장명',
    field: 'name',
    flex: 2,
    minWidth: 140,
    cellRenderer: (params: any) => {
      const link = document.createElement('a')
      link.href = '#'
      link.textContent = params.value
      link.style.color = '#0066CC'
      link.style.textDecoration = 'none'
      link.style.fontWeight = '600'
      link.addEventListener('click', (e: Event) => {
        e.preventDefault()
        navigateToSite(params.value)
      })
      return link
    },
  },
  {
    headerName: '태그 수',
    field: 'tags',
    width: 100,
    maxWidth: 100,
    flex: 0,
    type: 'numericColumn',
    valueFormatter: (params: any) => params.value?.toLocaleString(),
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
  {
    headerName: '수집태그',
    field: 'collectTags',
    width: 100,
    maxWidth: 100,
    flex: 0,
    type: 'numericColumn',
    valueFormatter: (params: any) => params.value?.toLocaleString(),
  },
  {
    headerName: '미수집',
    field: 'uncollect',
    width: 90,
    maxWidth: 90,
    flex: 0,
    type: 'numericColumn',
    cellRenderer: (params: any) => {
      const span = document.createElement('span')
      span.textContent = params.value?.toLocaleString()
      span.style.fontWeight = '500'
      if (params.value > 50) {
        span.style.color = '#DC3545'
      }
      return span
    },
  },
  { headerName: '데이터건수', field: 'dataCount', width: 110, maxWidth: 110, flex: 0 },
  {
    headerName: '상태',
    field: 'status',
    width: 80,
    maxWidth: 80,
    flex: 0,
    cellRenderer: (params: any) => {
      const badge = document.createElement('span')
      badge.textContent = params.value
      badge.style.padding = '2px 10px'
      badge.style.borderRadius = '10px'
      badge.style.fontSize = '11px'
      badge.style.fontWeight = '600'
      if (params.value === '정상') {
        badge.style.background = 'rgba(40, 167, 69, 0.1)'
        badge.style.color = '#28A745'
      } else if (params.value === '경고') {
        badge.style.background = 'rgba(255, 193, 7, 0.15)'
        badge.style.color = '#d48a00'
      } else {
        badge.style.background = 'rgba(220, 53, 69, 0.1)'
        badge.style.color = '#DC3545'
      }
      return badge
    },
  },
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
  h2 {
    font-size: $font-size-xl;
    font-weight: 700;
    margin: 0;
  }
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

    &:hover { color: $primary; }

    &.active {
      color: $primary;
      border-bottom-color: $primary;
      font-weight: 600;
    }
  }
}

/* Filter bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-md $spacing-lg;
  box-shadow: $shadow-sm;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  label {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-secondary;
    white-space: nowrap;
  }
}

.filter-select {
  height: 32px;
  padding: 0 $spacing-md;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  font-size: $font-size-sm;
  color: $text-primary;
  background: $white;
  min-width: 140px;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: $primary;
  }
}

.btn-search {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 $spacing-lg;
  background: $primary;
  color: $white;
  border: none;
  border-radius: $radius-md;
  font-size: $font-size-sm;
  font-weight: 600;
  cursor: pointer;
  transition: background $transition-fast;

  &:hover { background: $primary-dark; }
}

/* KPI Cards */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-md;
}

.kpi-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  border-left: 3px solid transparent;

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

  &.kpi-blue { border-left-color: #3b82f6; }
  &.kpi-green { border-left-color: #22c55e; }
  &.kpi-purple { border-left-color: #a855f7; }
  &.kpi-orange { border-left-color: #f97316; }
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

/* Horizontal bars */
.hbar-svg {
  width: 100%;
  height: auto;
}

.hbar-label {
  font-size: 11px;
  fill: $text-secondary;
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
    grid-template-columns: repeat(2, 1fr);
  }
  .chart-row {
    grid-template-columns: 1fr;
  }
  .filter-bar {
    flex-wrap: wrap;
  }
}
</style>
