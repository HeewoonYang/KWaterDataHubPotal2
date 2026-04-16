<template>
  <div class="gallery-page">
    <!-- 브레드크럼 -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">&gt;</span>
      <span class="current">시각화 갤러리 설정</span>
    </nav>

    <div class="page-header">
      <h2>시각화 갤러리 설정</h2>
      <p>갤러리 콘텐츠에서 차트를 선택하여 대시보드에 표시할 차트를 배치하세요.</p>
    </div>

    <!-- 저장 성공 메시지 -->
    <div v-if="showSavedMsg" class="saved-msg">
      <CheckCircleOutlined /> 갤러리 배치가 저장되었습니다. 대시보드에서 확인하세요.
      <button class="close-msg" @click="showSavedMsg = false"><CloseOutlined /></button>
    </div>

    <!-- 상단: 내 대시보드 캔버스 (대시보드 미리보기) -->
    <section class="canvas-section">
      <div class="canvas-header">
        <div class="canvas-title">
          <AppstoreOutlined /> 대시보드 갤러리 배치
          <span class="canvas-count">{{ canvasCharts.length }}개 배치됨</span>
        </div>
        <div class="canvas-actions">
          <button class="btn btn-sm btn-primary" @click="saveGalleryLayout">
            <SaveOutlined /> 저장
          </button>
          <button v-if="canvasCharts.length > 0" class="btn btn-sm btn-outline" @click="clearCanvas">
            <DeleteOutlined /> 전체 제거
          </button>
        </div>
      </div>
      <div class="canvas-area" :class="{ empty: canvasCharts.length === 0 }">
        <div v-if="canvasCharts.length === 0" class="canvas-placeholder">
          <BarChartOutlined class="placeholder-icon" />
          <p>아래 차트 라이브러리에서 차트를 더블클릭하여 대시보드에 추가하세요.</p>
        </div>
        <div v-else class="canvas-grid">
          <div v-for="(chart, i) in canvasCharts" :key="chart.id + '-' + i" class="canvas-card">
            <div class="canvas-card-header">
              <span class="canvas-card-name">{{ chart.chart_name || chart.name }}</span>
              <button class="btn-remove" @click="removeFromCanvas(i)" title="제거"><CloseOutlined /></button>
            </div>
            <div class="canvas-chart-preview" :class="{ 'map-preview': chart.chart_type === 'MAP' }">
              <template v-if="chart.chart_type === 'MAP'">
                <div class="map-preview-placeholder"><EnvironmentOutlined class="map-icon" /><span>GIS 지도</span></div>
              </template>
              <template v-else>
                <div v-html="chart.previewSvg || chart.svg || ''"></div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 하단: 차트 라이브러리 (갤러리 콘텐츠에서 가져온 차트 목록) -->
    <section class="library-section">
      <div class="lib-header">
        <div class="lib-title">
          <DatabaseOutlined /> 차트 라이브러리
          <span class="lib-count">— {{ availableCharts.length }}개 사용 가능</span>
        </div>
        <div class="lib-filter">
          <select v-model="filterType">
            <option value="">전체 유형</option>
            <option value="bar">막대</option>
            <option value="line">선</option>
            <option value="pie">원</option>
            <option value="scatter">산점도</option>
            <option value="area">영역</option>
            <option value="MAP">GIS 지도</option>
          </select>
          <input v-model="searchText" placeholder="차트 검색..." />
        </div>
      </div>
      <div class="lib-grid">
        <div v-for="chart in availableCharts" :key="chart.id" class="chart-lib-card" @dblclick="addToCanvas(chart)">
          <div class="lib-card-top">
            <EnvironmentOutlined v-if="chart.chart_type === 'MAP'" class="chart-icon-antd" :style="{ color: '#28A745' }" />
            <BarChartOutlined v-else class="chart-icon-antd" :style="{ color: typeColor[chart.chart_type] || '#1677ff' }" />
            <span class="chart-name">{{ chart.chart_name }}</span>
          </div>
          <div class="chart-preview" :class="{ 'map-preview': chart.chart_type === 'MAP' }">
            <template v-if="chart.chart_type === 'MAP'">
              <div class="map-preview-placeholder">
                <EnvironmentOutlined class="map-icon" />
                <span>GIS 지도</span>
              </div>
            </template>
            <template v-else>
              <div v-html="buildPreviewSvg(chart)"></div>
            </template>
          </div>
          <div class="chart-meta-row">
            <span class="chart-type-tag" :style="{ background: (typeColor[chart.chart_type] || '#666') + '15', color: typeColor[chart.chart_type] || '#666' }">
              {{ typeLabel[chart.chart_type] || chart.chart_type }}
            </span>
            <span v-if="chart.chart_config?.dataset_name" class="chart-ds">{{ chart.chart_config.dataset_name }}</span>
            <span class="chart-owner">{{ chart.owner_name || '나' }}</span>
          </div>
          <div class="add-hint">더블클릭하여 대시보드에 추가</div>
        </div>
        <div v-if="availableCharts.length === 0" class="lib-empty">
          <p v-if="allCharts.length === 0">저장된 차트가 없습니다. <router-link to="/portal/gallery-content">갤러리 콘텐츠 관리</router-link>에서 차트를 생성하세요.</p>
          <p v-else>조건에 맞는 차트가 없거나 모두 배치되었습니다.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  AppstoreOutlined, BarChartOutlined, DatabaseOutlined,
  DeleteOutlined, CloseOutlined, SaveOutlined, CheckCircleOutlined, EnvironmentOutlined,
} from '@ant-design/icons-vue'
import { visualizationApi, widgetApi } from '../../api/portal.api'

const filterType = ref('')
const searchText = ref('')
const canvasCharts = ref<any[]>([])
const allCharts = ref<any[]>([])
const showSavedMsg = ref(false)

const typeLabel: Record<string, string> = { bar: '막대', line: '선', pie: '원', scatter: '산점도', area: '영역', MAP: 'GIS 지도' }
const typeColor: Record<string, string> = { bar: '#fa8c16', line: '#1677ff', pie: '#722ed1', scatter: '#eb2f96', area: '#13c2c2', MAP: '#28A745' }
const previewColors = ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8']

// ── API에서 갤러리 콘텐츠 차트 목록 로딩 ──
async function fetchCharts() {
  try {
    const res = await visualizationApi.listCharts({ page: 1, page_size: 100 })
    if (res.data?.items && res.data.items.length > 0) {
      allCharts.value = res.data.items
    }
  } catch {
    // fallback: mock
    allCharts.value = [
      { id: 'mock1', chart_name: '월별 수집량 추이', chart_type: 'bar', owner_name: '관리자', chart_config: { dataset_name: '댐 수위 관측 데이터', series: [{ name: '수위', data: [195, 138, 162, 115, 148] }] } },
      { id: 'mock2', chart_name: '수질 항목별 변화', chart_type: 'line', owner_name: '홍길동', chart_config: { dataset_name: '수질 모니터링', series: [{ name: 'pH', data: [7.2, 7.4, 7.1, 7.3, 7.5] }] } },
      { id: 'mock3', chart_name: '데이터 유형 분포', chart_type: 'pie', owner_name: '관리자', chart_config: { dataset_name: '카탈로그 통계', series: [{ name: '건수', data: [423, 287, 215, 178, 89] }] } },
    ]
  }
}

// 캔버스에 없는 차트만 라이브러리에 표시
const availableCharts = computed(() => {
  let charts = allCharts.value
  if (filterType.value) charts = charts.filter(c => c.chart_type === filterType.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    charts = charts.filter(c =>
      (c.chart_name || '').toLowerCase().includes(q) ||
      (c.chart_config?.dataset_name || '').toLowerCase().includes(q)
    )
  }
  const canvasIds = new Set(canvasCharts.value.map(c => c.id))
  return charts.filter(c => !canvasIds.has(c.id))
})

function addToCanvas(chart: any) {
  if (!canvasCharts.value.some(c => c.id === chart.id)) {
    canvasCharts.value.push({
      ...chart,
      previewSvg: buildPreviewSvg(chart),
    })
  }
}

function removeFromCanvas(index: number) {
  canvasCharts.value.splice(index, 1)
}

function clearCanvas() {
  canvasCharts.value = []
}

// 저장 버튼: localStorage + DB에 모두 저장하고 대시보드 레이아웃에도 반영
async function saveGalleryLayout() {
  // 1. localStorage에 갤러리 캔버스 저장
  const saveData = canvasCharts.value.map(c => ({
    id: c.id,
    name: c.chart_name || c.name,
    svg: c.previewSvg || c.svg || buildPreviewSvg(c),
    chart_type: c.chart_type,
    chart_config: c.chart_config,
  }))
  localStorage.setItem('datahub_gallery_canvas', JSON.stringify(saveData))

  // 2. 대시보드 레이아웃에 갤러리 차트를 반영하여 DB 저장
  try {
    // 기존 대시보드 레이아웃 로드
    const dashRes = await widgetApi.getUserDashboard()
    let items: any[] = dashRes.data?.data?.widget_layout?.items || []

    // 기존 갤러리 아이템 제거
    items = items.filter((it: any) => it.type !== 'gallery')

    // 새 갤러리 차트를 대시보드 레이아웃에 추가
    canvasCharts.value.forEach(c => {
      const isMap = c.chart_type === 'MAP'
      items.push({
        id: `gallery-${c.id}`,
        type: 'gallery',
        chartId: String(c.id),
        colSpan: isMap ? 2 : 2,
        rowSpan: isMap ? 2 : 1,
      })
    })

    await widgetApi.saveUserDashboard({ widget_layout: { items } })
  } catch (e) {
    console.warn('대시보드 레이아웃 DB 저장 실패:', e)
  }

  showSavedMsg.value = true
  setTimeout(() => { showSavedMsg.value = false }, 4000)
}

// 캔버스 변경 시 localStorage에 저장 → 대시보드에서 읽어감
watch(canvasCharts, (val) => {
  const saveData = val.map(c => ({
    id: c.id,
    name: c.chart_name || c.name,
    svg: c.previewSvg || c.svg || buildPreviewSvg(c),
    chart_type: c.chart_type,
    chart_config: c.chart_config,
  }))
  localStorage.setItem('datahub_gallery_canvas', JSON.stringify(saveData))
}, { deep: true })

// ── SVG 빌더 (갤러리 콘텐츠와 동일) ──
function linePoints(data: number[], w: number, h: number): string {
  if (!data || data.length === 0) return ''
  const maxVal = Math.max(...data) || 1
  return data.map((v: number, i: number) => `${i / (data.length - 1 || 1) * w},${h - (v / maxVal * (h - 10))}`).join(' ')
}

function buildPreviewSvg(c: any): string {
  const cfg = c.chart_config || {}
  const series: any[] = cfg.series || []
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
  // scatter / fallback
  const data: number[] = series[0]?.data || []
  const max = Math.max(...data, 1)
  let dots = ''
  data.forEach((v: number, i: number) => {
    dots += `<circle cx="${i / (data.length - 1 || 1) * 270}" cy="${100 - (v / max * 90)}" r="4" fill="${colors[0]}" fill-opacity="0.6"/>`
  })
  return `<svg viewBox="0 0 280 120" class="preview-svg"><g transform="translate(5,10)">${dots}</g></svg>`
}

// 초기 로드
onMounted(async () => {
  await fetchCharts()
  // 기존 캔버스 배치 복원
  try {
    const saved = localStorage.getItem('datahub_gallery_canvas')
    if (saved) {
      const savedItems = JSON.parse(saved)
      // API 차트에서 매칭하여 복원
      canvasCharts.value = savedItems.map((s: any) => {
        const match = allCharts.value.find(c => c.id === s.id)
        if (match) return { ...match, previewSvg: buildPreviewSvg(match) }
        return { id: s.id, chart_name: s.name, svg: s.svg, previewSvg: s.svg, chart_type: s.chart_type, chart_config: s.chart_config }
      }).filter(Boolean)
    }
  } catch { /* ignore */ }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.gallery-page { display: flex; flex-direction: column; gap: $spacing-lg; }

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

// ===== 캔버스 (상단) =====
.canvas-section {
  background: $white; border: 2px solid $primary; border-radius: $radius-lg; overflow: hidden;
}
.canvas-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: linear-gradient(135deg, #0055aa, #0077cc); color: #fff;
  .canvas-title { font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .canvas-count { font-weight: 400; opacity: 0.8; font-size: $font-size-xs; }
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
  display: grid; grid-template-columns: repeat(3, 1fr); gap: $spacing-md;
}
.canvas-card {
  border: 1px solid $border-color; border-radius: $radius-md; overflow: hidden; background: $white;
  box-shadow: $shadow-sm;
}
.canvas-card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid $bg-light;
  .canvas-card-name { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .btn-remove { background: none; border: none; font-size: 12px; cursor: pointer; color: $text-muted; padding: 2px 4px; border-radius: 3px;
    &:hover { color: $error; background: #fff1f0; }
  }
}
.canvas-chart-preview {
  padding: 10px; display: flex; align-items: center; justify-content: center; min-height: 80px;
  :deep(svg) { width: 100%; height: 70px; }
}

// ===== 차트 라이브러리 (하단) =====
.library-section {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg; overflow: hidden;
}
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
  padding: $spacing-md; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: $spacing-md;
  max-height: 500px; overflow-y: auto;
}
.chart-lib-card {
  background: $white; border: 1.5px solid #e8e8e8; border-radius: 10px; padding: 12px; cursor: pointer;
  transition: all 0.2s; user-select: none; position: relative;
  &:hover { border-color: $primary; box-shadow: 0 4px 12px rgba(0,102,204,0.1);
    .add-hint { opacity: 1; }
  }
}
.lib-card-top {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
  .chart-name { font-size: 12px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .chart-icon-antd { font-size: 16px; flex-shrink: 0; }
}
.chart-preview {
  background: #fafafa; border-radius: 6px; padding: 6px; margin-bottom: 6px; min-height: 50px;
  display: flex; align-items: center; justify-content: center;
  :deep(svg) { width: 100%; height: 40px; }
}
.chart-meta-row {
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  .chart-type-tag { font-size: 10px; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
  .chart-ds { font-size: 10px; color: $text-muted; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100px; }
  .chart-owner { font-size: 10px; color: #aaa; margin-left: auto; }
}
.add-hint {
  font-size: 10px; color: $primary; text-align: center; margin-top: 6px;
  opacity: 0; transition: opacity 0.2s;
}
.map-preview-placeholder {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px; color: #28A745; padding: 8px;
  .map-icon { font-size: 24px; }
  span { font-size: 10px; font-weight: 600; }
}
.lib-empty {
  grid-column: 1 / -1; text-align: center; padding: 40px; color: $text-muted; font-size: $font-size-sm;
  a { color: $primary; }
}

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .canvas-grid { grid-template-columns: repeat(2, 1fr); }
  .lib-grid { grid-template-columns: repeat(2, 1fr); }
  .lib-header { flex-direction: column; gap: 8px; align-items: flex-start; }
}
</style>
