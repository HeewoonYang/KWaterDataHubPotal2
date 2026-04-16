<template>
  <div class="onto-page">
    <div class="page-header">
      <h2>온톨로지 관리*</h2>
      <div class="header-actions">
        <button class="btn btn-sm btn-outline" @click="showImport = true"><ImportOutlined /> OWL 가져오기</button>
        <button class="btn btn-sm btn-outline" @click="showExport = true"><ExportOutlined /> OWL 내보내기</button>
        <button class="btn btn-sm btn-primary" @click="showAddClass = true"><PlusOutlined /> 클래스 추가</button>
      </div>
    </div>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-label">그래프DB 상태</div><div class="kpi-value green">정상</div><div class="kpi-sub">Neo4j 5.x</div></div>
      <div class="kpi-card"><div class="kpi-label">클래스 수</div><div class="kpi-value blue">142</div><div class="kpi-sub">최상위 8 / 하위 134</div></div>
      <div class="kpi-card"><div class="kpi-label">속성 수</div><div class="kpi-value purple">1,284</div><div class="kpi-sub">Data 948 / Object 336</div></div>
      <div class="kpi-card"><div class="kpi-label">관계 수</div><div class="kpi-value">3,456</div><div class="kpi-sub">활성 3,412 / 비활성 44</div></div>
    </div>

    <!-- 클래스 트리 + 상세 -->
    <div class="tree-detail-layout">
      <div class="tree-panel">
        <div class="tree-title"><ApartmentOutlined /> 클래스 계층 구조</div>
        <input type="text" v-model="treeSearch" placeholder="클래스 검색..." class="tree-search" />
        <div class="tree-body">
          <div class="tree-node root" @click="selectClass('owl:Thing')"><span class="caret">▼</span> <strong class="node-root">owl:Thing</strong> <span class="node-count">(142)</span></div>
          <div v-for="cls in filteredTree" :key="cls.id" class="tree-node level1" @click="selectClass(cls.id)">
            <span class="caret">{{ selectedClassId === cls.id ? '▼' : '▶' }}</span>
            <span class="node-icon">{{ cls.icon }}</span> <strong>{{ cls.name }}</strong> <span class="node-count">({{ cls.count }})</span>
            <div v-if="selectedClassId === cls.id && cls.children" class="tree-children">
              <div v-for="ch in cls.children" :key="ch" class="tree-node level2" :class="{ active: selectedSubClass === ch }" @click.stop="selectedSubClass = ch">{{ ch }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-panel">
        <!-- 클래스 기본 정보 -->
        <div class="detail-card">
          <div class="card-title">
            <FileTextOutlined /> 클래스 상세: <span class="highlight">{{ activeClass.name }} ({{ activeClass.eng }})</span>
            <div class="card-actions">
              <button class="btn btn-xs btn-outline" @click="showMsg('수정 모달')">수정</button>
              <button class="btn btn-xs btn-danger-outline" @click="showMsg('삭제 확인')">삭제</button>
            </div>
          </div>
          <div class="info-2col">
            <table class="info-table"><tbody>
              <tr><td class="lbl">클래스 URI</td><td class="mono">{{ activeClass.uri }}</td></tr>
              <tr><td class="lbl">네임스페이스</td><td class="mono">https://onto.kwater.or.kr/</td></tr>
              <tr><td class="lbl">상위 클래스</td><td class="link">{{ activeClass.parent }}</td></tr>
              <tr><td class="lbl">하위 클래스</td><td>{{ activeClass.children }}</td></tr>
            </tbody></table>
            <table class="info-table"><tbody>
              <tr><td class="lbl">인스턴스 수</td><td><strong class="blue">{{ activeClass.instances }}</strong>개</td></tr>
              <tr><td class="lbl">관계 수</td><td>{{ activeClass.relations }}</td></tr>
              <tr><td class="lbl">등록일</td><td>2025-06-20</td></tr>
              <tr><td class="lbl">최종수정</td><td>2026-02-15 09:30</td></tr>
            </tbody></table>
          </div>
        </div>

        <!-- Data Properties -->
        <div class="detail-card">
          <div class="card-title"><TagsOutlined /> 데이터 속성 (Data Properties) <button class="btn btn-xs btn-outline" @click="showMsg('속성 추가')">+ 속성 추가</button></div>
          <table class="data-table">
            <thead><tr><th>속성명</th><th>URI</th><th>데이터 타입</th><th>카디널리티</th><th>설명</th><th>표준용어</th></tr></thead>
            <tbody>
              <tr v-for="p in activeClass.dataProps" :key="p.name">
                <td><strong>{{ p.name }}</strong></td>
                <td class="mono">{{ p.uri }}</td>
                <td><span class="type-badge" :class="p.typeColor">{{ p.type }}</span></td>
                <td>{{ p.cardinality }}</td>
                <td>{{ p.desc }}</td>
                <td><span v-if="p.term" class="term-link" @click="$router.push('/admin/standard/terms')">{{ p.term }}</span><span v-else class="muted">-</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Object Properties -->
        <div class="detail-card">
          <div class="card-title"><LinkOutlined /> 관계 속성 (Object Properties) <button class="btn btn-xs btn-outline" @click="showMsg('관계 추가')">+ 관계 추가</button></div>
          <table class="data-table">
            <thead><tr><th>관계명</th><th>URI</th><th>방향</th><th>대상 클래스</th><th>카디널리티</th><th>역관계</th></tr></thead>
            <tbody>
              <tr v-for="r in activeClass.objectProps" :key="r.name">
                <td><strong>{{ r.name }}</strong></td>
                <td class="mono">{{ r.uri }}</td>
                <td><span :class="r.dir === 'out' ? 'dir-out' : 'dir-in'">{{ r.dir === 'out' ? '→ 출력' : '← 입력' }}</span></td>
                <td class="link">{{ r.target }}</td>
                <td>{{ r.cardinality }}</td>
                <td class="mono muted">{{ r.inverse }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 하단: 인스턴스 + 변경이력 -->
    <div class="bottom-grid">
      <div class="detail-card">
        <div class="card-title"><DatabaseOutlined /> 인스턴스 목록 ({{ activeClass.name }}) <span class="sub-count">총 {{ activeClass.instances }}건</span></div>
        <table class="data-table">
          <thead><tr><th>코드</th><th>이름</th><th>유역</th><th>용량</th><th>관측소</th></tr></thead>
          <tbody>
            <tr v-for="inst in instances" :key="inst.code"><td class="mono">{{ inst.code }}</td><td><strong>{{ inst.name }}</strong></td><td>{{ inst.basin }}</td><td>{{ inst.capacity }}</td><td>{{ inst.stations }}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="detail-card">
        <div class="card-title"><HistoryOutlined /> 최근 변경 이력</div>
        <div class="changelog">
          <div v-for="log in changeLogs" :key="log.id" class="log-item">
            <span class="log-badge" :class="log.type">{{ log.typeLabel }}</span>
            <div class="log-body">
              <div class="log-text" v-html="log.text"></div>
              <div class="log-meta">{{ log.author }} / {{ log.date }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cypher 질의 -->
    <div class="detail-card cypher-section">
      <div class="card-title"><CodeOutlined /> Cypher 질의</div>
      <div class="cypher-input">
        <textarea v-model="cypherQuery" rows="3" class="cypher-textarea" placeholder="MATCH (d:Dam)-[:hasObservationStation]->(s) RETURN d.damName, s.stationName LIMIT 10"></textarea>
        <button class="btn btn-primary" @click="runCypher"><ThunderboltOutlined /> 실행</button>
      </div>
      <div class="cypher-result" v-if="cypherResults.length">
        <table class="data-table">
          <thead><tr><th>시설명</th><th>유형</th><th>시스템</th><th>데이터셋</th><th>레코드수</th><th>품질</th><th>갱신</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="r in cypherResults" :key="r.facility + r.dataset">
              <td><strong>{{ r.facility }}</strong></td>
              <td><span class="type-badge" :class="r.typeClass">{{ r.type }}</span></td>
              <td class="mono">{{ r.system }}</td>
              <td>{{ r.dataset }}</td>
              <td class="right">{{ r.records }}</td>
              <td><span :style="{ color: r.qualityColor, fontWeight: 700 }">{{ r.quality }}</span></td>
              <td>{{ r.lastUpdate }}</td>
              <td><span class="status-badge" :class="r.statusClass">{{ r.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Import Modal -->
    <AdminModal :visible="showImport" title="OWL/RDF 가져오기" size="lg" @close="showImport = false">
      <div class="modal-form">
        <div class="form-group">
          <label>파일 형식</label>
          <div class="radio-row-wide">
            <label><input type="radio" name="importFmt" value="owl" checked /> OWL/XML</label>
            <label><input type="radio" name="importFmt" value="ttl" /> Turtle (.ttl)</label>
            <label><input type="radio" name="importFmt" value="rdf" /> RDF/XML</label>
            <label><input type="radio" name="importFmt" value="jsonld" /> JSON-LD</label>
          </div>
        </div>
        <div class="form-group">
          <label>파일 선택</label>
          <div class="drop-zone"><ImportOutlined style="font-size:28px;color:#ccc;" /><div>파일을 드래그하거나 <span class="link">클릭하여 선택</span></div><div class="muted">최대 50MB / .owl, .ttl, .rdf, .jsonld</div></div>
        </div>
        <div class="form-group">
          <label>옵션</label>
          <div class="check-row-wide">
            <label><input type="checkbox" checked /> 기존 온톨로지와 병합 (Merge)</label>
            <label><input type="checkbox" /> 기존 온톨로지 덮어쓰기 (Replace)</label>
            <label><input type="checkbox" checked /> 충돌 시 건너뛰기</label>
          </div>
        </div>
      </div>
      <template #footer><button class="btn btn-outline" @click="showImport = false">취소</button><button class="btn btn-primary" @click="showImport = false; showMsg('가져오기 실행됨')">가져오기 실행</button></template>
    </AdminModal>

    <!-- Export Modal -->
    <AdminModal :visible="showExport" title="OWL/RDF 내보내기" size="lg" @close="showExport = false">
      <div class="modal-form">
        <div class="form-group">
          <label>내보내기 형식</label>
          <div class="radio-row-wide">
            <label><input type="radio" name="exportFmt" value="owl" checked /> OWL/XML</label>
            <label><input type="radio" name="exportFmt" value="ttl" /> Turtle (.ttl)</label>
            <label><input type="radio" name="exportFmt" value="rdf" /> RDF/XML</label>
            <label><input type="radio" name="exportFmt" value="jsonld" /> JSON-LD</label>
          </div>
        </div>
        <div class="form-group">
          <label>내보내기 범위</label>
          <div class="radio-row-wide">
            <label><input type="radio" name="exportScope" value="all" checked /> 전체 온톨로지 (142 클래스)</label>
            <label><input type="radio" name="exportScope" value="selected" /> 선택된 도메인만 (수자원시설)</label>
          </div>
        </div>
        <div class="form-group">
          <label>포함 항목</label>
          <div class="check-row-wide">
            <label><input type="checkbox" checked /> 클래스 정의</label>
            <label><input type="checkbox" checked /> 데이터 속성</label>
            <label><input type="checkbox" checked /> 관계 속성</label>
            <label><input type="checkbox" /> 인스턴스 데이터</label>
            <label><input type="checkbox" checked /> 어노테이션</label>
          </div>
        </div>
        <div class="info-box">예상 파일: <strong>kwater-ontology-20260227.owl</strong> (~2.4 MB)</div>
      </div>
      <template #footer><button class="btn btn-outline" @click="showExport = false">취소</button><button class="btn btn-primary" @click="showExport = false; showMsg('내보내기 완료')">내보내기</button></template>
    </AdminModal>

    <!-- Add Class Modal -->
    <AdminModal :visible="showAddClass" title="새 클래스 등록" size="md" @close="showAddClass = false">
      <div class="form-group"><label>클래스명 (한글) *</label><input type="text" placeholder="예: 양수장" /></div>
      <div class="form-group"><label>클래스명 (영문) *</label><input type="text" placeholder="예: PumpStation" class="mono" /></div>
      <div class="form-group"><label>상위 클래스 *</label><select><option>수자원시설</option><option>수문관측</option><option>수질정보</option><option>관로네트워크</option></select></div>
      <div class="form-group"><label>설명</label><textarea rows="2" placeholder="클래스 설명"></textarea></div>
      <template #footer><button class="btn btn-outline" @click="showAddClass = false">취소</button><button class="btn btn-primary" @click="showAddClass = false; showMsg('클래스가 등록되었습니다')">등록</button></template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ApartmentOutlined, FileTextOutlined, TagsOutlined, LinkOutlined, DatabaseOutlined, HistoryOutlined, CodeOutlined, ThunderboltOutlined, ImportOutlined, ExportOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import AdminModal from '../../components/AdminModal.vue'

const treeSearch = ref('')
const selectedClassId = ref('water-facility')
const selectedSubClass = ref('댐')
const showImport = ref(false)
const showExport = ref(false)
const showAddClass = ref(false)
const cypherQuery = ref('MATCH (d:Dam)-[:hasObservationStation]->(s) RETURN d.damName, s.stationName LIMIT 10')

const classTree = [
  { id: 'water-facility', icon: '\uD83C\uDFD7\uFE0F', name: '수자원시설', count: 28, children: ['댐', '보', '저수지', '취수장', '정수장', '하수처리장'] },
  { id: 'hydro-obs', icon: '\uD83D\uDCCA', name: '수문관측', count: 35, children: ['수위관측소', '유량관측소', '강수량관측소'] },
  { id: 'water-quality', icon: '\uD83E\uDDEA', name: '수질정보', count: 22, children: ['수질측정지점', '자동측정기', '시료분석'] },
  { id: 'pipeline', icon: '\uD83D\uDD27', name: '관로네트워크', count: 18, children: ['도수관로', '송수관로', '배수관로'] },
  { id: 'customer', icon: '\uD83D\uDC64', name: '고객/요금', count: 15, children: ['수용가', '요금체계'] },
  { id: 'gis', icon: '\uD83D\uDDFA\uFE0F', name: 'GIS공간정보', count: 12, children: ['행정구역', '유역경계'] },
  { id: 'weather', icon: '\uD83C\uDF26\uFE0F', name: '기상/기후', count: 8, children: ['기상관측소', '예보모델'] },
  { id: 'operation', icon: '\u2699\uFE0F', name: '운영관리', count: 4, children: ['조직', '인력'] },
]

const filteredTree = computed(() => {
  if (!treeSearch.value) return classTree
  const q = treeSearch.value.toLowerCase()
  return classTree.filter(c => c.name.toLowerCase().includes(q) || c.children?.some(ch => ch.includes(q)))
})

const activeClass = ref({
  name: '댐', eng: 'Dam', uri: 'kw:Dam', parent: '수자원시설', children: '다목적댐, 용수전용댐, 홍수조절댐',
  instances: 38, relations: '12개 (입력 5 / 출력 7)',
  dataProps: [
    { name: '댐코드', uri: 'kw:damCode', type: 'xsd:string', typeColor: 'blue', cardinality: '1..1', desc: '댐 고유 식별코드', term: '댐코드' },
    { name: '댐명', uri: 'kw:damName', type: 'xsd:string', typeColor: 'blue', cardinality: '1..1', desc: '댐 명칭', term: '댐명' },
    { name: '총저수용량', uri: 'kw:totalCapacity', type: 'xsd:float', typeColor: 'purple', cardinality: '0..1', desc: '총 저수 용량 (만m3)', term: '총저수용량' },
    { name: '유효저수용량', uri: 'kw:effectiveCapacity', type: 'xsd:float', typeColor: 'purple', cardinality: '0..1', desc: '유효 저수 용량 (만m3)', term: '유효저수용량' },
    { name: '준공년도', uri: 'kw:completionYear', type: 'xsd:gYear', typeColor: 'orange', cardinality: '0..1', desc: '댐 준공 연도', term: '' },
    { name: '위치좌표', uri: 'kw:location', type: 'geo:wktLiteral', typeColor: 'teal', cardinality: '0..1', desc: 'GIS 좌표 (WKT)', term: '' },
  ],
  objectProps: [
    { name: '보유수문관측소', uri: 'kw:hasObservationStation', dir: 'out', target: '수문관측소', cardinality: '0..*', inverse: 'kw:locatedAtDam' },
    { name: '소속유역', uri: 'kw:belongsToBasin', dir: 'out', target: '유역', cardinality: '1..1', inverse: 'kw:containsDam' },
    { name: '연결관로', uri: 'kw:connectedPipeline', dir: 'out', target: '도수관로', cardinality: '0..*', inverse: 'kw:sourceFrom' },
    { name: '수질측정지점', uri: 'kw:hasWaterQualityPoint', dir: 'out', target: '수질측정지점', cardinality: '0..*', inverse: 'kw:measuredAt' },
    { name: '관리기관', uri: 'kw:managedBy', dir: 'in', target: '관리기관', cardinality: '1..1', inverse: 'kw:manages' },
  ],
})

const instances = [
  { code: 'DAM-001', name: '소양강댐', basin: '북한강', capacity: '29억m3', stations: 4 },
  { code: 'DAM-002', name: '충주댐', basin: '남한강', capacity: '27.5억m3', stations: 3 },
  { code: 'DAM-003', name: '안동댐', basin: '낙동강', capacity: '12.5억m3', stations: 3 },
  { code: 'DAM-004', name: '합천댐', basin: '낙동강', capacity: '7.9억m3', stations: 2 },
  { code: 'DAM-005', name: '대청댐', basin: '금강', capacity: '14.9억m3', stations: 3 },
]

const changeLogs = [
  { id: 1, type: 'add', typeLabel: '추가', text: '<strong>수질측정지점</strong> 클래스에 <code>kw:sampleDepth</code> 속성 추가', author: '김메타', date: '2026-02-26 14:30' },
  { id: 2, type: 'edit', typeLabel: '수정', text: '<strong>댐</strong> → <strong>수문관측소</strong> 관계 카디널리티 0..* → 1..* 변경', author: '박온톨', date: '2026-02-25 11:15' },
  { id: 3, type: 'add', typeLabel: '추가', text: '<strong>홍수조절댐</strong> 하위 클래스 신규 등록 (상위: 댐)', author: '이수자', date: '2026-02-24 16:45' },
  { id: 4, type: 'delete', typeLabel: '삭제', text: '<strong>관로네트워크</strong>에서 미사용 속성 <code>kw:legacyId</code> 제거', author: '김메타', date: '2026-02-23 09:20' },
  { id: 5, type: 'sync', typeLabel: '동기화', text: 'Neo4j ↔ 마인즈DB 전체 동기화 완료 (48,230건)', author: '시스템', date: '2026-02-23 06:00' },
]

const cypherResults = ref([
  { facility: '소양강댐', type: '댐', typeClass: 'dam', system: 'RWIS', dataset: '수위관측 시계열', records: '1,234,567', quality: '94.2%', qualityColor: '#389e0d', lastUpdate: '11:45:02', status: '활성', statusClass: 'active' },
  { facility: '소양강댐', type: '댐', typeClass: 'dam', system: 'HDAPS', dataset: '발전량 통계', records: '23,456', quality: '97.1%', qualityColor: '#389e0d', lastUpdate: '11:44:50', status: '활성', statusClass: 'active' },
  { facility: '충주댐', type: '댐', typeClass: 'dam', system: 'RWIS', dataset: '수위관측 시계열', records: '1,102,340', quality: '93.5%', qualityColor: '#389e0d', lastUpdate: '11:45:00', status: '활성', statusClass: 'active' },
  { facility: '세종보', type: '보', typeClass: 'weir', system: 'SCADA', dataset: '수문 개도율', records: '456,789', quality: '89.3%', qualityColor: '#d48806', lastUpdate: '11:42:15', status: '점검중', statusClass: 'warning' },
  { facility: '구미정수장', type: '정수장', typeClass: 'plant', system: 'IoT센서', dataset: '수질측정 자동화', records: '2,340,120', quality: '88.1%', qualityColor: '#d48806', lastUpdate: '11:44:30', status: '활성', statusClass: 'active' },
  { facility: '낙동강하천', type: '하천', typeClass: 'river', system: 'RWIS', dataset: '방류량 관측', records: '678,900', quality: '84.7%', qualityColor: '#cf1322', lastUpdate: '09:00:00', status: '비활성', statusClass: 'inactive' },
])

function selectClass(id: string) { selectedClassId.value = id }
function runCypher() { message.info('Cypher 질의가 실행되었습니다. (시뮬레이션)') }
function showMsg(msg: string) { message.info(msg) }
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.onto-page { display: flex; flex-direction: column; gap: 16px; }
.breadcrumb { font-size: 12px; color: #999; a { color: $primary; text-decoration: none; } }
.page-header { display: flex; justify-content: space-between; align-items: center; h2 { font-size: 20px; margin: 0; } .header-actions { display: flex; gap: 6px; } }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px 18px;
  .kpi-label { font-size: 11px; color: #999; margin-bottom: 4px; }
  .kpi-value { font-size: 24px; font-weight: 800; &.green { color: #4caf50; } &.blue { color: #1967d2; } &.purple { color: #7b1fa2; } }
  .kpi-sub { font-size: 11px; color: #bbb; margin-top: 2px; }
}

.tree-detail-layout { display: grid; grid-template-columns: 320px 1fr; gap: 16px; }
.tree-panel { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; max-height: 600px; overflow-y: auto; padding: 12px;
  .tree-title { font-weight: 700; font-size: 13px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
  .tree-search { width: 100%; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 12px; margin-bottom: 8px; box-sizing: border-box; }
  .tree-body { font-size: 12px; line-height: 2; font-family: monospace; }
  .tree-node { cursor: pointer; padding: 0 4px; border-radius: 4px; &:hover { background: #f0f7ff; }
    &.root { color: #555; } &.level1 { margin-left: 12px; } &.level2 { margin-left: 28px; font-size: 11px; color: #555; &.active { background: #e8f0fe; color: #1967d2; font-weight: 600; border-radius: 4px; padding: 0 6px; } }
  }
  .caret { font-size: 10px; color: #999; } .node-root { color: #1967d2; } .node-icon { font-size: 13px; } .node-count { font-size: 10px; color: #aaa; }
  .tree-children { margin-top: 2px; }
}

.detail-panel { display: flex; flex-direction: column; gap: 14px; }
.detail-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; .highlight { color: #1967d2; } .card-actions { margin-left: auto; display: flex; gap: 4px; } .sub-count { margin-left: auto; font-size: 11px; color: #888; font-weight: 400; } }
.btn-xs { padding: 2px 8px !important; font-size: 11px !important; }
.btn-danger-outline { color: #DC3545 !important; border-color: #DC3545 !important; &:hover { background: #fff1f0 !important; } }

.info-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-table { width: 100%; font-size: 12px; border-collapse: collapse; td { padding: 6px 10px; border-bottom: 1px solid #f5f5f5; } .lbl { width: 100px; font-weight: 600; color: #555; } .mono { font-family: monospace; font-size: 11px; } .link { color: #1967d2; cursor: pointer; } }

.data-table { width: 100%; font-size: 12px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 8px 10px; text-align: left; font-weight: 600; font-size: 11px; border-bottom: 2px solid #e8e8e8; }
  td { padding: 7px 10px; border-bottom: 1px solid #f0f0f0; }
  tr:hover td { background: #fafafa; }
  .mono { font-family: monospace; font-size: 10px; } .muted { color: #aaa; } .link { color: #1967d2; cursor: pointer; } .right { text-align: right; }
}
.type-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.blue { background: #e8f0fe; color: #1967d2; } &.purple { background: #f3e5f5; color: #7b1fa2; } &.orange { background: #fff3e0; color: #e65100; } &.teal { background: #e0f2f1; color: #00695c; }
  &.dam { background: #e6f7ff; color: #0958d9; } &.weir { background: #f6ffed; color: #389e0d; } &.plant { background: #fff7e6; color: #d48806; } &.river { background: #f9f0ff; color: #722ed1; }
}
.term-link { background: #e8f5e9; color: #2e7d32; padding: 1px 6px; border-radius: 3px; font-size: 10px; cursor: pointer; }
.dir-out { color: #1967d2; font-size: 11px; } .dir-in { color: #2e7d32; font-size: 11px; }
.status-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;
  &.active { background: #f6ffed; color: #389e0d; } &.warning { background: #fff7e6; color: #d48806; } &.inactive { background: #f5f5f5; color: #999; }
  &::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
  &.active::before { background: #52c41a; } &.warning::before { background: #faad14; } &.inactive::before { background: #bbb; }
}

.bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.changelog { font-size: 12px; .log-item { display: flex; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; align-items: flex-start; }
  .log-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; white-space: nowrap; font-weight: 600;
    &.add { background: #e8f0fe; color: #1967d2; } &.edit { background: #fff3e0; color: #e65100; } &.delete { background: #ffebee; color: #c62828; } &.sync { background: #e8f5e9; color: #2e7d32; }
  }
  .log-body { .log-text { line-height: 1.5; :deep(code) { background: #f5f5f5; padding: 1px 4px; border-radius: 2px; font-size: 10px; } } .log-meta { color: #aaa; font-size: 11px; margin-top: 2px; } }
}

.cypher-section { .cypher-input { display: flex; gap: 8px; margin-bottom: 12px; }
  .cypher-textarea { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-family: monospace; font-size: 12px; resize: vertical; }
}

// Modal form styles
.form-group { margin-bottom: 12px; label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; } input, select, textarea { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; box-sizing: border-box; } }
.modal-form { display: flex; flex-direction: column; gap: 16px; }
.radio-row { display: flex; gap: 12px; font-size: 12px; label { display: flex; align-items: center; gap: 4px; font-weight: 400; } }
.radio-row-wide { display: flex; flex-wrap: wrap; gap: 16px 24px; font-size: 13px; label { display: flex; align-items: center; gap: 6px; font-weight: 400; white-space: nowrap; cursor: pointer; } }
.check-col { display: flex; flex-direction: column; gap: 6px; font-size: 12px; label { display: flex; align-items: center; gap: 6px; font-weight: 400; } }
.check-row-wide { display: flex; flex-wrap: wrap; gap: 10px 24px; font-size: 13px; label { display: flex; align-items: center; gap: 6px; font-weight: 400; white-space: nowrap; cursor: pointer; } }
.drop-zone { border: 2px dashed #ccc; border-radius: 8px; padding: 24px; text-align: center; background: #fafafa; font-size: 12px; color: #888; .link { color: #1967d2; cursor: pointer; text-decoration: underline; } .muted { font-size: 11px; color: #aaa; margin-top: 4px; } }
.info-box { background: #f0f7ff; border-radius: 8px; padding: 10px 12px; font-size: 11px; color: #1565c0; }
</style>
