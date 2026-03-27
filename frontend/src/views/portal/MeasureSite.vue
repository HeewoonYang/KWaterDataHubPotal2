<template>
  <div class="measure-page">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <router-link to="/portal/realtime-measure">실시간 계측DB</router-link>
      <span class="separator">/</span>
      <router-link :to="{ path: '/portal/realtime-measure/office', query: { region: selectedRegion } }">사무소 대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">사업장 대시보드</span>
    </nav>

    <!-- Header -->
    <div class="page-header">
      <h2>사업장 대시보드 ({{ selectedRegion }} &gt; {{ selectedOffice }} &gt; {{ selectedSite }})</h2>
    </div>

    <!-- Tab bar -->
    <div class="measure-tabs">
      <router-link to="/portal/realtime-measure">전체</router-link>
      <router-link to="/portal/realtime-measure/office">사무소 대시보드</router-link>
      <router-link to="/portal/realtime-measure/site" class="active">사업장 대시보드</router-link>
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
      <div class="filter-group">
        <label>사업장</label>
        <select v-model="selectedSite" class="filter-select">
          <option v-for="s in siteOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <button class="btn-search" @click="handleSearch">
        <SearchOutlined /> 조회
      </button>
    </div>

    <!-- KPI Top Row -->
    <div class="kpi-row kpi-row-3">
      <div class="kpi-card kpi-blue">
        <div class="kpi-label">태그수</div>
        <div class="kpi-value">2,149</div>
      </div>
      <div class="kpi-card kpi-green">
        <div class="kpi-label">데이터건수</div>
        <div class="kpi-value">1.6억</div>
      </div>
      <div class="kpi-card kpi-purple">
        <div class="kpi-label">데이터기간</div>
        <div class="kpi-value">2024.01~</div>
      </div>
    </div>

    <!-- KPI Bottom Row with mini donuts -->
    <div class="kpi-row kpi-row-3">
      <div class="kpi-card-donut">
        <div class="kpi-donut-left">
          <svg viewBox="0 0 80 80" class="mini-donut">
            <circle cx="40" cy="40" r="30" fill="none" stroke="#e8e8e8" stroke-width="8" />
            <circle cx="40" cy="40" r="30" fill="none" stroke="#DC3545" stroke-width="8"
              :stroke-dasharray="miniCircum" :stroke-dashoffset="miniCircum - miniCircum * 0.3985"
              transform="rotate(-90 40 40)" stroke-linecap="round" />
            <text x="40" y="44" text-anchor="middle" font-size="12" font-weight="700" fill="#DC3545">39.85%</text>
          </svg>
        </div>
        <div class="kpi-donut-right">
          <div class="kpi-label">유효율</div>
          <div class="kpi-value kpi-red">39.85%</div>
        </div>
      </div>
      <div class="kpi-card-donut">
        <div class="kpi-donut-left">
          <svg viewBox="0 0 80 80" class="mini-donut">
            <circle cx="40" cy="40" r="30" fill="none" stroke="#e8e8e8" stroke-width="8" />
            <circle cx="40" cy="40" r="30" fill="none" stroke="#28A745" stroke-width="8"
              :stroke-dasharray="miniCircum" :stroke-dashoffset="miniCircum - miniCircum * 0.6015"
              transform="rotate(-90 40 40)" stroke-linecap="round" />
            <text x="40" y="44" text-anchor="middle" font-size="12" font-weight="700" fill="#28A745">60.15%</text>
          </svg>
        </div>
        <div class="kpi-donut-right">
          <div class="kpi-label">수집률</div>
          <div class="kpi-value kpi-green-text">60.15%</div>
        </div>
      </div>
      <div class="kpi-card-status">
        <div class="kpi-label">최근 3일</div>
        <div class="status-row">
          <span class="status-item status-ok">정상 <strong>1,800</strong></span>
          <span class="status-item status-warn">경고 <strong>0</strong></span>
          <span class="status-item status-err">오류 <strong>349</strong></span>
        </div>
      </div>
    </div>

    <!-- Three-column donut charts -->
    <div class="donut-triple-row">
      <div class="chart-card" v-for="(donut, dIdx) in tripleDonutData" :key="'td'+dIdx">
        <div class="chart-title">{{ donut.title }}</div>
        <div class="triple-donut-body">
          <svg viewBox="0 0 160 160" class="triple-donut-svg">
            <circle v-for="(seg, sIdx) in computeTripleSegments(donut.segments)" :key="'tds'+sIdx"
              cx="80" cy="80" r="55" fill="none"
              :stroke="seg.color" stroke-width="24"
              :stroke-dasharray="seg.dashArray"
              :stroke-dashoffset="seg.dashOffset"
              transform="rotate(-90 80 80)"
            />
            <text x="80" y="76" text-anchor="middle" font-size="16" font-weight="700" fill="#333">{{ donut.total }}</text>
            <text x="80" y="92" text-anchor="middle" font-size="10" fill="#999">태그</text>
          </svg>
          <div class="triple-legend">
            <div v-for="(seg, sIdx) in donut.segments" :key="'tl'+sIdx" class="legend-item">
              <span class="legend-dot" :style="{ background: seg.color }"></span>
              <span class="legend-name">{{ seg.name }}</span>
              <span class="legend-value">{{ seg.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Two-column charts -->
    <div class="chart-row">
      <!-- Bar chart: 일별 데이터 유입량 -->
      <div class="chart-card">
        <div class="chart-title">일별 데이터 유입량</div>
        <svg viewBox="0 0 560 260" class="bar-chart-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="barGradVert" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3b82f6" stop-opacity="1" />
              <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.6" />
            </linearGradient>
          </defs>
          <!-- Grid lines -->
          <line v-for="i in 5" :key="'bgl'+i" :x1="50" :x2="540" :y1="20 + (i-1)*50" :y2="20 + (i-1)*50" stroke="#eee" stroke-width="1" />
          <!-- Y axis labels -->
          <text v-for="(lbl, i) in barYLabels" :key="'byl'+i" :x="45" :y="25 + i*50" text-anchor="end" class="axis-text">{{ lbl }}</text>
          <!-- Bars -->
          <g v-for="(val, i) in dailyBarData" :key="'bar'+i">
            <rect :x="60 + i * 35" :y="220 - (200 * val / barMax)" width="24" :height="200 * val / barMax" rx="3" fill="url(#barGradVert)" />
            <text :x="72 + i * 35" :y="238" text-anchor="middle" class="axis-text">{{ dailyBarLabels[i] }}</text>
          </g>
        </svg>
      </div>

      <!-- Horizontal bars: 유입량 변화 상위 태그 Top 8 -->
      <div class="chart-card">
        <div class="chart-title">유입량 변화 상위 태그 Top 8</div>
        <svg viewBox="0 0 520 320" class="hbar-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="topTagGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#f97316" stop-opacity="0.85" />
              <stop offset="100%" stop-color="#f97316" stop-opacity="1" />
            </linearGradient>
          </defs>
          <g v-for="(item, idx) in topTagsData" :key="'tt'+idx">
            <rect :x="100" :y="10 + idx * 38" width="380" height="24" rx="4" fill="#f0f0f0" />
            <rect :x="100" :y="10 + idx * 38" :width="380 * (item.value / topTagMax)" height="24" rx="4" fill="url(#topTagGrad)" />
            <text :x="95" :y="26 + idx * 38" text-anchor="end" class="hbar-label">{{ item.name }}</text>
            <text :x="105 + 380 * (item.value / topTagMax) - 8" :y="26 + idx * 38" text-anchor="end" fill="#fff" font-size="10" font-weight="600">
              {{ item.value.toLocaleString() }}
            </text>
          </g>
        </svg>
      </div>
    </div>

    <!-- AG Grid: 태그 목록 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">태그 목록 <strong>{{ tagGridData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(tagColumnDefs, tagGridData, selectedSite + '_태그목록')">
            <FileExcelOutlined />
          </button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="tagGridData"
          :columnDefs="tagColumnDefs"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="20"
          domLayout="autoHeight"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  FileExcelOutlined,
  SearchOutlined,
} from '@ant-design/icons-vue'
import { exportGridToExcel } from '../../utils/exportExcel'

ModuleRegistry.registerModules([AllCommunityModule])

const route = useRoute()

const regionOptions = ref(['수도권', '한강권역', '강원지역', '충청지역', '금영섬권역', '광주전남', '낙동강권역', '경남부산'])
const officeOptions = ref(['과천관리단', '시흥관리단', '안산관리단', '수원관리단'])
const siteOptions = ref(['G81', '시흥정수장', '반월정수장', '거점가압장', '안산가압장', '구천암', '경인가압장'])

const selectedRegion = ref((route.query.region as string) || '수도권')
const selectedOffice = ref((route.query.office as string) || '과천관리단')
const selectedSite = ref((route.query.site as string) || 'G81')

function handleSearch() {
  // In real app, fetch data based on selected filters
}

// Mini donut circumference
const miniCircum = 2 * Math.PI * 30

// Triple donut data
interface DonutSegment {
  name: string
  value: number
  color: string
}

interface TripleDonut {
  title: string
  total: string
  segments: DonutSegment[]
}

const tripleDonutData = ref<TripleDonut[]>([
  {
    title: '수량별 태그 분포',
    total: '2,149',
    segments: [
      { name: '유량', value: 820, color: '#3b82f6' },
      { name: '수위', value: 450, color: '#22c55e' },
      { name: '수질', value: 380, color: '#eab308' },
      { name: '기타', value: 499, color: '#a855f7' },
    ],
  },
  {
    title: '현행별 태그 분포',
    total: '2,149',
    segments: [
      { name: '수집중', value: 1293, color: '#22c55e' },
      { name: '미수집', value: 507, color: '#DC3545' },
      { name: '점검', value: 349, color: '#eab308' },
    ],
  },
  {
    title: '전후별 태그 분포',
    total: '2,149',
    segments: [
      { name: '전처리', value: 680, color: '#3b82f6' },
      { name: '후처리', value: 920, color: '#14b8a6' },
      { name: '미분류', value: 549, color: '#9ca3af' },
    ],
  },
])

function computeTripleSegments(segments: DonutSegment[]) {
  const circumference = 2 * Math.PI * 55
  const total = segments.reduce((s, seg) => s + seg.value, 0)
  let offset = 0
  return segments.map(seg => {
    const pct = seg.value / total
    const dashLen = circumference * pct
    const result = {
      color: seg.color,
      dashArray: `${dashLen} ${circumference - dashLen}`,
      dashOffset: `${-offset}`,
    }
    offset += dashLen
    return result
  })
}

// Daily bar chart data
const dailyBarData = [85, 92, 78, 105, 98, 110, 95, 88, 115, 102, 90, 108, 100, 96]
const dailyBarLabels = ['14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27']
const barMax = Math.max(...dailyBarData)
const barYLabels = ['120만', '90만', '60만', '30만', '0']

// Top tags horizontal bar data
const topTagsData = ref([
  { name: 'TAG001', value: 12500 },
  { name: 'TAG045', value: 10800 },
  { name: 'TAG012', value: 9600 },
  { name: 'TAG089', value: 8200 },
  { name: 'TAG034', value: 7500 },
  { name: 'TAG067', value: 6800 },
  { name: 'TAG023', value: 5900 },
  { name: 'TAG078', value: 5200 },
])

const topTagMax = computed(() => Math.max(...topTagsData.value.map(t => t.value)))

// Tag grid data
const tagGridData = ref([
  { tagName: 'TAG001', status: '정상', desc: '유량계_전류센서(합천)(10장) 수처리-1', category: 'GSCL0035-10-41270', supplier: '계측', tagType: '전류(A)', dataCount: '1시간', section: 90, unit: 'A', id: '053' },
  { tagName: 'TAG002', status: '정상', desc: '유량계_전류센서(합천)(101) 수처리-2', category: 'GSCL0035-10-41270', supplier: '계측', tagType: '전류(A)', dataCount: '1시간', section: 90, unit: 'A', id: '064' },
  { tagName: 'TAG003', status: '정상', desc: '유량계_전류센서(합천)(10) 수처리-3', category: 'GSCL0035-10-41270', supplier: '계측', tagType: '전류(A)', dataCount: '1시간', section: 90, unit: 'A', id: '005' },
  { tagName: 'TAG004', status: '정상', desc: '전력계_MCC-시설+태양광(구/시) 8호', category: 'SHNO355-10-41270', supplier: '전력', tagType: '전력(kW)', dataCount: '1시간', section: 90, unit: 'kW', id: '201' },
  { tagName: 'TAG005', status: '경고', desc: '전력계_MCC-4호 전력부(2진입) 8호', category: 'SHNO355-10-41270', supplier: '전력', tagType: '전력(kW)', dataCount: '1시간', section: 90, unit: 'kW', id: '202' },
  { tagName: 'TAG006', status: '정상', desc: '전력계_MCC-4로+태양(6진입) 8호', category: 'SHNO355-10-41270', supplier: '전력', tagType: '전력(kW)', dataCount: '1시간', section: 90, unit: 'kW', id: '203' },
  { tagName: 'TAG007', status: '정상', desc: '압력계_송수관 압력센서 FLT', category: 'BYAV1333-35-41270', supplier: '압력', tagType: '압력(MPa)', dataCount: '1시간', section: 90, unit: 'MPa', id: '204' },
  { tagName: 'TAG008', status: '정상', desc: '압력계_배수지 압력센서 FLT', category: 'BYAV1333-35-41270', supplier: '압력', tagType: '전류(A)', dataCount: '1시간', section: 90, unit: 'A', id: '205' },
  { tagName: 'TAG009', status: '정상', desc: '수위계_취수장 수위센서 L-01', category: 'WLVL2010-20-31240', supplier: '수위', tagType: '수위(m)', dataCount: '15분', section: 85, unit: 'm', id: '301' },
  { tagName: 'TAG010', status: '정상', desc: '수위계_정수지 수위센서 L-02', category: 'WLVL2010-20-31240', supplier: '수위', tagType: '수위(m)', dataCount: '15분', section: 85, unit: 'm', id: '302' },
  { tagName: 'TAG011', status: '오류', desc: '유량계_원수 유입 유량센서 F-01', category: 'FLOW3015-30-21150', supplier: '유량', tagType: '유량(m3/h)', dataCount: '1시간', section: 92, unit: 'm3/h', id: '401' },
  { tagName: 'TAG012', status: '정상', desc: '유량계_송수 유량센서 F-02', category: 'FLOW3015-30-21150', supplier: '유량', tagType: '유량(m3/h)', dataCount: '1시간', section: 92, unit: 'm3/h', id: '402' },
  { tagName: 'TAG013', status: '정상', desc: '수질계_탁도 측정센서 TU-01', category: 'QUAL4020-40-11080', supplier: '수질', tagType: '탁도(NTU)', dataCount: '15분', section: 88, unit: 'NTU', id: '501' },
  { tagName: 'TAG014', status: '정상', desc: '수질계_잔류염소 측정 CL-01', category: 'QUAL4020-40-11080', supplier: '수질', tagType: '염소(mg/L)', dataCount: '15분', section: 88, unit: 'mg/L', id: '502' },
  { tagName: 'TAG015', status: '오류', desc: '수질계_pH 측정센서 PH-01', category: 'QUAL4020-40-11080', supplier: '수질', tagType: 'pH', dataCount: '15분', section: 88, unit: 'pH', id: '503' },
  { tagName: 'TAG016', status: '경고', desc: '온도계_원수 수온센서 TE-01', category: 'TEMP5010-50-41270', supplier: '온도', tagType: '온도(C)', dataCount: '1시간', section: 90, unit: 'C', id: '601' },
])

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 70 }

const tagColumnDefs: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '태그명', field: 'tagName', width: 90, maxWidth: 90, flex: 0, cellStyle: { fontWeight: '600' } },
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
  { headerName: '설명', field: 'desc', flex: 3, minWidth: 200 },
  { headerName: '범주', field: 'category', flex: 1.5, minWidth: 150 },
  { headerName: '공급인', field: 'supplier', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '태그타입', field: 'tagType', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '데이터건수', field: 'dataCount', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '구간', field: 'section', width: 70, maxWidth: 70, flex: 0, type: 'numericColumn' },
  { headerName: '단위', field: 'unit', width: 70, maxWidth: 70, flex: 0 },
  { headerName: 'ID', field: 'id', width: 60, maxWidth: 60, flex: 0 },
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
  min-width: 120px;
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
  gap: $spacing-md;

  &.kpi-row-3 {
    grid-template-columns: repeat(3, 1fr);
  }
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
}

/* KPI Donut cards */
.kpi-card-donut {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  display: flex;
  align-items: center;
  gap: $spacing-md;
}

.kpi-donut-left {
  flex-shrink: 0;
}

.mini-donut {
  width: 70px;
  height: 70px;
}

.kpi-donut-right {
  .kpi-label {
    font-size: $font-size-xs;
    color: $text-muted;
    margin-bottom: 4px;
  }
  .kpi-value {
    font-size: 20px;
    font-weight: 700;
  }
  .kpi-red { color: #DC3545; }
  .kpi-green-text { color: #28A745; }
}

/* KPI Status card */
.kpi-card-status {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;

  .kpi-label {
    font-size: $font-size-xs;
    color: $text-muted;
    margin-bottom: 8px;
  }
}

.status-row {
  display: flex;
  gap: $spacing-md;
}

.status-item {
  font-size: $font-size-sm;
  padding: 4px 12px;
  border-radius: $radius-md;
  font-weight: 500;

  strong { font-weight: 700; }

  &.status-ok {
    background: rgba(40, 167, 69, 0.08);
    color: #28A745;
  }
  &.status-warn {
    background: rgba(255, 193, 7, 0.1);
    color: #d48a00;
  }
  &.status-err {
    background: rgba(220, 53, 69, 0.08);
    color: #DC3545;
  }
}

/* Triple donut row */
.donut-triple-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-lg;
}

.triple-donut-body {
  display: flex;
  align-items: center;
  gap: $spacing-lg;
}

.triple-donut-svg {
  width: 130px;
  height: 130px;
  flex-shrink: 0;
}

.triple-legend {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: $font-size-sm;
}

.legend-dot {
  width: 8px;
  height: 8px;
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

/* Bar chart */
.bar-chart-svg {
  width: 100%;
  height: auto;
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

.axis-text {
  font-size: 10px;
  fill: #999;
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
  .kpi-row.kpi-row-3 {
    grid-template-columns: 1fr 1fr;
  }
  .donut-triple-row {
    grid-template-columns: 1fr;
  }
  .chart-row {
    grid-template-columns: 1fr;
  }
  .filter-bar {
    flex-wrap: wrap;
  }
  .triple-donut-body {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
