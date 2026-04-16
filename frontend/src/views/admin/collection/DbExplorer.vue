<template>
  <div class="admin-page db-explorer">
    <div class="page-header">
      <h2>DB 탐색기</h2>
      <p class="page-desc">원본DB의 스키마·테이블을 탐색하고 컬럼/DDL 확인 및 읽기 전용 SQL을 실행할 수 있습니다.</p>
    </div>

    <div class="explorer-toolbar">
      <div class="form-row">
        <label>원본DB</label>
        <select v-model="selectedSid" @change="onSourceChange">
          <option value="">-- 선택 --</option>
          <option v-for="s in sources" :key="s.id" :value="s.id">
            {{ s.source_name }} ({{ s.db_type }}) — {{ s.connection_host }}
          </option>
        </select>
        <button class="btn btn-outline btn-sm" :disabled="!selectedSid || loadingSchemas" @click="loadSchemas">
          <ReloadOutlined /> 스키마 새로고침
        </button>
      </div>
    </div>

    <div class="explorer-body" v-if="selectedSid">
      <!-- 좌측: 스키마/테이블 트리 -->
      <aside class="sidebar-tree">
        <div class="tree-title">Schema · Tables</div>
        <input v-model="treeFilter" placeholder="이름 필터..." class="tree-filter" />
        <div class="tree-scroll">
          <div v-if="!schemas.length" class="muted pad">스키마를 불러오려면 "스키마 새로고침" 클릭</div>
          <div v-for="s in filteredSchemas" :key="s" class="tree-schema">
            <div class="tree-row" @click="toggleSchema(s)">
              <span class="tree-toggle">{{ expanded[s] ? '▾' : '▸' }}</span>
              <DatabaseOutlined /> <strong>{{ s }}</strong>
            </div>
            <div v-if="expanded[s]" class="tree-tables">
              <div v-if="loadingTables[s]" class="muted pad">로드 중...</div>
              <div v-for="t in filteredTablesOf(s)" :key="t"
                   class="tree-table"
                   :class="{ active: active.schema === s && active.table === t }"
                   @click="openTable(s, t)">
                <TableOutlined /> {{ t }}
              </div>
              <div v-if="expanded[s] && (tables[s] || []).length === 0 && !loadingTables[s]" class="muted pad">(테이블 없음)</div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 우측: 탭 뷰 -->
      <main class="detail-pane">
        <div class="detail-header" v-if="active.schema">
          <h3>{{ active.schema }}.{{ active.table || '—' }}</h3>
          <div class="tabs">
            <button v-for="t in TABS" :key="t.key" class="tab" :class="{ active: activeTab === t.key }"
                    @click="switchTab(t.key)">{{ t.label }}</button>
          </div>
        </div>

        <!-- 컬럼 탭 -->
        <div v-show="activeTab === 'columns'" class="tab-pane">
          <div v-if="loading.columns" class="muted pad">조회 중...</div>
          <div v-else-if="!columnData.length" class="muted pad">테이블을 선택하세요.</div>
          <div v-else class="ag-grid-wrapper">
            <AgGridVue class="ag-theme-alpine"
                       :rowData="columnData"
                       :columnDefs="columnCols"
                       :defaultColDef="defCol"
                       :pagination="true"
                       :paginationPageSize="20"
                       domLayout="autoHeight" />
            <div class="meta-info" v-if="metaExtra">
              <span class="badge" v-if="metaExtra.table_comment" style="background:#fff7e6;color:#874d00;border-color:#ffd591">
                📖 {{ metaExtra.table_comment }}
              </span>
              <span class="badge">PK: {{ (metaExtra.pk_columns || []).join(', ') || '-' }}</span>
              <span class="badge" v-if="metaExtra.row_count_estimate != null">예상 행수: {{ metaExtra.row_count_estimate.toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <!-- DDL 탭 -->
        <div v-show="activeTab === 'ddl'" class="tab-pane">
          <div class="pane-toolbar">
            <button class="btn btn-outline btn-sm" @click="copyDdl" :disabled="!ddl"><CopyOutlined /> 복사</button>
            <button class="btn btn-outline btn-sm" @click="loadDdl" :disabled="loading.ddl || !active.table"><ReloadOutlined /> 재조회</button>
          </div>
          <div v-if="loading.ddl" class="muted pad">DDL 로딩 중...</div>
          <pre v-else-if="ddl" class="ddl-pre">{{ ddl }}</pre>
          <div v-else class="muted pad">테이블을 선택하면 DDL이 표시됩니다.</div>
        </div>

        <!-- 쿼리 탭 -->
        <div v-show="activeTab === 'query'" class="tab-pane query-pane">
          <div class="query-editor-row">
            <textarea v-model="queryText" class="query-editor" spellcheck="false"
                      placeholder="SELECT / WITH / SHOW / DESC / EXPLAIN 만 허용됩니다&#10;예) SELECT * FROM HR.EMPLOYEES WHERE ROWNUM < 10"></textarea>
            <div class="query-actions">
              <div class="query-limit">
                <label>행 제한</label>
                <input type="number" v-model.number="queryLimit" min="1" max="10000" />
              </div>
              <button class="btn btn-primary" @click="runQuery" :disabled="running">
                <ThunderboltOutlined /> {{ running ? '실행 중...' : '실행 (Ctrl+Enter)' }}
              </button>
              <button class="btn btn-outline" @click="insertSelectTable" :disabled="!active.table">
                <TableOutlined /> SELECT * 샘플
              </button>
            </div>
          </div>
          <div v-if="queryError" class="query-error">
            <CloseCircleOutlined /> {{ queryError }}
          </div>
          <div v-if="queryResult" class="query-result">
            <div class="query-meta">
              <span class="badge">{{ queryResult.row_count }}행</span>
              <span class="badge">{{ queryResult.elapsed_ms }} ms</span>
              <span class="badge badge-warning" v-if="queryResult.truncated">결과가 {{ queryLimit }}행으로 잘림</span>
            </div>
            <div class="ag-grid-wrapper" v-if="queryResult.row_count">
              <AgGridVue class="ag-theme-alpine"
                         :rowData="queryRowData"
                         :columnDefs="queryColDefs"
                         :defaultColDef="defCol"
                         :pagination="true"
                         :paginationPageSize="20"
                         domLayout="autoHeight" />
            </div>
            <div v-else class="muted pad">결과 없음</div>
          </div>
        </div>
      </main>
    </div>
    <div v-else class="empty-state">
      <DatabaseOutlined style="font-size:32px;color:#bfbfbf" />
      <div class="muted">상단에서 원본DB를 선택하세요.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { DatabaseOutlined, TableOutlined, ReloadOutlined, ThunderboltOutlined, CopyOutlined, CloseCircleOutlined } from '@ant-design/icons-vue'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { message } from '../../../utils/message'
import { adminCollectionApi, adminDrApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const TABS = [
  { key: 'columns', label: '컬럼' },
  { key: 'ddl', label: 'DDL' },
  { key: 'query', label: '쿼리' },
]

const sources = ref<any[]>([])
const selectedSid = ref<string>('')
const schemas = ref<string[]>([])
const tables = reactive<Record<string, string[]>>({})
const expanded = reactive<Record<string, boolean>>({})
const loadingTables = reactive<Record<string, boolean>>({})
const loadingSchemas = ref(false)
const treeFilter = ref('')
const active = reactive<any>({ schema: '', table: '' })
const activeTab = ref<'columns' | 'ddl' | 'query'>('columns')
const columnData = ref<any[]>([])
const metaExtra = ref<any>(null)
const ddl = ref('')
const queryText = ref('')
const queryLimit = ref(500)
const queryResult = ref<any>(null)
const queryError = ref('')
const running = ref(false)
const loading = reactive({ columns: false, ddl: false })
const defCol = { ...baseDefaultColDef }

const columnCols: ColDef[] = withHeaderTooltips([
  { headerName: '#', valueGetter: 'node.rowIndex + 1', width: 55 },
  { headerName: '컬럼명(물리)', field: 'name', flex: 1, minWidth: 130 },
  { headerName: '한글명(논리/주석)', field: 'comment', flex: 1.5, minWidth: 160,
    tooltipField: 'comment',
    cellStyle: (p: any): any => p.value
      ? { color: '#1677ff', fontStyle: 'normal' }
      : { color: '#bbb', fontStyle: 'italic' },
    cellRenderer: (p: any) => p.value || '<span style="color:#bbb">—</span>' },
  { headerName: '타입', field: 'type', flex: 0.8, minWidth: 100 },
  { headerName: '길이', field: 'length', width: 75 },
  { headerName: 'Precision', field: 'precision', width: 90 },
  { headerName: 'Scale', field: 'scale', width: 70 },
  { headerName: 'Nullable', field: 'nullable', width: 85,
    cellRenderer: (p: any) => p.value ? '✓' : '—' },
  { headerName: 'PK', field: 'isPk', width: 55,
    cellRenderer: (p: any) => p.value ? '🔑' : '' },
])

const filteredSchemas = computed(() => {
  if (!treeFilter.value) return schemas.value
  const q = treeFilter.value.toLowerCase()
  return schemas.value.filter(s => s.toLowerCase().includes(q))
})

function filteredTablesOf(s: string) {
  const list = tables[s] || []
  if (!treeFilter.value) return list
  const q = treeFilter.value.toLowerCase()
  return list.filter(t => t.toLowerCase().includes(q))
}

const queryRowData = computed(() => {
  if (!queryResult.value) return []
  const { columns, rows } = queryResult.value
  return rows.map((row: any[]) => {
    const o: any = {}
    columns.forEach((c: string, i: number) => { o[c] = formatCell(row[i]) })
    return o
  })
})

const queryColDefs = computed<ColDef[]>(() => {
  if (!queryResult.value) return []
  return queryResult.value.columns.map((c: string) => ({
    headerName: c, field: c, flex: 1, minWidth: 100, tooltipField: c,
  }))
})

function formatCell(v: any) {
  if (v === null || v === undefined) return null
  if (v instanceof Date) return v.toISOString()
  if (typeof v === 'object') return JSON.stringify(v)
  return v
}

async function loadSources() {
  try {
    const res = await adminCollectionApi.dataSources()
    sources.value = (res.data.data || []).filter((s: any) => s.db_type)
  } catch (e: any) {
    message.error('데이터소스 목록 조회 실패')
  }
}

function onSourceChange() {
  schemas.value = []
  Object.keys(tables).forEach(k => delete tables[k])
  Object.keys(expanded).forEach(k => delete expanded[k])
  active.schema = ''
  active.table = ''
  ddl.value = ''
  columnData.value = []
  queryResult.value = null
  queryError.value = ''
}

async function loadSchemas() {
  if (!selectedSid.value) return
  loadingSchemas.value = true
  try {
    const res = await adminDrApi.listSchemas(selectedSid.value)
    schemas.value = res.data.data || []
    if (!schemas.value.length) message.info('조회된 스키마가 없습니다')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '스키마 조회 실패')
  } finally {
    loadingSchemas.value = false
  }
}

async function toggleSchema(s: string) {
  if (expanded[s]) { expanded[s] = false; return }
  expanded[s] = true
  if (tables[s]) return
  loadingTables[s] = true
  try {
    const res = await adminDrApi.listTables(selectedSid.value, s)
    tables[s] = res.data.data || []
  } catch (e: any) {
    message.error(`${s}: 테이블 조회 실패`)
    tables[s] = []
  } finally {
    loadingTables[s] = false
  }
}

async function openTable(s: string, t: string) {
  active.schema = s
  active.table = t
  if (activeTab.value === 'columns') await loadColumns()
  else if (activeTab.value === 'ddl') await loadDdl()
}

function switchTab(k: any) {
  activeTab.value = k
  if (!active.table) return
  if (k === 'columns' && !columnData.value.length) loadColumns()
  else if (k === 'ddl' && !ddl.value) loadDdl()
}

async function loadColumns() {
  if (!active.table) return
  loading.columns = true
  try {
    const res = await adminDrApi.describeColumns(selectedSid.value, active.schema, active.table)
    const d = res.data.data || {}
    metaExtra.value = d
    const pkSet = new Set(d.pk_columns || [])
    columnData.value = (d.columns || []).map((c: any) => ({
      ...c, isPk: pkSet.has(c.name),
    }))
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '컬럼 조회 실패')
    columnData.value = []
  } finally {
    loading.columns = false
  }
}

async function loadDdl() {
  if (!active.table) return
  loading.ddl = true
  ddl.value = ''
  try {
    const res = await adminDrApi.getTableDdl(selectedSid.value, active.schema, active.table)
    ddl.value = (res.data.data || {}).ddl || ''
  } catch (e: any) {
    message.error(e?.response?.data?.detail || 'DDL 조회 실패')
  } finally {
    loading.ddl = false
  }
}

function copyDdl() {
  if (!ddl.value) return
  navigator.clipboard?.writeText(ddl.value).then(
    () => message.success('DDL이 클립보드에 복사되었습니다'),
    () => message.error('복사 실패'),
  )
}

function insertSelectTable() {
  if (!active.table) return
  queryText.value = `SELECT * FROM ${active.schema}.${active.table}`
  activeTab.value = 'query'
}

async function runQuery() {
  const sql = queryText.value.trim()
  if (!sql) { message.warning('SQL을 입력하세요'); return }
  running.value = true
  queryError.value = ''
  queryResult.value = null
  try {
    const res = await adminDrApi.runQuery(selectedSid.value, sql, queryLimit.value)
    queryResult.value = res.data.data
  } catch (e: any) {
    // 에러 상세를 최대한 복원: detail → message → 서버 응답 원문 → 기본
    const data = e?.response?.data
    let detail: string
    if (typeof data === 'string') detail = data
    else if (data?.detail) detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    else if (data?.message) detail = data.message
    else detail = e?.message || '쿼리 실행 실패 (알 수 없는 오류)'
    const status = e?.response?.status
    queryError.value = status ? `[HTTP ${status}] ${detail}` : detail
  } finally {
    running.value = false
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && activeTab.value === 'query') {
    e.preventDefault()
    runQuery()
  }
}

onMounted(() => {
  loadSources()
  window.addEventListener('keydown', onKeyDown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';

.db-explorer { height: 100%; display: flex; flex-direction: column; }
.explorer-toolbar {
  background: #fff; padding: 10px 12px; border: 1px solid #eee;
  border-radius: 6px; margin-bottom: 10px;
  .form-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  label { font-size: 13px; color: #555; font-weight: 600; }
  select { min-width: 360px; padding: 6px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }
}

.explorer-body {
  display: grid; grid-template-columns: 280px 1fr; gap: 12px;
  flex: 1; min-height: 600px;
}
.sidebar-tree {
  background: #fff; border: 1px solid #eee; border-radius: 6px; padding: 10px;
  display: flex; flex-direction: column; max-height: 800px;
}
.tree-title { font-weight: 600; font-size: 13px; color: #333; margin-bottom: 6px; }
.tree-filter { width: 100%; padding: 4px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; margin-bottom: 6px; }
.tree-scroll { flex: 1; overflow-y: auto; }
.tree-row {
  display: flex; align-items: center; gap: 6px; padding: 4px 6px;
  cursor: pointer; border-radius: 3px; font-size: 13px;
  &:hover { background: #f0f5ff; }
}
.tree-toggle { width: 12px; font-size: 10px; color: #888; }
.tree-tables { padding-left: 20px; }
.tree-table {
  display: flex; align-items: center; gap: 5px; padding: 3px 6px;
  font-size: 12px; color: #555; cursor: pointer; border-radius: 3px;
  &:hover { background: #e6f4ff; color: #1677ff; }
  &.active { background: #bae0ff; color: #003a8c; font-weight: 600; }
}
.pad { padding: 6px 10px; font-size: 12px; }
.muted { color: #888; }

.detail-pane {
  background: #fff; border: 1px solid #eee; border-radius: 6px; padding: 12px;
  display: flex; flex-direction: column;
}
.detail-header { margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
.detail-header h3 { margin: 0 0 8px; font-size: 16px; color: #262626; }
.tabs { display: flex; gap: 4px; }
.tab {
  padding: 6px 14px; font-size: 13px; background: none;
  border: none; border-bottom: 2px solid transparent; cursor: pointer; color: #595959;
  &:hover { color: #1677ff; }
  &.active { color: #1677ff; font-weight: 600; border-bottom-color: #1677ff; }
}
.tab-pane { flex: 1; min-height: 300px; }
.pane-toolbar { display: flex; gap: 6px; margin-bottom: 8px; }
.ddl-pre {
  background: #1e1e1e; color: #d4d4d4; padding: 14px;
  border-radius: 4px; font-size: 12px; line-height: 1.5;
  white-space: pre; overflow: auto; max-height: 560px;
  font-family: Consolas, 'Courier New', monospace;
}
.meta-info { margin-top: 8px; display: flex; gap: 6px; }
.badge {
  display: inline-flex; align-items: center; padding: 2px 8px;
  border-radius: 10px; font-size: 11px; font-weight: 600;
  background: #e6f4ff; color: #003a8c; border: 1px solid #91caff;
  &.badge-warning { background: #fff7e6; color: #874d00; border-color: #ffd591; }
}

/* 쿼리 탭 */
.query-pane { display: flex; flex-direction: column; gap: 10px; }
.query-editor-row { display: grid; grid-template-columns: 1fr; gap: 8px; }
.query-editor {
  width: 100%; min-height: 120px; padding: 10px;
  font-family: Consolas, 'Courier New', monospace; font-size: 13px;
  border: 1px solid #d9d9d9; border-radius: 4px; resize: vertical;
  background: #fafafa;
  &:focus { border-color: #1677ff; outline: none; background: #fff; }
}
.query-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.query-limit { display: flex; align-items: center; gap: 4px; font-size: 12px; }
.query-limit input { width: 80px; padding: 4px 6px; border: 1px solid #d9d9d9; border-radius: 3px; }
.query-error {
  padding: 10px; background: #fff2f0; border: 1px solid #ffccc7; border-radius: 4px;
  color: #820014; font-size: 13px; display: flex; align-items: flex-start; gap: 8px;
  :deep(.anticon) { font-size: 16px; }
}
.query-meta { display: flex; gap: 6px; margin-bottom: 6px; }
.query-result { display: flex; flex-direction: column; gap: 4px; }
.empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; padding: 60px;
  background: #fff; border: 1px dashed #ddd; border-radius: 6px;
}
</style>
