<template>
  <div class="admin-page">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">&gt;</span>
      <span class="current">갤러리 콘텐츠 관리</span>
    </nav>

    <div class="page-header">
      <h2>갤러리 콘텐츠 관리</h2>
      <p class="page-desc">시각화 갤러리에 제공할 차트 콘텐츠를 관리합니다.</p>
    </div>

    <!-- 저장 알림 -->
    <div v-if="showSavedMsg" class="saved-msg">
      <CheckCircleOutlined /> 차트가 저장되었습니다.
      <button class="close-msg" @click="showSavedMsg = false"><CloseOutlined /></button>
    </div>

    <!-- KPI Cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:#0066CC"><BarChartOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ charts.length }}</span><span class="stat-label">총 차트 수</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#28A745"><GlobalOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ publicCount }}</span><span class="stat-label">공개 차트</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#9b59b6"><LockOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ internalCount }}</span><span class="stat-label">내부 차트</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#e74c3c"><HeartOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ popularCount }}</span><span class="stat-label">인기 차트</span></div>
      </div>
    </div>

    <!-- Search / Filter -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group">
          <label>도메인</label>
          <select v-model="filterDomain">
            <option value="">전체</option>
            <option value="water">수질수량</option>
            <option value="dam">댐저수지</option>
            <option value="supply">광역상수도</option>
            <option value="energy">에너지발전</option>
            <option value="env">환경기상</option>
          </select>
        </div>
        <div class="filter-group">
          <label>차트유형</label>
          <select v-model="filterType">
            <option value="">전체</option>
            <option value="line">Line</option>
            <option value="bar">Bar</option>
            <option value="area">Area</option>
            <option value="pie">Pie</option>
            <option value="scatter">Scatter</option>
            <option value="gauge">Gauge</option>
            <option value="heatmap">Heatmap</option>
            <option value="table">Table</option>
            <option value="MAP">GIS 지도</option>
          </select>
        </div>
        <div class="filter-group search-group">
          <label>검색</label>
          <input type="text" v-model="searchText" placeholder="차트명, 데이터소스, 작성자 검색" @keyup.enter="applyFilter" />
        </div>
        <div class="filter-actions">
          <button class="btn btn-primary" @click="applyFilter"><SearchOutlined /> 조회</button>
          <button class="btn btn-outline" @click="resetFilter"><ReloadOutlined /> 초기화</button>
        </div>
      </div>
    </div>

    <!-- Tab + Actions bar -->
    <div class="tab-bar">
      <div class="tab-buttons">
        <button :class="['tab-btn', { active: activeTab === 'list' }]" @click="activeTab = 'list'">
          <UnorderedListOutlined /> 목록보기
        </button>
        <button :class="['tab-btn', { active: activeTab === 'card' }]" @click="activeTab = 'card'">
          <AppstoreOutlined /> 차트보기
        </button>
      </div>
      <div class="tab-actions">
        <span class="table-count">전체 <strong>{{ filteredData.length }}</strong>건</span>
        <button class="btn btn-success" @click="goCreateChart"><PlusOutlined /> 차트 생성</button>
        <button v-if="activeTab === 'list'" class="btn-excel" title="엑셀 다운로드" @click="handleExcelExport"><FileExcelOutlined /></button>
      </div>
    </div>

    <!-- Tab: 목록보기 (AG Grid) -->
    <div v-show="activeTab === 'list'" class="table-section">
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="filteredData"
          :columnDefs="columnDefs"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="10"
          domLayout="autoHeight"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- Tab: 차트보기 (Card Gallery) -->
    <div v-show="activeTab === 'card'" class="gallery-section">
      <div v-if="filteredData.length === 0" class="empty-state">
        <BarChartOutlined class="empty-icon" />
        <p>저장된 차트가 없습니다.</p>
        <router-link to="/portal/visualization" class="btn btn-primary">D&D 시각화에서 차트 만들기</router-link>
      </div>

      <div v-else class="gallery-grid">
        <div v-for="c in filteredData" :key="c.id" class="gallery-card" @click="openDetail(c)">
          <!-- 차트 미리보기 SVG -->
          <div class="card-preview">
            <div v-if="c.chart_config?.series" class="preview-svg-wrap" v-html="buildPreviewSvg(c)"></div>
            <div v-else class="preview-fallback" :style="{ background: typeColors[c.chart_type] || '#e3f2fd' }">
              <component :is="iconMap[c.chart_type] || BarChartOutlined" class="preview-icon" />
            </div>
            <span class="chart-type-badge">{{ typeLabels[c.chart_type] || c.chart_type }}</span>
          </div>
          <div class="card-body">
            <h4>{{ c.chart_name }}</h4>
            <p class="card-dataset" v-if="c.chart_config?.dataset_name">
              <DatabaseOutlined /> {{ c.chart_config.dataset_name }}
            </p>
            <div class="card-axes" v-if="c.chart_config?.x_axis_kr">
              <span class="axis-label x">X: {{ c.chart_config.x_axis_kr }}</span>
              <span v-for="(y, i) in (c.chart_config.y_axes_kr || [])" :key="i" class="axis-label y">Y: {{ y }}</span>
            </div>
            <div class="card-meta">
              <span><UserOutlined /> {{ c.owner_name || '나' }}</span>
              <span><ClockCircleOutlined /> {{ formatDate(c.created_at) }}</span>
              <span v-if="c.view_count"><EyeOutlined /> {{ c.view_count }}</span>
            </div>
          </div>
          <div class="card-actions" @click.stop>
            <button title="편집" @click="editChart(c)"><EditOutlined /></button>
            <button title="복제" @click="cloneChart(c.id)"><CopyOutlined /></button>
            <button title="삭제" @click="deleteChart(c.id)"><DeleteOutlined /></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Modal (AdminModal) -->
    <AdminModal :visible="showDetail" :title="detailChart?.chart_name + ' 상세'" size="lg" @close="showDetail = false">
      <template v-if="detailChart">
        <div class="modal-stats">
          <div class="modal-stat-card primary"><div class="stat-title">차트유형</div><div class="stat-number" style="font-size:16px">{{ typeLabels[detailChart.chart_type] || detailChart.chart_type }}</div></div>
          <div class="modal-stat-card success"><div class="stat-title">데이터소스</div><div class="stat-number" style="font-size:16px">{{ detailChart.chart_config?.dataset_name || '-' }}</div></div>
          <div class="modal-stat-card warning"><div class="stat-title">조회수</div><div class="stat-number">{{ detailChart.view_count || 0 }}</div></div>
          <div class="modal-stat-card danger"><div class="stat-title">작성자</div><div class="stat-number" style="font-size:16px">{{ detailChart.owner_name || '-' }}</div></div>
        </div>

        <!-- 상세 SVG 미리보기 -->
        <div class="detail-chart-area">
          <div v-if="detailChart.chart_config?.series" class="detail-svg-wrap" v-html="buildDetailSvg(detailChart)"></div>
          <div v-else class="detail-fallback">
            <component :is="iconMap[detailChart.chart_type] || BarChartOutlined" class="detail-fallback-icon" />
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">기본 정보</div>
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">차트 ID</span><span class="info-value">{{ detailChart.id }}</span></div>
            <div class="modal-info-item"><span class="info-label">차트명</span><span class="info-value">{{ detailChart.chart_name }}</span></div>
            <div class="modal-info-item"><span class="info-label">차트유형</span><span class="info-value">{{ typeLabels[detailChart.chart_type] || detailChart.chart_type }}</span></div>
            <div class="modal-info-item"><span class="info-label">데이터소스</span><span class="info-value">{{ detailChart.chart_config?.dataset_name || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">X축</span><span class="info-value">{{ detailChart.chart_config?.x_axis_kr || detailChart.chart_config?.x_axis || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">Y축</span><span class="info-value">{{ (detailChart.chart_config?.y_axes_kr || detailChart.chart_config?.y_axes || []).join(', ') || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">작성자</span><span class="info-value">{{ detailChart.owner_name || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">생성일</span><span class="info-value">{{ formatDate(detailChart.created_at) }}</span></div>
          </div>
        </div>
      </template>
      <template #footer>
        <button class="btn btn-primary" @click="editChart(detailChart)"><EditOutlined /> 편집</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  SearchOutlined, ReloadOutlined, PlusOutlined, FileExcelOutlined, EditOutlined,
  BarChartOutlined, GlobalOutlined, LockOutlined, HeartOutlined,
  LineChartOutlined, PieChartOutlined, DotChartOutlined, AreaChartOutlined,
  UserOutlined, ClockCircleOutlined, EyeOutlined, DeleteOutlined, CopyOutlined,
  DatabaseOutlined, CheckCircleOutlined, CloseOutlined,
  UnorderedListOutlined, AppstoreOutlined,
} from '@ant-design/icons-vue'
import type { Component } from 'vue'

import AdminModal from '../../components/AdminModal.vue'
import { exportGridToExcel } from '../../utils/exportExcel'
import { visualizationApi } from '../../api/portal.api'

ModuleRegistry.registerModules([AllCommunityModule])

const route = useRoute()
const router = useRouter()

// ─── State ───
const activeTab = ref<'list' | 'card'>('list')
const searchText = ref('')
const filterDomain = ref('')
const filterType = ref('')
const showDetail = ref(false)
const showSavedMsg = ref(false)
const detailChart = ref<any>(null)

// ─── Constants ───
const iconMap: Record<string, Component> = {
  bar: BarChartOutlined, line: LineChartOutlined, pie: PieChartOutlined,
  scatter: DotChartOutlined, area: AreaChartOutlined,
}
const typeLabels: Record<string, string> = {
  bar: '막대', line: '선', pie: '원', scatter: '산점도', area: '영역',
  gauge: '게이지', heatmap: '히트맵', table: '테이블',
}
const typeColors: Record<string, string> = {
  bar: '#e3f2fd', line: '#e8f5e9', pie: '#fff3e0', scatter: '#f3e5f5', area: '#fce4ec',
}
const previewColors = ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8']

// ─── Default (fallback) charts ───
const defaultCharts = [
  { id: 'mock1', chart_name: '월별 수집량 추이', chart_type: 'bar', owner_name: '관리자', created_at: '2026-03-25', view_count: 42, chart_config: { dataset_name: '댐 수위 관측 데이터', x_axis_kr: '댐명', y_axes_kr: ['수위(m)'], labels: ['소양강댐', '충주댐', '안동댐', '임하댐', '합천댐'], series: [{ name: '수위(m)', data: [195.2, 138.4, 162.8, 115.3, 148.7] }] } },
  { id: 'mock2', chart_name: '수질 항목별 변화', chart_type: 'line', owner_name: '홍길동', created_at: '2026-03-24', view_count: 28, chart_config: { dataset_name: '수질 모니터링 센서', x_axis_kr: '측정일', y_axes_kr: ['pH', 'DO(mg/L)'], labels: ['3/20', '3/21', '3/22', '3/23', '3/24', '3/25'], series: [{ name: 'pH', data: [7.2, 7.4, 7.1, 7.3, 7.5, 7.2] }, { name: 'DO', data: [8.1, 8.3, 7.9, 8.5, 8.2, 8.4] }] } },
  { id: 'mock3', chart_name: '데이터 유형 분포', chart_type: 'pie', owner_name: '관리자', created_at: '2026-03-23', view_count: 55, chart_config: { dataset_name: '카탈로그 통계', x_axis_kr: '유형', y_axes_kr: ['건수'], labels: ['DB', 'IoT', 'API', 'CSV', 'FILE'], series: [{ name: '건수', data: [423, 287, 215, 178, 89] }] } },
]

const charts = ref<any[]>(defaultCharts)

// ─── KPI computed ───
const publicCount = computed(() => charts.value.filter(c => c.is_public || c.dataLevel === 'public').length)
const internalCount = computed(() => charts.value.filter(c => !c.is_public || c.dataLevel === 'internal').length)
const popularCount = computed(() => charts.value.filter(c => (c.view_count || 0) >= 50 || (c.likes || 0) >= 50).length)

// ─── Filter ───
const filteredData = computed(() => {
  let data = charts.value
  if (filterDomain.value) {
    data = data.filter(r => r.domain === filterDomain.value)
  }
  if (filterType.value) {
    data = data.filter(r => r.chart_type === filterType.value || r.type === filterType.value)
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    data = data.filter(r =>
      (r.chart_name || r.name || '').toLowerCase().includes(q) ||
      (r.chart_config?.dataset_name || '').toLowerCase().includes(q) ||
      (r.owner_name || r.author || '').toLowerCase().includes(q)
    )
  }
  return data
})

// ─── AG Grid ───
const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }

const columnDefs: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 55, resizable: false },
  { headerName: '차트명', field: 'chart_name', flex: 1.5, minWidth: 160,
    cellRenderer: (params: any) => {
      const name = params.value || params.data?.name || ''
      return `<span style="font-weight:600">${name}</span>`
    }
  },
  { headerName: '차트유형', field: 'chart_type', width: 110,
    cellRenderer: (params: any) => {
      const label = typeLabels[params.value] || params.value || ''
      return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#f0f2f5;color:#555">${label}</span>`
    }
  },
  { headerName: '데이터소스', flex: 1.2, minWidth: 140,
    valueGetter: (params: any) => params.data?.chart_config?.dataset_name || '-'
  },
  { headerName: 'X축', width: 120,
    valueGetter: (params: any) => params.data?.chart_config?.x_axis_kr || '-'
  },
  { headerName: 'Y축', width: 150,
    valueGetter: (params: any) => (params.data?.chart_config?.y_axes_kr || []).join(', ') || '-'
  },
  { headerName: '작성자', width: 110,
    valueGetter: (params: any) => params.data?.owner_name || params.data?.author || '-'
  },
  { headerName: '생성일', width: 120,
    valueGetter: (params: any) => formatDate(params.data?.created_at)
  },
  { headerName: '조회수', width: 90,
    valueGetter: (params: any) => params.data?.view_count || 0
  },
  { headerName: '관리', width: 150, sortable: false,
    cellRenderer: () => {
      return `<span class="grid-actions">
        <button class="grid-btn grid-btn-detail" data-action="detail">상세</button>
        <button class="grid-btn grid-btn-edit" data-action="edit">편집</button>
        <button class="grid-btn grid-btn-delete" data-action="delete">삭제</button>
      </span>`
    },
    onCellClicked: (params: any) => {
      const target = params.event?.target as HTMLElement
      const action = target?.getAttribute('data-action')
      if (action === 'detail') {
        openDetail(params.data)
      } else if (action === 'edit') {
        editChart(params.data)
      } else if (action === 'delete') {
        deleteChart(params.data.id)
      }
    }
  },
]

// ─── API ───
async function fetchCharts() {
  try {
    const params: Record<string, any> = { page: 1, page_size: 50 }
    if (filterType.value) params.chart_type = filterType.value
    const res = await visualizationApi.listCharts(params)
    if (res.data?.items && res.data.items.length > 0) {
      charts.value = res.data.items
    }
  } catch (e) {
    console.warn('차트 갤러리 API 실패, fallback 사용')
  }
}

async function deleteChart(id: string) {
  if (!confirm('차트를 삭제하시겠습니까?')) return
  try {
    await visualizationApi.deleteChart(id)
    charts.value = charts.value.filter(c => c.id !== id)
  } catch (e) {
    console.error('차트 삭제 실패:', e)
  }
}

async function cloneChart(id: string) {
  try {
    await visualizationApi.cloneChart(id)
    await fetchCharts()
  } catch (e) {
    console.error('차트 복제 실패:', e)
  }
}

// ─── Navigation ───
function goCreateChart() {
  router.push('/portal/visualization')
}

function editChart(c: any) {
  if (!c) return
  router.push({ path: '/portal/visualization', query: { edit: c.id } })
}

function openDetail(c: any) {
  detailChart.value = c
  showDetail.value = true
}

function onRowClick(event: any) {
  const target = event.event?.target as HTMLElement
  // Skip if a button in the actions column was clicked
  if (target?.getAttribute('data-action')) return
  openDetail(event.data)
}

function formatDate(dt: string) {
  if (!dt) return '-'
  return dt.substring(0, 10)
}

function handleExcelExport() {
  exportGridToExcel(columnDefs, filteredData.value, '갤러리_콘텐츠')
}

function applyFilter() { /* filters are reactive via computed */ }
function resetFilter() { filterDomain.value = ''; filterType.value = ''; searchText.value = '' }

// ─── SVG Preview Builders ───
function linePoints(data: number[], w: number, h: number): string {
  if (!data || data.length === 0) return ''
  const maxVal = Math.max(...data) || 1
  return data.map((v: number, i: number) => `${i / (data.length - 1 || 1) * w},${h - (v / maxVal * (h - 10))}`).join(' ')
}

function buildPreviewSvg(c: any): string {
  const cfg = c.chart_config
  const series: any[] = cfg?.series || []
  const colors = previewColors
  const type = c.chart_type

  if (type === 'bar') {
    let rects = ''
    series.forEach((s: any, si: number) => {
      const data: number[] = (s.data || []).slice(0, 8)
      const max = Math.max(...data, 1)
      const n = data.length
      const groupW = 270 / n
      const barW = groupW / (series.length + 1)
      data.forEach((val: number, vi: number) => {
        const x = vi * groupW + si * barW
        const h = (val / max) * 100
        rects += `<rect x="${x}" y="${110 - h}" width="${barW}" height="${h}" fill="${colors[si]}" rx="2"/>`
      })
    })
    return `<svg viewBox="0 0 280 120" class="preview-svg"><g transform="translate(5,5)">${rects}</g></svg>`
  }
  if (type === 'line') {
    let lines = ''
    series.forEach((s: any, si: number) => {
      lines += `<polyline points="${linePoints(s.data, 270, 100)}" fill="none" stroke="${colors[si]}" stroke-width="2.5"/>`
    })
    return `<svg viewBox="0 0 280 120" class="preview-svg"><g transform="translate(5,10)">${lines}</g></svg>`
  }
  if (type === 'pie') {
    const data: number[] = series[0]?.data || []
    const total = data.reduce((a: number, b: number) => a + b, 0) || 1
    let paths = '', cum = 0
    data.forEach((val: number, i: number) => {
      const angle = (val / total) * Math.PI * 2
      const x1 = Math.cos(cum) * 45, y1 = Math.sin(cum) * 45
      cum += angle
      const x2 = Math.cos(cum) * 45, y2 = Math.sin(cum) * 45
      paths += `<path d="M0,0 L${x1},${y1} A45,45 0 ${angle > Math.PI ? 1 : 0},1 ${x2},${y2} Z" fill="${colors[i % colors.length]}" stroke="white" stroke-width="1.5"/>`
    })
    return `<svg viewBox="0 0 280 120" class="preview-svg"><g transform="translate(140,60)">${paths}</g></svg>`
  }
  if (type === 'area') {
    const data: number[] = series[0]?.data || []
    const lp = linePoints(data, 270, 100)
    const ap = `${lp} 270,100 0,100`
    return `<svg viewBox="0 0 280 120" class="preview-svg"><defs><linearGradient id="aG" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1677ff" stop-opacity="0.3"/><stop offset="100%" stop-color="#1677ff" stop-opacity="0.02"/></linearGradient></defs><g transform="translate(5,10)"><polygon points="${ap}" fill="url(#aG)"/><polyline points="${lp}" fill="none" stroke="#1677ff" stroke-width="2"/></g></svg>`
  }
  // scatter
  const data: number[] = series[0]?.data || []
  const max = Math.max(...data, 1)
  let dots = ''
  data.forEach((v: number, i: number) => {
    dots += `<circle cx="${i / (data.length - 1 || 1) * 270}" cy="${100 - (v / max * 90)}" r="4" fill="${colors[0]}" fill-opacity="0.6"/>`
  })
  return `<svg viewBox="0 0 280 120" class="preview-svg"><g transform="translate(5,10)">${dots}</g></svg>`
}

function buildDetailSvg(c: any): string {
  const cfg = c.chart_config
  const series: any[] = cfg?.series || []
  const labels: string[] = cfg?.labels || []
  const colors = previewColors
  const type = c.chart_type
  const W = 520, H = 250

  if (type === 'bar') {
    let rects = '', labelTexts = ''
    series.forEach((s: any, si: number) => {
      const data: number[] = s.data || []
      const max = Math.max(...data, 1)
      const n = data.length
      const groupW = W / n
      const barW = groupW / (series.length + 1)
      data.forEach((val: number, vi: number) => {
        const x = vi * groupW + si * barW
        const h = (val / max) * (H - 20)
        rects += `<rect x="${x}" y="${H - h}" width="${barW}" height="${h}" fill="${colors[si]}" rx="3"/>`
      })
    })
    labels.forEach((l: string, i: number) => {
      const x = i * (W / labels.length) + W / labels.length / 2
      const txt = l.length > 5 ? l.slice(0, 5) + '...' : l
      labelTexts += `<text x="${x}" y="${H + 18}" text-anchor="middle" fill="#666" font-size="11">${txt}</text>`
    })
    let legend = ''
    series.forEach((s: any, si: number) => {
      legend += `<g transform="translate(${si * 100},0)"><rect width="10" height="10" fill="${colors[si]}" rx="2"/><text x="14" y="9" fill="#666" font-size="11">${s.name}</text></g>`
    })
    return `<svg viewBox="0 0 600 300" class="detail-svg"><g transform="translate(40,20)">${rects}${labelTexts}<g transform="translate(${W - series.length * 100},-8)">${legend}</g></g></svg>`
  }
  if (type === 'line') {
    let lines = ''
    series.forEach((s: any, si: number) => {
      const data: number[] = s.data || []
      const max = Math.max(...data, 1)
      lines += `<polyline points="${linePoints(data, W, H)}" fill="none" stroke="${colors[si]}" stroke-width="2.5"/>`
      data.forEach((v: number, vi: number) => {
        lines += `<circle cx="${vi / (data.length - 1 || 1) * W}" cy="${H - (v / max * (H - 10))}" r="4" fill="${colors[si]}"/>`
      })
    })
    let labelTexts = ''
    labels.forEach((l: string, i: number) => {
      const x = i / ((labels.length || 1) - 1 || 1) * W
      labelTexts += `<text x="${x}" y="${H + 18}" text-anchor="middle" fill="#666" font-size="11">${l.length > 5 ? l.slice(0, 5) + '...' : l}</text>`
    })
    return `<svg viewBox="0 0 600 300" class="detail-svg"><g transform="translate(40,20)">${lines}${labelTexts}</g></svg>`
  }
  // pie / area / scatter - reuse preview logic at larger scale
  return buildPreviewSvg(c).replace('280', '600').replace('120', '300')
}

// ─── Lifecycle ───
onMounted(() => {
  fetchCharts()
  if (route.query.saved === '1') {
    showSavedMsg.value = true
    setTimeout(() => { showSavedMsg.value = false }, 4000)
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.admin-page { display: flex; flex-direction: column; gap: $spacing-lg; }

/* Breadcrumb */
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}

.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  .page-desc { font-size: $font-size-sm; color: $text-muted; }
}

/* Saved message */
.saved-msg {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #f6ffed; border: 1px solid #b7eb8f; border-radius: $radius-md;
  color: #389e0d; font-size: $font-size-sm;
  .close-msg { background: none; border: none; color: #389e0d; cursor: pointer; margin-left: auto; }
}

/* Search Filter */
.search-filter { background: #f5f7fa; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; }
.filter-row { display: flex; align-items: flex-end; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group {
  display: flex; flex-direction: column; gap: $spacing-xs;
  label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; }
  select, input { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 130px; background: $white; outline: none; &:focus { border-color: $primary; } }
  &.search-group { flex: 1; input { width: 100%; } }
}
.filter-actions { display: flex; gap: $spacing-sm; }

/* KPI Cards */
.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: $spacing-md; }
.stat-card {
  background: $white; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; display: flex; align-items: center; gap: $spacing-md; box-shadow: $shadow-sm;
  .stat-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: $white; flex-shrink: 0; }
  .stat-info { flex: 1; display: flex; flex-direction: column; }
  .stat-value { font-size: $font-size-xl; font-weight: 700; }
  .stat-label { font-size: $font-size-xs; color: $text-muted; }
}

/* Tab Bar */
.tab-bar {
  display: flex; justify-content: space-between; align-items: center;
  background: $white; border: 1px solid $border-color; border-radius: $radius-md;
  padding: $spacing-sm $spacing-lg; box-shadow: $shadow-sm;
}
.tab-buttons { display: flex; gap: 4px; }
.tab-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: 1px solid transparent; border-radius: $radius-sm;
  background: none; color: $text-secondary; font-size: $font-size-sm; font-weight: 500;
  cursor: pointer; transition: all 0.15s;
  &:hover { background: #f5f7fa; color: $text-primary; }
  &.active { background: $primary; color: $white; border-color: $primary; }
}
.tab-actions {
  display: flex; align-items: center; gap: $spacing-sm;
}
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }

/* Excel button */
.btn-excel {
  background: none; border: 1px solid #2e7d32; color: #2e7d32; width: 32px; height: 32px; border-radius: $radius-md; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; cursor: pointer;
  &:hover { background: #2e7d32; color: $white; }
}

/* AG Grid (목록보기) */
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.ag-grid-wrapper {
  :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; --ag-row-border-color: #f0f0f0; --ag-selected-row-background-color: #e8f0fe; font-family: $font-family; }
  :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; }
  :deep(.ag-header-cell) { color: #fff; }
}
:deep(.ag-row) { cursor: pointer; }
:deep(.grid-actions) { display: flex; gap: 4px; align-items: center; }
:deep(.grid-btn) {
  padding: 2px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; border: 1px solid; background: #fff;
  &.grid-btn-detail { border-color: #0066CC; color: #0066CC; &:hover { background: #0066CC; color: #fff; } }
  &.grid-btn-edit { border-color: #28A745; color: #28A745; &:hover { background: #28A745; color: #fff; } }
  &.grid-btn-delete { border-color: #DC3545; color: #DC3545; &:hover { background: #DC3545; color: #fff; } }
}

/* Gallery (차트보기) */
.gallery-section { }

.empty-state {
  text-align: center; padding: 60px 20px; color: $text-muted;
  .empty-icon { font-size: 64px; opacity: 0.15; display: block; margin-bottom: $spacing-lg; }
  p { font-size: $font-size-md; margin-bottom: $spacing-lg; }
}

.gallery-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: $spacing-lg; }

.gallery-card {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg;
  overflow: hidden; box-shadow: $shadow-sm; cursor: pointer;
  transition: all 0.2s;
  &:hover { box-shadow: $shadow-md; transform: translateY(-2px); }
}

.card-preview {
  height: 160px; display: flex; align-items: center; justify-content: center;
  background: #f8fafd; position: relative; overflow: hidden;
  .preview-svg-wrap { width: 90%; height: 85%; display: flex; align-items: center; justify-content: center;
    :deep(svg) { width: 100%; height: 100%; }
  }
  .chart-type-badge {
    position: absolute; top: 8px; right: 8px; font-size: 10px; padding: 2px 8px;
    background: rgba(0,0,0,0.06); border-radius: 10px; color: $text-muted;
  }
}

.preview-fallback {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  .preview-icon { font-size: 48px; opacity: 0.25; }
}

.card-body {
  padding: 12px 16px;
  h4 { font-size: $font-size-md; font-weight: 600; margin-bottom: 4px; color: $text-primary; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .card-dataset { font-size: $font-size-xs; color: $text-muted; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; }
}

.card-axes {
  display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;
  .axis-label {
    font-size: 10px; padding: 1px 6px; border-radius: 8px;
    &.x { background: #e6f0ff; color: #0066CC; }
    &.y { background: #f6ffed; color: #28A745; }
  }
}

.card-meta {
  display: flex; gap: $spacing-md;
  span { font-size: $font-size-xs; color: $text-muted; display: flex; align-items: center; gap: 3px; }
}

.card-actions {
  display: flex; justify-content: flex-end; gap: $spacing-sm; padding: 6px 16px;
  border-top: 1px solid #f5f7fa;
  button {
    background: none; border: none; color: $text-muted; font-size: 14px; padding: 4px 6px;
    border-radius: $radius-sm; cursor: pointer;
    &:hover { color: $primary; background: #f5f7fa; }
  }
}

/* Detail modal chart area */
.detail-chart-area {
  background: #f8fafd; border: 1px solid $border-color; border-radius: $radius-md;
  padding: 20px; margin-bottom: 20px; min-height: 280px;
  display: flex; align-items: center; justify-content: center;
  .detail-svg-wrap { width: 100%; display: flex; align-items: center; justify-content: center;
    :deep(svg) { width: 100%; max-height: 300px; }
  }
}
.detail-fallback {
  text-align: center;
  .detail-fallback-icon { font-size: 64px; opacity: 0.15; }
}

/* Responsive - Tablet */
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .filter-row { flex-direction: column; align-items: stretch; }
  .gallery-grid { grid-template-columns: repeat(2, 1fr); }
  .tab-bar { flex-direction: column; gap: $spacing-sm; align-items: stretch;
    .tab-actions { justify-content: flex-end; }
  }
}
</style>
