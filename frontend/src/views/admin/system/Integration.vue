<template>
  <div class="admin-page">
    <div class="page-header"><h2>이기종 통합</h2><p class="page-desc">이기종 시스템 간 데이터 통합 연계 현황을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">연계 현황 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="openRegister"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '이기종_통합_현황')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 상세/수정 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.integration_name + ' 상세'" size="lg" @close="showDetail = false">
      <!-- 탭 -->
      <div class="tab-nav">
        <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</button>
      </div>

      <!-- 연계 정보 탭 -->
      <div v-show="activeTab === 'info'" class="modal-section">
        <template v-if="!isEditing">
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">통합명</span><span class="info-value">{{ detailData.integration_name }}</span></div>
            <div class="modal-info-item"><span class="info-label">원본 DB유형</span><span class="info-value">{{ detailData.source_db_type }}</span></div>
            <div class="modal-info-item"><span class="info-label">동기화 방향</span><span class="info-value">{{ directionLabel(detailData.sync_direction) }}</span></div>
            <div class="modal-info-item"><span class="info-label">동기화 상태</span><span class="info-value"><span class="badge" :class="statusBadge(detailData.sync_status)">{{ statusLabel(detailData.sync_status) }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">최근 동기화</span><span class="info-value">{{ formatDt(detailData.last_sync_at) }}</span></div>
          </div>
        </template>
        <template v-else>
          <div class="modal-form">
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">통합명</label><input v-model="editForm.integration_name" /></div>
              <div class="modal-form-group"><label class="required">원본 DB유형</label><select v-model="editForm.source_db_type" @change="onDbTypeChange(editForm)"><option v-for="d in dbTypes" :key="d" :value="d">{{ d }}</option></select></div>
            </div>
            <div class="modal-form-group"><label>동기화 방향</label><select v-model="editForm.sync_direction"><option v-for="s in syncDirs" :key="s" :value="s">{{ directionLabel(s) }}</option></select></div>
          </div>
        </template>
      </div>

      <!-- 연결 설정 탭 -->
      <div v-show="activeTab === 'connection'" class="modal-section">
        <div class="modal-section-title">연결 설정</div>
        <template v-if="!isEditing">
          <div class="modal-info-grid">
            <div class="modal-info-item" v-for="(v, k) in connDisplay" :key="k"><span class="info-label">{{ k }}</span><span class="info-value">{{ k === 'password' ? '********' : v }}</span></div>
          </div>
        </template>
        <template v-else>
          <div class="modal-form">
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">호스트</label><input v-model="editForm.connection_config.host" placeholder="10.0.1.100" /></div>
              <div class="modal-form-group"><label class="required">포트</label><input type="number" v-model.number="editForm.connection_config.port" /></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>데이터베이스</label><input v-model="editForm.connection_config.database" /></div>
              <div class="modal-form-group"><label>스키마</label><input v-model="editForm.connection_config.schema" /></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">사용자</label><input v-model="editForm.connection_config.user" /></div>
              <div class="modal-form-group"><label>비밀번호</label><input type="password" v-model="editForm.connection_config.password" /></div>
            </div>
          </div>
        </template>
      </div>

      <!-- 매핑 설정 탭 -->
      <div v-show="activeTab === 'mapping'" class="modal-section">
        <div class="modal-section-title">필드 매핑<button v-if="isEditing" class="btn btn-sm btn-outline" style="margin-left:8px" @click="addMapping"><PlusOutlined /> 추가</button></div>
        <table class="data-table" v-if="mappings.length > 0">
          <thead><tr><th>소스 컬럼</th><th>대상 컬럼</th><th>변환</th><th v-if="isEditing" style="width:40px"></th></tr></thead>
          <tbody>
            <tr v-for="(m, i) in mappings" :key="i">
              <template v-if="!isEditing">
                <td>{{ m.source }}</td><td>{{ m.target }}</td><td>{{ m.transform || '-' }}</td>
              </template>
              <template v-else>
                <td><input v-model="m.source" class="table-input" /></td>
                <td><input v-model="m.target" class="table-input" /></td>
                <td><input v-model="m.transform" class="table-input" placeholder="선택" /></td>
                <td><button class="btn-icon-danger" @click="mappings.splice(i, 1)"><DeleteOutlined /></button></td>
              </template>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-text">매핑 설정이 없습니다.</div>
      </div>

      <!-- 동기화 이력 탭 -->
      <div v-show="activeTab === 'history'" class="modal-section">
        <div class="modal-section-title">동기화 이력</div>
        <div class="ag-grid-wrapper" v-if="logRows.length > 0"><AgGridVue class="ag-theme-alpine" :rowData="logRows" :columnDefs="logCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="5" domLayout="autoHeight" /></div>
        <div v-else class="empty-text">동기화 이력이 없습니다.</div>
      </div>

      <template #footer>
        <template v-if="!isEditing">
          <button class="btn btn-outline" @click="handleTest" :disabled="testing"><ApiOutlined /> {{ testing ? '테스트 중...' : '연결 테스트' }}</button>
          <button class="btn btn-outline" @click="handleSync" :disabled="syncing"><SyncOutlined /> {{ syncing ? '동기화 중...' : '수동 동기화' }}</button>
          <button class="btn btn-primary" @click="startEdit"><EditOutlined /> 수정</button>
          <button class="btn btn-danger" @click="handleDelete"><DeleteOutlined /> 삭제</button>
          <button class="btn btn-outline" @click="showDetail = false">닫기</button>
        </template>
        <template v-else>
          <button class="btn btn-primary" @click="handleSaveEdit"><SaveOutlined /> 저장</button>
          <button class="btn btn-outline" @click="isEditing = false">취소</button>
        </template>
      </template>
    </AdminModal>

    <!-- 등록 팝업 -->
    <AdminModal :visible="showRegister" title="이기종 통합 등록" size="lg" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">통합명</label><input v-model="regForm.integration_name" placeholder="통합명 입력" /></div>
          <div class="modal-form-group"><label class="required">원본 DB유형</label><select v-model="regForm.source_db_type" @change="onDbTypeChange(regForm)"><option v-for="d in dbTypes" :key="d" :value="d">{{ d }}</option></select></div>
        </div>
        <div class="modal-form-group"><label>동기화 방향</label><select v-model="regForm.sync_direction"><option v-for="s in syncDirs" :key="s" :value="s">{{ directionLabel(s) }}</option></select></div>
        <div class="modal-section-title" style="margin-top:12px">연결 설정</div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">호스트</label><input v-model="regForm.connection_config.host" placeholder="10.0.1.100" /></div>
          <div class="modal-form-group"><label class="required">포트</label><input type="number" v-model.number="regForm.connection_config.port" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>데이터베이스</label><input v-model="regForm.connection_config.database" /></div>
          <div class="modal-form-group"><label>스키마</label><input v-model="regForm.connection_config.schema" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">사용자</label><input v-model="regForm.connection_config.user" /></div>
          <div class="modal-form-group"><label>비밀번호</label><input type="password" v-model="regForm.connection_config.password" /></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, reactive, computed, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined, ApiOutlined, SyncOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const dbTypes = ['ORACLE', 'TIBERO', 'POSTGRESQL', 'MYSQL', 'MSSQL', 'MONGODB', 'SAP']
const syncDirs = ['INBOUND', 'OUTBOUND', 'BIDIRECTIONAL']
const defaultPorts: Record<string, number> = { ORACLE: 1521, TIBERO: 8629, POSTGRESQL: 5432, MYSQL: 3306, MSSQL: 1433, MONGODB: 27017, SAP: 3200 }
const tabs = [{ key: 'info', label: '연계 정보' }, { key: 'connection', label: '연결 설정' }, { key: 'mapping', label: '매핑 설정' }, { key: 'history', label: '동기화 이력' }]

const showDetail = ref(false), showRegister = ref(false), isEditing = ref(false)
const testing = ref(false), syncing = ref(false), activeTab = ref('info')
const detailData = ref<any>({})
const editForm = reactive<any>({ connection_config: {} })
const mappings = ref<any[]>([])
const logRows = ref<any[]>([])

const initRegForm = () => ({
  integration_name: '', source_db_type: 'ORACLE', sync_direction: 'INBOUND',
  connection_config: { host: '', port: 1521, database: '', schema: '', user: '', password: '' },
})
const regForm = reactive(initRegForm())

function onDbTypeChange(form: any) {
  form.connection_config.port = defaultPorts[form.source_db_type] || 5432
}

function directionLabel(d: string) { return d === 'INBOUND' ? '수신' : d === 'OUTBOUND' ? '송신' : d === 'BIDIRECTIONAL' ? '양방향' : d || '-' }
function statusLabel(s: string) { return s === 'SUCCESS' ? '정상' : s === 'IDLE' ? '대기' : s === 'RUNNING' ? '실행 중' : s === 'FAIL' ? '실패' : s || '-' }
function statusBadge(s: string) { return s === 'SUCCESS' || s === 'IDLE' ? 'badge-success' : s === 'FAIL' ? 'badge-danger' : 'badge-warning' }
function formatDt(dt: string | null) { return dt ? String(dt).replace('T', ' ').substring(0, 19) : '-' }

const connDisplay = computed(() => {
  const c = detailData.value?.connection_config
  if (!c || typeof c !== 'object') return {}
  return c
})

const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 45 },
  { headerName: '통합명', field: 'integration_name', flex: 1.5 },
  { headerName: 'DB유형', field: 'source_db_type', width: 90 },
  { headerName: '방향', field: '_direction', width: 70 },
  { headerName: '상태', field: '_status', width: 70 },
  { headerName: '최근 동기화', field: '_lastSync', width: 140 },
])

const logCols = withHeaderTooltips([
  { headerName: '실행일시', field: 'started_at', width: 140 },
  { headerName: '유형', field: 'execution_type', width: 70 },
  { headerName: '상태', field: 'status', width: 70 },
  { headerName: '소요시간', field: 'duration_label', width: 80 },
  { headerName: '전체건수', field: 'total_records', width: 75 },
  { headerName: '성공', field: 'success_records', width: 60 },
  { headerName: '오류', field: 'error_records', width: 60 },
])

const rows = ref<any[]>([])

async function loadData() {
  try {
    const res = await adminSystemApi.integrations()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        ...r,
        _direction: directionLabel(r.sync_direction),
        _status: statusLabel(r.sync_status),
        _lastSync: formatDt(r.last_sync_at),
      }))
    }
  } catch (e) {
    console.warn('Integration: API call failed, using mock data', e)
    rows.value = [
      { integration_name: 'Oracle (수자원)', source_db_type: 'ORACLE', _direction: '수신', _status: '정상', _lastSync: '2026-03-25 08:00' },
      { integration_name: 'MySQL (경영)', source_db_type: 'MYSQL', _direction: '수신', _status: '정상', _lastSync: '2026-03-25 06:00' },
      { integration_name: 'MongoDB (IoT)', source_db_type: 'MONGODB', _direction: '수신', _status: '지연', _lastSync: '2026-03-25 09:00' },
    ]
  }
}

onMounted(() => loadData())

function openRegister() {
  Object.assign(regForm, initRegForm())
  showRegister.value = true
}

async function onRowClick(event: any) {
  const row = event.data
  activeTab.value = 'info'
  isEditing.value = false
  if (row.id) {
    try {
      const res = await adminSystemApi.getIntegration(row.id)
      detailData.value = res.data.data
    } catch { detailData.value = row }
  } else {
    detailData.value = row
  }
  // 매핑 파싱
  const mc = detailData.value?.mapping_config
  mappings.value = mc?.mappings ? [...mc.mappings] : []
  showDetail.value = true
  loadLogs()
}

async function loadLogs() {
  logRows.value = []
  const id = detailData.value?.id
  if (!id) return
  try {
    const res = await adminSystemApi.integrationLogs(id, { page_size: 20 })
    const items = res.data.items || []
    logRows.value = items.map((l: any) => ({
      ...l,
      started_at: l.started_at ? String(l.started_at).replace('T', ' ').substring(0, 19) : '-',
      duration_label: l.duration_ms != null ? (l.duration_ms >= 1000 ? (l.duration_ms / 1000).toFixed(1) + 's' : l.duration_ms + 'ms') : '-',
    }))
  } catch { /* no logs */ }
}

function startEdit() {
  const d = detailData.value
  const cc = d.connection_config && typeof d.connection_config === 'object' ? { ...d.connection_config } : { host: '', port: 5432, database: '', schema: '', user: '', password: '' }
  Object.assign(editForm, {
    integration_name: d.integration_name, source_db_type: d.source_db_type,
    sync_direction: d.sync_direction, connection_config: cc,
  })
  mappings.value = d.mapping_config?.mappings ? d.mapping_config.mappings.map((m: any) => ({ ...m })) : []
  isEditing.value = true
}

function addMapping() { mappings.value.push({ source: '', target: '', transform: '' }) }

async function handleSaveEdit() {
  const id = detailData.value?.id
  if (!id) return
  try {
    await adminSystemApi.updateIntegration(id, {
      ...editForm,
      mapping_config: mappings.value.length > 0 ? { mappings: mappings.value } : null,
    })
    message.success('수정되었습니다.')
    isEditing.value = false
    showDetail.value = false
    await loadData()
  } catch { message.error('수정에 실패했습니다.') }
}

async function handleRegister() {
  if (!regForm.integration_name.trim()) { message.warning('통합명을 입력해주세요.'); return }
  try {
    await adminSystemApi.createIntegration({ ...regForm })
    message.success('등록되었습니다.')
    showRegister.value = false
    await loadData()
  } catch { message.error('등록에 실패했습니다.') }
}

async function handleDelete() {
  const id = detailData.value?.id
  if (!id) { message.warning('삭제할 수 없습니다.'); return }
  try {
    await adminSystemApi.deleteIntegration(id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    await loadData()
  } catch { message.error('삭제에 실패했습니다.') }
}

async function handleTest() {
  const id = detailData.value?.id
  if (!id) return
  testing.value = true
  try {
    const res = await adminSystemApi.testIntegration(id)
    message.success(res.data.message || '연결 테스트 성공')
  } catch { message.error('연결 테스트에 실패했습니다.') }
  finally { testing.value = false }
}

async function handleSync() {
  const id = detailData.value?.id
  if (!id) return
  syncing.value = true
  try {
    const res = await adminSystemApi.syncIntegration(id)
    message.success(res.data.message || '동기화 완료')
    await loadData()
    await loadLogs()
  } catch { message.error('동기화에 실패했습니다.') }
  finally { syncing.value = false }
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.tab-nav { display: flex; gap: 0; border-bottom: 2px solid #e8e8e8; margin-bottom: 12px; }
.tab-btn { padding: 8px 16px; border: none; background: none; cursor: pointer; font-size: 13px; font-weight: 500; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px;
  &.active { color: #0066CC; border-bottom-color: #0066CC; font-weight: 600; }
  &:hover { color: #0066CC; }
}
.empty-text { padding: 20px; text-align: center; color: #999; font-size: 13px; }
.data-table { width: 100%; font-size: 13px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }
}
.table-input { width: 100%; padding: 4px 6px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }
.btn-icon-danger { border: none; background: none; color: #ff4d4f; cursor: pointer; padding: 2px 6px; }
</style>
