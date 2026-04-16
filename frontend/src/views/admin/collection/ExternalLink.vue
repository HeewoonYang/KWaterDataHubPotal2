<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>기관 연계</h2>
      <p class="page-desc">외부 기관(공공/민간)과의 API·DB·메시지큐 연계 포인트를 등록하고 상태를 실시간으로 점검/모니터링합니다. (REQ-DHUB-005-005-001)</p>
    </div>

    <!-- KPI 카드 ─────────────────────────────────── -->
    <div class="stat-cards">
      <div class="stat-card"><div class="stat-icon" style="background:#0066CC"><ApiOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.total }}</span><span class="stat-label">전체 연계</span></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#28A745"><CheckCircleOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.healthy }}</span><span class="stat-label">정상</span></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#FFC107"><ExclamationCircleOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.degraded }}</span><span class="stat-label">지연/경고</span></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#DC3545"><CloseCircleOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.unhealthy + stats.failed }}</span><span class="stat-label">장애</span></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#9b59b6"><LineChartOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.availability_7d ?? '-' }}{{ stats.availability_7d != null ? '%' : '' }}</span><span class="stat-label">7일 가용률</span></div></div>
      <div class="stat-card"><div class="stat-icon" style="background:#17a2b8"><SwapOutlined /></div><div class="stat-info"><span class="stat-value">{{ stats.success_tx_24h }}/{{ stats.total_tx_24h }}</span><span class="stat-label">24h 성공/전체</span></div></div>
    </div>

    <!-- 그리드 ───────────────────────────────────── -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">기관 연계 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-outline btn-sm" @click="runAllHealthCheck" :disabled="runningAll"><ThunderboltOutlined /> {{ runningAll ? '점검 중...' : '전수 점검' }}</button>
          <button class="btn btn-primary btn-sm" @click="openRegister"><PlusOutlined /> 연계 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '기관_연계')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="rows"
          :columnDefs="cols"
          :defaultColDef="defCol"
          :pagination="true"
          :paginationPageSize="10"
          domLayout="autoHeight"
          :tooltipShowDelay="0"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- 상세 모달 ─────────────────────────────────── -->
    <AdminModal :visible="showDetail" :title="(detailData.agency_name || '') + ' 상세'" size="lg" @close="showDetail = false">
      <div class="tab-nav">
        <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">{{ t.label }}</button>
      </div>

      <!-- 연계 정보 탭 -->
      <div v-show="activeTab === 'info'" class="modal-section">
        <template v-if="!isEditing">
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">기관명</span><span class="info-value">{{ detailData.agency_name }}</span></div>
            <div class="modal-info-item"><span class="info-label">기관코드</span><span class="info-value">{{ detailData.agency_code || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">연계유형</span><span class="info-value">{{ detailData.endpoint_type || 'API' }}</span></div>
            <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">엔드포인트</span><span class="info-value" style="word-break:break-all">{{ detailData.api_endpoint || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">수집주기</span><span class="info-value">{{ detailData.schedule_cron || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="statusBadge(detailData.status)">{{ statusLabel(detailData.status) }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">인증방식</span><span class="info-value">{{ detailData.auth_method || 'NONE' }}</span></div>
          </div>

          <div class="modal-section-title" style="margin-top:16px">최근 점검 결과</div>
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="healthBadge(detailData.last_health_status)">{{ detailData.last_health_status || '-' }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">응답시간</span><span class="info-value">{{ detailData.last_health_latency_ms != null ? detailData.last_health_latency_ms + 'ms' : '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">최근 점검</span><span class="info-value">{{ formatDt(detailData.last_health_check_at) }}</span></div>
            <div class="modal-info-item"><span class="info-label">연속 실패</span><span class="info-value">{{ detailData.consecutive_failures ?? 0 }}</span></div>
            <div class="modal-info-item" style="grid-column: span 2"><span class="info-label">메시지</span><span class="info-value" style="word-break:break-all">{{ detailData.last_health_message || '-' }}</span></div>
          </div>

          <div class="modal-section-title" style="margin-top:16px">핫스왑 / OpenMetadata</div>
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">failover 엔드포인트</span><span class="info-value" style="word-break:break-all">{{ detailData.failover_endpoint || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">failover 활성</span><span class="info-value"><span class="badge" :class="detailData.failover_active ? 'badge-warning' : 'badge-success'">{{ detailData.failover_active ? '활성' : '비활성' }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">OM 서비스명</span><span class="info-value">{{ detailData.om_service_name || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">OM 최근동기화</span><span class="info-value">{{ formatDt(detailData.om_last_sync_at) }}</span></div>
          </div>
        </template>
        <template v-else>
          <div class="modal-form">
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">기관명</label><input v-model="editForm.agency_name" /></div>
              <div class="modal-form-group"><label>기관코드</label><input v-model="editForm.agency_code" /></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">연계유형</label>
                <select v-model="editForm.endpoint_type">
                  <option value="API">API</option><option value="DB">DB</option><option value="MQ">MQ</option>
                </select>
              </div>
              <div class="modal-form-group"><label>프로토콜</label><input v-model="editForm.protocol" placeholder="REST/SOAP/FILE/Kafka" /></div>
            </div>
            <div class="modal-form-group"><label>엔드포인트 URL</label><input v-model="editForm.api_endpoint" placeholder="https://api.example.com/v1" /></div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>수집주기 (CRON)</label><input v-model="editForm.schedule_cron" placeholder="0 */1 * * *" /></div>
              <div class="modal-form-group"><label>상태</label>
                <select v-model="editForm.status">
                  <option value="ACTIVE">ACTIVE</option><option value="INACTIVE">INACTIVE</option>
                  <option value="MAINTENANCE">MAINTENANCE</option><option value="FAILED">FAILED</option>
                </select>
              </div>
            </div>
            <div class="modal-section-title" style="margin-top:12px">인증/보안</div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>인증 방식</label>
                <select v-model="editForm.auth_method">
                  <option value="NONE">NONE</option><option value="API_KEY">API_KEY</option>
                  <option value="BASIC">BASIC</option><option value="OAUTH2">OAUTH2</option><option value="MTLS">MTLS</option>
                </select>
              </div>
              <div class="modal-form-group"><label>API Key (저장 시 암호화)</label><input type="password" v-model="editForm.api_key" placeholder="변경 시에만 입력" /></div>
            </div>
            <div class="modal-form-group"><label>failover 엔드포인트 (핫스왑)</label><input v-model="editForm.failover_endpoint" /></div>
          </div>
        </template>
      </div>

      <!-- 점검 설정 탭 -->
      <div v-show="activeTab === 'check'" class="modal-section">
        <div class="modal-section-title">자동 점검 / 재시도</div>
        <div class="modal-form">
          <div class="modal-form-row">
            <div class="modal-form-group"><label>자동점검 활성</label>
              <select :value="String(editData.health_check_enabled)" :disabled="!isEditing" @change="onBoolChange($event, 'health_check_enabled')">
                <option value="true">YES</option><option value="false">NO</option>
              </select>
            </div>
            <div class="modal-form-group"><label>점검주기(초)</label><input type="number" :value="editData.health_check_interval_sec" :disabled="!isEditing" @input="onNumChange($event, 'health_check_interval_sec')" /></div>
            <div class="modal-form-group"><label>타임아웃(초)</label><input type="number" :value="editData.health_timeout_sec" :disabled="!isEditing" @input="onNumChange($event, 'health_timeout_sec')" /></div>
          </div>
          <div class="modal-form-row">
            <div class="modal-form-group"><label>재시도 활성</label>
              <select :value="String(editData.retry_enabled)" :disabled="!isEditing" @change="onBoolChange($event, 'retry_enabled')">
                <option value="true">YES</option><option value="false">NO</option>
              </select>
            </div>
            <div class="modal-form-group"><label>최대 재시도</label><input type="number" :value="editData.max_retries" :disabled="!isEditing" @input="onNumChange($event, 'max_retries')" /></div>
            <div class="modal-form-group"><label>재시도 간격(초)</label><input type="number" :value="editData.retry_interval_sec" :disabled="!isEditing" @input="onNumChange($event, 'retry_interval_sec')" /></div>
            <div class="modal-form-group"><label>백오프</label>
              <select :value="editData.retry_backoff" :disabled="!isEditing" @change="onStrChange($event, 'retry_backoff')">
                <option value="FIXED">FIXED</option><option value="EXPONENTIAL">EXPONENTIAL</option>
              </select>
            </div>
          </div>
          <div class="modal-section-title" style="margin-top:8px">알림</div>
          <div class="modal-form-row">
            <div class="modal-form-group"><label>알림 활성</label>
              <select :value="String(editData.alert_enabled)" :disabled="!isEditing" @change="onBoolChange($event, 'alert_enabled')">
                <option value="true">YES</option><option value="false">NO</option>
              </select>
            </div>
            <div class="modal-form-group"><label>연속실패 임계</label><input type="number" :value="editData.alert_threshold_failures" :disabled="!isEditing" @input="onNumChange($event, 'alert_threshold_failures')" /></div>
          </div>
          <div class="modal-form-group"><label>알림 채널 (JSON)</label>
            <textarea rows="3" :value="alertChannelsText" :disabled="!isEditing" @input="onJsonChange($event, 'alert_channels')" placeholder='[{"type":"WEBHOOK","url":"https://hooks.slack.com/..."}]'></textarea>
          </div>
        </div>
      </div>

      <!-- 점검 이력 탭 -->
      <div v-show="activeTab === 'healthLogs'" class="modal-section">
        <div class="modal-section-title">
          연계 포인트 점검 이력
          <button class="btn btn-outline btn-sm" style="margin-left:8px" @click="triggerHealthCheck" :disabled="checking"><ThunderboltOutlined /> {{ checking ? '점검 중...' : '지금 점검' }}</button>
        </div>
        <div class="ag-grid-wrapper" v-if="healthLogs.length">
          <AgGridVue class="ag-theme-alpine" :rowData="healthLogs" :columnDefs="healthLogCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" />
        </div>
        <div v-else class="empty-text">점검 이력이 없습니다.</div>
      </div>

      <!-- 송수신 이력 탭 -->
      <div v-show="activeTab === 'txLogs'" class="modal-section">
        <div class="modal-section-title">송·수신 이력</div>
        <div class="ag-grid-wrapper" v-if="txLogs.length">
          <AgGridVue class="ag-theme-alpine" :rowData="txLogs" :columnDefs="txLogCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" />
        </div>
        <div v-else class="empty-text">송수신 이력이 없습니다.</div>
      </div>

      <template #footer>
        <template v-if="!isEditing">
          <button class="btn btn-outline" @click="triggerHealthCheck" :disabled="checking"><ThunderboltOutlined /> {{ checking ? '점검 중...' : '지금 점검' }}</button>
          <button class="btn btn-outline" @click="toggleFailover" v-if="detailData.failover_endpoint">
            <SwapOutlined /> {{ detailData.failover_active ? 'failover 해제' : 'failover 활성' }}
          </button>
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

    <!-- 등록 모달 -->
    <AdminModal :visible="showRegister" title="기관 연계 등록" size="lg" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">기관명</label><input v-model="regForm.agency_name" placeholder="기상청" /></div>
          <div class="modal-form-group"><label class="required">기관코드</label><input v-model="regForm.agency_code" placeholder="KMA" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">연계유형</label>
            <select v-model="regForm.endpoint_type">
              <option value="API">API</option><option value="DB">DB</option><option value="MQ">MQ</option>
            </select>
          </div>
          <div class="modal-form-group"><label>프로토콜</label><input v-model="regForm.protocol" placeholder="REST/SOAP/Kafka" /></div>
        </div>
        <div class="modal-form-group"><label>엔드포인트 URL (API/웹훅)</label><input v-model="regForm.api_endpoint" placeholder="https://api.example.com/health" /></div>
        <div class="modal-form-group"><label>DB/MQ 접속 파라미터 (JSON)</label>
          <textarea rows="3" :value="endpointConfigText" @input="onRegJsonChange($event, 'endpoint_config')"
                    placeholder='{"host":"10.0.0.10","port":5432,"database":"ext","user":"u","driver":"postgresql"}'></textarea>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>수집주기 (CRON)</label><input v-model="regForm.schedule_cron" placeholder="0 */1 * * *" /></div>
          <div class="modal-form-group"><label>점검주기(초)</label><input type="number" v-model.number="regForm.health_check_interval_sec" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>인증 방식</label>
            <select v-model="regForm.auth_method">
              <option value="NONE">NONE</option><option value="API_KEY">API_KEY</option>
              <option value="BASIC">BASIC</option><option value="OAUTH2">OAUTH2</option><option value="MTLS">MTLS</option>
            </select>
          </div>
          <div class="modal-form-group"><label>API Key</label><input type="password" v-model="regForm.api_key" /></div>
        </div>
        <div class="modal-form-group"><label>failover 엔드포인트</label><input v-model="regForm.failover_endpoint" /></div>
        <div class="modal-form-group"><label>OpenMetadata 서비스명</label><input v-model="regForm.om_service_name" /></div>
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
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined,
  ThunderboltOutlined, SwapOutlined, ApiOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ExclamationCircleOutlined, LineChartOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const tabs = [
  { key: 'info', label: '연계 정보' },
  { key: 'check', label: '점검 설정' },
  { key: 'healthLogs', label: '점검 이력' },
  { key: 'txLogs', label: '송·수신 이력' },
]

const showDetail = ref(false), showRegister = ref(false), isEditing = ref(false)
const checking = ref(false), runningAll = ref(false)
const activeTab = ref('info')
const detailData = ref<any>({})
const healthLogs = ref<any[]>([])
const txLogs = ref<any[]>([])
const rows = ref<any[]>([])

const stats = ref<any>({
  total: 0, active: 0, failed: 0, maintenance: 0,
  healthy: 0, degraded: 0, unhealthy: 0,
  availability_7d: null, total_tx_24h: 0, success_tx_24h: 0, fail_tx_24h: 0,
})

const initRegForm = () => ({
  agency_name: '', agency_code: '', endpoint_type: 'API',
  api_endpoint: '', api_key: '', endpoint_config: null as any,
  protocol: '', schedule_cron: '', status: 'ACTIVE',
  health_check_enabled: true, health_check_interval_sec: 300, health_timeout_sec: 10,
  retry_enabled: true, max_retries: 3, retry_interval_sec: 60, retry_backoff: 'EXPONENTIAL',
  auth_method: 'NONE', auth_config: null as any, security_policy: null as any,
  alert_enabled: true, alert_threshold_failures: 3, alert_channels: null as any,
  failover_endpoint: '', om_service_name: '',
})
const regForm = reactive(initRegForm())
const editForm = reactive<any>({})
const editData = computed(() => (isEditing.value ? editForm : detailData.value))

const endpointConfigText = computed(() => regForm.endpoint_config ? JSON.stringify(regForm.endpoint_config, null, 2) : '')
const alertChannelsText = computed(() => {
  const v = editData.value?.alert_channels
  if (!v) return ''
  try { return JSON.stringify(v, null, 2) } catch { return '' }
})
function parseJson(text: string) { try { return text ? JSON.parse(text) : null } catch { return null } }
function targetValue(ev: Event): string { return (ev.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)?.value ?? '' }
function onStrChange(ev: Event, key: string) { editForm[key] = targetValue(ev) }
function onNumChange(ev: Event, key: string) { editForm[key] = Number(targetValue(ev)) }
function onBoolChange(ev: Event, key: string) { editForm[key] = targetValue(ev) === 'true' }
function onJsonChange(ev: Event, key: string) { editForm[key] = parseJson(targetValue(ev)) }
function onRegJsonChange(ev: Event, key: string) { (regForm as any)[key] = parseJson(targetValue(ev)) }

function statusLabel(s?: string) {
  return s === 'ACTIVE' ? '활성' : s === 'INACTIVE' ? '비활성' : s === 'MAINTENANCE' ? '점검 중' : s === 'FAILED' ? '장애' : (s || '-')
}
function statusBadge(s?: string) {
  return s === 'ACTIVE' ? 'badge-success' : s === 'FAILED' ? 'badge-danger' : s === 'MAINTENANCE' ? 'badge-warning' : 'badge-secondary'
}
function healthBadge(s?: string) {
  return s === 'HEALTHY' ? 'badge-success' : s === 'DEGRADED' ? 'badge-warning' : s === 'UNHEALTHY' ? 'badge-danger' : 'badge-secondary'
}
function formatDt(v?: string | null) { return v ? String(v).replace('T', ' ').substring(0, 19) : '-' }

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 45 },
  { headerName: '기관명', field: 'agency_name', flex: 1.2 },
  { headerName: '기관코드', field: 'agency_code', width: 100 },
  { headerName: '유형', field: 'endpoint_type', width: 70 },
  { headerName: '엔드포인트', field: 'api_endpoint', flex: 1.5 },
  { headerName: '상태', field: '_statusLabel', width: 80,
    cellRenderer: (p: any) => `<span class="badge ${p.data._statusBadge}">${p.value}</span>` },
  { headerName: '점검결과', field: '_healthLabel', width: 100,
    cellRenderer: (p: any) => p.value ? `<span class="badge ${p.data._healthBadge}">${p.value}</span>` : '-' },
  { headerName: '응답(ms)', field: 'last_health_latency_ms', width: 90 },
  { headerName: '연속실패', field: 'consecutive_failures', width: 80 },
  { headerName: 'failover', field: '_failoverLabel', width: 80 },
  { headerName: '최근 점검', field: '_lastChecked', width: 150 },
])

const healthLogCols: ColDef[] = withHeaderTooltips([
  { headerName: '점검일시', field: '_checkedAt', width: 150 },
  { headerName: '유형', field: 'check_type', width: 90 },
  { headerName: '포인트', field: 'endpoint_type', width: 70 },
  { headerName: '결과', field: 'status', width: 90,
    cellRenderer: (p: any) => `<span class="badge ${healthBadge(p.value)}">${p.value}</span>` },
  { headerName: '응답(ms)', field: 'latency_ms', width: 90 },
  { headerName: 'HTTP', field: 'http_status', width: 70 },
  { headerName: '에러코드', field: 'error_code', width: 110 },
  { headerName: '메시지', field: 'message', flex: 1, tooltipField: 'message' },
  { headerName: 'failover', field: 'failover_used', width: 80,
    cellRenderer: (p: any) => p.value ? 'Y' : '' },
])

const txLogCols: ColDef[] = withHeaderTooltips([
  { headerName: '시작일시', field: '_startedAt', width: 150 },
  { headerName: '방향', field: 'tx_direction', width: 70 },
  { headerName: '유형', field: 'tx_type', width: 90 },
  { headerName: '결과', field: 'status', width: 80 },
  { headerName: '건수', field: 'record_count', width: 80 },
  { headerName: '바이트', field: 'bytes_size', width: 90 },
  { headerName: '소요(ms)', field: 'duration_ms', width: 80 },
  { headerName: '재시도', field: 'retry_count', width: 70 },
  { headerName: '에러', field: 'error_message', flex: 1, tooltipField: 'error_message' },
])

async function loadStats() {
  try {
    const res = await adminCollectionApi.externalAgencyStats()
    stats.value = { ...stats.value, ...(res.data.data || {}) }
  } catch (e) {
    console.warn('external-agency stats 실패', e)
  }
}

async function loadData() {
  try {
    const res = await adminCollectionApi.externalAgencies()
    const items = res.data.data || []
    rows.value = items.map((r: any) => ({
      ...r,
      _statusLabel: statusLabel(r.status),
      _statusBadge: statusBadge(r.status),
      _healthLabel: r.last_health_status || '',
      _healthBadge: healthBadge(r.last_health_status),
      _failoverLabel: r.failover_active ? '활성' : '',
      _lastChecked: formatDt(r.last_health_check_at),
    }))
  } catch (e) {
    console.warn('externalAgencies API 실패', e)
    rows.value = []
  }
}

onMounted(async () => { await Promise.all([loadData(), loadStats()]) })

function openRegister() { Object.assign(regForm, initRegForm()); showRegister.value = true }

async function onRowClick(event: any) {
  const row = event.data
  activeTab.value = 'info'
  isEditing.value = false
  if (row.id) {
    try {
      const res = await adminCollectionApi.getExternalAgency(row.id)
      detailData.value = res.data.data
    } catch { detailData.value = row }
  } else {
    detailData.value = row
  }
  showDetail.value = true
  await Promise.all([loadHealthLogs(), loadTxLogs()])
}

async function loadHealthLogs() {
  healthLogs.value = []
  const id = detailData.value?.id; if (!id) return
  try {
    const res = await adminCollectionApi.externalAgencyHealthLogs(id, { page_size: 50 })
    healthLogs.value = (res.data.items || []).map((l: any) => ({ ...l, _checkedAt: formatDt(l.checked_at) }))
  } catch { /* no logs */ }
}

async function loadTxLogs() {
  txLogs.value = []
  const id = detailData.value?.id; if (!id) return
  try {
    const res = await adminCollectionApi.externalAgencyTxLogs(id, { page_size: 50 })
    txLogs.value = (res.data.items || []).map((l: any) => ({ ...l, _startedAt: formatDt(l.started_at) }))
  } catch { /* no logs */ }
}

function startEdit() {
  Object.keys(editForm).forEach(k => delete editForm[k])
  Object.assign(editForm, {
    agency_name: detailData.value.agency_name,
    agency_code: detailData.value.agency_code,
    endpoint_type: detailData.value.endpoint_type || 'API',
    api_endpoint: detailData.value.api_endpoint,
    api_key: '',
    protocol: detailData.value.protocol,
    schedule_cron: detailData.value.schedule_cron,
    status: detailData.value.status || 'ACTIVE',
    health_check_enabled: detailData.value.health_check_enabled ?? true,
    health_check_interval_sec: detailData.value.health_check_interval_sec ?? 300,
    health_timeout_sec: detailData.value.health_timeout_sec ?? 10,
    retry_enabled: detailData.value.retry_enabled ?? true,
    max_retries: detailData.value.max_retries ?? 3,
    retry_interval_sec: detailData.value.retry_interval_sec ?? 60,
    retry_backoff: detailData.value.retry_backoff || 'EXPONENTIAL',
    auth_method: detailData.value.auth_method || 'NONE',
    alert_enabled: detailData.value.alert_enabled ?? true,
    alert_threshold_failures: detailData.value.alert_threshold_failures ?? 3,
    alert_channels: detailData.value.alert_channels,
    failover_endpoint: detailData.value.failover_endpoint,
    om_service_name: detailData.value.om_service_name,
  })
  isEditing.value = true
}

async function handleSaveEdit() {
  const id = detailData.value?.id; if (!id) return
  try {
    const payload: any = { ...editForm }
    if (!payload.api_key) delete payload.api_key
    await adminCollectionApi.updateExternalAgency(id, payload)
    message.success('수정되었습니다.')
    isEditing.value = false
    showDetail.value = false
    await Promise.all([loadData(), loadStats()])
  } catch { message.error('수정에 실패했습니다.') }
}

async function handleRegister() {
  if (!regForm.agency_name.trim() || !regForm.agency_code.trim()) {
    message.warning('기관명/기관코드는 필수입니다.'); return
  }
  try {
    const payload: any = { ...regForm }
    if (!payload.api_key) delete payload.api_key
    await adminCollectionApi.createExternalAgency(payload)
    message.success('등록되었습니다.')
    showRegister.value = false
    await Promise.all([loadData(), loadStats()])
  } catch { message.error('등록에 실패했습니다.') }
}

async function handleDelete() {
  const id = detailData.value?.id; if (!id) return
  if (!confirm('정말 삭제하시겠습니까?')) return
  try {
    await adminCollectionApi.deleteExternalAgency(id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    await Promise.all([loadData(), loadStats()])
  } catch { message.error('삭제에 실패했습니다.') }
}

async function triggerHealthCheck() {
  const id = detailData.value?.id; if (!id) return
  checking.value = true
  try {
    const res = await adminCollectionApi.externalAgencyHealthCheck(id)
    const d = res.data.data
    message.success(`점검 결과: ${d?.status || 'OK'} (${d?.latency_ms ?? '-'}ms)`)
    const fresh = await adminCollectionApi.getExternalAgency(id)
    detailData.value = fresh.data.data
    await Promise.all([loadHealthLogs(), loadData(), loadStats()])
  } catch (e: any) {
    message.error('점검에 실패했습니다.')
  } finally { checking.value = false }
}

async function runAllHealthCheck() {
  runningAll.value = true
  try {
    await adminCollectionApi.externalAgencyHealthCheckAll()
    message.success('전수 점검이 백그라운드에서 실행 중입니다.')
    setTimeout(async () => { await Promise.all([loadData(), loadStats()]); runningAll.value = false }, 2500)
  } catch { message.error('전수 점검 실행에 실패했습니다.'); runningAll.value = false }
}

async function toggleFailover() {
  const id = detailData.value?.id; if (!id) return
  const activate = !detailData.value.failover_active
  try {
    await adminCollectionApi.externalAgencyFailover(id, { activate })
    message.success(activate ? 'failover 활성화' : 'failover 해제')
    const fresh = await adminCollectionApi.getExternalAgency(id)
    detailData.value = fresh.data.data
    await loadData()
  } catch { message.error('failover 전환에 실패했습니다.') }
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
textarea { width: 100%; padding: 6px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-family: monospace; font-size: 12px; }
</style>
