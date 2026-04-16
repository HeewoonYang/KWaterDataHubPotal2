<template>
  <div class="knowledge-graph-page">
    <div class="page-header">
      <h2>지식그래프 / 온톨로지*</h2>
      <p>K-water 데이터 자산 간 관계를 그래프로 탐색합니다. 노드를 드래그하거나 휠로 줌합니다.</p>
    </div>

    <!-- 필터 + 검색 + 컨트롤 -->
    <div class="toolbar">
      <div class="filter-chips">
        <button v-for="f in filterList" :key="f.key" class="chip" :class="{ active: filters[f.key] }"
          :style="{ '--chip-color': f.color }" @click="toggleFilter(f.key)">
          {{ f.icon }} {{ f.label }}
        </button>
      </div>
      <div class="toolbar-right">
        <input type="text" v-model="searchQuery" placeholder="노드 검색..." class="search-input" @input="onSearch" />
        <button class="ctrl-btn theme-toggle" :class="{ dark: isDark }" @click="isDark = !isDark" :title="isDark ? 'Light Mode' : 'Dark Mode'">
          {{ isDark ? '\u2600\uFE0F' : '\uD83C\uDF19' }}
        </button>
        <button class="ctrl-btn" @click="zoomGraph(1.3)" title="확대">+</button>
        <button class="ctrl-btn" @click="zoomGraph(0.7)" title="축소">-</button>
        <button class="ctrl-btn" @click="fitGraph" title="맞춤">Fit</button>
        <button class="ctrl-btn" @click="resetGraph" title="초기화">Reset</button>
        <span class="stats">{{ visibleNodeCount }}노드 / {{ visibleEdgeCount }}엣지</span>
      </div>
    </div>

    <!-- 그래프 + 상세 패널 -->
    <div class="graph-layout" :class="{ 'dark-mode': isDark }">
      <div class="canvas-wrap" ref="wrapRef">
        <canvas ref="canvasRef"></canvas>
      </div>
      <div class="side-panel" :class="{ open: !!selectedNode || !!selectedEdge }">
        <!-- 노드 상세 -->
        <template v-if="selectedNode">
          <div class="panel-header">
            <span class="panel-icon">{{ selectedNode.icon }}</span>
            <div>
              <div class="panel-title">{{ selectedNode.label }}</div>
              <div class="panel-sub">{{ selectedNode.detail?.ontology || selectedNode.type }}</div>
            </div>
            <button class="panel-close" @click="selectedNode = null"><CloseOutlined /></button>
          </div>
          <!-- 품질 배지 (데이터셋만) -->
          <div class="panel-quality" v-if="selectedNode.detail?.quality">
            <div class="quality-bar">
              <div class="quality-fill" :style="{ width: selectedNode.detail.quality, background: qualityColor(selectedNode.detail.quality) }"></div>
            </div>
            <span class="quality-label">품질 {{ selectedNode.detail.quality }}</span>
          </div>
          <!-- 바로가기 버튼 -->
          <div class="panel-actions">
            <button v-if="selectedNode.type === 'dataset'" class="action-btn catalog" @click="goToCatalog(selectedNode)">
              <DatabaseOutlined /> 카탈로그 상세
            </button>
            <button v-if="selectedNode.type === 'system'" class="action-btn pipeline" @click="goToPipeline(selectedNode)">
              <ApiOutlined /> 수집 파이프라인
            </button>
            <button v-if="selectedNode.type === 'metric'" class="action-btn dashboard" @click="goToDashboard()">
              <DashboardOutlined /> 대시보드
            </button>
            <button v-if="selectedNode.type === 'dataset' || selectedNode.type === 'system'" class="action-btn lineage" @click="goToLineage(selectedNode)">
              <BranchesOutlined /> 데이터리니지 보기
            </button>
            <button class="action-btn impact" :class="{ active: impactMode }" @click="toggleImpact(selectedNode)">
              <ThunderboltOutlined /> {{ impactMode ? '영향도 해제' : '영향도 분석' }}
            </button>
          </div>
          <div class="panel-section">
            <div class="panel-section-title">속성</div>
            <div v-for="(val, key) in filteredDetail" :key="String(key)" class="info-row">
              <span class="info-label">{{ detailLabel(String(key)) }}</span>
              <span class="info-value">{{ val }}</span>
            </div>
          </div>
          <!-- 영향도 분석 결과 -->
          <div class="panel-section" v-if="impactMode && impactNodes.length > 0">
            <div class="panel-section-title">영향 범위 ({{ impactNodes.length }}개 노드)</div>
            <div v-for="imp in impactNodes" :key="imp.id" class="conn-item" @click="focusNode(imp.id)">
              <span class="conn-dot" :style="{ background: nodeColors[imp.type] }"></span>
              <span class="conn-name">{{ imp.label }}</span>
              <span class="impact-depth">depth {{ imp.depth }}</span>
            </div>
          </div>
          <div class="panel-section">
            <div class="panel-section-title">연결 ({{ connections.length }})</div>
            <div v-for="conn in connections" :key="conn.id" class="conn-item" @click="focusNode(conn.id)">
              <span class="conn-dot" :style="{ background: nodeColors[conn.type] }"></span>
              <span class="conn-name">{{ conn.label }}</span>
              <span class="conn-rel">{{ conn.rel }}</span>
            </div>
          </div>
        </template>
        <!-- 엣지 상세 -->
        <template v-else-if="selectedEdge">
          <div class="panel-header">
            <span class="panel-icon" style="font-size:18px">&#8594;</span>
            <div>
              <div class="panel-title">{{ selectedEdge.label }}</div>
              <div class="panel-sub">엣지 (관계)</div>
            </div>
            <button class="panel-close" @click="selectedEdge = null"><CloseOutlined /></button>
          </div>
          <div class="panel-section">
            <div class="panel-section-title">관계 정보</div>
            <div class="info-row"><span class="info-label">관계명</span><span class="info-value">{{ selectedEdge.label }}</span></div>
            <div class="info-row">
              <span class="info-label">출발 노드</span>
              <span class="info-value edge-node-link" @click="focusNode(selectedEdge!.source)">{{ getNodeLabel(selectedEdge.source) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">도착 노드</span>
              <span class="info-value edge-node-link" @click="focusNode(selectedEdge!.target)">{{ getNodeLabel(selectedEdge.target) }}</span>
            </div>
            <div class="info-row"><span class="info-label">관계 유형</span><span class="info-value">{{ edgeTypeDesc(selectedEdge.label) }}</span></div>
          </div>
          <div class="panel-section">
            <div class="panel-section-title">연결 노드</div>
            <div class="conn-item" @click="focusNode(selectedEdge!.source)">
              <span class="conn-dot" :style="{ background: nodeColors[getNodeType(selectedEdge.source)] }"></span>
              <span class="conn-name">{{ getNodeLabel(selectedEdge.source) }}</span>
              <span class="conn-rel">source</span>
            </div>
            <div class="conn-item" @click="focusNode(selectedEdge!.target)">
              <span class="conn-dot" :style="{ background: nodeColors[getNodeType(selectedEdge.target)] }"></span>
              <span class="conn-name">{{ getNodeLabel(selectedEdge.target) }}</span>
              <span class="conn-rel">target</span>
            </div>
          </div>
        </template>
        <div v-else class="panel-placeholder">
          <NodeIndexOutlined class="placeholder-icon" />
          <p>노드 또는 엣지를 클릭하여<br/>상세 정보를 확인하세요</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { CloseOutlined, NodeIndexOutlined, DatabaseOutlined, ApiOutlined, DashboardOutlined, ThunderboltOutlined, BranchesOutlined } from '@ant-design/icons-vue'

const router = useRouter()

// ── 데이터 ──
const nodeColors: Record<string, string> = {
  facility: '#4caf50', system: '#ff9800', dataset: '#42a5f5', metric: '#ec407a', domain: '#ab47bc'
}
const filterList = [
  { key: 'facility', icon: '\uD83C\uDFED', label: '시설', color: '#4caf50' },
  { key: 'system', icon: '\u2699\uFE0F', label: '시스템', color: '#ff9800' },
  { key: 'dataset', icon: '\uD83D\uDCCA', label: '데이터셋', color: '#42a5f5' },
  { key: 'metric', icon: '\uD83D\uDCC8', label: '지표', color: '#ec407a' },
  { key: 'domain', icon: '\uD83C\uDF10', label: '도메인', color: '#ab47bc' },
]

interface GNode {
  id: string; label: string; type: string; icon: string; detail: Record<string, any>
  x: number; y: number; vx: number; vy: number; radius: number; visible: boolean; searchMatch: boolean
}
interface GEdge { source: string; target: string; label: string }

const rawNodes: Omit<GNode, 'x'|'y'|'vx'|'vy'|'radius'|'visible'|'searchMatch'>[] = [
  { id: 'soyang', label: '소양강댐', type: 'facility', icon: '\uD83C\uDFD4\uFE0F', detail: { ontology: 'kw:WaterFacility', desc: '다목적댐 (1973)', region: '강원 춘천', datasets: 8, grade: '2등급' } },
  { id: 'chungju', label: '충주댐', type: 'facility', icon: '\uD83C\uDFDE\uFE0F', detail: { ontology: 'kw:WaterFacility', desc: '다목적댐 (1985)', region: '충북 충주', datasets: 6, grade: '2등급' } },
  { id: 'rwis', label: 'RWIS', type: 'system', icon: '\uD83D\uDCE1', detail: { ontology: 'kw:System', desc: '실시간 수자원정보시스템', protocol: 'CDC/REST', status: '정상' } },
  { id: 'hdaps', label: 'HDAPS', type: 'system', icon: '\u26A1', detail: { ontology: 'kw:System', desc: '수력발전 관리시스템', protocol: 'Batch', status: '정상' } },
  { id: 'scada', label: 'SCADA', type: 'system', icon: '\uD83D\uDDA5\uFE0F', detail: { ontology: 'kw:System', desc: '원격감시제어', protocol: 'OPC-UA', status: '정상' } },
  { id: 'kma', label: '기상청 API', type: 'system', icon: '\uD83C\uDF24\uFE0F', detail: { ontology: 'kw:ExternalAPI', desc: '기상청 공공데이터', protocol: 'REST API', status: '지연' } },
  { id: 'ds_level', label: '수위관측', type: 'dataset', icon: '\uD83C\uDF0A', detail: { ontology: 'kw:WaterLevelObs', records: '1,234,567', quality: '94.2%', method: 'CDC 실시간' } },
  { id: 'ds_flow', label: '유량관측', type: 'dataset', icon: '\uD83D\uDCA7', detail: { ontology: 'kw:FlowRateObs', records: '987,654', quality: '92.8%', method: 'CDC 실시간' } },
  { id: 'ds_weather', label: '기상데이터', type: 'dataset', icon: '\uD83C\uDF21\uFE0F', detail: { ontology: 'kw:WeatherObs', records: '365,000', quality: '91.5%', method: 'API 시간별' } },
  { id: 'ds_power', label: '발전량', type: 'dataset', icon: '\u26A1', detail: { ontology: 'kw:PowerGeneration', records: '23,456', quality: '97.1%', method: '배치 일별' } },
  { id: 'ds_discharge', label: '방류량', type: 'dataset', icon: '\uD83D\uDEBF', detail: { ontology: 'kw:DischargeObs', records: '456,789', quality: '89.3%', method: 'CDC 실시간' } },
  { id: 'm_inflow', label: '유입량', type: 'metric', icon: '\uD83D\uDCC8', detail: { ontology: 'kw:InflowMetric', unit: 'm\u00B3/s', threshold: '> 500', alert: '주의' } },
  { id: 'm_waterlvl', label: '수위', type: 'metric', icon: '\uD83D\uDCCF', detail: { ontology: 'kw:WaterLevelMetric', unit: 'EL.m', threshold: '> 193.5', alert: '정상' } },
  { id: 'm_powergen', label: '발전출력', type: 'metric', icon: '\uD83D\uDD0B', detail: { ontology: 'kw:PowerMetric', unit: 'MW', threshold: '> 200', alert: '정상' } },
  { id: 'dom_water', label: '수자원', type: 'domain', icon: '\uD83D\uDC8E', detail: { ontology: 'kw:WaterDomain', desc: '수자원 관리 도메인', subDomains: '댐, 하천, 저수지', assets: 42 } },
]
const edges: GEdge[] = [
  { source: 'dom_water', target: 'soyang', label: 'hasFacility' },
  { source: 'dom_water', target: 'chungju', label: 'hasFacility' },
  { source: 'soyang', target: 'rwis', label: 'connectedTo' },
  { source: 'soyang', target: 'hdaps', label: 'connectedTo' },
  { source: 'soyang', target: 'scada', label: 'monitoredBy' },
  { source: 'chungju', target: 'rwis', label: 'connectedTo' },
  { source: 'chungju', target: 'hdaps', label: 'connectedTo' },
  { source: 'rwis', target: 'ds_level', label: 'produces' },
  { source: 'rwis', target: 'ds_flow', label: 'produces' },
  { source: 'rwis', target: 'ds_discharge', label: 'produces' },
  { source: 'kma', target: 'ds_weather', label: 'provides' },
  { source: 'hdaps', target: 'ds_power', label: 'produces' },
  { source: 'scada', target: 'ds_level', label: 'feeds' },
  { source: 'ds_level', target: 'm_waterlvl', label: 'measures' },
  { source: 'ds_flow', target: 'm_inflow', label: 'measures' },
  { source: 'ds_power', target: 'm_powergen', label: 'measures' },
  { source: 'ds_level', target: 'm_inflow', label: 'computes' },
  { source: 'ds_weather', target: 'm_inflow', label: 'influences' },
]

// ── State ──
const canvasRef = ref<HTMLCanvasElement | null>(null)
const wrapRef = ref<HTMLDivElement | null>(null)
const searchQuery = ref('')
const isDark = ref(true)
const selectedNode = ref<GNode | null>(null)
const selectedEdge = ref<GEdge | null>(null)
const filters = reactive<Record<string, boolean>>({ facility: true, system: true, dataset: true, metric: true, domain: true })

let nodes: GNode[] = []
let particles: { edgeIdx: number; t: number; speed: number }[] = []
let state = { zoom: 1, panX: 0, panY: 0, dragging: null as GNode | null, dragOffX: 0, dragOffY: 0, isPanning: false, panStartX: 0, panStartY: 0, hoveredNode: null as GNode | null, simAlpha: 1 }
let animFrame = 0
let w = 900, h = 500

const visibleNodeCount = ref(15)
const visibleEdgeCount = ref(18)

const filteredDetail = computed(() => {
  if (!selectedNode.value) return {}
  const d = { ...selectedNode.value.detail }
  delete d.ontology
  return d
})

const connections = computed(() => {
  if (!selectedNode.value) return []
  const result: { id: string; label: string; type: string; rel: string }[] = []
  edges.forEach(e => {
    let otherId: string | null = null, rel = e.label
    if (e.source === selectedNode.value!.id) otherId = e.target
    else if (e.target === selectedNode.value!.id) otherId = e.source
    if (!otherId) return
    const other = nodes.find(n => n.id === otherId)
    if (other) result.push({ id: other.id, label: other.label, type: other.type, rel })
  })
  return result
})

function getNodeLabel(id: string): string { return nodes.find(n => n.id === id)?.label || id }
function getNodeType(id: string): string { return nodes.find(n => n.id === id)?.type || 'system' }
function edgeTypeDesc(label: string): string {
  const m: Record<string, string> = {
    hasFacility: '도메인-시설 소유 관계', connectedTo: '시설-시스템 연결', monitoredBy: '모니터링 관계',
    produces: '데이터 생산', provides: '데이터 제공', feeds: '데이터 입력',
    measures: '지표 측정', computes: '지표 계산', influences: '영향 관계',
  }
  return m[label] || '관계'
}
function detailLabel(key: string): string {
  const m: Record<string, string> = { desc: '설명', region: '지역', datasets: '데이터셋', grade: '보안등급', protocol: '프로토콜', status: '상태', records: '레코드 수', quality: '품질점수', method: '수집방식', unit: '단위', threshold: '임계치', alert: '알림', subDomains: '하위도메인', assets: '데이터자산' }
  return m[key] || key
}

// ── Canvas 렌더링 (8080과 동일한 물리 시뮬레이션) ──
function initGraph() {
  const canvas = canvasRef.value!
  const wrap = wrapRef.value!
  const ctx = canvas.getContext('2d')!
  const dpr = window.devicePixelRatio || 1

  w = wrap.clientWidth
  h = wrap.clientHeight || 500

  // 노드 초기화
  nodes = rawNodes.map(n => ({
    ...n,
    x: w / 2 + (Math.random() - 0.5) * w * 0.6,
    y: h / 2 + (Math.random() - 0.5) * h * 0.6,
    vx: 0, vy: 0,
    radius: n.type === 'domain' ? 28 : n.type === 'facility' ? 26 : n.type === 'system' ? 22 : n.type === 'dataset' ? 20 : 18,
    visible: true, searchMatch: true,
  }))

  // 파티클 초기화
  particles = []
  edges.forEach((_, i) => {
    particles.push({ edgeIdx: i, t: Math.random(), speed: 0.002 + Math.random() * 0.003 })
    if (Math.random() > 0.5) particles.push({ edgeIdx: i, t: Math.random(), speed: 0.001 + Math.random() * 0.002 })
  })

  function resize() {
    w = wrap.clientWidth; h = wrap.clientHeight || 500
    canvas.width = w * dpr; canvas.height = h * dpr
    canvas.style.width = w + 'px'; canvas.style.height = h + 'px'
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  resize()
  new ResizeObserver(resize).observe(wrap)

  function simulate() {
    if (state.simAlpha < 0.001) return
    state.simAlpha *= 0.995
    const vis = nodes.filter(n => n.visible)
    for (let i = 0; i < vis.length; i++) {
      for (let j = i + 1; j < vis.length; j++) {
        const a = vis[i], b = vis[j]
        const dx = b.x - a.x, dy = b.y - a.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const force = 8000 * state.simAlpha / (dist * dist)
        const fx = dx / dist * force, fy = dy / dist * force
        if (a !== state.dragging) { a.vx -= fx; a.vy -= fy }
        if (b !== state.dragging) { b.vx += fx; b.vy += fy }
      }
    }
    edges.forEach(e => {
      const a = nodes.find(n => n.id === e.source), b = nodes.find(n => n.id === e.target)
      if (!a || !b || !a.visible || !b.visible) return
      const dx = b.x - a.x, dy = b.y - a.y, dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - 120) * 0.04 * state.simAlpha
      const fx = dx / dist * force, fy = dy / dist * force
      if (a !== state.dragging) { a.vx += fx; a.vy += fy }
      if (b !== state.dragging) { b.vx -= fx; b.vy -= fy }
    })
    vis.forEach(n => {
      if (n === state.dragging) return
      n.vx += (w / 2 - n.x) * 0.0005 * state.simAlpha
      n.vy += (h / 2 - n.y) * 0.0005 * state.simAlpha
      n.vx *= 0.85; n.vy *= 0.85
      n.x += n.vx; n.y += n.vy
      n.x = Math.max(n.radius, Math.min(w - n.radius, n.x))
      n.y = Math.max(n.radius, Math.min(h - n.radius, n.y))
    })
  }

  function lighten(hex: string, pct: number): string {
    let r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16)
    r = Math.min(255, r + pct); g = Math.min(255, g + pct); b = Math.min(255, b + pct)
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
  }

  function render() {
    ctx.save()
    ctx.clearRect(0, 0, w, h)

    // 배경
    ctx.fillStyle = isDark.value ? '#1a1d23' : '#f8fafb'
    ctx.fillRect(0, 0, w, h)

    ctx.translate(state.panX, state.panY)
    ctx.scale(state.zoom, state.zoom)

    // 엣지
    edges.forEach(e => {
      const a = nodes.find(n => n.id === e.source), b = nodes.find(n => n.id === e.target)
      if (!a || !b || !a.visible || !b.visible) return
      const isSel = selectedNode.value && (e.source === selectedNode.value.id || e.target === selectedNode.value.id)
      const isHov = state.hoveredNode && (e.source === state.hoveredNode.id || e.target === state.hoveredNode.id)
      const mx = (a.x + b.x) / 2 + (b.y - a.y) * 0.08, my = (a.y + b.y) / 2 - (b.x - a.x) * 0.08
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo(mx, my, b.x, b.y)
      const dk = isDark.value
      ctx.strokeStyle = isSel || isHov ? (dk ? 'rgba(100,181,246,0.6)' : 'rgba(0,102,204,0.5)') : (dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)')
      ctx.lineWidth = isSel || isHov ? 2 : 1; ctx.stroke()
      // 화살표
      const angle = Math.atan2(b.y - my, b.x - mx)
      const ax = b.x - b.radius * Math.cos(angle), ay = b.y - b.radius * Math.sin(angle)
      ctx.beginPath(); ctx.moveTo(ax, ay)
      ctx.lineTo(ax - 8 * Math.cos(angle - 0.35), ay - 8 * Math.sin(angle - 0.35))
      ctx.lineTo(ax - 8 * Math.cos(angle + 0.35), ay - 8 * Math.sin(angle + 0.35)); ctx.closePath()
      ctx.fillStyle = isSel || isHov ? (dk ? 'rgba(100,181,246,0.5)' : 'rgba(0,102,204,0.4)') : (dk ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'); ctx.fill()
      if (isSel) { ctx.font = '9px sans-serif'; ctx.fillStyle = dk ? 'rgba(100,181,246,0.7)' : 'rgba(0,102,204,0.7)'; ctx.textAlign = 'center'; ctx.fillText(e.label, mx, my - 6) }
    })

    // 파티클
    particles.forEach(p => {
      const e = edges[p.edgeIdx]
      const a = nodes.find(n => n.id === e.source), b = nodes.find(n => n.id === e.target)
      if (!a || !b || !a.visible || !b.visible) return
      p.t += p.speed; if (p.t > 1) p.t = 0
      const mx = (a.x + b.x) / 2 + (b.y - a.y) * 0.08, my = (a.y + b.y) / 2 - (b.x - a.x) * 0.08
      const t = p.t
      const px = (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * mx + t * t * b.x
      const py = (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * my + t * t * b.y
      ctx.beginPath(); ctx.arc(px, py, 1.5, 0, Math.PI * 2); ctx.fillStyle = isDark.value ? 'rgba(100,181,246,0.4)' : 'rgba(0,102,204,0.3)'; ctx.fill()
    })

    // 노드
    nodes.forEach(n => {
      if (!n.visible) return
      const col = nodeColors[n.type]
      const isSel = selectedNode.value === n, isHov = state.hoveredNode === n
      const dim = !n.searchMatch
      const isImpacted = impactMode.value && impactNodeIds.has(n.id)
      const dimByImpact = impactMode.value && !isImpacted

      // 영향도 모드 → 영향 받지 않는 노드 흐리게
      if (dimByImpact && !isSel) {
        ctx.globalAlpha = 0.15
      }

      // 영향도 하이라이트 (빨간 펄스 링)
      if (isImpacted && !isSel) {
        ctx.beginPath(); ctx.arc(n.x, n.y, n.radius + 8, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(245,34,45,0.5)'; ctx.lineWidth = 2; ctx.setLineDash([4, 3]); ctx.stroke(); ctx.setLineDash([])
      }

      // 글로우
      if (isSel || isHov) {
        ctx.beginPath(); ctx.arc(n.x, n.y, n.radius + 12, 0, Math.PI * 2)
        const glow = ctx.createRadialGradient(n.x, n.y, n.radius, n.x, n.y, n.radius + 12)
        glow.addColorStop(0, col + '40'); glow.addColorStop(1, col + '00'); ctx.fillStyle = glow; ctx.fill()
      }
      if (isSel) { ctx.beginPath(); ctx.arc(n.x, n.y, n.radius + 3, 0, Math.PI * 2); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke() }
      // 원
      ctx.beginPath(); ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2)
      const grad = ctx.createRadialGradient(n.x - n.radius * 0.3, n.y - n.radius * 0.3, 0, n.x, n.y, n.radius)
      grad.addColorStop(0, lighten(col, 40)); grad.addColorStop(1, col)
      const dkn = isDark.value
      ctx.fillStyle = (dim || dimByImpact) ? (dkn ? 'rgba(60,70,80,0.5)' : 'rgba(200,200,200,0.4)') : grad; ctx.fill()
      ctx.strokeStyle = (dim || dimByImpact) ? (dkn ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)') : 'rgba(255,255,255,0.5)'; ctx.lineWidth = 1.5; ctx.stroke()
      // 아이콘 + 라벨
      ctx.font = (n.radius * 0.65) + 'px serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(n.icon, n.x, n.y - 1)
      ctx.font = '600 10px "Pretendard", sans-serif'; ctx.textBaseline = 'top'
      ctx.fillStyle = (dim || dimByImpact) ? (dkn ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.15)') : (dkn ? 'rgba(255,255,255,0.85)' : '#333')
      ctx.fillText(n.label, n.x, n.y + n.radius + 5)

      // 품질 배지 (데이터셋만, 우상단)
      if (n.detail?.quality && !dimByImpact) {
        const qVal = parseFloat(n.detail.quality)
        const qColor = qVal >= 95 ? '#28A745' : qVal >= 85 ? '#0066CC' : qVal >= 70 ? '#fa8c16' : '#DC3545'
        const bx = n.x + n.radius * 0.6, by = n.y - n.radius * 0.6
        ctx.beginPath(); ctx.arc(bx, by, 9, 0, Math.PI * 2)
        ctx.fillStyle = qColor; ctx.fill()
        ctx.strokeStyle = dkn ? '#1a1d23' : '#fff'; ctx.lineWidth = 1.5; ctx.stroke()
        ctx.font = 'bold 7px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.fillStyle = '#fff'; ctx.fillText(Math.round(qVal) + '', bx, by)
      }

      ctx.globalAlpha = 1
    })

    ctx.restore()
    simulate()
    updateStats()
    animFrame = requestAnimationFrame(render)
  }

  // 마우스 이벤트
  function toGraph(mx: number, my: number) { return { x: (mx - state.panX) / state.zoom, y: (my - state.panY) / state.zoom } }
  function findAt(mx: number, my: number): GNode | null {
    const p = toGraph(mx, my)
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i]; if (!n.visible) continue
      if ((p.x - n.x) ** 2 + (p.y - n.y) ** 2 <= (n.radius + 4) ** 2) return n
    }
    return null
  }

  // 클릭 판정용
  let mouseDownX = 0, mouseDownY = 0
  let mouseDownNode: GNode | null = null  // mousedown 시점에 잡은 노드 기억

  // 엣지 위 클릭 감지
  function findEdgeAt(mx: number, my: number): GEdge | null {
    const p = toGraph(mx, my)
    for (const e of edges) {
      const a = nodes.find(n => n.id === e.source), b = nodes.find(n => n.id === e.target)
      if (!a || !b || !a.visible || !b.visible) continue
      const cx = (a.x + b.x) / 2 + (b.y - a.y) * 0.08, cy = (a.y + b.y) / 2 - (b.x - a.x) * 0.08
      for (let t = 0; t <= 1; t += 0.05) {
        const bx = (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * cx + t * t * b.x
        const by = (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * cy + t * t * b.y
        if ((p.x - bx) ** 2 + (p.y - by) ** 2 < 150) return e
      }
    }
    return null
  }

  canvas.addEventListener('mousedown', (e: MouseEvent) => {
    const r = canvas.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top
    mouseDownX = mx; mouseDownY = my
    const node = findAt(mx, my)
    mouseDownNode = node
    if (node) {
      const p = toGraph(mx, my)
      state.dragging = node; state.dragOffX = p.x - node.x; state.dragOffY = p.y - node.y; state.simAlpha = 0.3
    } else {
      state.isPanning = true; state.panStartX = mx - state.panX; state.panStartY = my - state.panY
    }
  })

  canvas.addEventListener('mousemove', (e: MouseEvent) => {
    const r = canvas.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top
    if (state.dragging) {
      const p = toGraph(mx, my)
      state.dragging.x = p.x - state.dragOffX; state.dragging.y = p.y - state.dragOffY
      state.dragging.vx = 0; state.dragging.vy = 0
    } else if (state.isPanning) {
      state.panX = mx - state.panStartX; state.panY = my - state.panStartY
    } else {
      const hovered = findAt(mx, my)
      state.hoveredNode = hovered
      canvas.style.cursor = hovered ? 'pointer' : (findEdgeAt(mx, my) ? 'pointer' : 'grab')
    }
  })

  canvas.addEventListener('mouseup', (e: MouseEvent) => {
    const r = canvas.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top
    const moveDist = Math.sqrt((mx - mouseDownX) ** 2 + (my - mouseDownY) ** 2)
    const isClick = moveDist < 8  // 8px 미만 → 클릭

    if (isClick) {
      if (mouseDownNode) {
        // mousedown 때 잡았던 노드를 바로 선택 (위치 변동 무관)
        selectedNode.value = mouseDownNode
        selectedEdge.value = null
      } else {
        // 빈 영역에서 클릭 → 엣지 확인
        const edge = findEdgeAt(mx, my)
        if (edge) {
          selectedEdge.value = edge
          selectedNode.value = null
        } else {
          selectedNode.value = null
          selectedEdge.value = null
        }
      }
    }

    state.dragging = null
    state.isPanning = false
    mouseDownNode = null
  })

  canvas.addEventListener('mouseleave', () => {
    state.dragging = null; state.isPanning = false; state.hoveredNode = null; mouseDownNode = null
  })
  canvas.addEventListener('wheel', (e: WheelEvent) => {
    e.preventDefault(); const r = canvas.getBoundingClientRect(); const mx = e.clientX - r.left, my = e.clientY - r.top
    const factor = e.deltaY > 0 ? 0.9 : 1.1; const nz = Math.max(0.3, Math.min(4, state.zoom * factor))
    state.panX = mx - (mx - state.panX) * (nz / state.zoom); state.panY = my - (my - state.panY) * (nz / state.zoom); state.zoom = nz
  }, { passive: false })

  render()
}

function updateStats() {
  visibleNodeCount.value = nodes.filter(n => n.visible).length
  visibleEdgeCount.value = edges.filter(e => { const a = nodes.find(n => n.id === e.source), b = nodes.find(n => n.id === e.target); return a?.visible && b?.visible }).length
}

// ── 외부 컨트롤 ──
function toggleFilter(key: string) {
  filters[key] = !filters[key]
  nodes.forEach(n => { n.visible = filters[n.type] })
  state.simAlpha = 0.5
}
function onSearch() {
  const q = searchQuery.value.toLowerCase()
  nodes.forEach(n => { n.searchMatch = !q || n.label.toLowerCase().includes(q) || n.id.includes(q) })
}
function zoomGraph(factor: number) {
  const nz = Math.max(0.3, Math.min(4, state.zoom * factor))
  const cx = w / 2, cy = h / 2
  state.panX = cx - (cx - state.panX) * (nz / state.zoom); state.panY = cy - (cy - state.panY) * (nz / state.zoom); state.zoom = nz
}
function fitGraph() {
  const vis = nodes.filter(n => n.visible); if (!vis.length) return
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  vis.forEach(n => { minX = Math.min(minX, n.x - n.radius); maxX = Math.max(maxX, n.x + n.radius); minY = Math.min(minY, n.y - n.radius); maxY = Math.max(maxY, n.y + n.radius) })
  const z = Math.min(w / (maxX - minX + 60), h / (maxY - minY + 60), 2)
  state.zoom = z; state.panX = (w - (minX + maxX) * z) / 2; state.panY = (h - (minY + maxY) * z) / 2
}
function resetGraph() { state.zoom = 1; state.panX = 0; state.panY = 0; state.simAlpha = 1; selectedNode.value = null; selectedEdge.value = null; impactMode.value = false; impactNodeIds.clear(); Object.keys(filters).forEach(k => { filters[k] = true }); nodes.forEach(n => { n.visible = true; n.searchMatch = true }); searchQuery.value = '' }

// ── 영향도 분석 ──
const impactMode = ref(false)
const impactNodeIds = reactive(new Set<string>())

const impactNodes = computed(() => {
  if (!impactMode.value) return []
  const result: { id: string; label: string; type: string; depth: number }[] = []
  impactNodeIds.forEach(nid => {
    const n = nodes.find(nd => nd.id === nid)
    if (n && n.id !== selectedNode.value?.id) result.push({ id: n.id, label: n.label, type: n.type, depth: 1 })
  })
  return result
})

function toggleImpact(node: GNode) {
  if (impactMode.value) {
    impactMode.value = false
    impactNodeIds.clear()
    return
  }
  impactMode.value = true
  impactNodeIds.clear()
  // BFS: downstream 영향 범위 탐색
  const visited = new Set<string>()
  const queue: { id: string; depth: number }[] = [{ id: node.id, depth: 0 }]
  while (queue.length > 0) {
    const cur = queue.shift()!
    if (visited.has(cur.id)) continue
    visited.add(cur.id)
    impactNodeIds.add(cur.id)
    // 이 노드에서 나가는 엣지 탐색
    edges.forEach(e => {
      if (e.source === cur.id && !visited.has(e.target)) queue.push({ id: e.target, depth: cur.depth + 1 })
    })
  }
}

// ── 카탈로그/파이프라인/대시보드 연계 ──
function goToCatalog(node: GNode) {
  // 데이터셋명으로 카탈로그 검색
  router.push({ path: '/portal/catalog/search', query: { keyword: node.label } })
}
function goToLineage(node: GNode) {
  router.push({ path: '/portal/catalog/lineage', query: { search: node.label } })
}
function goToPipeline(node: GNode) {
  router.push({ path: '/portal/monitoring', query: { system: node.id } })
}
function goToDashboard() {
  router.push('/portal')
}
function qualityColor(q: string): string {
  const val = parseFloat(q)
  if (val >= 95) return '#28A745'
  if (val >= 85) return '#0066CC'
  if (val >= 70) return '#fa8c16'
  return '#DC3545'
}

function focusNode(id: string) {
  const n = nodes.find(nd => nd.id === id); if (!n) return
  selectedNode.value = n; state.panX = w / 2 - n.x * state.zoom; state.panY = h / 2 - n.y * state.zoom
}

onMounted(initGraph)
onUnmounted(() => { if (animFrame) cancelAnimationFrame(animFrame) })
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.knowledge-graph-page { padding-bottom: 20px; }
.breadcrumb { font-size: 12px; color: #999; margin-bottom: 12px; a { color: $primary; text-decoration: none; } }
.page-header { margin-bottom: 12px; h2 { margin: 0 0 4px; font-size: 20px; } p { margin: 0; color: #666; font-size: 13px; } }

.toolbar {
  display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding: 8px 12px;
  background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; flex-wrap: wrap;
  .filter-chips { display: flex; gap: 4px; }
  .chip {
    padding: 4px 10px; border: 1.5px solid #e0e0e0; border-radius: 14px; font-size: 11px; cursor: pointer;
    background: #fff; transition: all 0.15s;
    &.active { border-color: var(--chip-color); background: color-mix(in srgb, var(--chip-color) 10%, white); color: var(--chip-color); font-weight: 600; }
  }
  .toolbar-right { display: flex; gap: 6px; align-items: center; margin-left: auto; }
  .search-input { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; width: 150px; &:focus { outline: none; border-color: $primary; } }
  .ctrl-btn { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 11px; cursor: pointer; background: #fff; &:hover { border-color: $primary; color: $primary; }
    &.theme-toggle { font-size: 14px; padding: 2px 8px; &.dark { background: #2d2f36; border-color: #555; color: #ffd54f; } }
  }
  .stats { font-size: 11px; color: #999; }
}

.graph-layout {
  display: flex; gap: 0; border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; background: #f8fafb;
  height: 560px;
  transition: background 0.3s, border-color 0.3s;
  &.dark-mode { background: #1a1d23; border-color: #333; }
}
.canvas-wrap { flex: 1; min-width: 0; height: 100%; position: relative; canvas { display: block; width: 100%; height: 100%; } }
.side-panel {
  width: 0; min-width: 0; height: 100%; overflow: hidden;
  transition: width 0.25s ease, min-width 0.25s ease, background 0.3s, border-color 0.3s, color 0.3s;
  background: #fff; border-left: 1px solid #e8e8e8;
  .dark-mode & { background: #22252b; border-left-color: #333; color: #e0e0e0; }
  &.open { width: 300px; min-width: 300px; overflow-y: auto; }
  .panel-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 1px solid #f0f0f0;
    .dark-mode & { border-bottom-color: #333; }
    .panel-icon { font-size: 24px; }
    .panel-title { font-weight: 700; font-size: 15px; }
    .panel-sub { font-size: 11px; color: #999; font-family: monospace; }
    .panel-close { margin-left: auto; background: none; border: none; cursor: pointer; color: #999; &:hover { color: #333; } }
  }
  .panel-section { padding: 12px 16px; border-bottom: 1px solid #f5f5f5; .dark-mode & { border-bottom-color: #333; } }
  .panel-section-title { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; }
  .info-row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 12px;
    .info-label { color: #999; } .info-value { color: #333; font-weight: 500; .dark-mode & { color: #ddd; } }
  }
  .conn-item { display: flex; align-items: center; gap: 6px; padding: 5px 0; font-size: 12px; cursor: pointer; &:hover { color: $primary; }
    .conn-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .conn-name { flex: 1; }
    .conn-rel { font-size: 10px; color: #bbb; font-family: monospace; }
    .edge-node-link { cursor: pointer; color: $primary; &:hover { text-decoration: underline; } }
  }
  // 품질 바
  .panel-quality { padding: 8px 16px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f0f0f0;
    .quality-bar { flex: 1; height: 6px; background: #e8e8e8; border-radius: 3px; overflow: hidden;
      .quality-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
    }
    .quality-label { font-size: 11px; font-weight: 700; color: #333; white-space: nowrap; .dark-mode & { color: #ddd; } }
  }
  // 바로가기 버튼
  .panel-actions { padding: 10px 16px; display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid #f0f0f0;
    .dark-mode & { border-bottom-color: #333; }
    .action-btn {
      padding: 5px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 11px; cursor: pointer; background: #fff;
      display: flex; align-items: center; gap: 4px; transition: all 0.15s;
      .dark-mode & { background: #2d2f36; border-color: #444; color: #ccc; }
      &:hover { border-color: $primary; color: $primary; }
      &.catalog { color: #42a5f5; border-color: #42a5f5; &:hover { background: #e3f2fd; } }
      &.pipeline { color: #ff9800; border-color: #ff9800; &:hover { background: #fff3e0; } }
      &.dashboard { color: #9b59b6; border-color: #9b59b6; &:hover { background: #f3e5f5; } }
      &.lineage { color: #13c2c2; border-color: #13c2c2; &:hover { background: #e6fffb; } }
      &.impact { color: #f5222d; border-color: #f5222d; &:hover { background: #fff1f0; }
        &.active { background: #f5222d; color: #fff; .dark-mode & { background: #f5222d; color: #fff; } }
      }
    }
  }
  .impact-depth { font-size: 9px; color: #f5222d; background: #fff1f0; padding: 1px 5px; border-radius: 8px; margin-left: auto; }
  .panel-placeholder { padding: 40px 20px; text-align: center; color: #ccc;
    .placeholder-icon { font-size: 36px; margin-bottom: 8px; display: block; }
    p { font-size: 12px; }
  }
}
</style>
