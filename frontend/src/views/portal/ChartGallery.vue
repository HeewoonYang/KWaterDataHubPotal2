<template>
  <div class="gallery-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">차트 갤러리</span>
    </nav>

    <div class="page-header">
      <h2>차트 갤러리</h2>
      <p>저장된 시각화 차트를 확인하고 공유하세요.</p>
    </div>

    <!-- 알림 메시지 -->
    <div v-if="showSavedMsg" class="saved-msg">
      <CheckCircleOutlined /> 차트가 저장되었습니다.
      <button class="close-msg" @click="showSavedMsg = false"><CloseOutlined /></button>
    </div>

    <div class="gallery-toolbar">
      <div class="toolbar-left">
        <select v-model="filterType" @change="fetchCharts">
          <option value="">전체 유형</option>
          <option value="bar">막대</option>
          <option value="line">선</option>
          <option value="pie">원</option>
          <option value="scatter">산점도</option>
          <option value="area">영역</option>
        </select>
        <select v-model="sortBy" @change="fetchCharts">
          <option value="latest">최신순</option>
          <option value="popular">인기순</option>
          <option value="name">이름순</option>
        </select>
      </div>
      <div class="toolbar-right">
        <span class="gallery-count">총 <strong>{{ charts.length }}</strong>개</span>
        <router-link to="/portal/visualization" class="btn btn-primary btn-sm">
          <PlusOutlined /> 새 차트 만들기
        </router-link>
      </div>
    </div>

    <div v-if="charts.length === 0" class="empty-state">
      <BarChartOutlined class="empty-icon" />
      <p>저장된 차트가 없습니다.</p>
      <router-link to="/portal/visualization" class="btn btn-primary">D&D 시각화에서 차트 만들기</router-link>
    </div>

    <div v-else class="gallery-grid">
      <div v-for="c in charts" :key="c.id" class="gallery-card" @click="openDetail(c)">
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

    <!-- 상세 모달 -->
    <div v-if="detailChart" class="modal-overlay" @click.self="detailChart = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ detailChart.chart_name }}</h3>
          <button @click="detailChart = null"><CloseOutlined /></button>
        </div>
        <div class="modal-body">
          <div class="detail-chart-area">
            <div v-if="detailChart.chart_config?.series" class="detail-svg-wrap" v-html="buildDetailSvg(detailChart)"></div>
            <div v-else class="detail-fallback">
              <component :is="iconMap[detailChart.chart_type] || BarChartOutlined" class="detail-fallback-icon" />
            </div>
          </div>
          <div class="detail-info">
            <div class="info-row"><span class="info-label">데이터소스</span><span>{{ detailChart.chart_config?.dataset_name || '-' }}</span></div>
            <div class="info-row"><span class="info-label">차트 유형</span><span>{{ typeLabels[detailChart.chart_type] || detailChart.chart_type }}</span></div>
            <div class="info-row"><span class="info-label">X축</span><span>{{ detailChart.chart_config?.x_axis_kr || detailChart.chart_config?.x_axis || '-' }}</span></div>
            <div class="info-row"><span class="info-label">Y축</span><span>{{ (detailChart.chart_config?.y_axes_kr || detailChart.chart_config?.y_axes || []).join(', ') || '-' }}</span></div>
            <div class="info-row"><span class="info-label">작성자</span><span>{{ detailChart.owner_name || '나' }}</span></div>
            <div class="info-row"><span class="info-label">생성일</span><span>{{ formatDate(detailChart.created_at) }}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BarChartOutlined, LineChartOutlined, PieChartOutlined, DotChartOutlined, AreaChartOutlined,
  UserOutlined, ClockCircleOutlined, EyeOutlined, DeleteOutlined, EditOutlined, CopyOutlined,
  PlusOutlined, DatabaseOutlined, CheckCircleOutlined, CloseOutlined,
} from '@ant-design/icons-vue'
import { visualizationApi } from '../../api/portal.api'
import type { Component } from 'vue'

const route = useRoute()
const router = useRouter()

const filterType = ref('')
const sortBy = ref('latest')
const showSavedMsg = ref(false)
const detailChart = ref<any>(null)

const iconMap: Record<string, Component> = {
  bar: BarChartOutlined, line: LineChartOutlined, pie: PieChartOutlined,
  scatter: DotChartOutlined, area: AreaChartOutlined,
}
const typeLabels: Record<string, string> = {
  bar: '막대', line: '선', pie: '원', scatter: '산점도', area: '영역',
}
const typeColors: Record<string, string> = {
  bar: '#e3f2fd', line: '#e8f5e9', pie: '#fff3e0', scatter: '#f3e5f5', area: '#fce4ec',
}
const previewColors = ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8']

// ─── 차트 목록 ───
const defaultCharts = [
  { id: 'mock1', chart_name: '월별 수집량 추이', chart_type: 'bar', owner_name: '관리자', created_at: '2026-03-25', view_count: 42, chart_config: { dataset_name: '댐 수위 관측 데이터', x_axis_kr: '댐명', y_axes_kr: ['수위(m)'], labels: ['소양강댐', '충주댐', '안동댐', '임하댐', '합천댐'], series: [{ name: '수위(m)', data: [195.2, 138.4, 162.8, 115.3, 148.7] }] } },
  { id: 'mock2', chart_name: '수질 항목별 변화', chart_type: 'line', owner_name: '홍길동', created_at: '2026-03-24', view_count: 28, chart_config: { dataset_name: '수질 모니터링 센서', x_axis_kr: '측정일', y_axes_kr: ['pH', 'DO(mg/L)'], labels: ['3/20', '3/21', '3/22', '3/23', '3/24', '3/25'], series: [{ name: 'pH', data: [7.2, 7.4, 7.1, 7.3, 7.5, 7.2] }, { name: 'DO', data: [8.1, 8.3, 7.9, 8.5, 8.2, 8.4] }] } },
  { id: 'mock3', chart_name: '데이터 유형 분포', chart_type: 'pie', owner_name: '관리자', created_at: '2026-03-23', view_count: 55, chart_config: { dataset_name: '카탈로그 통계', x_axis_kr: '유형', y_axes_kr: ['건수'], labels: ['DB', 'IoT', 'API', 'CSV', 'FILE'], series: [{ name: '건수', data: [423, 287, 215, 178, 89] }] } },
]

const charts = ref<any[]>(defaultCharts)

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

function editChart(c: any) {
  router.push({ path: '/portal/visualization', query: { edit: c.id } })
}

function openDetail(c: any) {
  detailChart.value = c
}

function formatDate(dt: string) {
  if (!dt) return '-'
  return dt.substring(0, 10)
}

// ─── SVG 빌더 ───
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
      const txt = l.length > 5 ? l.slice(0, 5) + '…' : l
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
      labelTexts += `<text x="${x}" y="${H + 18}" text-anchor="middle" fill="#666" font-size="11">${l.length > 5 ? l.slice(0, 5) + '…' : l}</text>`
    })
    return `<svg viewBox="0 0 600 300" class="detail-svg"><g transform="translate(40,20)">${lines}${labelTexts}</g></svg>`
  }
  // pie / area / scatter - reuse preview logic at larger scale
  return buildPreviewSvg(c).replace('280', '600').replace('120', '300')
}

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

.gallery-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}

.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  p { font-size: $font-size-sm; color: $text-muted; }
}

.saved-msg {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #f6ffed; border: 1px solid #b7eb8f; border-radius: $radius-md;
  color: #389e0d; font-size: $font-size-sm;
  .close-msg { background: none; border: none; color: #389e0d; cursor: pointer; margin-left: auto; }
}

.gallery-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  .toolbar-left { display: flex; gap: $spacing-sm;
    select { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; }
  }
  .toolbar-right { display: flex; align-items: center; gap: $spacing-md; }
  .gallery-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
}

.btn-sm { padding: 6px 12px; font-size: $font-size-xs; }

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
  border-top: 1px solid $bg-light;
  button {
    background: none; border: none; color: $text-muted; font-size: 14px; padding: 4px 6px;
    border-radius: $radius-sm; cursor: pointer;
    &:hover { color: $primary; background: $bg-light; }
  }
}

// ─── 상세 모달 ───
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.45); z-index: 1000;
  display: flex; align-items: center; justify-content: center;
}
.modal-content {
  background: $white; border-radius: $radius-lg; width: 800px; max-height: 90vh;
  overflow: auto; box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-bottom: 1px solid $border-color;
  h3 { font-size: $font-size-lg; font-weight: 700; }
  button { background: none; border: none; cursor: pointer; font-size: 16px; color: $text-muted; &:hover { color: $text-primary; } }
}
.modal-body { padding: 24px; }

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

.detail-info {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  .info-row { display: flex; gap: 8px; font-size: $font-size-sm;
    .info-label { color: $text-muted; min-width: 70px; }
  }
}

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .gallery-grid { grid-template-columns: repeat(2, 1fr); }
  .modal-content { width: 95%; }
}
</style>
