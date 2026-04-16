<template>
  <div class="lineage-page">
    <nav class="breadcrumb">
      <router-link to="/portal/catalog">데이터카탈로그</router-link>
      <span class="separator">&gt;</span>
      <span class="current">데이터 리니지(계보)</span>
    </nav>

    <div class="page-header">
      <h2>데이터 리니지(계보)</h2>
      <p>데이터의 수집 원천부터 활용까지 전체 흐름을 추적합니다.</p>
    </div>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-value">{{ graph.nodes.length }}</div><div class="kpi-label">데이터셋 노드</div></div>
      <div class="kpi-card"><div class="kpi-value">{{ graph.edges.length }}</div><div class="kpi-label">리니지 관계</div></div>
      <div class="kpi-card"><div class="kpi-value">{{ externalCount }}</div><div class="kpi-label">외부 원천</div></div>
      <div class="kpi-card"><div class="kpi-value">{{ avgQuality }}</div><div class="kpi-label">평균 품질</div></div>
    </div>

    <!-- 컨트롤바 -->
    <div class="control-bar">
      <!-- 엣지 유형 필터 -->
      <div class="filter-group">
        <span class="filter-label">유형</span>
        <div class="filter-chips">
          <button class="chip" :class="{ active: filterType === '' }" @click="filterType = ''">전체</button>
          <button v-for="t in lineageTypes" :key="t.key" class="chip" :class="{ active: filterType === t.key }" @click="filterType = t.key">
            {{ t.icon }} {{ t.label }}
          </button>
        </div>
      </div>
      <!-- 원천 필터 -->
      <div class="filter-group">
        <span class="filter-label">원천</span>
        <select v-model="filterSource" class="filter-select">
          <option value="">전체</option>
          <option v-for="s in sourceOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <!-- 노드 검색 -->
      <div class="filter-group search">
        <input type="text" v-model="searchText" placeholder="노드 검색..." class="filter-input" />
      </div>
      <!-- 영향도 -->
      <div class="control-right">
        <button class="ctrl-btn" :class="{ active: impactMode }" @click="impactMode = !impactMode; impactNodeId = selectedNode?.id || ''">
          <ThunderboltOutlined /> 영향도 분석
        </button>
      </div>
    </div>

    <!-- 그래프 시각화 -->
    <div class="lineage-graph-wrap" ref="graphWrap" @wheel.prevent="onWheel" @mousedown="onPanStart" @mousemove="onPanMove" @mouseup="onPanEnd" @mouseleave="onPanEnd">
      <div class="zoom-controls">
        <button @click="zoomIn" title="확대">+</button>
        <button @click="zoomOut" title="축소">-</button>
        <button @click="zoomFit" title="맞춤">Fit</button>
        <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
      </div>
      <svg ref="svgRef" :width="svgWidth" :height="svgHeight" :style="{ cursor: isPanning ? 'grabbing' : 'grab' }">
        <g :transform="`translate(${panX}, ${panY}) scale(${zoom})`">
        <!-- 엣지 -->
        <g v-for="(e, idx) in visibleEdges" :key="'e'+idx">
          <path :d="edgePath(e)" fill="none" :stroke="edgeColor(e)" stroke-width="2" :stroke-dasharray="e._type === 'COPY' ? '6,3' : ''" marker-end="url(#arrow)" />
          <text :x="edgeLabelX(e)" :y="edgeLabelY(e) - 6" font-size="9" :fill="edgeColor(e)" text-anchor="middle" font-weight="600">{{ edgeLabel(e.lineage_type) }}</text>
        </g>
        <defs><marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#999" /></marker></defs>
        <!-- 노드 -->
        <g v-for="n in positionedNodes" :key="n.id" :transform="`translate(${n.x}, ${n.y})`" class="lineage-node-g"
          :class="{ selected: selectedNode?.id === n.id, dimmed: (impactMode && !impactSet.has(String(n.id))) || ((filterSource || searchText) && !visibleNodeIds.has(String(n.id))) }"
          @click="selectNode(n)">
          <rect :width="nodeW" :height="nodeH" rx="8" :fill="nodeFill(n)" stroke="#ddd" stroke-width="1" />
          <!-- 품질 배지 -->
          <circle v-if="n.quality_score" :cx="nodeW - 8" cy="8" r="10" :fill="qualityColor(n.quality_score)" />
          <text v-if="n.quality_score" :x="nodeW - 8" y="12" font-size="8" fill="#fff" text-anchor="middle" font-weight="bold">{{ Math.round(n.quality_score) }}</text>
          <!-- 아이콘 -->
          <text x="14" y="22" font-size="16">{{ nodeIcon(n) }}</text>
          <!-- 이름 -->
          <text x="36" y="20" font-size="11" font-weight="600" fill="#333">{{ shortName(n.dataset_name_kr || n.dataset_name) }}</text>
          <!-- 부가정보 -->
          <text x="36" y="35" font-size="9" fill="#999">{{ n.source_system || n.node_type }} {{ n.row_count ? '/ ' + formatCount(n.row_count) : '' }}</text>
          <!-- 상태 점 -->
          <circle cx="14" cy="38" r="4" :fill="n.status === 'ACTIVE' ? '#52c41a' : '#faad14'" />
        </g>
        </g><!-- close zoom/pan group -->
      </svg>
    </div>

    <!-- 선택 노드 상세 -->
    <div class="detail-section" v-if="selectedNode">
      <div class="detail-card">
        <div class="card-title">
          {{ nodeIcon(selectedNode) }} {{ selectedNode.dataset_name_kr || selectedNode.dataset_name }}
          <div class="card-actions">
            <button class="btn btn-xs btn-primary" @click="goToCatalog(selectedNode)"><DatabaseOutlined /> 카탈로그 상세</button>
            <button class="btn btn-xs btn-outline" @click="selectedNode = null"><CloseOutlined /> 닫기</button>
          </div>
        </div>
        <div class="info-grid-3">
          <div class="info-item"><span class="lbl">유형</span><span class="val">{{ selectedNode.node_type }}</span></div>
          <div class="info-item"><span class="lbl">원천</span><span class="val">{{ selectedNode.source_system || '-' }}</span></div>
          <div class="info-item"><span class="lbl">포맷</span><span class="val">{{ selectedNode.data_format || '-' }}</span></div>
          <div class="info-item"><span class="lbl">부서</span><span class="val">{{ selectedNode.owner_department || '-' }}</span></div>
          <div class="info-item"><span class="lbl">레코드</span><span class="val">{{ selectedNode.row_count ? formatCount(selectedNode.row_count) : '-' }}</span></div>
          <div class="info-item"><span class="lbl">품질</span><span class="val" :style="{ color: qualityColor(selectedNode.quality_score) }">{{ selectedNode.quality_score ? selectedNode.quality_score + '%' : '-' }}</span></div>
        </div>
      </div>
      <!-- 연결된 리니지 -->
      <div class="detail-card" v-if="selectedEdges.length">
        <div class="card-title">연결 파이프라인 ({{ selectedEdges.length }})</div>
        <table class="data-table">
          <thead><tr><th>방향</th><th>유형</th><th>파이프라인</th><th>대상</th><th>설명</th></tr></thead>
          <tbody>
            <tr v-for="se in selectedEdges" :key="String(se.id)">
              <td><span :class="se._dir === 'up' ? 'dir-in' : 'dir-out'">{{ se._dir === 'up' ? '← 입력' : '→ 출력' }}</span></td>
              <td><span class="type-badge" :class="se.lineage_type?.toLowerCase()">{{ se.lineage_type }}</span></td>
              <td>{{ se.pipeline_name }}</td>
              <td class="link" @click="focusNodeById(se._dir === 'up' ? se.upstream_id : se.downstream_id)">{{ se._dir === 'up' ? se.upstream_name : se.downstream_name }}</td>
              <td class="muted">{{ se.description || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ThunderboltOutlined, DatabaseOutlined, CloseOutlined } from '@ant-design/icons-vue'
import { catalogApi } from '../../api/portal.api'

const route = useRoute()
const router = useRouter()
const graph = ref<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] })
const selectedNode = ref<any>(null)
const filterType = ref('')
const filterSource = ref('')
const searchText = ref('')
const impactMode = ref(false)
const impactNodeId = ref('')
const svgWidth = ref(1100)
const svgHeight = ref(500)
const nodeW = 180
const nodeH = 48

// 줌/패닝
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
let panStartX = 0, panStartY = 0
const graphWrap = ref<HTMLElement | null>(null)

function zoomIn() { zoom.value = Math.min(3, zoom.value * 1.2) }
function zoomOut() { zoom.value = Math.max(0.2, zoom.value / 1.2) }
function zoomFit() { zoom.value = 1; panX.value = 0; panY.value = 0 }
function onWheel(e: WheelEvent) {
  const factor = e.deltaY > 0 ? 0.9 : 1.1
  const newZoom = Math.max(0.2, Math.min(3, zoom.value * factor))
  const rect = graphWrap.value?.getBoundingClientRect()
  if (rect) {
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    panX.value = mx - (mx - panX.value) * (newZoom / zoom.value)
    panY.value = my - (my - panY.value) * (newZoom / zoom.value)
  }
  zoom.value = newZoom
}
function onPanStart(e: MouseEvent) {
  if ((e.target as HTMLElement)?.closest('.lineage-node-g, button')) return
  isPanning.value = true; panStartX = e.clientX - panX.value; panStartY = e.clientY - panY.value
}
function onPanMove(e: MouseEvent) {
  if (!isPanning.value) return
  panX.value = e.clientX - panStartX; panY.value = e.clientY - panStartY
}
function onPanEnd() { isPanning.value = false }

const lineageTypes = [
  { key: 'COPY', icon: '\uD83D\uDCE5', label: '수집' },
  { key: 'ETL', icon: '\u2699\uFE0F', label: 'ETL' },
  { key: 'TRANSFORM', icon: '\uD83D\uDD04', label: '변환' },
  { key: 'VIEW', icon: '\uD83D\uDC41', label: '뷰' },
]

// Fallback mock
const fallbackGraph = {
  nodes: [
    { id: 'ext-rwis', dataset_name: 'RWIS 센서', node_type: 'EXTERNAL', source_system: 'FA망', status: 'ACTIVE' },
    { id: 'ext-kma', dataset_name: '기상청 API', node_type: 'EXTERNAL', source_system: 'DMZ', status: 'ACTIVE' },
    { id: 'n1', dataset_name: '댐 수위 관측', dataset_name_kr: '댐 수위 관측', node_type: 'DATASET', source_system: 'K-water', row_count: 1234567, quality_score: 94.2, data_format: 'DB', status: 'ACTIVE' },
    { id: 'n2', dataset_name: '수질 모니터링', node_type: 'DATASET', row_count: 850000, quality_score: 92.8, data_format: 'IoT', status: 'ACTIVE' },
    { id: 'n3', dataset_name: '강수량 예측', node_type: 'DATASET', row_count: 365000, quality_score: 91.5, data_format: 'API', status: 'ACTIVE' },
  ],
  edges: [
    { id: 'e1', upstream_id: 'ext-rwis', downstream_id: 'n1', upstream_name: 'RWIS 센서', downstream_name: '댐 수위', lineage_type: 'COPY', pipeline_name: '실시간 CDC 수집' },
    { id: 'e2', upstream_id: 'ext-kma', downstream_id: 'n2', upstream_name: '기상청 API', downstream_name: '수질', lineage_type: 'ETL', pipeline_name: 'API 정제' },
    { id: 'e3', upstream_id: 'n1', downstream_id: 'n3', upstream_name: '댐 수위', downstream_name: '강수량 예측', lineage_type: 'TRANSFORM', pipeline_name: 'ML 모델' },
  ],
}

const sourceOptions = computed(() => {
  const sources = new Set<string>()
  graph.value.nodes.forEach(n => { if (n.source_system) sources.add(n.source_system) })
  return Array.from(sources).sort()
})

const externalCount = computed(() => graph.value.nodes.filter(n => n.node_type === 'EXTERNAL').length)
const avgQuality = computed(() => {
  const scored = graph.value.nodes.filter(n => n.quality_score)
  if (!scored.length) return '-'
  return (scored.reduce((s, n) => s + n.quality_score, 0) / scored.length).toFixed(1) + '%'
})

// 필터링된 노드 ID (원천/검색)
const visibleNodeIds = computed(() => {
  const ids = new Set<string>()
  graph.value.nodes.forEach(n => {
    if (filterSource.value && n.source_system !== filterSource.value) return
    if (searchText.value) {
      const q = searchText.value.toLowerCase()
      const name = (n.dataset_name_kr || n.dataset_name || '').toLowerCase()
      if (!name.includes(q) && !(n.source_system || '').toLowerCase().includes(q)) return
    }
    ids.add(String(n.id))
  })
  return ids
})

const visibleEdges = computed(() => {
  let edges = graph.value.edges
  if (filterType.value) edges = edges.filter(e => e.lineage_type === filterType.value)
  // 원천/검색 필터: 양쪽 노드 중 하나라도 보이면 엣지 표시
  if (filterSource.value || searchText.value) {
    edges = edges.filter(e => visibleNodeIds.value.has(String(e.upstream_id)) || visibleNodeIds.value.has(String(e.downstream_id)))
  }
  // 같은 노드 쌍 간 엣지 인덱스 계산 (겹침 방지용)
  const pairCount = new Map<string, number>()
  const pairIndex = new Map<string, number>()
  edges.forEach(e => {
    const key = [String(e.upstream_id), String(e.downstream_id)].sort().join('|')
    pairCount.set(key, (pairCount.get(key) || 0) + 1)
  })
  return edges.map(e => {
    const key = [String(e.upstream_id), String(e.downstream_id)].sort().join('|')
    const idx = pairIndex.get(key) || 0
    pairIndex.set(key, idx + 1)
    const total = pairCount.get(key) || 1
    return { ...e, _type: e.lineage_type, _pairIdx: idx, _pairTotal: total }
  })
})

// 노드 위치 계산 (계층 레이아웃)
const positionedNodes = computed(() => {
  const nodes = graph.value.nodes
  const edges = graph.value.edges
  // 진입 차수 기반 depth 계산
  const depthMap = new Map<string, number>()
  nodes.forEach(n => depthMap.set(String(n.id), 0))
  // BFS
  for (let iter = 0; iter < 10; iter++) {
    edges.forEach(e => {
      const upD = depthMap.get(String(e.upstream_id)) ?? 0
      const downD = depthMap.get(String(e.downstream_id)) ?? 0
      if (downD <= upD) depthMap.set(String(e.downstream_id), upD + 1)
    })
  }
  // 그룹별 배치
  const maxDepth = Math.max(...Array.from(depthMap.values()), 0)
  const colWidth = Math.max(svgWidth.value / (maxDepth + 1), 220)
  const groups: Map<number, any[]> = new Map()
  nodes.forEach(n => {
    const d = depthMap.get(String(n.id)) || 0
    if (!groups.has(d)) groups.set(d, [])
    groups.get(d)!.push(n)
  })
  const result: any[] = []
  groups.forEach((group, depth) => {
    const rowH = Math.max(svgHeight.value / (group.length + 1), 65)
    group.forEach((n, i) => {
      result.push({ ...n, x: depth * colWidth + 20, y: (i + 1) * rowH - 10 })
    })
  })
  svgHeight.value = Math.max(500, nodes.length * 55 + 50)
  return result
})

// 영향도 BFS
const impactSet = computed(() => {
  const set = new Set<string>()
  if (!impactMode.value || !selectedNode.value) return set
  const startId = String(selectedNode.value.id)
  const queue = [startId]
  while (queue.length) {
    const cur = queue.shift()!
    if (set.has(cur)) continue
    set.add(cur)
    graph.value.edges.forEach(e => {
      if (String(e.upstream_id) === cur && !set.has(String(e.downstream_id))) queue.push(String(e.downstream_id))
    })
  }
  return set
})

const selectedEdges = computed(() => {
  if (!selectedNode.value) return []
  const nid = String(selectedNode.value.id)
  return graph.value.edges
    .filter(e => String(e.upstream_id) === nid || String(e.downstream_id) === nid)
    .map(e => ({ ...e, _dir: String(e.downstream_id) === nid ? 'up' : 'down' }))
})

function edgeOffset(e: any): number {
  // 같은 노드 쌍에 여러 엣지가 있으면 Y 오프셋으로 분리
  const total = e._pairTotal || 1
  const idx = e._pairIdx || 0
  if (total <= 1) return 0
  const spread = 25 // 엣지 간 간격 (px)
  return (idx - (total - 1) / 2) * spread
}

function edgePath(e: any): string {
  const src = positionedNodes.value.find(n => String(n.id) === String(e.upstream_id))
  const tgt = positionedNodes.value.find(n => String(n.id) === String(e.downstream_id))
  if (!src || !tgt) return ''
  const offset = edgeOffset(e)
  const sx = src.x + nodeW, sy = src.y + nodeH / 2
  const tx = tgt.x, ty = tgt.y + nodeH / 2
  const mx = (sx + tx) / 2
  // 컨트롤 포인트에 Y 오프셋 적용 → 곡선이 위/아래로 분리
  return `M${sx},${sy} C${mx},${sy + offset} ${mx},${ty + offset} ${tx},${ty}`
}
function edgeLabelX(e: any): number {
  const src = positionedNodes.value.find(n => String(n.id) === String(e.upstream_id))
  const tgt = positionedNodes.value.find(n => String(n.id) === String(e.downstream_id))
  return src && tgt ? (src.x + nodeW + tgt.x) / 2 : 0
}
function edgeLabelY(e: any): number {
  const src = positionedNodes.value.find(n => String(n.id) === String(e.upstream_id))
  const tgt = positionedNodes.value.find(n => String(n.id) === String(e.downstream_id))
  const offset = edgeOffset(e)
  return src && tgt ? (src.y + tgt.y + nodeH) / 2 + offset : 0
}
function edgeColor(e: any): string {
  const m: Record<string, string> = { COPY: '#1890ff', ETL: '#fa8c16', TRANSFORM: '#722ed1', VIEW: '#13c2c2' }
  return m[e.lineage_type] || '#999'
}
function edgeLabel(type: string): string {
  const m: Record<string, string> = { COPY: '수집', ETL: 'ETL', TRANSFORM: '변환', VIEW: '뷰' }
  return m[type] || type
}
function nodeFill(n: any): string {
  if (n.node_type === 'EXTERNAL') return '#f0f5ff'
  return '#fff'
}
function nodeIcon(n: any): string {
  if (n.node_type === 'EXTERNAL') return '\uD83D\uDD17'
  const m: Record<string, string> = { DB: '\uD83D\uDDC4', IoT: '\uD83D\uDCE1', API: '\uD83D\uDD0C', CSV: '\uD83D\uDCC4', GIS: '\uD83D\uDDFA' }
  return m[n.data_format || ''] || '\uD83D\uDCCA'
}
function qualityColor(score: number | null | undefined): string {
  if (!score) return '#ccc'
  if (score >= 95) return '#28A745'
  if (score >= 85) return '#0066CC'
  if (score >= 70) return '#fa8c16'
  return '#DC3545'
}
function shortName(name: string | null): string {
  if (!name) return ''
  return name.length > 16 ? name.substring(0, 15) + '...' : name
}
function formatCount(n: number): string {
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '\uC5B5'
  if (n >= 10000) return (n / 10000).toFixed(0) + '\uB9CC'
  return n.toLocaleString()
}
function selectNode(n: any) {
  selectedNode.value = n
  if (impactMode.value) impactNodeId.value = String(n.id)
}
function focusNodeById(id: string) {
  const n = graph.value.nodes.find(nd => String(nd.id) === id)
  if (n) selectedNode.value = n
}
function goToCatalog(n: any) {
  router.push({ path: '/portal/catalog', query: { detail: String(n.id) } })
}

onMounted(async () => {
  try {
    const res = await catalogApi.lineage()
    if (res.data?.data?.nodes?.length) {
      graph.value = res.data.data
    } else {
      graph.value = fallbackGraph
    }
  } catch {
    graph.value = fallbackGraph
  }

  // 온톨로지에서 넘어온 경우: ?search=노드명 → 자동 검색 + 노드 선택
  const searchParam = route.query.search as string
  if (searchParam) {
    searchText.value = searchParam
    // 매칭되는 노드 자동 선택
    const matched = graph.value.nodes.find((n: any) => {
      const name = (n.dataset_name_kr || n.dataset_name || '').toLowerCase()
      return name.includes(searchParam.toLowerCase())
    })
    if (matched) {
      selectedNode.value = matched
    }
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.lineage-page { display: flex; flex-direction: column; gap: 14px; }
.breadcrumb { font-size: 12px; color: #999; a { color: $primary; text-decoration: none; } }
.page-header { h2 { margin: 0 0 4px; font-size: 20px; } p { margin: 0; color: #666; font-size: 13px; } }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px 16px; text-align: center;
  .kpi-value { font-size: 22px; font-weight: 800; color: $primary; } .kpi-label { font-size: 11px; color: #999; }
}

.control-bar { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; flex-wrap: wrap;
  .filter-group { display: flex; align-items: center; gap: 6px;
    &.search { flex: 1; min-width: 140px; }
  }
  .filter-label { font-size: 11px; font-weight: 600; color: #999; white-space: nowrap; }
  .filter-chips { display: flex; gap: 3px; }
  .chip { padding: 3px 9px; border: 1px solid #d9d9d9; border-radius: 12px; font-size: 11px; cursor: pointer; background: #fff; white-space: nowrap;
    &.active { background: #e6f7ff; border-color: #1890ff; color: #1890ff; font-weight: 600; }
    &:hover { border-color: #1890ff; }
  }
  .filter-select { padding: 3px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 11px; background: #fff; min-width: 100px; }
  .filter-input { padding: 3px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 11px; width: 100%; &:focus { outline: none; border-color: #1890ff; } }
  .control-right { margin-left: auto; }
  .ctrl-btn { padding: 4px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 11px; cursor: pointer; background: #fff; white-space: nowrap;
    &.active { background: #f5222d; color: #fff; border-color: #f5222d; }
  }
}

.lineage-graph-wrap { background: #fafbfc; border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; min-height: 400px; position: relative;
  .zoom-controls { position: absolute; top: 10px; right: 10px; z-index: 10; display: flex; gap: 4px; align-items: center;
    button { width: 28px; height: 28px; border: 1px solid #d9d9d9; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center;
      &:hover { border-color: $primary; color: $primary; }
    }
    .zoom-label { font-size: 11px; color: #999; margin-left: 4px; }
  }
  svg { display: block; min-width: 900px; }
}
.lineage-node-g { cursor: pointer; transition: opacity 0.2s;
  &.dimmed { opacity: 0.15; }
  &.selected rect { stroke: $primary; stroke-width: 2; }
  &:hover rect { stroke: $primary; stroke-width: 1.5; }
}

.detail-section { display: flex; flex-direction: column; gap: 12px; }
.detail-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; .card-actions { margin-left: auto; display: flex; gap: 4px; } }
.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }
.info-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  .info-item { display: flex; justify-content: space-between; padding: 5px 0; font-size: 12px; border-bottom: 1px solid #f5f5f5;
    .lbl { color: #999; } .val { font-weight: 500; }
  }
}
.data-table { width: 100%; font-size: 12px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; }
  .link { color: $primary; cursor: pointer; &:hover { text-decoration: underline; } } .muted { color: #aaa; }
}
.dir-in { color: #2e7d32; font-size: 11px; } .dir-out { color: #1967d2; font-size: 11px; }
.type-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.copy { background: #e6f7ff; color: #1890ff; } &.etl { background: #fff7e6; color: #fa8c16; }
  &.transform { background: #f9f0ff; color: #722ed1; } &.view { background: #e6fffb; color: #13c2c2; }
}
</style>
