<template>
  <div class="viz-page">
    <!-- 브레드크럼 -->
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">&gt;</span>
      <router-link to="/portal/gallery-content">갤러리 콘텐츠 관리</router-link>
      <span class="separator">&gt;</span>
      <span class="current">D&amp;D 시각화</span>
    </nav>

    <div class="page-header">
      <h2>데이터 시각화</h2>
      <p>데이터 소스를 선택하고 컬럼을 지정하면 최적의 차트가 자동 생성됩니다.</p>
    </div>

    <!-- 도구 영역 -->
    <div class="viz-toolbar">
      <div class="chart-types">
        <button v-for="ct in chartTypes" :key="ct.value" class="chart-type-btn"
          :class="{ active: selectedChartType === ct.value }" @click="changeChartType(ct.value)">
          <component :is="ct.icon" />
          <span>{{ ct.label }}</span>
        </button>
      </div>
      <div class="toolbar-actions">
        <span v-if="editingChartId" class="edit-mode-badge">편집 모드</span>
        <button class="btn btn-primary" @click="saveChart" :disabled="!hasChart">
          <SaveOutlined /> {{ editingChartId ? '수정 저장' : '저장' }}
        </button>
        <button class="btn btn-outline" @click="resetChart">
          <ReloadOutlined /> 초기화
        </button>
      </div>
    </div>

    <!-- 시각화 본문 -->
    <div class="viz-body">
      <!-- 좌측: 데이터 소스 + 컬럼 -->
      <aside class="data-panel">
        <div class="panel-header"><DatabaseOutlined /> 데이터 소스</div>
        <div class="panel-content">
          <!-- 데이터 소스 목록 -->
          <div v-if="dataSources.length === 0" class="empty-hint">데이터 소스가 없습니다</div>
          <div v-for="ds in dataSources" :key="ds.id" class="data-source-item"
            :class="{ active: String(selectedDataSourceId) === String(ds.id) }" @click="selectDataSource(ds)">
            <TableOutlined />
            <div class="ds-info">
              <span class="ds-name">{{ ds.dataset_name }}</span>
              <span class="ds-format">{{ ds.data_format || 'TABLE' }}</span>
            </div>
          </div>

          <!-- 컬럼 목록 -->
          <template v-if="columns.length > 0">
            <div class="panel-sub-header">
              <ColumnHeightOutlined /> 컬럼 ({{ columns.length }}개)
            </div>
            <div v-for="col in columns" :key="col.column_name" class="column-item"
              :class="{ selected: isColumnSelected(col), 'axis-x': xAxis?.column_name === col.column_name, 'axis-y': yAxisList.some(y => y.column_name === col.column_name) }"
              @click="toggleColumn(col)">
              <span class="col-type-badge" :class="getTypeClass(col.data_type)">{{ getTypeLabel(col.data_type) }}</span>
              <div class="col-info">
                <span class="col-name-kr">{{ col.column_name_kr || col.column_name }}</span>
                <span class="col-name-en">{{ col.column_name }}</span>
              </div>
              <span v-if="xAxis?.column_name === col.column_name" class="axis-tag x">X</span>
              <span v-else-if="yAxisList.some(y => y.column_name === col.column_name)" class="axis-tag y">Y</span>
            </div>
          </template>
          <div v-else-if="selectedDataSourceId" class="empty-hint">컬럼 정보를 불러오는 중...</div>
        </div>
      </aside>

      <!-- 중앙: 차트 캔버스 -->
      <div class="chart-canvas">
        <!-- 차트 미생성 상태 -->
        <div v-if="!hasChart" class="canvas-placeholder">
          <AreaChartOutlined class="placeholder-icon" />
          <p>데이터 소스를 선택하고 컬럼을 클릭하세요</p>
          <span class="placeholder-hint">숫자형 컬럼은 Y축, 문자/날짜형 컬럼은 X축으로 자동 배치됩니다</span>
        </div>
        <!-- 차트 렌더링 -->
        <div v-else class="chart-render-area">
          <div class="chart-title-bar">
            <input v-model="chartTitle" class="chart-title-input" placeholder="차트 제목을 입력하세요" />
          </div>
          <div class="chart-svg-wrapper">
            <!-- 막대 차트 -->
            <svg v-if="selectedChartType === 'bar'" :viewBox="`0 0 ${svgW} ${svgH}`" class="chart-svg">
              <g :transform="`translate(${margin.left},${margin.top})`">
                <!-- Y축 그리드 -->
                <line v-for="(tick, i) in yTicks" :key="'gy'+i" :x1="0" :x2="innerW" :y1="yScale(tick)" :y2="yScale(tick)" stroke="#e8e8e8" stroke-dasharray="3,3" />
                <!-- Y축 라벨 -->
                <text v-for="(tick, i) in yTicks" :key="'yl'+i" :x="-8" :y="yScale(tick)+4" text-anchor="end" fill="#999" font-size="11">{{ formatTick(tick) }}</text>
                <!-- X축 라벨 -->
                <text v-for="(label, i) in chartLabels" :key="'xl'+i" :x="barGroupX(i) + barGroupWidth/2" :y="innerH + 18" text-anchor="middle" fill="#666" font-size="11">{{ truncLabel(label) }}</text>
                <!-- 바 -->
                <template v-for="(series, si) in chartSeries" :key="'s'+si">
                  <rect v-for="(val, vi) in series.data" :key="'b'+si+vi"
                    :x="barGroupX(vi) + si * (barW + 2)" :y="yScale(val)" :width="barW" :height="innerH - yScale(val)"
                    :fill="colors[si % colors.length]" rx="2" />
                </template>
                <!-- 범례 -->
                <g :transform="`translate(${innerW - chartSeries.length * 90}, -12)`">
                  <g v-for="(series, si) in chartSeries" :key="'lg'+si" :transform="`translate(${si * 90}, 0)`">
                    <rect width="10" height="10" :fill="colors[si]" rx="2" />
                    <text x="14" y="9" fill="#666" font-size="11">{{ series.name }}</text>
                  </g>
                </g>
              </g>
            </svg>

            <!-- 선 차트 -->
            <svg v-else-if="selectedChartType === 'line'" :viewBox="`0 0 ${svgW} ${svgH}`" class="chart-svg">
              <g :transform="`translate(${margin.left},${margin.top})`">
                <line v-for="(tick, i) in yTicks" :key="'gy'+i" :x1="0" :x2="innerW" :y1="yScale(tick)" :y2="yScale(tick)" stroke="#e8e8e8" stroke-dasharray="3,3" />
                <text v-for="(tick, i) in yTicks" :key="'yl'+i" :x="-8" :y="yScale(tick)+4" text-anchor="end" fill="#999" font-size="11">{{ formatTick(tick) }}</text>
                <text v-for="(label, i) in chartLabels" :key="'xl'+i" :x="lineX(i)" :y="innerH + 18" text-anchor="middle" fill="#666" font-size="11">{{ truncLabel(label) }}</text>
                <template v-for="(series, si) in chartSeries" :key="'ls'+si">
                  <polyline :points="linePoints(series.data)" fill="none" :stroke="colors[si]" stroke-width="2.5" stroke-linejoin="round" />
                  <circle v-for="(val, vi) in series.data" :key="'dot'+vi" :cx="lineX(vi)" :cy="yScale(val)" r="3.5" :fill="colors[si]" />
                </template>
                <g :transform="`translate(${innerW - chartSeries.length * 90}, -12)`">
                  <g v-for="(series, si) in chartSeries" :key="'lg'+si" :transform="`translate(${si * 90}, 0)`">
                    <rect width="10" height="10" :fill="colors[si]" rx="2" />
                    <text x="14" y="9" fill="#666" font-size="11">{{ series.name }}</text>
                  </g>
                </g>
              </g>
            </svg>

            <!-- 원(도넛) 차트 -->
            <svg v-else-if="selectedChartType === 'pie'" :viewBox="`0 0 ${svgW} ${svgH}`" class="chart-svg">
              <g :transform="`translate(${svgW/2},${svgH/2})`">
                <path v-for="(slice, i) in pieSlices" :key="'pie'+i" :d="slice.path" :fill="colors[i % colors.length]" stroke="white" stroke-width="2" />
                <text text-anchor="middle" dy="0.35em" fill="#333" font-size="14" font-weight="700">{{ pieTotal }}</text>
              </g>
              <g :transform="`translate(${svgW - 120}, 20)`">
                <g v-for="(slice, i) in pieSlices" :key="'plg'+i" :transform="`translate(0, ${i * 20})`">
                  <rect width="10" height="10" :fill="colors[i % colors.length]" rx="2" />
                  <text x="14" y="9" fill="#666" font-size="11">{{ slice.label }} ({{ slice.pct }}%)</text>
                </g>
              </g>
            </svg>

            <!-- 산점도 -->
            <svg v-else-if="selectedChartType === 'scatter'" :viewBox="`0 0 ${svgW} ${svgH}`" class="chart-svg">
              <g :transform="`translate(${margin.left},${margin.top})`">
                <line v-for="(tick, i) in yTicks" :key="'gy'+i" :x1="0" :x2="innerW" :y1="yScale(tick)" :y2="yScale(tick)" stroke="#e8e8e8" stroke-dasharray="3,3" />
                <text v-for="(tick, i) in yTicks" :key="'yl'+i" :x="-8" :y="yScale(tick)+4" text-anchor="end" fill="#999" font-size="11">{{ formatTick(tick) }}</text>
                <circle v-for="(pt, i) in scatterPoints" :key="'sc'+i" :cx="pt.x" :cy="pt.y" r="5" :fill="colors[0]" fill-opacity="0.6" stroke="white" stroke-width="1" />
              </g>
            </svg>

            <!-- 영역 차트 -->
            <svg v-else-if="selectedChartType === 'area'" :viewBox="`0 0 ${svgW} ${svgH}`" class="chart-svg">
              <defs>
                <linearGradient v-for="(_s, si) in chartSeries" :key="'grad'+si" :id="'areaGrad'+si" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" :stop-color="colors[si]" stop-opacity="0.3" />
                  <stop offset="100%" :stop-color="colors[si]" stop-opacity="0.02" />
                </linearGradient>
              </defs>
              <g :transform="`translate(${margin.left},${margin.top})`">
                <line v-for="(tick, i) in yTicks" :key="'gy'+i" :x1="0" :x2="innerW" :y1="yScale(tick)" :y2="yScale(tick)" stroke="#e8e8e8" stroke-dasharray="3,3" />
                <text v-for="(tick, i) in yTicks" :key="'yl'+i" :x="-8" :y="yScale(tick)+4" text-anchor="end" fill="#999" font-size="11">{{ formatTick(tick) }}</text>
                <text v-for="(label, i) in chartLabels" :key="'xl'+i" :x="lineX(i)" :y="innerH + 18" text-anchor="middle" fill="#666" font-size="11">{{ truncLabel(label) }}</text>
                <template v-for="(series, si) in chartSeries" :key="'as'+si">
                  <polygon :points="areaPoints(series.data)" :fill="`url(#areaGrad${si})`" />
                  <polyline :points="linePoints(series.data)" fill="none" :stroke="colors[si]" stroke-width="2" />
                </template>
                <g :transform="`translate(${innerW - chartSeries.length * 90}, -12)`">
                  <g v-for="(series, si) in chartSeries" :key="'lg'+si" :transform="`translate(${si * 90}, 0)`">
                    <rect width="10" height="10" :fill="colors[si]" rx="2" />
                    <text x="14" y="9" fill="#666" font-size="11">{{ series.name }}</text>
                  </g>
                </g>
              </g>
            </svg>
          </div>
          <!-- 데이터 미리보기 테이블 -->
          <div class="data-preview">
            <div class="preview-header">
              <span><TableOutlined /> 데이터 미리보기 ({{ previewRows.length }}행)</span>
            </div>
            <div class="preview-table-wrap">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th v-if="xAxis">{{ xAxis.column_name_kr || xAxis.column_name }}</th>
                    <th v-for="y in yAxisList" :key="y.column_name">{{ y.column_name_kr || y.column_name }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in previewRows.slice(0, 8)" :key="i">
                    <td v-if="xAxis">{{ row.label }}</td>
                    <td v-for="(val, vi) in row.values" :key="vi">{{ val }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측: 축 설정 -->
      <aside class="config-panel">
        <div class="panel-header"><SettingOutlined /> 차트 설정</div>
        <div class="panel-content">
          <div class="config-group">
            <label>X축 (카테고리)</label>
            <div v-if="xAxis" class="axis-chip x" @click="removeXAxis">
              {{ xAxis.column_name_kr || xAxis.column_name }}
              <CloseOutlined class="chip-close" />
            </div>
            <div v-else class="drop-zone">컬럼 클릭으로 지정</div>
          </div>
          <div class="config-group">
            <label>Y축 (값) <span class="axis-count">({{ yAxisList.length }}개)</span></label>
            <div v-for="y in yAxisList" :key="y.column_name" class="axis-chip y" @click="removeYAxis(y)">
              {{ y.column_name_kr || y.column_name }}
              <CloseOutlined class="chip-close" />
            </div>
            <div v-if="yAxisList.length === 0" class="drop-zone">숫자형 컬럼 클릭으로 추가</div>
          </div>
          <div class="config-group">
            <label>차트 색상</label>
            <div class="color-options">
              <span v-for="(c, i) in colorSets" :key="i" class="color-set"
                :class="{ active: selectedColorSet === i }" @click="selectedColorSet = i">
                <span v-for="(cc, j) in c.slice(0, 4)" :key="j" class="color-dot" :style="{ background: cc }"></span>
              </span>
            </div>
          </div>
          <div class="config-group">
            <label>추천 차트</label>
            <div class="recommend-list">
              <div v-for="rec in recommendedCharts" :key="rec.type" class="recommend-item"
                :class="{ active: selectedChartType === rec.type }" @click="changeChartType(rec.type)">
                <component :is="rec.icon" />
                <span>{{ rec.label }}</span>
                <span class="rec-badge" v-if="rec.best">최적</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  AreaChartOutlined,
  SaveOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  TableOutlined,
  ColumnHeightOutlined,
  SettingOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'
import { visualizationApi } from '../../api/portal.api'
import { message } from '../../utils/message'

const router = useRouter()
const route = useRoute()
const editingChartId = ref<string | null>(null)
const isLoadingEdit = ref(false)
const skipWatchOnce = ref(false)

// ─── 차트 타입 ───
const chartTypes = [
  { label: '막대', value: 'bar', icon: BarChartOutlined },
  { label: '선', value: 'line', icon: LineChartOutlined },
  { label: '원', value: 'pie', icon: PieChartOutlined },
  { label: '산점도', value: 'scatter', icon: DotChartOutlined },
  { label: '영역', value: 'area', icon: AreaChartOutlined },
]

const selectedChartType = ref('bar')

// ─── 색상 세트 ───
const colorSets = [
  ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8'],
  ['#1677ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'],
  ['#3366FF', '#FF6633', '#33CC99', '#FF3399', '#9933FF', '#33CCFF'],
]
const selectedColorSet = ref(0)
const colors = computed(() => colorSets[selectedColorSet.value])

// ─── 데이터 소스 ───
interface DataSource { id: string; dataset_name: string; data_format?: string }
interface Column { column_name: string; column_name_kr?: string; data_type: string }

const dataSources = ref<DataSource[]>([])
const columns = ref<Column[]>([])
const selectedDataSourceId = ref('')
const selectedDataSourceName = ref('')

// ─── 축 선택 ───
const xAxis = ref<Column | null>(null)
const yAxisList = ref<Column[]>([])
const chartTitle = ref('')

// ─── SVG 크기 ───
const svgW = 700
const svgH = 340
const margin = { top: 30, right: 20, bottom: 30, left: 55 }
const innerW = svgW - margin.left - margin.right
const innerH = svgH - margin.top - margin.bottom

// ─── 샘플 데이터 생성 ───
const sampleData = ref<Record<string, (string | number)[]>>({})

function generateSampleData() {
  const data: Record<string, (string | number)[]> = {}
  const n = 10

  columns.value.forEach(col => {
    const dt = col.data_type?.toUpperCase() || 'VARCHAR'
    if (isNumericType(dt)) {
      const base = Math.random() * 500 + 100
      data[col.column_name] = Array.from({ length: n }, () => Math.round((base + Math.random() * base * 0.5) * 10) / 10)
    } else if (isDateType(dt)) {
      data[col.column_name] = Array.from({ length: n }, (_, i) => {
        const d = new Date(2026, 2, 25 - (n - i - 1))
        return `${d.getMonth() + 1}/${d.getDate()}`
      })
    } else {
      const labels = ['소양강댐', '충주댐', '안동댐', '임하댐', '합천댐', '대청댐', '섬진강댐', '밀양댐', '용담댐', '횡성댐']
      data[col.column_name] = labels.slice(0, n)
    }
  })
  sampleData.value = data
}

// ─── 유틸 ───
function isNumericType(dt: string): boolean {
  return /INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|NUMBER|REAL|BIGINT/.test(dt.toUpperCase())
}
function isDateType(dt: string): boolean {
  return /DATE|TIME|TIMESTAMP/.test(dt.toUpperCase())
}
function getTypeLabel(dt: string): string {
  const u = (dt || 'VARCHAR').toUpperCase()
  if (isNumericType(u)) return 'N'
  if (isDateType(u)) return 'T'
  return 'S'
}
function getTypeClass(dt: string): string {
  const u = (dt || 'VARCHAR').toUpperCase()
  if (isNumericType(u)) return 'type-num'
  if (isDateType(u)) return 'type-date'
  return 'type-str'
}

// ─── 컬럼 선택 로직 ───
function isColumnSelected(col: Column): boolean {
  return xAxis.value?.column_name === col.column_name || yAxisList.value.some(y => y.column_name === col.column_name)
}

function toggleColumn(col: Column) {
  const dt = (col.data_type || 'VARCHAR').toUpperCase()

  // 이미 선택된 컬럼이면 해제
  if (xAxis.value?.column_name === col.column_name) {
    xAxis.value = null
    autoRecommend()
    return
  }
  const yIdx = yAxisList.value.findIndex(y => y.column_name === col.column_name)
  if (yIdx >= 0) {
    yAxisList.value.splice(yIdx, 1)
    autoRecommend()
    return
  }

  // 숫자형 → Y축
  if (isNumericType(dt)) {
    if (yAxisList.value.length < 5) yAxisList.value.push(col)
  } else {
    // 문자/날짜형 → X축 (하나만)
    xAxis.value = col
  }

  // X축 자동 지정: X축이 없으면 첫 번째 비숫자 컬럼 자동 선택
  if (!xAxis.value && yAxisList.value.length > 0) {
    const candidate = columns.value.find(c => !isNumericType(c.data_type?.toUpperCase() || ''))
    if (candidate) xAxis.value = candidate
  }

  autoRecommend()

  // 차트 제목 자동 생성
  if (!chartTitle.value && yAxisList.value.length > 0) {
    chartTitle.value = `${selectedDataSourceName.value} - ${yAxisList.value.map(y => y.column_name_kr || y.column_name).join(', ')}`
  }
}

function removeXAxis() { xAxis.value = null }
function removeYAxis(col: Column) {
  yAxisList.value = yAxisList.value.filter(y => y.column_name !== col.column_name)
}

// ─── 차트 데이터 ───
const hasChart = computed(() => xAxis.value !== null && yAxisList.value.length > 0)

const chartLabels = computed(() => {
  if (!xAxis.value) return []
  return (sampleData.value[xAxis.value.column_name] || []).map(String)
})

const chartSeries = computed(() => {
  return yAxisList.value.map(y => ({
    name: y.column_name_kr || y.column_name,
    data: (sampleData.value[y.column_name] || []).map(Number),
  }))
})

const previewRows = computed(() => {
  if (!xAxis.value || yAxisList.value.length === 0) return []
  const labels = sampleData.value[xAxis.value.column_name] || []
  return labels.map((label, i) => ({
    label: String(label),
    values: yAxisList.value.map(y => sampleData.value[y.column_name]?.[i] ?? '-'),
  }))
})

// ─── 스케일 계산 ───
const allValues = computed(() => chartSeries.value.flatMap(s => s.data))
const yMax = computed(() => {
  const max = Math.max(...allValues.value, 1)
  return Math.ceil(max * 1.15)
})
const yTicks = computed(() => {
  const step = Math.ceil(yMax.value / 5)
  return Array.from({ length: 6 }, (_, i) => i * step)
})

function yScale(val: number): number {
  return innerH - (val / yMax.value) * innerH
}

// 막대 차트
const barGroupWidth = computed(() => chartLabels.value.length ? innerW / chartLabels.value.length : 40)
const barW = computed(() => Math.min(30, (barGroupWidth.value - 10) / Math.max(chartSeries.value.length, 1)))
function barGroupX(i: number) {
  return i * barGroupWidth.value + (barGroupWidth.value - chartSeries.value.length * (barW.value + 2)) / 2
}

// 선/영역 차트
function lineX(i: number) {
  const n = chartLabels.value.length || 1
  return (i / (n - 1 || 1)) * innerW
}
function linePoints(data: number[]) {
  return data.map((v, i) => `${lineX(i)},${yScale(v)}`).join(' ')
}
function areaPoints(data: number[]) {
  const top = data.map((v, i) => `${lineX(i)},${yScale(v)}`).join(' ')
  return `${top} ${lineX(data.length - 1)},${innerH} ${lineX(0)},${innerH}`
}

// 원 차트
const pieSlices = computed(() => {
  if (chartSeries.value.length === 0 || !chartLabels.value.length) return []
  const data = chartSeries.value[0].data
  const total = data.reduce((a, b) => a + b, 0) || 1
  let cumAngle = 0
  const radius = Math.min(svgW, svgH) / 2 - 40
  return data.map((val, i) => {
    const angle = (val / total) * Math.PI * 2
    const x1 = Math.cos(cumAngle) * radius
    const y1 = Math.sin(cumAngle) * radius
    cumAngle += angle
    const x2 = Math.cos(cumAngle) * radius
    const y2 = Math.sin(cumAngle) * radius
    const large = angle > Math.PI ? 1 : 0
    return {
      path: `M0,0 L${x1},${y1} A${radius},${radius} 0 ${large},1 ${x2},${y2} Z`,
      label: chartLabels.value[i] || `항목${i + 1}`,
      pct: Math.round(val / total * 100),
    }
  })
})
const pieTotal = computed(() => {
  if (chartSeries.value.length === 0) return 0
  return Math.round(chartSeries.value[0].data.reduce((a, b) => a + b, 0))
})

// 산점도
const scatterPoints = computed(() => {
  if (chartSeries.value.length < 1) return []
  return chartSeries.value[0].data.map((v, i) => ({
    x: (i / (chartSeries.value[0].data.length - 1 || 1)) * innerW,
    y: yScale(v),
  }))
})

// ─── 추천 차트 ───
const recommendedCharts = computed(() => {
  if (!hasChart.value) return []
  const numY = yAxisList.value.length
  const xType = xAxis.value?.data_type?.toUpperCase() || 'VARCHAR'
  const isTimeSeries = isDateType(xType)

  const recs: { type: string; label: string; icon: any; best: boolean }[] = []

  if (isTimeSeries) {
    recs.push({ type: 'line', label: '선 차트', icon: LineChartOutlined, best: true })
    recs.push({ type: 'area', label: '영역 차트', icon: AreaChartOutlined, best: false })
    recs.push({ type: 'bar', label: '막대 차트', icon: BarChartOutlined, best: false })
  } else if (numY === 1) {
    recs.push({ type: 'bar', label: '막대 차트', icon: BarChartOutlined, best: true })
    recs.push({ type: 'pie', label: '원 차트', icon: PieChartOutlined, best: false })
    recs.push({ type: 'line', label: '선 차트', icon: LineChartOutlined, best: false })
  } else {
    recs.push({ type: 'bar', label: '막대 차트', icon: BarChartOutlined, best: true })
    recs.push({ type: 'line', label: '선 차트', icon: LineChartOutlined, best: false })
    recs.push({ type: 'area', label: '영역 차트', icon: AreaChartOutlined, best: false })
  }

  if (numY >= 2) {
    recs.push({ type: 'scatter', label: '산점도', icon: DotChartOutlined, best: false })
  }

  return recs
})

function autoRecommend() {
  if (!xAxis.value || yAxisList.value.length === 0) return
  const xType = xAxis.value.data_type?.toUpperCase() || 'VARCHAR'
  if (isDateType(xType)) selectedChartType.value = 'line'
  else if (yAxisList.value.length === 1) selectedChartType.value = 'bar'
}

function changeChartType(type: string) { selectedChartType.value = type }

function formatTick(val: number) {
  if (val >= 10000) return (val / 10000).toFixed(1) + '만'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'K'
  return String(val)
}

function truncLabel(label: string) {
  return label.length > 6 ? label.slice(0, 6) + '…' : label
}

// ─── 데이터 소스 선택 ───
async function selectDataSource(ds: DataSource) {
  selectedDataSourceId.value = String(ds.id)
  selectedDataSourceName.value = ds.dataset_name
  xAxis.value = null
  yAxisList.value = []
  chartTitle.value = ''
}

// ─── 저장 ───
async function saveChart() {
  if (!hasChart.value) return
  const payload = {
    chart_name: chartTitle.value || '새 차트',
    chart_type: selectedChartType.value,
    dataset_id: selectedDataSourceId.value,
    chart_config: {
      x_axis: xAxis.value?.column_name,
      x_axis_kr: xAxis.value?.column_name_kr || xAxis.value?.column_name,
      x_axis_type: xAxis.value?.data_type || 'VARCHAR',
      y_axes: yAxisList.value.map(y => y.column_name),
      y_axes_kr: yAxisList.value.map(y => y.column_name_kr || y.column_name),
      y_axes_types: yAxisList.value.map(y => y.data_type || 'FLOAT'),
      color_set: selectedColorSet.value,
      labels: chartLabels.value,
      series: chartSeries.value,
      dataset_name: selectedDataSourceName.value,
    },
    is_public: false,
  }
  try {
    if (editingChartId.value) {
      await visualizationApi.updateChart(editingChartId.value, payload)
    } else {
      await visualizationApi.createChart(payload)
    }
    router.push({ path: '/portal/gallery-content', query: { saved: '1' } })
  } catch (e) {
    message.error('저장에 실패했습니다.')
  }
}

// ─── 편집 모드: 차트 로딩 ───
async function loadChartForEdit(chartId: string) {
  try {
    isLoadingEdit.value = true
    const res = await visualizationApi.getChart(chartId)
    const chart = res.data?.data
    if (!chart) { isLoadingEdit.value = false; return }

    editingChartId.value = chartId
    chartTitle.value = chart.chart_name || ''
    selectedChartType.value = chart.chart_type || 'bar'

    const cfg = chart.chart_config || {}

    // 데이터소스 선택 (UUID 문자열 비교 + 이름 fallback)
    if (chart.dataset_id) {
      const dsId = String(chart.dataset_id)
      const ds = dataSources.value.find(d => String(d.id) === dsId)
      if (ds) {
        selectedDataSourceId.value = String(ds.id)
        selectedDataSourceName.value = ds.dataset_name
      } else {
        selectedDataSourceId.value = dsId
        selectedDataSourceName.value = cfg.dataset_name || ''
      }
    } else if (cfg.dataset_name) {
      // dataset_id가 없으면 이름으로 매칭
      const ds = dataSources.value.find(d => d.dataset_name === cfg.dataset_name)
      if (ds) {
        selectedDataSourceId.value = String(ds.id)
        selectedDataSourceName.value = ds.dataset_name
      }
    }

    // 컬럼 로딩 대기
    if (selectedDataSourceId.value) {
      try {
        const colRes = await visualizationApi.columns(selectedDataSourceId.value)
        if (colRes.data?.data && colRes.data.data.length > 0) {
          columns.value = colRes.data.data
        }
      } catch { /* use fallback below */ }
    }

    // 컬럼 API 실패/빈 결과 시 chart_config 축 정보에서 컬럼 복원
    if (columns.value.length === 0 && (cfg.x_axis || (cfg.y_axes && cfg.y_axes.length))) {
      const restored: any[] = []
      if (cfg.x_axis) {
        restored.push({ column_name: cfg.x_axis, column_name_kr: cfg.x_axis_kr || cfg.x_axis, data_type: cfg.x_axis_type || 'VARCHAR' })
      }
      const yAxes = cfg.y_axes || []
      const yAxesKr = cfg.y_axes_kr || []
      const yAxesTypes = cfg.y_axes_types || []
      yAxes.forEach((name: string, i: number) => {
        if (!restored.some(c => c.column_name === name)) {
          restored.push({ column_name: name, column_name_kr: yAxesKr[i] || name, data_type: yAxesTypes[i] || 'FLOAT' })
        }
      })
      columns.value = restored
    }

    // 색상 세트 복원
    if (cfg.color_set !== undefined) selectedColorSet.value = cfg.color_set

    // X축 복원
    if (cfg.x_axis) {
      const xCol = columns.value.find(c => c.column_name === cfg.x_axis)
      if (xCol) {
        xAxis.value = xCol
      } else {
        // 컬럼 목록에 없으면 config에서 직접 복원
        xAxis.value = {
          column_name: cfg.x_axis,
          column_name_kr: cfg.x_axis_kr || cfg.x_axis,
          data_type: cfg.x_axis_type || 'VARCHAR',
        }
      }
    }

    // Y축 복원
    const yAxes: string[] = cfg.y_axes || []
    const yAxesKr: string[] = cfg.y_axes_kr || []
    const yAxesTypes: string[] = cfg.y_axes_types || []
    yAxisList.value = yAxes.map((name: string, i: number) => {
      const col = columns.value.find(c => c.column_name === name)
      if (col) return col
      return {
        column_name: name,
        column_name_kr: yAxesKr[i] || name,
        data_type: yAxesTypes[i] || 'FLOAT',
      }
    })

    // 샘플 데이터: config에 저장된 데이터 사용
    if (cfg.labels && cfg.series) {
      const data: Record<string, (string | number)[]> = {}
      if (cfg.x_axis) data[cfg.x_axis] = cfg.labels
      cfg.series.forEach((s: any) => {
        const yName = yAxes.find((_: string, i: number) => (yAxesKr[i] || yAxes[i]) === s.name) || s.name
        const matchCol = yAxisList.value.find(y => (y.column_name_kr || y.column_name) === s.name)
        if (matchCol) data[matchCol.column_name] = s.data
        else data[yName] = s.data
      })
      sampleData.value = data
    } else {
      generateSampleData()
    }
  } catch (e) {
    console.error('차트 로딩 실패:', e)
  }
  // watch가 트리거되더라도 한 번 건너뛰도록 설정
  skipWatchOnce.value = true
  isLoadingEdit.value = false
  await nextTick()
  await nextTick()
}

function resetChart() {
  xAxis.value = null
  yAxisList.value = []
  chartTitle.value = ''
  selectedChartType.value = 'bar'
}

// ─── API 호출 ───
onMounted(async () => {
  try {
    const res = await visualizationApi.dataSources()
    if (res.data?.data && res.data.data.length > 0) {
      dataSources.value = res.data.data
    }
  } catch (e) {
    console.warn('데이터 소스 API 호출 실패, fallback 사용')
  }

  // fallback
  if (dataSources.value.length === 0) {
    dataSources.value = [
      { id: 'ds1', dataset_name: '댐 수위 관측 데이터', data_format: 'DB' },
      { id: 'ds2', dataset_name: '수질 모니터링 센서', data_format: 'IoT' },
      { id: 'ds3', dataset_name: '전력 사용량 통계', data_format: 'CSV' },
      { id: 'ds4', dataset_name: '광역상수도 유량 데이터', data_format: 'DB' },
      { id: 'ds5', dataset_name: '강수량 예측 모델 결과', data_format: 'API' },
    ]
  }

  // 편집 모드: ?edit=chartId 일 때 차트 로딩
  const editId = route.query.edit as string
  if (editId) {
    await loadChartForEdit(editId)
  }

  // 데이터셋 자동 선택: ?dataset_id=xxx 일 때
  const queryDatasetId = route.query.dataset_id as string
  if (queryDatasetId && !editId) {
    const match = dataSources.value.find(ds => String(ds.id) === queryDatasetId)
    if (match) {
      await selectDataSource(match)
    }
  }
})

watch(selectedDataSourceId, async (newId) => {
  if (!newId) return
  // 편집 로딩 중이면 watch 무시
  if (isLoadingEdit.value) return
  // loadChartForEdit 완료 후 한 번 건너뛰기
  if (skipWatchOnce.value) { skipWatchOnce.value = false; return }
  columns.value = []
  try {
    const res = await visualizationApi.columns(newId)
    if (res.data?.data && res.data.data.length > 0) {
      columns.value = res.data.data
    }
  } catch { /* fallback */ }

  if (columns.value.length === 0) {
    const fallbackColumns: Record<string, Column[]> = {
      ds1: [
        { column_name: 'obs_date', column_name_kr: '관측일시', data_type: 'TIMESTAMP' },
        { column_name: 'dam_name', column_name_kr: '댐명', data_type: 'VARCHAR' },
        { column_name: 'water_level', column_name_kr: '수위(m)', data_type: 'FLOAT' },
        { column_name: 'inflow', column_name_kr: '유입량(㎥/s)', data_type: 'FLOAT' },
        { column_name: 'outflow', column_name_kr: '방류량(㎥/s)', data_type: 'FLOAT' },
        { column_name: 'storage_rate', column_name_kr: '저수율(%)', data_type: 'FLOAT' },
      ],
      ds2: [
        { column_name: 'measure_date', column_name_kr: '측정일', data_type: 'DATE' },
        { column_name: 'station_name', column_name_kr: '측정소', data_type: 'VARCHAR' },
        { column_name: 'ph', column_name_kr: 'pH', data_type: 'FLOAT' },
        { column_name: 'do_value', column_name_kr: '용존산소(mg/L)', data_type: 'FLOAT' },
        { column_name: 'bod', column_name_kr: 'BOD(mg/L)', data_type: 'FLOAT' },
        { column_name: 'temperature', column_name_kr: '수온(℃)', data_type: 'FLOAT' },
      ],
      ds3: [
        { column_name: 'month', column_name_kr: '월', data_type: 'VARCHAR' },
        { column_name: 'facility', column_name_kr: '시설명', data_type: 'VARCHAR' },
        { column_name: 'usage_kwh', column_name_kr: '사용량(kWh)', data_type: 'FLOAT' },
        { column_name: 'cost', column_name_kr: '비용(원)', data_type: 'FLOAT' },
        { column_name: 'peak_kw', column_name_kr: '피크(kW)', data_type: 'FLOAT' },
      ],
      ds4: [
        { column_name: 'measure_date', column_name_kr: '측정일', data_type: 'DATE' },
        { column_name: 'pipe_name', column_name_kr: '관로명', data_type: 'VARCHAR' },
        { column_name: 'flow_rate', column_name_kr: '유량(㎥/h)', data_type: 'FLOAT' },
        { column_name: 'pressure', column_name_kr: '압력(bar)', data_type: 'FLOAT' },
        { column_name: 'velocity', column_name_kr: '유속(m/s)', data_type: 'FLOAT' },
      ],
      ds5: [
        { column_name: 'forecast_date', column_name_kr: '예측일', data_type: 'DATE' },
        { column_name: 'region', column_name_kr: '지역', data_type: 'VARCHAR' },
        { column_name: 'rainfall_mm', column_name_kr: '강수량(mm)', data_type: 'FLOAT' },
        { column_name: 'probability', column_name_kr: '확률(%)', data_type: 'FLOAT' },
        { column_name: 'confidence', column_name_kr: '신뢰도', data_type: 'FLOAT' },
      ],
    }
    columns.value = fallbackColumns[newId] || fallbackColumns.ds1
  }

  generateSampleData()
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}

.viz-page {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  p { font-size: $font-size-sm; color: $text-muted; }
}

// ─── 도구 영역 ───
.viz-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: $spacing-sm $spacing-lg;
  box-shadow: $shadow-sm;
}

.chart-types { display: flex; gap: $spacing-xs; }

.chart-type-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  background: $white;
  font-size: $font-size-xs;
  color: $text-secondary;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { border-color: $primary; color: $primary; }
  &.active { background: $primary; color: $white; border-color: $primary; }
}

.toolbar-actions { display: flex; gap: $spacing-sm; align-items: center; }

.edit-mode-badge {
  font-size: $font-size-xs;
  padding: 3px 10px;
  background: #fff7e6;
  color: #d48806;
  border: 1px solid #ffe58f;
  border-radius: 12px;
  font-weight: 600;
}

// ─── 본문 ───
.viz-body {
  display: flex;
  gap: $spacing-md;
  min-height: 560px;
}

// ─── 좌측 패널 ───
.data-panel, .config-panel {
  width: 240px;
  flex-shrink: 0;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 10px 14px;
  background: #4a6a8a;
  color: $white;
  font-size: $font-size-sm;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.panel-content {
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}

.panel-sub-header {
  font-size: $font-size-xs;
  color: $text-muted;
  font-weight: 600;
  padding: 8px 6px 4px;
  margin-top: 6px;
  border-top: 1px solid $border-color;
  display: flex;
  align-items: center;
  gap: 4px;
}

.empty-hint {
  font-size: $font-size-xs;
  color: $text-muted;
  text-align: center;
  padding: $spacing-lg $spacing-sm;
}

// ─── 데이터 소스 아이템 ───
.data-source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  font-size: $font-size-sm;
  color: $text-secondary;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all 0.15s;
  &:hover { background: #f0f5ff; }
  &.active { background: #e6f0ff; color: $primary; font-weight: 600; border-left: 3px solid $primary; }
}

.ds-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  .ds-name { font-size: $font-size-xs; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ds-format { font-size: 10px; color: $text-muted; }
}

// ─── 컬럼 아이템 ───
.column-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  font-size: $font-size-xs;
  border-radius: $radius-sm;
  cursor: pointer;
  transition: all 0.15s;
  &:hover { background: #f0f5ff; }
  &.selected { background: #e6f0ff; }
  &.axis-x { border-left: 3px solid #0066CC; }
  &.axis-y { border-left: 3px solid #28A745; }
}

.col-type-badge {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  &.type-num { background: #e6f7ff; color: #0066CC; }
  &.type-date { background: #fff7e6; color: #d48806; }
  &.type-str { background: #f6ffed; color: #389e0d; }
}

.col-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
  .col-name-kr { font-size: $font-size-xs; color: $text-primary; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .col-name-en { font-size: 10px; color: $text-muted; }
}

.axis-tag {
  font-size: 9px;
  font-weight: 700;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  &.x { background: #e6f0ff; color: #0066CC; }
  &.y { background: #f6ffed; color: #28A745; }
}

// ─── 차트 캔버스 ───
.chart-canvas {
  flex: 1;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.canvas-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: $text-muted;
  .placeholder-icon { font-size: 64px; opacity: 0.12; margin-bottom: $spacing-lg; }
  p { font-size: $font-size-md; margin-bottom: $spacing-sm; }
  .placeholder-hint { font-size: $font-size-xs; }
}

.chart-render-area {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chart-title-bar {
  padding: 8px 14px;
  border-bottom: 1px solid $border-color;
}

.chart-title-input {
  width: 100%;
  border: none;
  font-size: $font-size-md;
  font-weight: 600;
  color: $text-primary;
  outline: none;
  background: transparent;
  &::placeholder { color: $text-muted; }
}

.chart-svg-wrapper {
  flex: 1;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.chart-svg {
  width: 100%;
  max-height: 340px;
}

// ─── 데이터 미리보기 ───
.data-preview {
  border-top: 1px solid $border-color;
  max-height: 180px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 6px 14px;
  font-size: $font-size-xs;
  font-weight: 600;
  color: $text-secondary;
  background: #fafafa;
  border-bottom: 1px solid $border-color;
  display: flex;
  align-items: center;
  gap: 6px;
}

.preview-table-wrap {
  overflow: auto;
  flex: 1;
}

.preview-table {
  width: 100%;
  font-size: $font-size-xs;
  border-collapse: collapse;
  th, td { padding: 4px 10px; border-bottom: 1px solid #f0f0f0; text-align: left; white-space: nowrap; }
  th { background: #fafafa; color: $text-secondary; font-weight: 600; position: sticky; top: 0; }
  td { color: $text-primary; }
}

// ─── 우측 설정 패널 ───
.config-group {
  padding: 8px 6px;
  border-bottom: 1px solid #f5f5f5;
  label {
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-secondary;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 6px;
  }
  .axis-count { font-weight: 400; color: $text-muted; }
}

.drop-zone {
  padding: 10px;
  border: 2px dashed #d9d9d9;
  border-radius: $radius-md;
  text-align: center;
  font-size: $font-size-xs;
  color: $text-muted;
}

.axis-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: $font-size-xs;
  cursor: pointer;
  margin-bottom: 4px;
  &.x { background: #e6f0ff; color: #0066CC; }
  &.y { background: #f6ffed; color: #28A745; }
  &:hover { opacity: 0.8; }
  .chip-close { font-size: 10px; margin-left: auto; }
}

.color-options {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.color-set {
  display: flex;
  gap: 2px;
  padding: 3px 5px;
  border: 2px solid transparent;
  border-radius: $radius-md;
  cursor: pointer;
  &.active { border-color: $primary; }
  &:hover { border-color: #bbd; }
}

.color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recommend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  cursor: pointer;
  color: $text-secondary;
  &:hover { background: #f0f5ff; }
  &.active { background: #e6f0ff; color: $primary; font-weight: 600; }
}

.rec-badge {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 8px;
  background: #fff7e6;
  color: #d48806;
  font-weight: 600;
  margin-left: auto;
}

// ─── 반응형 ───
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .data-panel, .config-panel { width: 190px; }
  .viz-body { min-height: 400px; }
}
</style>
