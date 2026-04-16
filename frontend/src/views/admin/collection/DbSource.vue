<template>
  <div class="admin-page">
    <div class="page-header"><h2>원본DB 설정</h2><p class="page-desc">DB 복제 원본 데이터베이스 연결 정보를 관리합니다. 비밀번호는 AES-256-GCM 으로 암호화 저장됩니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">원본DB <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="openRegister"><PlusOutlined /> DB 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '원본DB')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- DB 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="(detailData.name || '') + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">원본DB 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">DB명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">DBMS</span><span class="info-value">{{ detailData.dbms }}</span></div>
          <div class="modal-info-item"><span class="info-label">호스트</span><span class="info-value">{{ detailData.host }}</span></div>
          <div class="modal-info-item"><span class="info-label">포트</span><span class="info-value">{{ detailData.port }}</span></div>
          <div class="modal-info-item"><span class="info-label">스키마</span><span class="info-value">{{ detailData.schema }}</span></div>
          <div class="modal-info-item"><span class="info-label">접속계정</span><span class="info-value">{{ detailData.user || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">비밀번호</span><span class="info-value"><span class="badge" :class="detailData.hasPassword ? 'badge-success' : 'badge-warning'">{{ detailData.hasPassword ? '암호화 저장됨' : '미설정' }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">연결 상태</span><span class="info-value"><span class="badge" :class="detailData.status === '연결됨' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>

      <!-- 연결 테스트 & 스키마/테이블 브라우저 (REQ-DHUB-005-004-003) -->
      <div class="modal-section" v-if="detailData._raw?.id">
        <div class="modal-section-title">연결 테스트 · 스키마/테이블 조회</div>
        <div class="acct-toolbar">
          <button class="btn btn-outline btn-sm" @click="testSaved" :disabled="testingSaved">
            <ThunderboltOutlined /> {{ testingSaved ? '테스트 중' : '연결 테스트' }}
          </button>
          <button class="btn btn-outline btn-sm" @click="loadSchemas" :disabled="loadingSchemas">
            <DatabaseOutlined /> {{ loadingSchemas ? '조회 중' : '스키마 조회' }}
          </button>
          <span v-if="savedTestResult" class="inline-badge" :class="{ ok: savedTestResult.ok, fail: !savedTestResult.ok }">
            {{ savedTestResult.ok ? '✔ 연결됨' : '✘ 실패' }}
            <span v-if="savedTestResult.err" class="muted">({{ savedTestResult.err }})</span>
          </span>
        </div>
        <div v-if="schemas.length" class="schema-tree">
          <div v-for="s in schemas" :key="s" class="schema-item">
            <div class="schema-row" @click="toggleSchema(s)">
              <span class="tree-toggle">{{ expandedSchemas[s] ? '▾' : '▸' }}</span>
              <DatabaseOutlined /> <strong>{{ s }}</strong>
              <span v-if="schemaTables[s]" class="muted"> ({{ schemaTables[s].length }}개)</span>
            </div>
            <ul v-if="expandedSchemas[s] && schemaTables[s]" class="table-list">
              <li v-for="t in schemaTables[s]" :key="t">
                <TableOutlined /> {{ t }}
              </li>
              <li v-if="!schemaTables[s].length" class="muted">테이블이 없습니다</li>
            </ul>
            <div v-if="expandedSchemas[s] && schemaLoading[s]" class="muted pad-left">조회 중...</div>
          </div>
        </div>
      </div>

      <!-- 계정·권한 관리 (REQ-DHUB-005-004-002) -->
      <div class="modal-section" v-if="detailData._raw?.id">
        <div class="modal-section-title">DB 계정·권한 관리</div>
        <div class="acct-toolbar">
          <button class="btn btn-outline btn-sm" @click="loadAccounts"><ReloadOutlined /> 계정 조회</button>
          <button class="btn btn-outline btn-sm" @click="showCreateAcct = true"><UserAddOutlined /> 계정 생성</button>
          <button class="btn btn-outline btn-sm" @click="showGrantRevoke('GRANT')"><SafetyCertificateOutlined /> 권한 부여</button>
          <button class="btn btn-outline btn-sm" @click="showGrantRevoke('REVOKE')"><MinusCircleOutlined /> 권한 회수</button>
        </div>
        <div class="acct-list">
          <div v-if="!accounts.length" class="acct-empty">조회된 계정이 없습니다. "계정 조회" 버튼을 눌러주세요.</div>
          <table v-else class="acct-table">
            <thead><tr><th>계정명</th><th>권한</th><th>유효기간</th><th>조치</th></tr></thead>
            <tbody>
              <tr v-for="a in accounts" :key="a.account_name">
                <td>{{ a.account_name }}<span v-if="a.is_super" class="badge badge-warning" style="margin-left:4px">SUPER</span></td>
                <td><code>{{ JSON.stringify(a.privileges || {}) }}</code></td>
                <td>{{ a.valid_until || '-' }}</td>
                <td>
                  <button class="btn btn-ghost btn-xs" @click="changePassword(a.account_name)">비밀번호 변경</button>
                  <button class="btn btn-ghost btn-xs text-danger" @click="dropAccount(a.account_name)">삭제</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-primary" @click="editFromDetail" :disabled="!detailData._raw?.id">
          <EditOutlined /> 수정
        </button>
        <button class="btn btn-danger" @click="deleteFromDetail" :disabled="!detailData._raw?.id">
          <DeleteOutlined /> 삭제
        </button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- DB 등록/수정 팝업 -->
    <AdminModal :visible="showRegister" :title="form.id ? 'DB 수정' : 'DB 등록'" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">DB명</label><input v-model="form.source_name" placeholder="DB명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">DBMS</label>
            <select v-model="form.db_type" @change="onDbTypeChange">
              <option value="POSTGRESQL">PostgreSQL</option>
              <option value="ORACLE">Oracle</option>
              <option value="TIBERO">Tibero</option>
              <option value="SAP_HANA">SAP HANA</option>
              <option value="MSSQL">MSSQL</option>
            </select>
          </div>
          <div class="modal-form-group"><label class="required">포트</label><input v-model.number="form.connection_port" type="number" placeholder="예: 5432" /></div>
        </div>
        <div class="modal-form-group"><label class="required">호스트</label><input v-model="form.connection_host" placeholder="호스트 IP 또는 DNS" /></div>
        <!-- Oracle 전용: Service Name vs SID 접속 유형 -->
        <div class="modal-form-row" v-if="form.db_type === 'ORACLE'">
          <div class="modal-form-group">
            <label>접속 유형 <span class="muted">(Oracle)</span></label>
            <select v-model="form.dsn_mode">
              <option value="">자동 (12c+: Service Name, 11g 이하: SID)</option>
              <option value="service_name">Service Name</option>
              <option value="sid">SID</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>{{ form.dsn_mode === 'sid' ? 'SID' : '서비스명/SID' }}</label>
            <input v-model="form.connection_db" :placeholder="form.dsn_mode === 'sid' ? '예: ORCL' : '예: ORCL, FREEPDB1'" />
          </div>
        </div>
        <div class="modal-form-row" v-else>
          <div class="modal-form-group"><label>DB명</label><input v-model="form.connection_db" placeholder="DB 인스턴스명" /></div>
          <div class="modal-form-group"><label>스키마</label><input v-model="form.connection_schema" placeholder="스키마명" /></div>
        </div>
        <div class="modal-form-row" v-if="form.db_type === 'ORACLE'">
          <div class="modal-form-group"><label>스키마</label><input v-model="form.connection_schema" placeholder="스키마명(선택)" /></div>
          <div class="modal-form-group"></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>접속계정</label><input v-model="form.connection_user" placeholder="계정명" autocomplete="off" /></div>
          <div class="modal-form-group">
            <label>비밀번호 <span class="muted">(AES-256-GCM 암호화 저장)</span></label>
            <input v-model="form.connection_password" type="password" autocomplete="new-password"
                   :placeholder="form.id ? '변경 시에만 입력' : '비밀번호 입력'" />
          </div>
        </div>

        <!-- 연결 테스트 결과 배너 -->
        <div v-if="testResult" class="conn-test-result" :class="{ ok: testResult.ok, fail: !testResult.ok }">
          <CheckCircleOutlined v-if="testResult.ok" />
          <CloseCircleOutlined v-else />
          <div class="conn-test-content">
            <div class="conn-test-title">{{ testResult.ok ? '연결 성공' : '연결 실패' }}
              <span class="muted" v-if="testResult.driver"> · driver: {{ testResult.driver }}</span>
            </div>
            <div v-if="testResult.ok && testResult.result" class="conn-test-detail">{{ formatTestResult(testResult.result) }}</div>
            <div v-if="!testResult.ok" class="conn-test-detail err">{{ testResult.error || testResult.detail }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="testConnection" :disabled="testing || saving">
          <ThunderboltOutlined /> {{ testing ? '테스트 중...' : '연결 테스트' }}
        </button>
        <button class="btn btn-primary" @click="handleSave" :disabled="saving"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>

    <!-- 계정 생성 팝업 -->
    <AdminModal :visible="showCreateAcct" title="DB 계정 생성" size="sm" @close="showCreateAcct = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">계정명</label><input v-model="newAcct.account_name" placeholder="영숫자/언더스코어" /></div>
        <div class="modal-form-group"><label class="required">비밀번호</label><input v-model="newAcct.password" type="password" autocomplete="new-password" placeholder="최소 8자" /></div>
        <div class="modal-form-group"><label>비고</label><input v-model="newAcct.note" placeholder="변경 사유(선택)" /></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="createAccount"><SaveOutlined /> 생성</button>
        <button class="btn btn-outline" @click="showCreateAcct = false">취소</button>
      </template>
    </AdminModal>

    <!-- 권한 부여/회수 팝업 -->
    <AdminModal :visible="showGR" :title="grMode === 'GRANT' ? '권한 부여' : '권한 회수'" size="sm" @close="showGR = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">대상 계정</label>
          <select v-model="grForm.account_name"><option v-for="a in accounts" :key="a.account_name" :value="a.account_name">{{ a.account_name }}</option></select>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>스키마</label><input v-model="grForm.schema" placeholder="(선택)" /></div>
          <div class="modal-form-group"><label>테이블</label><input v-model="grForm.table" placeholder="(선택)" /></div>
        </div>
        <div class="modal-form-group"><label class="required">권한</label>
          <div class="priv-checks">
            <label v-for="p in PRIVS" :key="p"><input type="checkbox" :value="p" v-model="grForm.privileges" /> {{ p }}</label>
          </div>
        </div>
        <div class="modal-form-group"><label>비고</label><input v-model="grForm.note" placeholder="변경 사유(선택)" /></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="applyGrantRevoke"><SaveOutlined /> {{ grMode === 'GRANT' ? '부여' : '회수' }}</button>
        <button class="btn btn-outline" @click="showGR = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, reactive } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, SaveOutlined, ReloadOutlined, UserAddOutlined, SafetyCertificateOutlined, MinusCircleOutlined, ThunderboltOutlined, CheckCircleOutlined, CloseCircleOutlined, DatabaseOutlined, TableOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi, adminDrApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const PRIVS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'USAGE', 'CONNECT', 'ALL']
const DEFAULT_PORTS: Record<string, number> = {
  POSTGRESQL: 5432, ORACLE: 1521, TIBERO: 8629, SAP_HANA: 30015, MSSQL: 1433,
}
const showDetail = ref(false), showRegister = ref(false), showCreateAcct = ref(false), showGR = ref(false)
const saving = ref(false), grMode = ref<'GRANT' | 'REVOKE'>('GRANT')
const testing = ref(false), testingSaved = ref(false), loadingSchemas = ref(false)
const testResult = ref<any>(null), savedTestResult = ref<any>(null)
const schemas = ref<string[]>([])
const schemaTables = reactive<Record<string, string[]>>({})
const schemaLoading = reactive<Record<string, boolean>>({})
const expandedSchemas = reactive<Record<string, boolean>>({})
const detailData = ref<any>({})
const accounts = ref<any[]>([])
const form = reactive<any>({
  id: '', source_name: '', source_type: 'RDBMS', db_type: 'POSTGRESQL',
  connection_host: '', connection_port: 5432, connection_db: '', connection_schema: '',
  connection_user: '', connection_password: '', dsn_mode: '',
})
const newAcct = reactive<any>({ account_name: '', password: '', note: '' })
const grForm = reactive<any>({ account_name: '', privileges: [], schema: '', table: '', note: '' })

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: 'DB명', field: 'name', flex: 1.2, minWidth: 120 },
  { headerName: 'DBMS', field: 'dbms', flex: 0.6, minWidth: 70 },
  { headerName: '호스트', field: 'host', flex: 1, minWidth: 100 },
  { headerName: '포트', field: 'port', flex: 0.4, minWidth: 55 },
  { headerName: '스키마', field: 'schema', flex: 0.8, minWidth: 80 },
  { headerName: '계정', field: 'user', flex: 0.6, minWidth: 70 },
  { headerName: '비밀번호', field: 'pwBadge', flex: 0.5, minWidth: 70 },
  { headerName: '연결 상태', field: 'status', flex: 0.6, minWidth: 80 },
  { headerName: '작업', flex: 0.9, minWidth: 180, sortable: false, cellRenderer: (p: any) => {
      const wrap = document.createElement('div')
      wrap.className = 'grid-action-wrap'
      const testBtn = document.createElement('button')
      testBtn.className = 'grid-action-btn'
      testBtn.title = '연결 테스트'
      testBtn.innerHTML = '⚡ 테스트'
      testBtn.onclick = (ev) => { ev.stopPropagation(); quickTestRow(p.data) }
      const editBtn = document.createElement('button')
      editBtn.className = 'grid-action-btn edit'
      editBtn.title = '수정'
      editBtn.innerHTML = '✎ 수정'
      editBtn.onclick = (ev) => { ev.stopPropagation(); openEdit(p.data) }
      const delBtn = document.createElement('button')
      delBtn.className = 'grid-action-btn del'
      delBtn.title = '삭제'
      delBtn.innerHTML = '🗑 삭제'
      delBtn.onclick = (ev) => { ev.stopPropagation(); deleteRow(p.data) }
      wrap.appendChild(testBtn)
      wrap.appendChild(editBtn)
      wrap.appendChild(delBtn)
      return wrap
    } },
])
const rows = ref<any[]>([])

async function loadRows() {
  try {
    const res = await adminCollectionApi.dataSources()
    const items = res.data.data as any[] || []
    rows.value = items.map((r: any) => ({
      _raw: r,
      id: r.id,
      name: r.source_name || '',
      dbms: r.db_type || r.source_type || '',
      host: r.connection_host || '',
      port: r.connection_port ? String(r.connection_port) : '',
      schema: r.connection_db || r.connection_schema || '',
      user: r.connection_user || '',
      hasPassword: !!r.has_password,
      pwBadge: r.has_password ? '✔ 암호화' : '미설정',
      status: r.last_test_result === 'SUCCESS' ? '연결됨' : r.status === 'ACTIVE' ? '연결됨' : (r.status || '미연결'),
    }))
  } catch (e: any) {
    console.warn('DbSource: API 실패', e)
    message.error('데이터소스 조회 실패')
  }
}
loadRows()

function openRegister() {
  Object.assign(form, {
    id: '', source_name: '', source_type: 'RDBMS', db_type: 'POSTGRESQL',
    connection_host: '', connection_port: 5432, connection_db: '', connection_schema: '',
    connection_user: '', connection_password: '', dsn_mode: '',
  })
  testResult.value = null
  showRegister.value = true
}

function onDbTypeChange() {
  // DBMS 변경 시 기본 포트 자동 반영 (사용자가 값을 이미 수정하지 않은 경우만)
  const def = DEFAULT_PORTS[form.db_type]
  if (def && (!form.connection_port || Object.values(DEFAULT_PORTS).includes(Number(form.connection_port)))) {
    form.connection_port = def
  }
}

function onRowClick(event: any) {
  // 액션 버튼 셀 클릭 시 행 상세 열지 않음
  if (event?.event?.target?.closest?.('.grid-action-btn')) return
  const raw = event.data._raw || {}
  detailData.value = {
    _raw: raw,
    name: event.data.name, dbms: event.data.dbms, host: event.data.host,
    port: event.data.port, schema: event.data.schema, user: event.data.user,
    hasPassword: event.data.hasPassword, status: event.data.status,
  }
  accounts.value = []
  schemas.value = []
  Object.keys(schemaTables).forEach(k => delete schemaTables[k])
  Object.keys(expandedSchemas).forEach(k => delete expandedSchemas[k])
  savedTestResult.value = null
  showDetail.value = true
}

function formatTestResult(result: any): string {
  if (Array.isArray(result) && result.length) {
    const row = result[0]
    if (Array.isArray(row)) return row.join(' | ').slice(0, 300)
    return JSON.stringify(row).slice(0, 300)
  }
  return JSON.stringify(result).slice(0, 300)
}

function buildOptions(): any | undefined {
  // Oracle dsn_mode 지정 시 options 로 전달
  if (form.db_type === 'ORACLE' && form.dsn_mode) {
    return { dsn_mode: form.dsn_mode }
  }
  return undefined
}

async function testConnection() {
  if (!form.connection_host) { message.warning('호스트를 입력하세요'); return }
  testing.value = true
  testResult.value = null
  try {
    const res = await adminDrApi.testConnectorConfig({
      db_type: form.db_type,
      host: form.connection_host,
      port: Number(form.connection_port) || DEFAULT_PORTS[form.db_type],
      database: form.connection_db,
      schema: form.connection_schema,
      user: form.connection_user,
      password: form.connection_password,
      options: buildOptions(),
    })
    testResult.value = res.data.data
  } catch (e: any) {
    testResult.value = { ok: false, error: e?.response?.data?.detail || e.message || '연결 실패' }
  } finally {
    testing.value = false
  }
}

async function testSaved() {
  const sid = detailData.value?._raw?.id
  if (!sid) return
  testingSaved.value = true
  savedTestResult.value = null
  try {
    const res = await adminDrApi.testConnector(sid)
    const d = res.data.data || {}
    savedTestResult.value = { ok: !!d.ok, err: d.error }
    // 목록 상태도 동기화
    await loadRows()
    message[d.ok ? 'success' : 'error'](d.ok ? '연결 성공' : '연결 실패')
  } catch (e: any) {
    savedTestResult.value = { ok: false, err: e?.response?.data?.detail || '연결 실패' }
    message.error(savedTestResult.value.err)
  } finally {
    testingSaved.value = false
  }
}

async function loadSchemas() {
  const sid = detailData.value?._raw?.id
  if (!sid) return
  loadingSchemas.value = true
  try {
    const res = await adminDrApi.listSchemas(sid)
    schemas.value = res.data.data || []
    if (!schemas.value.length) message.info('조회된 스키마가 없습니다')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '스키마 조회 실패')
  } finally {
    loadingSchemas.value = false
  }
}

async function toggleSchema(sch: string) {
  if (expandedSchemas[sch]) {
    expandedSchemas[sch] = false
    return
  }
  expandedSchemas[sch] = true
  if (schemaTables[sch]) return
  schemaLoading[sch] = true
  try {
    const sid = detailData.value?._raw?.id
    const res = await adminDrApi.listTables(sid, sch)
    schemaTables[sch] = res.data.data || []
  } catch (e: any) {
    message.error(e?.response?.data?.detail || `"${sch}" 테이블 조회 실패`)
    schemaTables[sch] = []
  } finally {
    schemaLoading[sch] = false
  }
}

async function quickTestRow(row: any) {
  const sid = row._raw?.id
  if (!sid) return
  try {
    const res = await adminDrApi.testConnector(sid)
    const d = res.data.data || {}
    message[d.ok ? 'success' : 'error'](d.ok ? `${row.name}: 연결 성공` : `${row.name}: 연결 실패`)
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '연결 실패')
  }
}

// ── 수정 · 삭제 (기 연결 DB 관리) ──
function openEdit(row: any) {
  const raw = row?._raw || {}
  Object.assign(form, {
    id: raw.id,
    source_name: raw.source_name || row.name || '',
    source_type: raw.source_type || 'RDBMS',
    db_type: raw.db_type || row.dbms || 'POSTGRESQL',
    connection_host: raw.connection_host || row.host || '',
    connection_port: raw.connection_port || Number(row.port) || DEFAULT_PORTS[raw.db_type || 'POSTGRESQL'],
    connection_db: raw.connection_db || '',
    connection_schema: raw.connection_schema || '',
    connection_user: raw.connection_user || row.user || '',
    connection_password: '', // 보안상 비움 — 입력 시에만 재암호화 저장
    dsn_mode: raw.connection_options?.dsn_mode || '',
  })
  testResult.value = null
  showRegister.value = true
}

async function deleteRow(row: any) {
  const sid = row?._raw?.id
  const name = row?.name || ''
  if (!sid) return
  if (!confirm(`'${name}' 원본DB를 삭제하시겠습니까?\n\n※ soft-delete 입니다. 저장된 계정/권한 이력은 보존됩니다.`)) return
  try {
    await adminCollectionApi.deleteDataSource(sid)
    message.success(`'${name}' 원본DB가 삭제되었습니다`)
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '삭제 실패')
  }
}

function editFromDetail() {
  const raw = detailData.value?._raw
  if (!raw?.id) return
  // row 포맷으로 맵핑
  const row = {
    _raw: raw,
    name: raw.source_name,
    dbms: raw.db_type || raw.source_type,
    host: raw.connection_host,
    port: raw.connection_port,
    user: raw.connection_user,
  }
  showDetail.value = false
  openEdit(row)
}

async function deleteFromDetail() {
  const raw = detailData.value?._raw
  if (!raw?.id) return
  const row = { _raw: raw, name: raw.source_name }
  await deleteRow(row)
  showDetail.value = false
}

async function handleSave() {
  if (!form.source_name) { message.warning('DB명을 입력하세요'); return }
  saving.value = true
  try {
    const payload: any = {
      source_name: form.source_name, source_type: form.source_type, db_type: form.db_type,
      connection_host: form.connection_host, connection_port: Number(form.connection_port) || null,
      connection_db: form.connection_db, connection_schema: form.connection_schema,
      connection_user: form.connection_user,
      connection_password: form.connection_password || null,
    }
    const opts = buildOptions()
    if (opts) payload.connection_options = opts
    if (form.id) {
      await adminCollectionApi.updateDataSource(form.id, payload)
      message.success('수정되었습니다')
    } else {
      await adminCollectionApi.createDataSource(payload)
      message.success('등록되었습니다')
    }
    showRegister.value = false
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '저장 실패')
  } finally {
    saving.value = false
  }
}

async function loadAccounts() {
  if (!detailData.value._raw?.id) return
  try {
    const res = await adminDrApi.listAccounts(detailData.value._raw.id)
    accounts.value = res.data.data || []
    if (!accounts.value.length) message.info('조회된 계정이 없습니다')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '계정 조회 실패')
  }
}

async function createAccount() {
  if (!newAcct.account_name || !newAcct.password) { message.warning('계정명과 비밀번호를 입력하세요'); return }
  try {
    await adminDrApi.createAccount(detailData.value._raw.id, { ...newAcct })
    message.success('계정이 생성되었습니다')
    showCreateAcct.value = false
    newAcct.account_name = ''; newAcct.password = ''; newAcct.note = ''
    await loadAccounts()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '계정 생성 실패')
  }
}

async function dropAccount(name: string) {
  if (!confirm(`계정 '${name}' 을(를) 삭제하시겠습니까?`)) return
  try {
    await adminDrApi.dropAccount(detailData.value._raw.id, name)
    message.success('삭제되었습니다')
    await loadAccounts()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '삭제 실패')
  }
}

async function changePassword(name: string) {
  const pw = prompt(`'${name}' 의 새 비밀번호 (최소 8자):`)
  if (!pw) return
  try {
    await adminDrApi.changeAccountPassword(detailData.value._raw.id, name, { new_password: pw })
    message.success('비밀번호가 변경되었습니다')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '비밀번호 변경 실패')
  }
}

function showGrantRevoke(mode: 'GRANT' | 'REVOKE') {
  if (!accounts.value.length) { message.warning('먼저 계정을 조회하세요'); return }
  grMode.value = mode
  grForm.account_name = accounts.value[0]?.account_name || ''
  grForm.privileges = []
  grForm.schema = ''; grForm.table = ''; grForm.note = ''
  showGR.value = true
}

async function applyGrantRevoke() {
  if (!grForm.account_name || !grForm.privileges.length) { message.warning('계정과 권한을 선택하세요'); return }
  try {
    const payload = {
      privileges: grForm.privileges,
      schema: grForm.schema || undefined,
      table: grForm.table || undefined,
      note: grForm.note || undefined,
    }
    if (grMode.value === 'GRANT') {
      await adminDrApi.grantPrivileges(detailData.value._raw.id, grForm.account_name, payload)
      message.success('권한이 부여되었습니다')
    } else {
      await adminDrApi.revokePrivileges(detailData.value._raw.id, grForm.account_name, payload)
      message.success('권한이 회수되었습니다')
    }
    showGR.value = false
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '처리 실패')
  }
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.muted { color: #888; font-size: 0.85em; font-weight: normal; }
.acct-toolbar { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.acct-empty { color: #888; padding: 12px; text-align: center; background: #f7f8fa; border-radius: 4px; }
.acct-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.acct-table th, .acct-table td { border-bottom: 1px solid #eee; padding: 6px 8px; text-align: left; }
.acct-table th { background: #f7f8fa; font-weight: 600; }
.acct-table code { background: #f0f2f5; padding: 2px 4px; border-radius: 3px; font-size: 11px; }
.priv-checks { display: flex; flex-wrap: wrap; gap: 10px; }
.priv-checks label { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; }
.btn-xs { padding: 2px 6px; font-size: 11px; margin-right: 4px; }
.text-danger { color: #d4380d; }

/* 연결 테스트 결과 배너 */
.conn-test-result {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; margin-top: 8px; border-radius: 4px;
  font-size: 13px; border: 1px solid;
  &.ok { background: #f6ffed; border-color: #b7eb8f; color: #135200; }
  &.fail { background: #fff2f0; border-color: #ffccc7; color: #820014; }
  :deep(.anticon) { font-size: 18px; margin-top: 2px; }
}
.conn-test-title { font-weight: 600; }
.conn-test-detail { margin-top: 4px; font-size: 12px; word-break: break-all; }
.conn-test-detail.err { color: #820014; }
.conn-test-content { flex: 1; }

/* 인라인 배지 */
.inline-badge {
  display: inline-flex; align-items: center; padding: 2px 8px;
  border-radius: 10px; font-size: 11px; font-weight: 600;
  &.ok { background: #f6ffed; color: #135200; border: 1px solid #b7eb8f; }
  &.fail { background: #fff2f0; color: #820014; border: 1px solid #ffccc7; }
}

/* 스키마 트리 */
.schema-tree { max-height: 260px; overflow-y: auto; border: 1px solid #eee; border-radius: 4px; padding: 6px; background: #fff; }
.schema-row { display: flex; align-items: center; gap: 6px; padding: 4px 6px; cursor: pointer; border-radius: 3px; }
.schema-row:hover { background: #f0f5ff; }
.tree-toggle { width: 14px; display: inline-block; color: #888; font-size: 10px; }
.table-list { list-style: none; margin: 0; padding: 4px 6px 4px 28px; }
.table-list li { padding: 2px 0; font-size: 12px; color: #555; display: flex; align-items: center; gap: 4px; }
.pad-left { padding-left: 28px; font-size: 12px; }

/* 그리드 행 액션 버튼들 (테스트/수정/삭제) */
:deep(.grid-action-wrap) {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  height: 100%;
}
:deep(.grid-action-btn) {
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 11px;
  color: #1677ff;
  cursor: pointer;
  transition: all 0.15s;
  line-height: 1.4;
}
:deep(.grid-action-btn:hover) {
  border-color: #1677ff;
  background: #e6f4ff;
}
:deep(.grid-action-btn.edit) { color: #595959; }
:deep(.grid-action-btn.edit:hover) { border-color: #8c8c8c; background: #f5f5f5; }
:deep(.grid-action-btn.del) { color: #cf1322; }
:deep(.grid-action-btn.del:hover) { border-color: #cf1322; background: #fff1f0; }

/* 상세 모달 삭제 버튼 */
.btn-danger {
  background: #ff4d4f;
  color: #fff;
  border: 1px solid #ff4d4f;
  &:hover { background: #d9363e; border-color: #d9363e; }
  &:disabled { background: #ffccc7; border-color: #ffccc7; cursor: not-allowed; }
}
</style>
