<template>
  <div class="admin-page">
    <div class="page-header"><h2>수집 현황 대시보드</h2><p class="page-desc">실시간/배치 수집 상태, 장애 알림, 재처리를 한눈에 관리합니다.</p></div>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-icon" style="background:#e6f7ff;color:#0066CC"><SyncOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ monitor.today_success }}</div><div class="kpi-label">오늘 성공</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff1f0;color:#DC3545"><WarningOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ monitor.today_fail }}</div><div class="kpi-label">오늘 실패</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f6ffed;color:#28A745"><DatabaseOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ monitor.today_rows?.toLocaleString() }}</div><div class="kpi-label">수집 건수</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff7e6;color:#fa8c16"><ApiOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ monitor.active_sources }}</div><div class="kpi-label">활성 소스</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f9f0ff;color:#9b59b6"><ClockCircleOutlined /></div><div class="kpi-body"><div class="kpi-value">{{ monitor.active_configs }}</div><div class="kpi-label">수집 구성</div></div></div>
    </div>

    <!-- 7일 트렌드 -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">7일 수집 트렌드</div>
        <table class="data-table">
          <thead><tr><th>날짜</th><th>성공</th><th>실패</th></tr></thead>
          <tbody>
            <tr v-for="t in monitor.trend || []" :key="t.date">
              <td>{{ t.date }}</td>
              <td style="color:#28A745;font-weight:600">{{ t.count }}</td>
              <td style="color:#DC3545;font-weight:600">{{ failureByDate[t.date] || 0 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-title">
          장애 / 재처리 현황
          <span class="card-title-right">
            <button class="btn btn-xs btn-outline" @click="openAlertsModal"><BellOutlined /> 알람 설정</button>
          </span>
        </div>
        <div v-for="item in failedJobs" :key="item.id" class="alert-item">
          <div class="alert-info">
            <span class="alert-badge fail">실패</span>
            <span v-if="item.failure_category" class="cat-badge" :class="`cat-${item.failure_category}`">
              {{ failureCategoryLabel(item.failure_category) }}
            </span>
            <strong @click="openJobDetail(item)" style="cursor:pointer;color:#0066CC;text-decoration:underline">{{ item.dataset_name }}</strong>
            <span class="alert-time">{{ item.started_at?.substring(0, 16) }}</span>
          </div>
          <button class="btn btn-xs btn-warning" @click="backfill(item)"><ReloadOutlined /> 재수집</button>
        </div>
        <div v-if="failedJobs.length === 0" class="empty-msg">장애 없음</div>
      </div>
    </div>

    <!-- 실패 패턴 분석 (REQ-DHUB-005-002-003) -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">
        실패 패턴 분석 (최근 {{ failureDays }}일)
        <span class="card-title-right">
          <select v-model.number="failureDays" @change="loadFailureAnalysis" class="select-sm">
            <option :value="7">최근 7일</option>
            <option :value="14">최근 14일</option>
            <option :value="30">최근 30일</option>
          </select>
        </span>
      </div>
      <div v-if="failureAnalysis.total_failed === 0" class="empty-msg">해당 기간 실패 잡 없음 ✓</div>
      <div v-else class="failure-grid">
        <div class="fail-summary">
          <div class="fail-total">
            <div class="fail-num">{{ failureAnalysis.total_failed }}</div>
            <div class="fail-label">총 실패 건수</div>
          </div>
        </div>
        <div class="fail-categories">
          <div v-for="c in failureAnalysis.by_category" :key="c.category" class="cat-row">
            <div class="cat-row-head">
              <span class="cat-badge" :class="`cat-${c.category}`">{{ c.label }}</span>
              <span class="cat-count">{{ c.count }}건</span>
            </div>
            <div class="cat-bar"><div class="cat-bar-fill" :style="{ width: percent(c.count, failureAnalysis.total_failed) + '%' }"></div></div>
            <div v-if="c.recommended_action" class="cat-action"><BulbOutlined /> {{ c.recommended_action }}</div>
            <div v-if="c.sample_message" class="cat-sample">샘플 메시지: <code>{{ c.sample_message.substring(0, 120) }}</code></div>
          </div>
        </div>
        <div v-if="failureAnalysis.top_sources?.length" class="fail-sources">
          <div class="sub-title">실패 다발 소스 Top {{ failureAnalysis.top_sources.length }}</div>
          <table class="data-table">
            <thead><tr><th>소스명</th><th>실패 건수</th></tr></thead>
            <tbody>
              <tr v-for="s in failureAnalysis.top_sources" :key="s.source_name">
                <td>{{ s.source_name }}</td>
                <td style="color:#DC3545;font-weight:600">{{ s.fail_count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 배치 흐름 안내 -->
    <div class="flow-banner" style="margin-top:16px;">
      <div class="flow-banner-inner">
        <span class="flow-step">원천DB</span><span class="flow-arrow">→</span>
        <span class="flow-step active">수집DB (PG)</span><span class="flow-arrow">→</span>
        <span class="flow-step">데이터 패브릭</span><span class="flow-arrow">→</span>
        <span class="flow-step">GPU DB</span><span class="flow-arrow">→</span>
        <span class="flow-step dim">분석DB</span>
      </div>
      <div class="flow-desc"><InfoCircleOutlined /> 분석DB에는 모든 데이터가 이동하는 것이 아니라, <strong>중요도가 높거나 조회 빈도가 많은 데이터셋만</strong> 데이터 패브릭을 통해 승격됩니다.</div>
    </div>

    <!-- 도메인별 수집 현황 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">도메인별 수집 현황</div>
      <div class="domain-grid">
        <div v-for="d in domainStatus" :key="d.domain" class="domain-card" @click="goToDomainDetail(d)" style="cursor:pointer">
          <div class="domain-header">
            <strong>{{ d.domain }}</strong>
            <span class="status-badge" :class="d.status === '정상' ? 'active' : 'inactive'">{{ d.status }}</span>
          </div>
          <div class="domain-body">
            <div class="domain-info"><span class="domain-label">원천</span><span>{{ d.source }}</span></div>
            <div class="domain-info"><span class="domain-label">수집경로</span><span class="mono" style="font-size:10px">{{ d.flowPath }}</span></div>
            <div class="domain-info"><span class="domain-label">최근 수집</span><span>{{ d.lastSync }}</span></div>
            <div class="domain-info"><span class="domain-label">수집 건수</span><span>{{ d.rowCount }}</span></div>
            <template v-if="d.rt">
              <div class="domain-info"><span class="domain-label">1분 수집</span><span>{{ d.rt.min1 }}</span></div>
              <div class="domain-info"><span class="domain-label">15분 수집</span><span>{{ d.rt.min15 }}</span></div>
              <div class="domain-info"><span class="domain-label">1시간 수집</span><span>{{ d.rt.hour1 }}</span></div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- 소스별 현황 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">데이터 소스별 수집 현황</div>
      <table class="data-table">
        <thead><tr><th>소스명</th><th>유형</th><th>호스트</th><th>상태</th><th>최근 테스트</th><th>액션</th></tr></thead>
        <tbody>
          <tr v-for="src in sources" :key="src.id">
            <td><strong>{{ src.source_name }}</strong></td>
            <td><span class="type-badge">{{ src.source_type }}</span></td>
            <td class="mono">{{ src.connection_host || '-' }}</td>
            <td><span class="status-badge" :class="src.status === 'ACTIVE' ? 'active' : 'inactive'">{{ src.status }}</span></td>
            <td>{{ src.last_test_result || '-' }}</td>
            <td><button class="btn btn-xs btn-outline" @click="testSource(src)"><ThunderboltOutlined /> 테스트</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 잡 상세 모달 (실패 분류 + 품질 결과) -->
    <AdminModal :visible="showJobDetail" :title="`수집 작업 상세 - ${jobDetail?.dataset_name || ''}`" size="lg" @close="showJobDetail = false">
      <div v-if="jobDetail" class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value">
            <span class="status-badge" :class="jobDetail.job_status === 'SUCCESS' ? 'active' : 'inactive'">{{ jobDetail.job_status }}</span>
          </span></div>
          <div class="modal-info-item"><span class="info-label">소스</span><span class="info-value">{{ jobDetail.source_name || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">시작</span><span class="info-value">{{ jobDetail.started_at?.replace('T', ' ').substring(0, 19) || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">종료</span><span class="info-value">{{ jobDetail.finished_at?.replace('T', ' ').substring(0, 19) || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">소요</span><span class="info-value">{{ jobDetail.elapsed_sec != null ? jobDetail.elapsed_sec + '초' : '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">처리/성공/오류</span><span class="info-value">{{ jobDetail.total_rows || 0 }} / {{ jobDetail.success_rows || 0 }} / {{ jobDetail.error_rows || 0 }}</span></div>
        </div>
      </div>

      <div v-if="jobDetail?.failure_category" class="modal-section">
        <div class="modal-section-title">실패 분류</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">카테고리</span><span class="info-value">
            <span class="cat-badge" :class="`cat-${jobDetail.failure_category}`">{{ failureCategoryLabel(jobDetail.failure_category) }}</span>
          </span></div>
          <div class="modal-info-item"><span class="info-label">권장 조치</span><span class="info-value">{{ jobDetail.failure_detail?.recommended_action || '-' }}</span></div>
        </div>
        <div v-if="jobDetail.error_message" class="modal-info-item" style="margin-top:8px;">
          <span class="info-label">오류 메시지</span>
          <pre class="error-msg">{{ jobDetail.error_message }}</pre>
        </div>
      </div>

      <div class="modal-section">
        <div class="modal-section-title">품질 검증 결과 ({{ jobDetail?.quality_results?.length || 0 }}건)</div>
        <div v-if="jobDetail?.quality_score != null" class="quality-score-banner">
          평균 품질 점수: <strong>{{ jobDetail.quality_score }}</strong> / 100
          <span v-if="jobDetail.quality_check_at" class="alert-time">{{ jobDetail.quality_check_at.replace('T', ' ').substring(0, 19) }} 검증</span>
        </div>
        <table v-if="jobDetail?.quality_results?.length" class="modal-table">
          <thead><tr><th>유형</th><th>점수</th><th>총건수/오류</th><th>AI피드백</th><th>실행</th></tr></thead>
          <tbody>
            <tr v-for="qr in jobDetail.quality_results" :key="qr.id">
              <td>{{ qr.check_type || '-' }}</td>
              <td style="font-weight:600" :style="{ color: (qr.score || 0) >= 80 ? '#28A745' : (qr.score || 0) >= 60 ? '#fa8c16' : '#DC3545' }">{{ qr.score != null ? qr.score : '-' }}</td>
              <td>{{ qr.total_count || 0 }} / {{ qr.error_count || 0 }}</td>
              <td>{{ qr.ai_feedback_used ? 'Y' : 'N' }}</td>
              <td>{{ qr.executed_at?.replace('T', ' ').substring(0, 16) || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#888; font-size:13px;">품질 검증이 아직 실행되지 않았습니다 (수집 성공 시 자동 트리거됨).</p>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showJobDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 알람 설정 모달 -->
    <AdminModal :visible="showAlerts" title="수집 장애 알람 설정" size="xl" @close="showAlerts = false">
      <div class="modal-section">
        <div class="alerts-toolbar">
          <button class="btn btn-sm btn-primary" @click="openAlertEditor(null)"><PlusOutlined /> 새 알람</button>
          <button class="btn btn-sm btn-outline" @click="dispatchNow"><SyncOutlined /> 지금 평가/발송</button>
        </div>
        <table class="modal-table">
          <thead>
            <tr>
              <th>알람명</th><th>채널</th><th>트리거</th><th>임계/주기</th><th>대상소스</th>
              <th>활성</th><th>최근발송</th><th>누적</th><th style="width:160px;">액션</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in alerts" :key="a.id">
              <td>{{ a.config_name }}</td>
              <td><span class="type-badge">{{ a.channel_type }}</span></td>
              <td>{{ triggerLabel(a.trigger_type) }}</td>
              <td>{{ a.threshold }} / {{ a.period_minutes }}분</td>
              <td>{{ a.target_source_name || '전체' }}</td>
              <td><span class="status-badge" :class="a.enabled ? 'active' : 'inactive'">{{ a.enabled ? 'ON' : 'OFF' }}</span></td>
              <td>{{ a.last_triggered_at ? (a.last_triggered_at.substring(0, 16) + ' (' + (a.last_triggered_status || '-') + ')') : '-' }}</td>
              <td>{{ a.trigger_count }}</td>
              <td>
                <button class="btn btn-xs btn-outline" @click="testAlert(a)" title="테스트 발송"><ThunderboltOutlined /></button>
                <button class="btn btn-xs btn-outline" @click="openAlertEditor(a)"><EditOutlined /></button>
                <button class="btn btn-xs btn-danger" @click="deleteAlert(a)"><DeleteOutlined /></button>
              </td>
            </tr>
            <tr v-if="!alerts.length"><td colspan="9" style="text-align:center;color:#888;padding:24px;">등록된 알람이 없습니다. 새 알람을 추가하세요.</td></tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showAlerts = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 알람 편집 모달 -->
    <AdminModal :visible="showAlertForm" :title="alertForm.id ? '알람 수정' : '알람 등록'" size="md" @close="showAlertForm = false">
      <div class="modal-form">
        <div class="form-row">
          <label>알람명 *</label>
          <input v-model="alertForm.config_name" placeholder="예: 운영DB 수집 연속 실패 알람" />
        </div>
        <div class="form-row">
          <label>채널유형 *</label>
          <select v-model="alertForm.channel_type">
            <option value="WEBHOOK">Webhook (일반 JSON)</option>
            <option value="SLACK">Slack</option>
            <option value="TEAMS">MS Teams</option>
            <option value="EMAIL">Email (stub)</option>
          </select>
        </div>
        <div v-if="alertForm.channel_type !== 'EMAIL'" class="form-row">
          <label>웹훅 URL *</label>
          <input v-model="alertForm.webhook_url" placeholder="https://hooks.slack.com/services/..." />
        </div>
        <div v-if="alertForm.channel_type === 'EMAIL'" class="form-row">
          <label>이메일 (콤마구분)</label>
          <input v-model="alertForm.email_to" placeholder="ops@kwater.or.kr,admin@kwater.or.kr" />
        </div>
        <div class="form-row">
          <label>트리거 유형 *</label>
          <select v-model="alertForm.trigger_type">
            <option value="CONSECUTIVE_FAIL">연속 실패 횟수</option>
            <option value="FAILURE_RATE">실패율(%) 초과</option>
            <option value="QUALITY_FAIL">품질점수 미달</option>
            <option value="CATEGORY_MATCH">실패 카테고리 매치</option>
          </select>
        </div>
        <div class="form-row">
          <label>{{ thresholdLabel }}</label>
          <input v-model.number="alertForm.threshold" type="number" min="1" />
        </div>
        <div class="form-row">
          <label>평가 주기 (분)</label>
          <input v-model.number="alertForm.period_minutes" type="number" min="1" />
        </div>
        <div v-if="alertForm.trigger_type === 'CATEGORY_MATCH'" class="form-row">
          <label>감시 카테고리</label>
          <div class="checkbox-group">
            <label v-for="c in categoryOptions" :key="c.value" class="checkbox-inline">
              <input type="checkbox" :value="c.value" v-model="alertForm.failure_categories" />
              {{ c.label }}
            </label>
          </div>
        </div>
        <div class="form-row">
          <label>대상 소스</label>
          <select v-model="alertForm.target_source_id">
            <option :value="null">전체 (모든 소스)</option>
            <option v-for="s in sources" :key="s.id" :value="s.id">{{ s.source_name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>심각도</label>
          <select v-model="alertForm.severity">
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>
        <div class="form-row">
          <label>활성화</label>
          <label class="switch">
            <input type="checkbox" v-model="alertForm.enabled" />
            <span>{{ alertForm.enabled ? '사용' : '미사용' }}</span>
          </label>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="saveAlert"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showAlertForm = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import {
  SyncOutlined, WarningOutlined, DatabaseOutlined, ApiOutlined, ClockCircleOutlined,
  ReloadOutlined, ThunderboltOutlined, InfoCircleOutlined, BellOutlined, BulbOutlined,
  PlusOutlined, EditOutlined, DeleteOutlined, SaveOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import { adminCollectionApi } from '../../../api/admin.api'
import { useRouter } from 'vue-router'
import AdminModal from '../../../components/AdminModal.vue'
const router = useRouter()

const monitor = ref<any>({})
const failedJobs = ref<any[]>([])
const sources = ref<any[]>([])

// 실패 패턴 분석
const failureDays = ref(7)
const failureAnalysis = ref<any>({ total_failed: 0, by_category: [], daily_trend: [], top_sources: [] })
const failureByDate = computed<Record<string, number>>(() => {
  const m: Record<string, number> = {}
  for (const d of failureAnalysis.value.daily_trend || []) m[d.date] = d.total
  return m
})

// 잡 상세 모달
const showJobDetail = ref(false)
const jobDetail = ref<any>(null)

// 알람 설정 모달
const showAlerts = ref(false)
const showAlertForm = ref(false)
const alerts = ref<any[]>([])
const alertForm = reactive<any>({
  id: null, config_name: '', channel_type: 'WEBHOOK', webhook_url: '', email_to: '',
  trigger_type: 'CONSECUTIVE_FAIL', threshold: 3, period_minutes: 60,
  failure_categories: [] as string[], target_source_id: null, severity: 'WARNING', enabled: true,
})

const categoryOptions = [
  { value: 'CONNECTION_ERROR', label: '원천 연결 실패' },
  { value: 'PERMISSION_DENIED', label: '권한/인증 실패' },
  { value: 'TIMEOUT', label: '타임아웃' },
  { value: 'QUOTA_EXCEEDED', label: '쿼터/자원 초과' },
  { value: 'SCHEMA_MISMATCH', label: '스키마 불일치' },
  { value: 'DATA_TYPE_ERROR', label: '데이터타입 오류' },
  { value: 'QUALITY_FAIL', label: '품질검증 실패' },
  { value: 'UNKNOWN', label: '원인 미상' },
]

const thresholdLabel = computed(() => {
  switch (alertForm.trigger_type) {
    case 'CONSECUTIVE_FAIL': return '연속 실패 횟수 (회)'
    case 'FAILURE_RATE': return '실패율 임계값 (%)'
    case 'QUALITY_FAIL': return '품질점수 하한 (점)'
    case 'CATEGORY_MATCH': return '매치 발생 최소 횟수'
    default: return '임계값'
  }
})

function failureCategoryLabel(c: string) {
  return categoryOptions.find(o => o.value === c)?.label || c
}
function triggerLabel(t: string) {
  return { CONSECUTIVE_FAIL: '연속 실패', FAILURE_RATE: '실패율', QUALITY_FAIL: '품질 미달', CATEGORY_MATCH: '카테고리 매치' }[t] || t
}
function percent(part: number, total: number) {
  if (!total) return 0
  return Math.round((part / total) * 1000) / 10
}

async function loadFailureAnalysis() {
  try {
    const res = await adminCollectionApi.failureAnalysis(failureDays.value)
    if (res.data?.data) failureAnalysis.value = res.data.data
  } catch (e) { console.warn('failure analysis load failed:', e) }
}

async function openJobDetail(job: any) {
  try {
    const res = await adminCollectionApi.getJob(job.id)
    if (res.data?.data) {
      jobDetail.value = res.data.data
      showJobDetail.value = true
    }
  } catch { message.error('상세 조회에 실패했습니다.') }
}

async function loadAlerts() {
  try {
    const res = await adminCollectionApi.alerts()
    if (res.data?.data) alerts.value = res.data.data
  } catch (e) { console.warn('alerts load failed:', e) }
}

async function openAlertsModal() {
  showAlerts.value = true
  await loadAlerts()
}

function openAlertEditor(a: any | null) {
  if (a) {
    Object.assign(alertForm, {
      id: a.id, config_name: a.config_name, channel_type: a.channel_type,
      webhook_url: a.webhook_url || '', email_to: a.email_to || '',
      trigger_type: a.trigger_type, threshold: a.threshold || 1, period_minutes: a.period_minutes || 60,
      failure_categories: a.failure_categories || [], target_source_id: a.target_source_id,
      severity: a.severity || 'WARNING', enabled: a.enabled !== false,
    })
  } else {
    Object.assign(alertForm, {
      id: null, config_name: '', channel_type: 'WEBHOOK', webhook_url: '', email_to: '',
      trigger_type: 'CONSECUTIVE_FAIL', threshold: 3, period_minutes: 60,
      failure_categories: [], target_source_id: null, severity: 'WARNING', enabled: true,
    })
  }
  showAlertForm.value = true
}

async function saveAlert() {
  if (!alertForm.config_name?.trim()) { message.error('알람명을 입력하세요'); return }
  if (alertForm.channel_type !== 'EMAIL' && !alertForm.webhook_url?.trim()) {
    message.error('웹훅 URL을 입력하세요'); return
  }
  try {
    await adminCollectionApi.upsertAlert({ ...alertForm })
    message.success('알람이 저장되었습니다')
    showAlertForm.value = false
    await loadAlerts()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '저장 실패')
  }
}

async function deleteAlert(a: any) {
  if (!confirm(`"${a.config_name}" 알람을 삭제하시겠습니까?`)) return
  try {
    await adminCollectionApi.deleteAlert(a.id)
    message.success('삭제되었습니다')
    await loadAlerts()
  } catch { message.error('삭제 실패') }
}

async function testAlert(a: any) {
  try {
    await adminCollectionApi.testAlert(a.id)
    message.success('테스트 발송 성공')
    await loadAlerts()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '테스트 발송 실패')
  }
}

async function dispatchNow() {
  try {
    await adminCollectionApi.dispatchAlertsNow()
    message.success('알람 평가/발송이 비동기로 시작되었습니다')
  } catch { message.error('실행 실패') }
}
const domainStatus = ref([
  { domain: '시설(WFM)', source: 'OA망 (SAP HANA)', flowPath: 'ETL(Airflow) → 수집DB', lastSync: '2026-04-06 22:00', rowCount: '15,600', status: '점검' },
  { domain: '자산(AMS)', source: 'OA망 (Tibero)', flowPath: 'CDC → 수집DB', lastSync: '2026-04-07 06:00', rowCount: '28,800', status: '정상' },
  { domain: '운영통합(WRO)', source: 'OA망 (Oracle)', flowPath: 'CDC → 수집DB', lastSync: '2026-04-07 08:30', rowCount: '32,100', status: '정상' },
  { domain: '수질통합(WQM)', source: 'OA망 (Oracle)', flowPath: 'CDC → 수집DB', lastSync: '2026-04-07 09:15', rowCount: '45,200', status: '정상' },
  { domain: '관망(WATER-NET)', source: 'OA망 (Oracle)', flowPath: 'CDC → 수집DB', lastSync: '2026-04-07 07:00', rowCount: '18,400', status: '정상' },
  { domain: '기상/NASA', source: 'DMZ (기상청 + NASA)', flowPath: 'DMZ 수집서버 → 수집DB', lastSync: '2026-04-07 10:00', rowCount: '9,840', status: '정상' },
  { domain: '실시간계측(RWIS)', source: 'Tibero Zeta7', flowPath: '실시간 스트리밍', lastSync: '2026-04-07 09:25', rowCount: '실시간', status: '정상', rt: { min1: '120건', min15: '1,800건', hour1: '7,200건' } },
  { domain: '실시간계측(HDAPS)', source: 'Tibero Zeta7', flowPath: '실시간 스트리밍', lastSync: '2026-04-07 09:25', rowCount: '실시간', status: '정상', rt: { min1: '85건', min15: '1,275건', hour1: '5,100건' } },
  { domain: '실시간계측(GIOS)', source: 'Tibero Zeta7', flowPath: '실시간 스트리밍', lastSync: '2026-04-07 09:24', rowCount: '실시간', status: '정상', rt: { min1: '45건', min15: '675건', hour1: '2,700건' } },
  { domain: '실시간계측(Smart Metering)', source: 'Tibero Zeta7', flowPath: '실시간 스트리밍', lastSync: '2026-04-07 09:25', rowCount: '실시간', status: '정상', rt: { min1: '200건', min15: '3,000건', hour1: '12,000건' } },
])

function goToDomainDetail(d: any) {
  if (d.domain.startsWith('실시간계측')) {
    message.info('실시간계측은 별도 모니터링 화면에서 관리합니다.')
    return
  }
  if (d.domain === '기상/NASA' || d.domain === '기상' || d.domain === 'NASA') {
    message.info('외부 API 수집은 [기관 연계] 화면에서 관리합니다.')
    return
  }
  router.push({ path: '/admin/collection/domain-detail', query: { domain: d.domain } })
}

onMounted(async () => {
  try {
    const [monRes, jobRes, srcRes] = await Promise.all([
      adminCollectionApi.monitoringSummary(),
      adminCollectionApi.jobs({ status: 'FAIL', page: 1, page_size: 10 }),
      adminCollectionApi.dataSources(),
    ])
    if (monRes.data?.data) monitor.value = monRes.data.data
    if (jobRes.data?.items) failedJobs.value = jobRes.data.items
    if (srcRes.data?.data) sources.value = srcRes.data.data
  } catch (e) { console.warn('수집 대시보드 로드 실패:', e) }
  await loadFailureAnalysis()
})

async function backfill(_job: any) {
  try {
    await adminCollectionApi.executeCollection()
    message.success('재수집이 시작되었습니다.')
  } catch { message.error('재수집에 실패했습니다.') }
}

async function testSource(src: any) {
  try {
    await adminCollectionApi.testDataSource(src.id)
    message.success(src.source_name + ' 연결 테스트 성공')
  } catch { message.error('연결 테스트에 실패했습니다.') }
}
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; } }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } }
.alert-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0;
  .alert-info { display: flex; align-items: center; gap: 8px; font-size: 12px; }
  .alert-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; &.fail { background: #fff1f0; color: #DC3545; } }
  .alert-time { font-size: 11px; color: #999; }
}
.empty-msg { text-align: center; color: #999; padding: 20px; font-size: 12px; }
.type-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600; background: #e6f7ff; color: #0066CC; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.inactive { background: #f5f5f5; color: #999; } }
.mono { font-family: monospace; font-size: 11px; }
.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }
.btn-warning { border-color: #fa8c16 !important; color: #fa8c16 !important; &:hover { background: #fff7e6 !important; } }
.domain-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.domain-card { background: #fafbfc; border: 1px solid #e8e8e8; border-radius: 8px; padding: 12px; }
.domain-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; }
.domain-body { display: flex; flex-direction: column; gap: 4px; }
.domain-info { display: flex; justify-content: space-between; font-size: 11px; color: #666; }
.domain-label { color: #999; }
.domain-card:hover { border-color: #0066CC; background: #f0f7ff; transition: all 0.2s; }
.flow-banner { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px 16px; }
.flow-banner-inner { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.flow-step { padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; background: #f0f0f0; color: #333; &.active { background: #0066CC; color: #fff; } &.dim { background: #f9f0ff; color: #9b59b6; border: 1px dashed #d3adf7; } }
.flow-arrow { color: #bbb; font-size: 14px; font-weight: 700; }
.flow-desc { font-size: 11px; color: #ad6800; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px; padding: 6px 10px; display: flex; align-items: center; gap: 6px; }
@media (max-width: 1279px) { .domain-grid { grid-template-columns: repeat(2, 1fr); } }

/* === 실패 분석 / 알람 === */
.card-title { display: flex; justify-content: space-between; align-items: center; }
.card-title-right { display: inline-flex; align-items: center; gap: 6px; font-weight: normal; }
.select-sm { height: 26px; padding: 2px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; background: #fff; }

.cat-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.cat-CONNECTION_ERROR { background: #fde9e9; color: #d93b3b; }
.cat-PERMISSION_DENIED { background: #fff7e6; color: #c47700; }
.cat-TIMEOUT { background: #f0f5ff; color: #3360b8; }
.cat-QUOTA_EXCEEDED { background: #fff1f0; color: #cf1322; }
.cat-SCHEMA_MISMATCH { background: #f9f0ff; color: #722ed1; }
.cat-DATA_TYPE_ERROR { background: #fff8e6; color: #ad6800; }
.cat-QUALITY_FAIL { background: #fce4ec; color: #c2185b; }
.cat-UNKNOWN { background: #f0f1f3; color: #6a7a8c; }

.failure-grid { display: grid; grid-template-columns: 140px 1fr 240px; gap: 16px; }
.fail-summary { display: flex; flex-direction: column; gap: 8px; align-items: center; justify-content: center; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; padding: 16px; }
.fail-num { font-size: 32px; font-weight: 800; color: #d46b08; }
.fail-label { font-size: 11px; color: #ad6800; }
.fail-categories { display: flex; flex-direction: column; gap: 12px; max-height: 360px; overflow-y: auto; }
.cat-row { padding: 10px 12px; background: #fafbfc; border: 1px solid #e8e8e8; border-radius: 6px; }
.cat-row-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.cat-count { font-weight: 700; color: #d93b3b; }
.cat-bar { height: 6px; background: #f0f0f0; border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
.cat-bar-fill { height: 100%; background: linear-gradient(90deg, #ff7875, #ff4d4f); }
.cat-action { font-size: 11px; color: #1e64d8; display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.cat-sample { font-size: 10px; color: #888; code { background: #f5f5f5; padding: 1px 4px; border-radius: 2px; font-size: 10px; } }
.fail-sources { background: #fafbfc; border: 1px solid #e8e8e8; border-radius: 6px; padding: 10px 12px; }
.sub-title { font-size: 12px; font-weight: 700; margin-bottom: 6px; color: #4a5568; }

/* 알람 모달 */
.alerts-toolbar { display: flex; gap: 6px; margin-bottom: 10px; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 8px 16px; }
.checkbox-inline { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; cursor: pointer;
  input { margin: 0; }
}
.switch { display: inline-flex; align-items: center; gap: 8px; cursor: pointer;
  input { transform: scale(1.1); margin: 0; }
}

/* 잡 상세 모달 */
.error-msg { background: #fff1f0; border: 1px solid #ffa39e; border-radius: 4px; padding: 8px 10px; font-size: 11px; color: #a8071a; max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-all; }
.quality-score-banner { background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }
.btn-danger { background: #fff1f0 !important; color: #DC3545 !important; border: 1px solid #ffa39e !important; &:hover { background: #ffccc7 !important; } }

@media (max-width: 1279px) {
  .failure-grid { grid-template-columns: 1fr; }
}
</style>
