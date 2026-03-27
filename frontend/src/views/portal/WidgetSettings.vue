<template>
  <div class="widget-page">
    <!-- 브레드크럼 -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">위젯 설정</span>
    </nav>

    <div class="page-header">
      <h2>위젯 설정</h2>
      <p>대시보드에 표시할 위젯을 선택하고 배치를 미리 확인하세요.</p>
    </div>

    <!-- 저장 성공 메시지 -->
    <div v-if="showSavedMsg" class="saved-msg">
      <CheckCircleOutlined /> 위젯 배치가 저장되었습니다. 대시보드에서 확인하세요.
      <button class="close-msg" @click="showSavedMsg = false"><CloseOutlined /></button>
    </div>

    <!-- 상단: 대시보드 위젯 캔버스 (미리보기) -->
    <section class="canvas-section">
      <div class="canvas-header">
        <div class="canvas-title">
          <AppstoreOutlined /> 대시보드 위젯 배치
          <span class="canvas-count">{{ selectedWidgets.length }}개 배치됨</span>
        </div>
        <div class="canvas-actions">
          <button class="btn btn-sm btn-primary" @click="saveLayout"><SaveOutlined /> 저장</button>
          <button class="btn btn-sm btn-outline" @click="resetWidgets"><ReloadOutlined /> 초기화</button>
          <button v-if="selectedWidgets.length > 0" class="btn btn-sm btn-outline" @click="selectedWidgets = []">
            <DeleteOutlined /> 전체 제거
          </button>
        </div>
      </div>
      <div class="canvas-area" :class="{ empty: selectedWidgets.length === 0 }">
        <div v-if="selectedWidgets.length === 0" class="canvas-placeholder">
          <AppstoreOutlined class="placeholder-icon" />
          <p>아래 위젯 라이브러리에서 위젯을 더블클릭하여 대시보드에 추가하세요.</p>
        </div>
        <div v-else class="canvas-grid">
          <div
            v-for="(code, i) in selectedWidgets"
            :key="code"
            class="canvas-card"
            draggable="true"
            @dragstart="onDragStart($event, i)"
            @dragover.prevent="onDragOver(i)"
            @dragleave="onDragLeave"
            @drop="onDrop($event, i)"
            @dragend="onDragEnd"
            :style="{
              gridColumn: `span ${getColSpan(code)}`,
              gridRow: `span ${getRowSpan(code)}`,
              opacity: dragIndex === i ? 0.4 : 1,
              border: dropTarget === i ? '2px solid #0066CC' : '',
            }"
          >
            <div class="canvas-card-header">
              <span class="canvas-card-name">
                <DragOutlined class="drag-icon" />
                {{ getWidgetName(code) }}
              </span>
              <div class="size-controls">
                <span class="size-label">{{ getColSpan(code) }}x{{ getRowSpan(code) }}</span>
                <select :value="getColSpan(code)" @change="setColSpan(code, +($event.target as HTMLSelectElement).value)" title="가로 칸" class="size-select">
                  <option v-for="n in 4" :key="n" :value="n">{{ n }}열</option>
                </select>
                <select :value="getRowSpan(code)" @change="setRowSpan(code, +($event.target as HTMLSelectElement).value)" title="세로 칸" class="size-select">
                  <option v-for="n in 4" :key="n" :value="n">{{ n }}행</option>
                </select>
                <button class="btn-remove" @click="removeByCode(code)" title="제거"><CloseOutlined /></button>
              </div>
            </div>
            <div class="canvas-card-body">
              <!-- KPI 미리보기 -->
              <template v-if="getWidgetType(code) === 'KPI'">
                <div class="preview-kpi">
                  <div class="preview-kpi-icon" :style="{ background: getWidgetColor(code) }">
                    <component :is="getWidgetIconComp(code)" />
                  </div>
                  <div class="preview-kpi-detail">
                    <span class="preview-kpi-value">{{ getKpiValue(code) }}</span>
                    <span class="preview-kpi-label">{{ getWidgetLabel(code) }}</span>
                  </div>
                </div>
              </template>
              <!-- CHART 미리보기 -->
              <template v-else-if="getWidgetType(code) === 'CHART'">
                <div class="preview-chart" v-html="getChartSvg(code)"></div>
              </template>
              <!-- TABLE 미리보기 -->
              <template v-else-if="getWidgetType(code) === 'TABLE'">
                <div class="preview-table">
                  <div v-for="(row, ri) in getTableRows(code)" :key="ri" class="preview-table-row">
                    <span class="row-text">{{ row.text }}</span>
                    <span class="row-sub">{{ row.sub }}</span>
                  </div>
                </div>
              </template>
              <!-- SEARCH 미리보기 -->
              <template v-else-if="getWidgetType(code) === 'SEARCH'">
                <div class="preview-search">
                  <SearchOutlined /> AI 검색...
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 하단: 위젯 라이브러리 -->
    <section class="library-section">
      <div class="lib-header">
        <div class="lib-title">
          <DatabaseOutlined /> 위젯 라이브러리
          <span class="lib-count">— {{ availableWidgets.length }}개 사용 가능</span>
        </div>
        <div class="lib-filter">
          <select v-model="filterType">
            <option value="">전체 유형</option>
            <option value="KPI">KPI</option>
            <option value="CHART">차트</option>
            <option value="TABLE">테이블</option>
            <option value="SEARCH">검색</option>
          </select>
          <input v-model="searchText" placeholder="위젯 검색..." />
        </div>
      </div>
      <div class="lib-grid">
        <div v-for="w in availableWidgets" :key="w.code" class="widget-lib-card" @dblclick="addWidget(w.code)">
          <div class="lib-card-top">
            <div class="lib-card-icon" :style="{ background: getWidgetColor(w.code) }">
              <component :is="getWidgetIconComp(w.code)" />
            </div>
            <div class="lib-card-info">
              <span class="lib-card-name">{{ w.name }}</span>
              <span class="lib-card-type" :style="{ background: typeColor[w.type] + '15', color: typeColor[w.type] }">{{ w.type }}</span>
            </div>
          </div>
          <div class="add-hint">더블클릭하여 대시보드에 추가</div>
        </div>
        <div v-if="availableWidgets.length === 0" class="lib-empty">
          <p>모든 위젯이 배치되었습니다.</p>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Component } from 'vue'
import {
  AppstoreOutlined, SaveOutlined, ReloadOutlined, DeleteOutlined,
  CloseOutlined, CheckCircleOutlined, DragOutlined, SearchOutlined,
  DatabaseOutlined, BarChartOutlined,
  SyncOutlined, DownloadOutlined, TeamOutlined,
  HddOutlined, SafetyCertificateOutlined, FundOutlined, PieChartOutlined,
} from '@ant-design/icons-vue'
import { widgetApi, dashboardApi } from '../../api/portal.api'

const searchText = ref('')
const filterType = ref('')
const showSavedMsg = ref(false)
const selectedWidgets = ref<string[]>([])

// D&D
const dragIndex = ref(-1)
const dropTarget = ref(-1)

function onDragStart(e: DragEvent, i: number) { dragIndex.value = i; e.dataTransfer!.effectAllowed = 'move' }
function onDragOver(i: number) { dropTarget.value = i }
function onDragLeave() { dropTarget.value = -1 }
function onDrop(_e: DragEvent, i: number) {
  const from = dragIndex.value
  if (from < 0 || from === i) return
  const arr = [...selectedWidgets.value]
  const [item] = arr.splice(from, 1)
  arr.splice(i, 0, item)
  selectedWidgets.value = arr
  dropTarget.value = -1
}
function onDragEnd() { dragIndex.value = -1; dropTarget.value = -1 }

// 위젯 정의 — KPI 기본: 2열x1행, 나머지 기본: 2열x2행
const widgetDefs: Record<string, { name: string; type: string; label: string; icon: Component; iconColor: string; defaultCol: number; defaultRow: number }> = {
  TOTAL_DATASETS:   { name: '총 데이터셋',     type: 'KPI',    label: '전체 데이터셋',  icon: DatabaseOutlined,          iconColor: '#0066CC', defaultCol: 1, defaultRow: 1 },
  TODAY_COLLECTION: { name: '금일 수집건수',    type: 'KPI',    label: '금일 수집',      icon: SyncOutlined,              iconColor: '#28A745', defaultCol: 1, defaultRow: 1 },
  TODAY_LOAD:       { name: '금일 적재건수',    type: 'KPI',    label: '금일 적재',      icon: DownloadOutlined,          iconColor: '#4a8fd9', defaultCol: 1, defaultRow: 1 },
  ACTIVE_USERS:     { name: '활성 사용자',      type: 'KPI',    label: '접속 중',        icon: TeamOutlined,              iconColor: '#9b59b6', defaultCol: 1, defaultRow: 1 },
  STORAGE_USAGE:    { name: '저장 용량',        type: 'KPI',    label: '사용률',         icon: HddOutlined,               iconColor: '#e67e22', defaultCol: 1, defaultRow: 1 },
  QUALITY_SCORE:    { name: '품질 점수',        type: 'KPI',    label: '전체 품질',      icon: SafetyCertificateOutlined,  iconColor: '#28A745', defaultCol: 1, defaultRow: 1 },
  COLLECTION_CHART: { name: '수집/적재 현황',   type: 'CHART',  label: '',               icon: BarChartOutlined,          iconColor: '#1677ff', defaultCol: 2, defaultRow: 2 },
  CATEGORY_CHART:   { name: '분류별 현황',      type: 'CHART',  label: '',               icon: PieChartOutlined,          iconColor: '#722ed1', defaultCol: 2, defaultRow: 2 },
  RECENT_DATA:      { name: '최근 등록 데이터', type: 'TABLE',  label: '',               icon: DatabaseOutlined,          iconColor: '#fa8c16', defaultCol: 2, defaultRow: 2 },
  NOTICES:          { name: '공지사항',          type: 'TABLE',  label: '',               icon: FundOutlined,              iconColor: '#f5222d', defaultCol: 2, defaultRow: 2 },
  AI_SEARCH:        { name: 'AI 검색',          type: 'SEARCH', label: '',               icon: SearchOutlined,            iconColor: '#13c2c2', defaultCol: 4, defaultRow: 1 },
  DOWNLOAD_RANK:    { name: '다운로드 순위',     type: 'CHART',  label: '',               icon: BarChartOutlined,          iconColor: '#fa8c16', defaultCol: 2, defaultRow: 2 },
}

// 위젯별 크기 (colSpan, rowSpan) — 사용자가 조절 가능
const widgetSizes = ref<Record<string, { col: number; row: number }>>({})

function getColSpan(code: string) { return widgetSizes.value[code]?.col ?? widgetDefs[code]?.defaultCol ?? 2 }
function getRowSpan(code: string) { return widgetSizes.value[code]?.row ?? widgetDefs[code]?.defaultRow ?? 1 }

function setColSpan(code: string, v: number) {
  if (!widgetSizes.value[code]) widgetSizes.value[code] = { col: getColSpan(code), row: getRowSpan(code) }
  widgetSizes.value[code].col = Math.max(1, Math.min(4, v))
}
function setRowSpan(code: string, v: number) {
  if (!widgetSizes.value[code]) widgetSizes.value[code] = { col: getColSpan(code), row: getRowSpan(code) }
  widgetSizes.value[code].row = Math.max(1, Math.min(4, v))
}

const typeColor: Record<string, string> = { KPI: '#0066CC', CHART: '#28A745', TABLE: '#FFC107', SEARCH: '#17a2b8' }

const allWidgetList = computed(() => {
  return Object.entries(widgetDefs).map(([code, def]) => ({ code, ...def }))
})

const availableWidgets = computed(() => {
  let list = allWidgetList.value.filter(w => !selectedWidgets.value.includes(w.code))
  if (filterType.value) list = list.filter(w => w.type === filterType.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter(w => w.name.toLowerCase().includes(q))
  }
  return list
})

function getWidgetName(code: string) { return widgetDefs[code]?.name || code }
function getWidgetType(code: string) { return widgetDefs[code]?.type || '' }
function getWidgetLabel(code: string) { return widgetDefs[code]?.label || '' }
function getWidgetColor(code: string) { return widgetDefs[code]?.iconColor || '#666' }
function getWidgetIconComp(code: string) { return widgetDefs[code]?.icon || DatabaseOutlined }
// KPI 실제 값
const kpiValues = ref<Record<string, string>>({})

async function loadDashboardData() {
  try {
    const res = await dashboardApi.summary()
    const s = res.data?.data
    if (s) {
      kpiValues.value = {
        TOTAL_DATASETS: String(s.total_datasets ?? '1,247'),
        TODAY_COLLECTION: String(s.today_collection ?? '328'),
        TODAY_LOAD: String(s.today_load ?? '312'),
        ACTIVE_USERS: String(s.active_users ?? '156'),
        STORAGE_USAGE: s.storage_used_gb ? Math.round(s.storage_used_gb / (s.storage_total_gb || 5000) * 100) + '%' : '62%',
        QUALITY_SCORE: (s.quality_score ?? '92.4') + '점',
      }
    }
  } catch {
    kpiValues.value = {
      TOTAL_DATASETS: '1,247', TODAY_COLLECTION: '328', TODAY_LOAD: '312',
      ACTIVE_USERS: '156', STORAGE_USAGE: '62%', QUALITY_SCORE: '92.4점',
    }
  }
}

function getKpiValue(code: string) { return kpiValues.value[code] || '-' }

// 차트 미리보기 SVG
const chartSvgs: Record<string, string> = {
  COLLECTION_CHART: '<svg viewBox="0 0 200 60"><rect x="5" y="15" width="22" height="40" fill="#4a8fd9" rx="2"/><rect x="30" y="20" width="22" height="35" fill="#28A745" rx="2"/><rect x="55" y="8" width="22" height="47" fill="#4a8fd9" rx="2"/><rect x="80" y="12" width="22" height="43" fill="#28A745" rx="2"/><rect x="105" y="18" width="22" height="37" fill="#4a8fd9" rx="2"/><rect x="130" y="22" width="22" height="33" fill="#28A745" rx="2"/><rect x="155" y="25" width="22" height="30" fill="#4a8fd9" rx="2"/></svg>',
  CATEGORY_CHART: '<svg viewBox="0 0 140 60"><circle cx="70" cy="30" r="25" fill="none" stroke="#e0e0e0" stroke-width="8"/><circle cx="70" cy="30" r="25" fill="none" stroke="#0066CC" stroke-width="8" stroke-dasharray="57 100" stroke-dashoffset="0" transform="rotate(-90 70 30)"/><circle cx="70" cy="30" r="25" fill="none" stroke="#28A745" stroke-width="8" stroke-dasharray="36 121" stroke-dashoffset="-57" transform="rotate(-90 70 30)"/><circle cx="70" cy="30" r="25" fill="none" stroke="#FFC107" stroke-width="8" stroke-dasharray="25 132" stroke-dashoffset="-93" transform="rotate(-90 70 30)"/></svg>',
  DOWNLOAD_RANK: '<svg viewBox="0 0 200 60"><rect x="5" y="5" width="180" height="8" fill="#e6f7ff" rx="3"/><rect x="5" y="5" width="140" height="8" fill="#1677ff" rx="3"/><rect x="5" y="18" width="180" height="8" fill="#e6f7ff" rx="3"/><rect x="5" y="18" width="105" height="8" fill="#40a9ff" rx="3"/><rect x="5" y="31" width="180" height="8" fill="#e6f7ff" rx="3"/><rect x="5" y="31" width="72" height="8" fill="#69b1ff" rx="3"/><rect x="5" y="44" width="180" height="8" fill="#e6f7ff" rx="3"/><rect x="5" y="44" width="50" height="8" fill="#91caff" rx="3"/></svg>',
}

function getChartSvg(code: string) { return chartSvgs[code] || '<svg viewBox="0 0 100 40"><text x="50" y="25" text-anchor="middle" fill="#ccc" font-size="10">차트</text></svg>' }

// 테이블 미리보기
function getTableRows(code: string) {
  if (code === 'RECENT_DATA') return [
    { text: '댐 수위 관측 데이터', sub: '2026-03-25' },
    { text: '수질 모니터링 센서', sub: '2026-03-24' },
    { text: '상수도 관로 GIS', sub: '2026-03-24' },
  ]
  if (code === 'NOTICES') return [
    { text: '데이터허브 포털 오픈 안내', sub: '2026-03-25' },
    { text: '3월 정기 품질 진단 결과', sub: '2026-03-22' },
    { text: '신규 데이터셋 등록 절차', sub: '2026-03-20' },
  ]
  return []
}

function addWidget(code: string) {
  if (!selectedWidgets.value.includes(code)) selectedWidgets.value.push(code)
}

function removeByCode(code: string) {
  selectedWidgets.value = selectedWidgets.value.filter(c => c !== code)
}

function resetWidgets() {
  selectedWidgets.value = ['TOTAL_DATASETS', 'TODAY_COLLECTION', 'TODAY_LOAD', 'ACTIVE_USERS', 'COLLECTION_CHART', 'CATEGORY_CHART', 'RECENT_DATA', 'NOTICES']
}

async function saveLayout() {
  // localStorage에 위젯 목록 + 크기 저장
  localStorage.setItem('datahub_widget_layout', JSON.stringify(selectedWidgets.value))
  localStorage.setItem('datahub_widget_sizes', JSON.stringify(widgetSizes.value))

  // DB에도 저장
  try {
    const dashRes = await widgetApi.getUserDashboard()
    let items: any[] = dashRes.data?.data?.widget_layout?.items || []
    items = items.filter((it: any) => it.type !== 'widget')

    selectedWidgets.value.forEach(code => {
      items.unshift({
        id: `widget-${code}`,
        type: 'widget',
        code,
        colSpan: getColSpan(code),
        rowSpan: getRowSpan(code),
      })
    })

    await widgetApi.saveUserDashboard({ widget_layout: { items } })
  } catch (e) {
    console.warn('대시보드 레이아웃 DB 저장 실패:', e)
  }

  showSavedMsg.value = true
  setTimeout(() => { showSavedMsg.value = false }, 4000)
}

onMounted(async () => {
  await loadDashboardData()

  // 저장된 레이아웃 복원
  const saved = localStorage.getItem('datahub_widget_layout')
  if (saved) {
    try { selectedWidgets.value = JSON.parse(saved) } catch { /* ignore */ }
  } else {
    resetWidgets()
  }

  // 저장된 위젯 크기 복원
  const savedSizes = localStorage.getItem('datahub_widget_sizes')
  if (savedSizes) {
    try { widgetSizes.value = JSON.parse(savedSizes) } catch { /* ignore */ }
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.widget-page { display: flex; flex-direction: column; gap: $spacing-lg; }

.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}

.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: 4px; }
  p { font-size: $font-size-sm; color: $text-muted; }
}

.saved-msg {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #f6ffed; border: 1px solid #b7eb8f; border-radius: $radius-md;
  color: #389e0d; font-size: $font-size-sm;
  .close-msg { background: none; border: none; color: #389e0d; cursor: pointer; margin-left: auto; }
}

// ===== 캔버스 =====
.canvas-section { background: $white; border: 2px solid $primary; border-radius: $radius-lg; overflow: hidden; }
.canvas-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: linear-gradient(135deg, #0055aa, #0077cc); color: #fff;
  .canvas-title { font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .canvas-count { font-weight: 400; opacity: 0.8; font-size: $font-size-xs; }
  .canvas-actions { display: flex; gap: 6px; }
}
.canvas-area {
  padding: $spacing-md; min-height: 140px;
  &.empty { display: flex; align-items: center; justify-content: center; background: #f8fafd; }
}
.canvas-placeholder {
  text-align: center; color: $text-muted; padding: 20px;
  .placeholder-icon { font-size: 36px; opacity: 0.15; display: block; margin-bottom: 8px; }
  p { font-size: $font-size-sm; }
}
.canvas-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(80px, auto); gap: $spacing-sm;
}
.canvas-card {
  border: 1px solid $border-color; border-radius: $radius-md; overflow: hidden; background: $white;
  box-shadow: $shadow-sm; cursor: grab; transition: all 0.15s;
  // grid-column / grid-row are set inline via :style
  &:active { cursor: grabbing; }
}
.canvas-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 10px; background: #f5f7fa; border-bottom: 1px solid $bg-light;
  .canvas-card-name { font-size: 11px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; display: flex; align-items: center; gap: 4px; }
  .drag-icon { font-size: 12px; color: $text-muted; }
}
.size-controls {
  display: flex; align-items: center; gap: 4px; flex-shrink: 0;
  .size-label { font-size: 10px; color: $primary; font-weight: 700; background: #e8f0fe; padding: 1px 5px; border-radius: 3px; }
  .size-select { width: 42px; padding: 1px 2px; border: 1px solid $border-color; border-radius: 3px; font-size: 10px; background: $white; cursor: pointer;
    &:hover { border-color: $primary; }
  }
  .btn-remove { background: none; border: none; font-size: 11px; cursor: pointer; color: $text-muted; padding: 2px 4px; border-radius: 3px;
    &:hover { color: $error; background: #fff1f0; }
  }
}
.canvas-card-body { padding: 10px; }

// KPI 미리보기
.preview-kpi {
  display: flex; align-items: center; gap: 10px;
  .preview-kpi-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; color: $white; }
  .preview-kpi-value { font-size: 18px; font-weight: 700; color: $text-primary; line-height: 1.1; display: block; }
  .preview-kpi-label { font-size: 10px; color: $text-muted; display: block; }
}

// 차트 미리보기
.preview-chart {
  display: flex; align-items: center; justify-content: center; min-height: 50px;
  :deep(svg) { width: 100%; height: 50px; }
}

// 테이블 미리보기
.preview-table { display: flex; flex-direction: column; gap: 2px; }
.preview-table-row {
  display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #f5f5f5;
  &:last-child { border-bottom: none; }
  .row-text { font-size: 11px; color: $text-primary; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .row-sub { font-size: 10px; color: $text-muted; flex-shrink: 0; margin-left: 8px; }
}

// 검색 미리보기
.preview-search {
  padding: 8px 12px; background: $bg-light; border-radius: $radius-sm; color: $text-muted; font-size: 12px;
  display: flex; align-items: center; gap: 6px;
}

// ===== 위젯 라이브러리 =====
.library-section { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; overflow: hidden; }
.lib-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: #4a6a8a; color: #fff;
  .lib-title { font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .lib-count { font-weight: 400; opacity: 0.8; }
}
.lib-filter {
  display: flex; gap: 8px;
  select, input { padding: 4px 8px; border: 1px solid rgba(255,255,255,0.3); border-radius: $radius-sm; font-size: $font-size-xs; background: rgba(255,255,255,0.15); color: #fff;
    &::placeholder { color: rgba(255,255,255,0.6); }
    option { color: #333; background: #fff; }
  }
  input { width: 160px; }
}
.lib-grid {
  padding: $spacing-md; display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: $spacing-md;
}
.widget-lib-card {
  background: $white; border: 1.5px solid #e8e8e8; border-radius: 10px; padding: 12px; cursor: pointer;
  transition: all 0.2s; user-select: none;
  &:hover { border-color: $primary; box-shadow: 0 4px 12px rgba(0,102,204,0.1);
    .add-hint { opacity: 1; }
  }
}
.lib-card-top {
  display: flex; align-items: center; gap: 10px;
  .lib-card-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; color: $white; }
  .lib-card-info { flex: 1; }
  .lib-card-name { font-size: 13px; font-weight: 600; display: block; }
  .lib-card-type { font-size: 10px; padding: 1px 6px; border-radius: 3px; font-weight: 600; display: inline-block; margin-top: 2px; }
}
.add-hint { font-size: 10px; color: $primary; text-align: center; margin-top: 8px; opacity: 0; transition: opacity 0.2s; }
.lib-empty { grid-column: 1 / -1; text-align: center; padding: 40px; color: $text-muted; font-size: $font-size-sm; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .canvas-grid { grid-template-columns: repeat(2, 1fr); }
  .lib-header { flex-direction: column; gap: 8px; align-items: flex-start; }
}
</style>
