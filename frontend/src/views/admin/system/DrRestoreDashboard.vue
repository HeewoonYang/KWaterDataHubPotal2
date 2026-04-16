<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>재해복구 / PIT 복구 대시보드</h2>
      <p class="page-desc">백업 스케줄, 포인트-인-타임 복구, 복구 실행 이력, DB 계정 이력을 한 화면에서 관리합니다. (REQ-DHUB-005-003)</p>
    </div>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-icon" style="background:#e6f7ff;color:#0066CC"><CloudServerOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ stats.total || 0 }}</div><div class="kpi-label">최근 {{ dashboardDays }}일 복구시도</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f6ffed;color:#28A745"><CheckCircleOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ stats.success_rate || 0 }}%</div><div class="kpi-label">성공률 ({{ stats.success }}/{{ stats.total }})</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff1f0;color:#DC3545"><WarningOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ stats.failed || 0 }}</div><div class="kpi-label">실패</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff7e6;color:#fa8c16"><ClockCircleOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ Math.round(stats.avg_duration_sec || 0) }}초</div><div class="kpi-label">평균 소요시간</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f9f0ff;color:#9b59b6"><DatabaseOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ (stats.total_restored_rows || 0).toLocaleString() }}</div><div class="kpi-label">복구 행수 (누적)</div></div></div>
    </div>

    <!-- 드라이버/OM 상태 -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">DB 커넥터 드라이버 현황</div>
        <table class="data-table">
          <thead><tr><th>드라이버</th><th>버전</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="c in connectors" :key="c.driver">
              <td><strong>{{ c.driver.toUpperCase() }}</strong></td>
              <td class="mono">{{ c.version }}</td>
              <td><span class="status-badge" :class="c.available ? 'active' : 'inactive'">{{ c.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-title">OpenMetadata 연동 상태</div>
        <div class="modal-info-grid" style="grid-template-columns: 1fr 2fr;">
          <div class="modal-info-item"><span class="info-label">연동 활성</span><span class="info-value"><span class="status-badge" :class="omStatus.configured ? 'active' : 'inactive'">{{ omStatus.configured ? '활성' : '미연결' }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">Base URL</span><span class="info-value mono">{{ omStatus.base_url || '미설정' }}</span></div>
          <div class="modal-info-item"><span class="info-label">토큰</span><span class="info-value">{{ omStatus.token_set ? '설정됨' : '미설정' }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 {{ omDays }}일</span><span class="info-value">전체 {{ omStats.total || 0 }} / 성공 {{ omStats.success || 0 }} / 실패 {{ omStats.failed || 0 }} / SKIP {{ omStats.skipped || 0 }}</span></div>
        </div>
        <div style="margin-top:10px;display:flex;gap:6px;">
          <button class="btn btn-xs btn-outline" @click="syncPending"><SyncOutlined /> 대기분 동기화</button>
          <button class="btn btn-xs btn-outline" @click="loadOmLogs"><ReloadOutlined /> 로그 새로고침</button>
        </div>
      </div>
    </div>

    <!-- 백업 설정 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">
        백업 설정
        <span class="card-title-right">
          <button class="btn btn-sm btn-primary" @click="openBackupEditor(null)"><PlusOutlined /> 백업 등록</button>
        </span>
      </div>
      <table class="data-table">
        <thead><tr><th>백업명</th><th>유형</th><th>대상</th><th>스케줄</th><th>보관(일)</th><th>최근실행</th><th>결과</th><th>활성</th><th style="width:150px;">액션</th></tr></thead>
        <tbody>
          <tr v-for="b in backups" :key="b.id">
            <td><strong>{{ b.backup_name }}</strong></td>
            <td><span class="type-badge">{{ b.backup_type }}</span></td>
            <td>{{ b.target_system || '-' }}</td>
            <td class="mono">{{ b.schedule_cron || '-' }}</td>
            <td>{{ b.retention_days }}</td>
            <td>{{ b.last_backup_at ? b.last_backup_at.substring(0,16).replace('T',' ') : '-' }}</td>
            <td><span class="status-badge" :class="b.last_backup_status === 'SUCCESS' ? 'active' : 'inactive'">{{ b.last_backup_status || '-' }}</span></td>
            <td><span class="status-badge" :class="b.is_active ? 'active' : 'inactive'">{{ b.is_active ? 'ON' : 'OFF' }}</span></td>
            <td>
              <button class="btn btn-xs btn-outline" @click="runBackup(b)" title="즉시실행"><PlayCircleOutlined /></button>
              <button class="btn btn-xs btn-outline" @click="openBackupEditor(b)"><EditOutlined /></button>
              <button class="btn btn-xs btn-danger" @click="delBackup(b)"><DeleteOutlined /></button>
            </td>
          </tr>
          <tr v-if="!backups.length"><td colspan="9" style="text-align:center;color:#888;padding:20px;">등록된 백업이 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- PIT 복구 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">
        PIT (Point-In-Time) 복구
        <span class="card-title-right">
          <button class="btn btn-sm btn-primary" @click="openPitEditor(null)"><PlusOutlined /> 복구 등록</button>
        </span>
      </div>
      <table class="data-table">
        <thead><tr><th>복구명</th><th>목표시각</th><th>참조백업</th><th>시뮬레이션</th><th>승인</th><th>상태</th><th style="width:260px;">액션</th></tr></thead>
        <tbody>
          <tr v-for="p in pits" :key="p.id">
            <td><strong>{{ p.recovery_name }}</strong></td>
            <td class="mono">{{ p.target_timestamp ? p.target_timestamp.substring(0,19).replace('T',' ') : '-' }}</td>
            <td class="mono">{{ p.target_backup_id ? p.target_backup_id.substring(0,8) : '-' }}</td>
            <td><span class="status-badge" :class="p.simulation_only ? 'inactive' : 'active'">{{ p.simulation_only ? '시뮬레이션만' : '실복구가능' }}</span></td>
            <td><span class="badge" :class="p.approval_status === 'APPROVED' ? 'badge-success' : 'badge-warning'">{{ p.approval_status }}</span></td>
            <td><span class="badge" :class="`badge-${pitStatusClass(p.status)}`">{{ p.status }}</span></td>
            <td>
              <button class="btn btn-xs btn-outline" @click="simulatePit(p)"><ExperimentOutlined /> 시뮬레이션</button>
              <button class="btn btn-xs btn-outline" @click="approvePit(p)" :disabled="p.approval_status === 'APPROVED' || p.simulation_only">승인</button>
              <button class="btn btn-xs btn-warning" @click="executePit(p)" :disabled="p.approval_status !== 'APPROVED'" title="실제 복구 실행">
                <ThunderboltOutlined /> 실행
              </button>
              <button class="btn btn-xs btn-outline" @click="viewPit(p)"><EyeOutlined /></button>
            </td>
          </tr>
          <tr v-if="!pits.length"><td colspan="7" style="text-align:center;color:#888;padding:20px;">등록된 PIT 복구가 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 최근 복구 로그 + OM 로그 -->
    <div class="grid-2" style="margin-top:16px;">
      <div class="card">
        <div class="card-title">
          최근 복구 로그
          <span class="card-title-right"><button class="btn btn-xs btn-outline" @click="loadRestoreLogs"><ReloadOutlined /></button></span>
        </div>
        <table class="data-table">
          <thead><tr><th>유형</th><th>대상</th><th>시작</th><th>소요</th><th>행수</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="r in restoreLogs" :key="r.id">
              <td><span class="type-badge">{{ r.restore_type }}</span></td>
              <td>{{ r.target_system || r.source_system || '-' }}</td>
              <td class="mono">{{ r.started_at ? r.started_at.substring(5,16).replace('T',' ') : '-' }}</td>
              <td>{{ r.duration_sec || 0 }}초</td>
              <td>{{ (r.restored_rows || 0).toLocaleString() }}</td>
              <td><span class="badge" :class="r.status === 'SUCCESS' ? 'badge-success' : 'badge-warning'">{{ r.status }}</span></td>
            </tr>
            <tr v-if="!restoreLogs.length"><td colspan="6" style="text-align:center;color:#888;padding:20px;">복구 로그 없음</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-title">
          OpenMetadata 동기화 로그
          <span class="card-title-right">
            <select v-model="omFilterStatus" @change="loadOmLogs" class="select-sm">
              <option value="">전체</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAIL">FAIL</option>
              <option value="SKIPPED">SKIPPED</option>
            </select>
          </span>
        </div>
        <table class="data-table">
          <thead><tr><th>엔티티</th><th>이름</th><th>HTTP</th><th>소요</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="l in omLogs" :key="l.id">
              <td><span class="type-badge">{{ l.entity_type }}</span></td>
              <td>{{ l.entity_name || l.entity_id?.substring(0,8) }}</td>
              <td>{{ l.http_status || '-' }}</td>
              <td>{{ l.duration_ms || 0 }}ms</td>
              <td><span class="badge" :class="omStatusClass(l.status)">{{ l.status }}</span></td>
            </tr>
            <tr v-if="!omLogs.length"><td colspan="5" style="text-align:center;color:#888;padding:20px;">동기화 로그 없음</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- DB 계정 이력 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">
        DB 계정 이력
        <span class="card-title-right">
          <select v-model="acctSourceId" @change="loadAccountHistory" class="select-sm">
            <option value="">전체 소스</option>
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.source_name }}</option>
          </select>
          <button class="btn btn-xs btn-outline" @click="snapshotAccounts" :disabled="!acctSourceId"><CameraOutlined /> 현재 계정 스냅샷</button>
        </span>
      </div>
      <table class="data-table">
        <thead><tr><th>일시</th><th>소스</th><th>계정</th><th>액션</th><th>비고</th></tr></thead>
        <tbody>
          <tr v-for="a in accountHistory" :key="a.id">
            <td class="mono">{{ a.changed_at ? a.changed_at.substring(0,19).replace('T',' ') : '-' }}</td>
            <td>{{ sourceNameMap[a.source_id] || '-' }}</td>
            <td><strong>{{ a.account_name }}</strong></td>
            <td><span class="badge" :class="`badge-${a.action.toLowerCase()}`">{{ a.action }}</span></td>
            <td>{{ a.note || '-' }}</td>
          </tr>
          <tr v-if="!accountHistory.length"><td colspan="5" style="text-align:center;color:#888;padding:20px;">계정 이력 없음 — 위 [현재 계정 스냅샷] 버튼으로 시작하세요.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 백업 편집 모달 -->
    <AdminModal :visible="showBackupEditor" :title="backupForm.id ? '백업 수정' : '백업 등록'" size="md" @close="showBackupEditor = false">
      <div class="modal-form">
        <div class="form-row"><label>백업명 *</label><input v-model="backupForm.backup_name" placeholder="예: 운영DB 일간 풀백업" /></div>
        <div class="form-row"><label>유형 *</label>
          <select v-model="backupForm.backup_type">
            <option>FULL</option><option>INCREMENTAL</option><option>DIFFERENTIAL</option>
          </select>
        </div>
        <div class="form-row"><label>대상 소스</label>
          <select v-model="backupForm.source_id">
            <option :value="null">(직접 명령어 사용)</option>
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.source_name }} ({{ s.db_type || s.source_type }})</option>
          </select>
        </div>
        <div class="form-row"><label>대상 시스템명</label><input v-model="backupForm.target_system" placeholder="예: OPS-DB" /></div>
        <div class="form-row"><label>스케줄 CRON</label><input v-model="backupForm.schedule_cron" class="mono" placeholder="0 2 * * * (매일 02시)" /></div>
        <div class="form-row"><label>보관기간(일)</label><input type="number" v-model.number="backupForm.retention_days" min="1" /></div>
        <div class="form-row"><label>저장 경로</label><input v-model="backupForm.storage_path" placeholder="s3://backups/ 또는 /mnt/backup" /></div>
        <div class="form-row"><label>백업 명령 (선택)</label><textarea v-model="backupForm.backup_command" rows="2" class="mono" placeholder="$HOST,$PORT,$DB,$USER,$PASSWORD,$FILE 치환 지원"></textarea></div>
        <div class="form-row"><label>활성화</label>
          <label class="switch"><input type="checkbox" v-model="backupForm.is_active" /><span>{{ backupForm.is_active ? '사용' : '미사용' }}</span></label>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="saveBackup"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showBackupEditor = false">취소</button>
      </template>
    </AdminModal>

    <!-- PIT 편집 모달 -->
    <AdminModal :visible="showPitEditor" :title="pitForm.id ? 'PIT 복구 수정' : 'PIT 복구 등록'" size="md" @close="showPitEditor = false">
      <div class="modal-form">
        <div class="form-notice"><InfoCircleOutlined /> PIT 복구는 <strong>시뮬레이션 → 승인 → 실행</strong> 단계를 거칩니다. 시뮬레이션만 플래그가 켜진 경우 실제 복구는 수행되지 않습니다.</div>
        <div class="form-row"><label>복구명 *</label><input v-model="pitForm.recovery_name" placeholder="예: OPS-DB 2026-04-10 오전 시점 복원" /></div>
        <div class="form-row"><label>대상 소스</label>
          <select v-model="pitForm.target_source_id">
            <option :value="null">선택</option>
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.source_name }}</option>
          </select>
        </div>
        <div class="form-row"><label>참조 백업</label>
          <select v-model="pitForm.target_backup_id">
            <option :value="null">(선택 안 함)</option>
            <option v-for="b in backups" :key="b.id" :value="b.id">{{ b.backup_name }}</option>
          </select>
        </div>
        <div class="form-row"><label>목표 복원 시각 *</label><input type="datetime-local" v-model="pitForm.target_timestamp" /></div>
        <div class="form-row"><label>시뮬레이션만</label>
          <label class="switch"><input type="checkbox" v-model="pitForm.simulation_only" /><span>{{ pitForm.simulation_only ? '실복구 금지' : '실복구 허용' }}</span></label>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="savePit"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showPitEditor = false">취소</button>
      </template>
    </AdminModal>

    <!-- PIT 결과 조회 모달 -->
    <AdminModal :visible="showPitView" :title="`복구 상세 - ${pitView?.recovery_name || ''}`" size="md" @close="showPitView = false">
      <div v-if="pitView" class="modal-section">
        <div class="modal-section-title">시뮬레이션 결과</div>
        <pre class="json-preview" v-if="pitView.simulation_result">{{ JSON.stringify(pitView.simulation_result, null, 2) }}</pre>
        <p v-else style="color:#888;">시뮬레이션 미실행</p>
      </div>
      <div v-if="pitView?.execution_result" class="modal-section">
        <div class="modal-section-title">실행 결과</div>
        <pre class="json-preview">{{ JSON.stringify(pitView.execution_result, null, 2) }}</pre>
      </div>
      <template #footer><button class="btn btn-outline" @click="showPitView = false">닫기</button></template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import {
  CloudServerOutlined, CheckCircleOutlined, WarningOutlined, ClockCircleOutlined, DatabaseOutlined,
  SyncOutlined, ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined,
  PlayCircleOutlined, ExperimentOutlined, ThunderboltOutlined, EyeOutlined,
  CameraOutlined, InfoCircleOutlined, SaveOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import { adminDrApi, adminCollectionApi } from '../../../api/admin.api'
import AdminModal from '../../../components/AdminModal.vue'

const dashboardDays = ref(30)
const omDays = ref(7)
const stats = ref<any>({})
const connectors = ref<any[]>([])
const omStatus = ref<any>({})
const omStats = ref<any>({})
const backups = ref<any[]>([])
const pits = ref<any[]>([])
const restoreLogs = ref<any[]>([])
const omLogs = ref<any[]>([])
const sources = ref<any[]>([])
const accountHistory = ref<any[]>([])
const acctSourceId = ref<string>('')
const omFilterStatus = ref<string>('')

const sourceNameMap = computed<Record<string, string>>(() => {
  const m: Record<string, string> = {}
  for (const s of sources.value) m[s.id] = s.source_name
  return m
})

// 편집 상태
const showBackupEditor = ref(false)
const showPitEditor = ref(false)
const showPitView = ref(false)
const pitView = ref<any>(null)

const backupForm = reactive<any>({
  id: null, backup_name: '', backup_type: 'FULL', target_system: '',
  schedule_cron: '0 2 * * *', retention_days: 30, storage_path: '',
  source_id: null, backup_command: '', is_active: true,
})
const pitForm = reactive<any>({
  id: null, recovery_name: '', target_source_id: null, target_backup_id: null,
  target_timestamp: '', simulation_only: true,
})

function pitStatusClass(s: string) {
  if (s === 'COMPLETED') return 'success'
  if (s === 'FAILED') return 'danger'
  if (s === 'EXECUTING') return 'info'
  if (s === 'READY' || s === 'SIMULATED') return 'warning'
  return 'default'
}
function omStatusClass(s: string) {
  return { SUCCESS: 'badge-success', FAIL: 'badge-warning', SKIPPED: 'badge-default', PENDING: 'badge-info' }[s] || 'badge-default'
}

async function loadAll() {
  try {
    const [drv, om, omd, bks, ps, rls, ols, srcs] = await Promise.all([
      adminDrApi.connectors(), adminDrApi.omStatus(), adminDrApi.omDashboard(omDays.value),
      adminDrApi.backups(), adminDrApi.pitList(),
      adminDrApi.restoreLogs({ page: 1, page_size: 10 }), adminDrApi.omLogs({ page: 1, page_size: 10 }),
      adminCollectionApi.dataSources(),
    ])
    connectors.value = drv.data?.data || []
    omStatus.value = om.data?.data || {}
    omStats.value = omd.data?.data || {}
    backups.value = bks.data?.data || []
    pits.value = ps.data?.data || []
    restoreLogs.value = rls.data?.items || []
    omLogs.value = ols.data?.items || []
    sources.value = srcs.data?.data || []
  } catch (e) { console.warn('DR dashboard load failed', e) }

  try {
    const d = await adminDrApi.restoreDashboard(dashboardDays.value)
    stats.value = d.data?.data || {}
  } catch { /* ignore */ }
}

async function loadOmLogs() {
  try {
    const res = await adminDrApi.omLogs({ page: 1, page_size: 10, status: omFilterStatus.value || undefined })
    omLogs.value = res.data?.items || []
    const omd = await adminDrApi.omDashboard(omDays.value)
    omStats.value = omd.data?.data || {}
  } catch { /* ignore */ }
}

async function loadRestoreLogs() {
  const res = await adminDrApi.restoreLogs({ page: 1, page_size: 10 })
  restoreLogs.value = res.data?.items || []
}

async function loadAccountHistory() {
  const params: any = { page: 1, page_size: 30 }
  if (acctSourceId.value) params.source_id = acctSourceId.value
  const res = await adminDrApi.accountHistory(params)
  accountHistory.value = res.data?.items || []
}

async function snapshotAccounts() {
  if (!acctSourceId.value) return
  try {
    const res = await adminDrApi.accountSnapshot(acctSourceId.value)
    message.success(`${res.data?.data?.saved || 0}개 계정 스냅샷이 저장되었습니다`)
    await loadAccountHistory()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '스냅샷 실패 (커넥터 연결 확인 필요)')
  }
}

async function syncPending() {
  try {
    await adminDrApi.omSyncPending()
    message.success('대기분 OM 동기화가 시작되었습니다')
  } catch { message.error('실행 실패') }
}

// 백업 CRUD
function openBackupEditor(b: any | null) {
  if (b) Object.assign(backupForm, b)
  else Object.assign(backupForm, {
    id: null, backup_name: '', backup_type: 'FULL', target_system: '',
    schedule_cron: '0 2 * * *', retention_days: 30, storage_path: '',
    source_id: null, backup_command: '', is_active: true,
  })
  showBackupEditor.value = true
}
async function saveBackup() {
  if (!backupForm.backup_name?.trim()) { message.error('백업명을 입력하세요'); return }
  try {
    await adminDrApi.upsertBackup(backupForm)
    message.success('저장되었습니다')
    showBackupEditor.value = false
    await loadAll()
  } catch (e: any) { message.error(e?.response?.data?.detail || '저장 실패') }
}
async function runBackup(b: any) {
  try { await adminDrApi.executeBackup(b.id); message.success('백업이 비동기로 시작되었습니다') }
  catch { message.error('실행 실패') }
}
async function delBackup(b: any) {
  if (!confirm(`"${b.backup_name}" 백업을 삭제하시겠습니까?`)) return
  try { await adminDrApi.deleteBackup(b.id); message.success('삭제되었습니다'); await loadAll() }
  catch { message.error('삭제 실패') }
}

// PIT
function openPitEditor(p: any | null) {
  if (p) {
    Object.assign(pitForm, {
      id: p.id, recovery_name: p.recovery_name,
      target_source_id: p.target_source_id, target_backup_id: p.target_backup_id,
      target_timestamp: p.target_timestamp ? p.target_timestamp.substring(0, 16) : '',
      simulation_only: p.simulation_only,
    })
  } else {
    Object.assign(pitForm, { id: null, recovery_name: '', target_source_id: null, target_backup_id: null, target_timestamp: '', simulation_only: true })
  }
  showPitEditor.value = true
}
async function savePit() {
  if (!pitForm.recovery_name?.trim()) { message.error('복구명을 입력하세요'); return }
  if (!pitForm.target_timestamp) { message.error('목표 복원 시각을 입력하세요'); return }
  try {
    await adminDrApi.pitUpsert(pitForm)
    message.success('저장되었습니다')
    showPitEditor.value = false
    await loadAll()
  } catch (e: any) { message.error(e?.response?.data?.detail || '저장 실패') }
}
async function simulatePit(p: any) {
  try {
    const res = await adminDrApi.pitSimulate(p.id)
    message.success('시뮬레이션 완료')
    pitView.value = { ...p, simulation_result: res.data?.data }
    showPitView.value = true
    await loadAll()
  } catch (e: any) { message.error(e?.response?.data?.detail || '시뮬레이션 실패') }
}
async function approvePit(p: any) {
  try { await adminDrApi.pitApprove(p.id); message.success('승인되었습니다'); await loadAll() }
  catch (e: any) { message.error(e?.response?.data?.detail || '승인 실패') }
}
async function executePit(p: any) {
  if (!confirm(`"${p.recovery_name}" 실제 복구를 실행하시겠습니까? 복구 후 되돌릴 수 없습니다.`)) return
  try { await adminDrApi.pitExecute(p.id); message.success('복구가 비동기로 실행됩니다'); await loadAll() }
  catch (e: any) { message.error(e?.response?.data?.detail || '실행 실패') }
}
function viewPit(p: any) { pitView.value = p; showPitView.value = true }

onMounted(loadAll)
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';

.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
.card-title-right { display: inline-flex; align-items: center; gap: 6px; font-weight: normal; }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; }
}
.type-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; background: #e6f7ff; color: #0066CC; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;
  &.active { background: #f6ffed; color: #28A745; }
  &.inactive { background: #f5f5f5; color: #999; }
}
.mono { font-family: monospace; font-size: 11px; }
.select-sm { height: 26px; padding: 2px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; background: #fff; }

.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }
.btn-warning { border-color: #fa8c16 !important; color: #fa8c16 !important; &:hover { background: #fff7e6 !important; } }
.btn-danger { background: #fff1f0 !important; color: #DC3545 !important; border: 1px solid #ffa39e !important; }

.badge-success { background: #f6ffed; color: #28A745; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.badge-warning { background: #fff7e6; color: #fa8c16; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.badge-info { background: #e6f0ff; color: #1e64d8; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.badge-danger { background: #fff1f0; color: #DC3545; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.badge-default { background: #f0f1f3; color: #6a7a8c; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; }
.badge-snapshot, .badge-create, .badge-alter, .badge-grant, .badge-revoke, .badge-drop, .badge-password_change { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; background: #f0f1f3; color: #6a7a8c; }

.form-notice { display: flex; gap: 8px; align-items: flex-start; padding: 10px 12px; margin-bottom: 14px; background: #fff8e6; border: 1px solid #ffe1a8; border-radius: 6px; font-size: 12px; color: #8a6100; line-height: 1.5; }
.switch { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; input { transform: scale(1.1); margin: 0; } }
.json-preview { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; font-size: 11px; max-height: 240px; overflow: auto; margin: 0; }

@media (max-width: 1279px) {
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
