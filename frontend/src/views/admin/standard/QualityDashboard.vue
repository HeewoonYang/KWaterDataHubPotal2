<template>
  <div class="admin-page quality-dashboard">
    <div class="page-header">
      <h2>품질 대시보드</h2>
      <p class="page-desc">수집·유통 데이터 품질 검증 결과와 AI 학습 피드백 현황을 실시간으로 확인·관리합니다.</p>
    </div>

    <!-- 상단 KPI 카드 -->
    <div class="kpi-row">
      <div class="kpi-card" :class="kpiLevel(summary.avg_score_7d)">
        <SafetyCertificateOutlined class="kpi-icon" />
        <div class="kpi-body">
          <div class="kpi-label">최근 7일 평균 점수</div>
          <div class="kpi-value">{{ summary.avg_score_7d.toFixed(1) }}<span class="unit">점</span></div>
          <div class="kpi-sub">30일 평균 {{ summary.avg_score_30d.toFixed(1) }}점</div>
        </div>
      </div>
      <div class="kpi-card">
        <FileSearchOutlined class="kpi-icon" />
        <div class="kpi-body">
          <div class="kpi-label">7일 검증 건수</div>
          <div class="kpi-value">{{ summary.checks_7d.toLocaleString() }}</div>
          <div class="kpi-sub">30일 {{ summary.checks_30d.toLocaleString() }}건</div>
        </div>
      </div>
      <div class="kpi-card" :class="summary.failing_rules_count > 0 ? 'danger' : ''">
        <WarningOutlined class="kpi-icon" />
        <div class="kpi-body">
          <div class="kpi-label">실패 규칙 수 (7일)</div>
          <div class="kpi-value">{{ summary.failing_rules_count }}</div>
          <div class="kpi-sub">저점수 데이터셋 {{ summary.low_score_datasets_7d }}건</div>
        </div>
      </div>
      <div class="kpi-card" :class="summary.ai_feedback_pending > 0 ? 'warn' : ''">
        <RobotOutlined class="kpi-icon" />
        <div class="kpi-body">
          <div class="kpi-label">AI 피드백 대기</div>
          <div class="kpi-value">{{ summary.ai_feedback_pending }}</div>
          <div class="kpi-sub">7일 전송 {{ summary.ai_feedback_sent_7d }} · 실패 {{ summary.ai_feedback_failed_7d }}</div>
        </div>
      </div>
    </div>

    <!-- 액션 바 -->
    <div class="action-bar">
      <div class="action-group">
        <button class="btn btn-primary btn-sm" @click="runCatalogAll"><ThunderboltOutlined /> 카탈로그 전량 검증</button>
        <button class="btn btn-primary btn-sm" @click="runDistributionAll"><ThunderboltOutlined /> 유통 전량 검증</button>
        <button class="btn btn-outline btn-sm" @click="runCompliance"><CheckCircleOutlined /> 용어 준수 검사</button>
        <button class="btn btn-outline btn-sm" @click="dispatchNow"><SendOutlined /> AI 피드백 즉시 발송</button>
      </div>
      <div class="action-group">
        <button class="btn btn-outline btn-sm" @click="refreshAll"><ReloadOutlined /> 새로고침</button>
      </div>
    </div>

    <!-- 추이 + 규칙 실패 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-header">
          <h3>일별 평균 점수 추이 (최근 30일)</h3>
          <span class="chart-meta">{{ trend.length }} days</span>
        </div>
        <svg class="trend-svg" :viewBox="`0 0 ${trendWidth} ${trendHeight}`" preserveAspectRatio="none">
          <line v-for="g in [20,40,60,80,100]" :key="g"
                :x1="0" :x2="trendWidth" :y1="scoreY(g)" :y2="scoreY(g)"
                stroke="#eee" stroke-dasharray="3 3" />
          <polyline v-if="trendPath" :points="trendPath" fill="none" stroke="#0066CC" stroke-width="2" />
          <circle v-for="(p, i) in trendPoints" :key="i"
                  :cx="p.x" :cy="p.y" r="2.5" fill="#0066CC">
            <title>{{ p.day }}: {{ p.score.toFixed(1) }}점 ({{ p.count }}건)</title>
          </circle>
        </svg>
        <div class="trend-axis">
          <span>{{ trend[0]?.day || '-' }}</span>
          <span>{{ trend[trend.length - 1]?.day || '-' }}</span>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <h3>규칙별 실패 Top 10 (최근 7일)</h3>
          <span class="chart-meta">{{ ruleFailures.length }} rules</span>
        </div>
        <div v-if="ruleFailures.length === 0" class="empty-note">실패 규칙 없음</div>
        <ul class="bar-list">
          <li v-for="(r, i) in ruleFailures" :key="i">
            <div class="bar-label" :title="r.rule_name">{{ r.rule_name }}</div>
            <div class="bar-wrap">
              <div class="bar-fill" :style="{ width: barPct(r.failure_count) + '%' }"></div>
            </div>
            <div class="bar-value">{{ r.failure_count }}건 / {{ r.avg_score.toFixed(1) }}점</div>
          </li>
        </ul>
      </div>
    </div>

    <!-- 최근 검증 결과 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">최근 검증 결과 <strong>{{ results.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(resultCols, results, '품질_검증결과')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="results" :columnDefs="resultCols"
                   :defaultColDef="defCol" :pagination="true" :paginationPageSize="10"
                   domLayout="autoHeight" :tooltipShowDelay="0" />
      </div>
    </div>

    <!-- AI 피드백 이력 -->
    <div class="section">
      <div class="section-header">
        <h3><RobotOutlined /> AI 학습 피드백 이력</h3>
        <div class="tabs">
          <button v-for="t in feedbackTabs" :key="t.key"
                  :class="['tab-btn', { active: feedbackStatus === t.key }]"
                  @click="selectFeedbackTab(t.key)">
            {{ t.label }}
          </button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="feedbackRows" :columnDefs="feedbackCols"
                   :defaultColDef="defCol" :pagination="true" :paginationPageSize="10"
                   domLayout="autoHeight" :tooltipShowDelay="0"
                   @row-clicked="openFeedbackDetail" />
      </div>
    </div>

    <!-- 스케줄 -->
    <div class="section">
      <div class="section-header">
        <h3><CalendarOutlined /> 품질 검증 스케줄</h3>
        <button class="btn btn-primary btn-sm" @click="openScheduleForm()"><PlusOutlined /> 스케줄 추가</button>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="schedules" :columnDefs="scheduleCols"
                   :defaultColDef="defCol" :pagination="false"
                   domLayout="autoHeight" :tooltipShowDelay="0" />
      </div>
    </div>

    <!-- 피드백 상세 모달 -->
    <AdminModal :visible="showFeedbackModal" title="AI 피드백 상세" size="lg" @close="showFeedbackModal = false">
      <div v-if="feedbackDetail" class="modal-section">
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">ID</span><span class="info-value">{{ feedbackDetail.id }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 시스템</span><span class="info-value">{{ feedbackDetail.target_system }}</span></div>
          <div class="modal-info-item"><span class="info-label">피드백 유형</span><span class="info-value">{{ feedbackDetail.feedback_type }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="statusClass(feedbackDetail.dispatch_status)">{{ feedbackDetail.dispatch_status }}</span></span></div>
          <div class="modal-info-item" v-if="feedbackDetail.dispatched_at"><span class="info-label">전송일시</span><span class="info-value">{{ feedbackDetail.dispatched_at }}</span></div>
          <div class="modal-info-item" v-if="feedbackDetail.dispatch_error"><span class="info-label">오류</span><span class="info-value">{{ feedbackDetail.dispatch_error }}</span></div>
        </div>
        <div class="modal-section-title" style="margin-top:16px">학습 페이로드(JSON)</div>
        <pre class="payload-pre">{{ JSON.stringify(feedbackDetail.payload, null, 2) }}</pre>
      </div>
      <template #footer>
        <button v-if="feedbackDetail?.dispatch_status !== 'PENDING'" class="btn btn-primary" @click="retryFeedback(feedbackDetail.id)">
          <ReloadOutlined /> PENDING 으로 되돌리기
        </button>
        <button class="btn btn-outline" @click="showFeedbackModal = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 스케줄 추가/수정 모달 -->
    <AdminModal :visible="showScheduleModal" :title="scheduleForm.id ? '스케줄 수정' : '스케줄 추가'" size="md" @close="showScheduleModal = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">스케줄명</label><input v-model="scheduleForm.schedule_name" placeholder="예: 일일 카탈로그 전량 검증" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">Cron 식</label><input v-model="scheduleForm.schedule_cron" placeholder="예: 0 2 * * *" /></div>
          <div class="modal-form-group"><label class="required">대상</label>
            <select v-model="scheduleForm.target_dataset">
              <option value="CATALOG:ALL">카탈로그 전체</option>
              <option value="DISTRIBUTION:ALL">유통 전체</option>
              <option value="">사용자 지정(데이터셋명)</option>
            </select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>규칙 ID(선택)</label><input type="number" v-model.number="scheduleForm.rule_id" /></div>
          <div class="modal-form-group">
            <label style="display:flex;align-items:center;gap:6px;">
              <input type="checkbox" v-model="scheduleForm.is_active" /> 활성화
            </label>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="submitSchedule"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showScheduleModal = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  SafetyCertificateOutlined, FileSearchOutlined, WarningOutlined, RobotOutlined,
  ThunderboltOutlined, CheckCircleOutlined, SendOutlined, ReloadOutlined,
  FileExcelOutlined, CalendarOutlined, PlusOutlined, SaveOutlined,
} from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { message } from '../../../utils/message'
import { qualityApi } from '../../../api/standard.api'
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'

ModuleRegistry.registerModules([AllCommunityModule])

const defCol = { ...baseDefaultColDef }

// ── KPI ──
const summary = reactive({
  avg_score_7d: 0,
  avg_score_30d: 0,
  checks_7d: 0,
  checks_30d: 0,
  failing_rules_count: 0,
  ai_feedback_pending: 0,
  ai_feedback_sent_7d: 0,
  ai_feedback_failed_7d: 0,
  low_score_datasets_7d: 0,
})

function kpiLevel(score: number): string {
  if (score <= 0) return ''
  if (score >= 80) return 'good'
  if (score >= 60) return 'warn'
  return 'danger'
}

// ── Trend Line ──
const trend = ref<Array<{ day: string; avg_score: number; check_count: number }>>([])
const trendWidth = 600
const trendHeight = 140
const trendPoints = computed(() => {
  const n = trend.value.length
  if (n === 0) return []
  const step = n > 1 ? trendWidth / (n - 1) : trendWidth / 2
  return trend.value.map((t, i) => ({
    x: n === 1 ? trendWidth / 2 : i * step,
    y: scoreY(t.avg_score),
    day: t.day,
    score: t.avg_score,
    count: t.check_count,
  }))
})
const trendPath = computed(() => trendPoints.value.map(p => `${p.x},${p.y}`).join(' '))
function scoreY(score: number): number {
  const clamped = Math.max(0, Math.min(100, score))
  return trendHeight - (clamped / 100) * trendHeight
}

// ── Rule Failures ──
const ruleFailures = ref<Array<{ rule_id: number | null; rule_name: string; failure_count: number; avg_score: number }>>([])
function barPct(cnt: number): number {
  const max = Math.max(1, ...ruleFailures.value.map(r => r.failure_count))
  return (cnt / max) * 100
}

// ── Results Grid ──
const results = ref<any[]>([])
const resultCols: ColDef[] = withHeaderTooltips([
  { headerName: '#', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 48 },
  { headerName: '대상', field: 'target_type', flex: 0.6, minWidth: 80 },
  { headerName: '데이터셋', field: 'dataset_name', flex: 1.6 },
  { headerName: '검증유형', field: 'check_type', flex: 0.8 },
  { headerName: '점수', field: 'score_display', width: 90, cellStyle: (p: any) => ({ color: scoreColor(p.data?.score) }) },
  { headerName: '오류', field: 'error_count', width: 70 },
  { headerName: 'AI 반영', field: 'ai_feedback_used_display', width: 80 },
  { headerName: '실행일시', field: 'executed_display', flex: 1.1 },
])

function scoreColor(score: any): string {
  const s = Number(score)
  if (s >= 80) return '#28A745'
  if (s >= 60) return '#FFC107'
  return '#DC3545'
}

// ── Feedback Grid ──
type FeedbackStatus = 'PENDING' | 'SENT' | 'FAILED'
const feedbackTabs: Array<{ key: FeedbackStatus; label: string }> = [
  { key: 'PENDING', label: 'PENDING' },
  { key: 'SENT', label: 'SENT' },
  { key: 'FAILED', label: 'FAILED' },
]
const feedbackStatus = ref<FeedbackStatus>('PENDING')
const feedbackRows = ref<any[]>([])
const feedbackCols: ColDef[] = withHeaderTooltips([
  { headerName: '#', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 48 },
  { headerName: '대상AI', field: 'target_system', width: 90 },
  { headerName: '유형', field: 'feedback_type', flex: 1 },
  { headerName: '상태', field: 'dispatch_status', width: 100 },
  { headerName: '결과ID', field: 'source_result_id', width: 85 },
  { headerName: '생성일시', field: 'created_display', flex: 1 },
  { headerName: '전송일시', field: 'dispatched_display', flex: 1 },
  { headerName: '에러', field: 'dispatch_error', flex: 1.4 },
])

const showFeedbackModal = ref(false)
const feedbackDetail = ref<any>(null)

function openFeedbackDetail(evt: any) {
  feedbackDetail.value = evt.data._raw
  showFeedbackModal.value = true
}

function statusClass(status: string): string {
  if (status === 'SENT') return 'badge-success'
  if (status === 'FAILED') return 'badge-error'
  if (status === 'PENDING') return 'badge-warning'
  return 'badge-muted'
}

async function selectFeedbackTab(key: FeedbackStatus) {
  feedbackStatus.value = key
  await loadFeedback()
}

async function retryFeedback(id: string) {
  try {
    await qualityApi.retryAiFeedback(id)
    message.success('PENDING 으로 되돌렸습니다. 다음 일괄 발송에서 재시도됩니다.')
    showFeedbackModal.value = false
    await loadFeedback()
    await loadSummary()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '실패')
  }
}

// ── Schedules Grid ──
const schedules = ref<any[]>([])
const scheduleCols: ColDef[] = withHeaderTooltips([
  { headerName: '#', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 48 },
  { headerName: '스케줄명', field: 'schedule_name', flex: 1.6 },
  { headerName: 'Cron', field: 'schedule_cron', flex: 0.9 },
  { headerName: '대상', field: 'target_dataset', flex: 1 },
  { headerName: '규칙ID', field: 'rule_id', width: 80 },
  { headerName: '활성', field: 'is_active_display', width: 70 },
  { headerName: '최근실행', field: 'last_display', flex: 1 },
  { headerName: '다음실행', field: 'next_display', flex: 1 },
  {
    headerName: '',
    field: '_actions',
    width: 120,
    cellRenderer: (params: any) => {
      const el = document.createElement('span')
      el.style.display = 'inline-flex'; el.style.gap = '4px'
      const edit = document.createElement('button')
      edit.textContent = '수정'
      edit.className = 'btn btn-outline btn-xs'
      edit.onclick = (ev) => { ev.stopPropagation(); openScheduleForm(params.data._raw) }
      const del = document.createElement('button')
      del.textContent = '삭제'
      del.className = 'btn btn-outline btn-xs'
      del.onclick = async (ev) => {
        ev.stopPropagation()
        if (!confirm('삭제하시겠습니까?')) return
        try {
          await qualityApi.deleteSchedule(params.data.id)
          message.success('삭제되었습니다')
          await loadSchedules()
        } catch (e: any) { message.error(e?.response?.data?.detail || '실패') }
      }
      el.appendChild(edit); el.appendChild(del)
      return el
    },
  },
])

const showScheduleModal = ref(false)
const scheduleForm = reactive<any>({
  id: null,
  rule_id: null,
  schedule_name: '',
  schedule_cron: '',
  target_dataset: 'CATALOG:ALL',
  is_active: true,
})

function openScheduleForm(row?: any) {
  if (row) {
    Object.assign(scheduleForm, {
      id: row.id,
      rule_id: row.rule_id,
      schedule_name: row.schedule_name,
      schedule_cron: row.schedule_cron,
      target_dataset: row.target_dataset || 'CATALOG:ALL',
      is_active: row.is_active,
    })
  } else {
    Object.assign(scheduleForm, {
      id: null, rule_id: null, schedule_name: '', schedule_cron: '0 2 * * *',
      target_dataset: 'CATALOG:ALL', is_active: true,
    })
  }
  showScheduleModal.value = true
}

async function submitSchedule() {
  if (!scheduleForm.schedule_name || !scheduleForm.schedule_cron) {
    message.warning('스케줄명과 Cron 식을 입력하세요.')
    return
  }
  try {
    const payload = {
      schedule_name: scheduleForm.schedule_name,
      schedule_cron: scheduleForm.schedule_cron,
      target_dataset: scheduleForm.target_dataset || null,
      rule_id: scheduleForm.rule_id || null,
      is_active: !!scheduleForm.is_active,
    }
    if (scheduleForm.id) {
      await qualityApi.updateSchedule(scheduleForm.id, payload)
      message.success('스케줄이 수정되었습니다')
    } else {
      await qualityApi.createSchedule(payload)
      message.success('스케줄이 생성되었습니다')
    }
    showScheduleModal.value = false
    await loadSchedules()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '실패')
  }
}

// ── 데이터 로더 ──
async function loadSummary() {
  try {
    const res = await qualityApi.dashboardSummary()
    Object.assign(summary, res.data.data || {})
  } catch (e) { console.warn(e) }
}

async function loadTrend() {
  try {
    const res = await qualityApi.dashboardTrend(30)
    trend.value = res.data.data || []
  } catch (e) { console.warn(e) }
}

async function loadRuleFailures() {
  try {
    const res = await qualityApi.dashboardRuleFailures(10)
    ruleFailures.value = res.data.data || []
  } catch (e) { console.warn(e) }
}

async function loadResults() {
  try {
    const res = await qualityApi.listResults({ page: 1, page_size: 50 } as any)
    results.value = (res.data.items || []).map((r: any) => ({
      ...r,
      target_type: r.distribution_dataset_id ? '유통' : (r.catalog_dataset_id ? '카탈로그' : '기타'),
      score_display: r.score != null ? `${Number(r.score).toFixed(1)}점` : '-',
      executed_display: r.executed_at?.substring(0, 19).replace('T', ' ') || '',
      ai_feedback_used_display: r.ai_feedback_used ? 'Y' : '-',
    }))
  } catch (e) { console.warn(e) }
}

async function loadFeedback() {
  try {
    const res = await qualityApi.listAiFeedback({
      status: feedbackStatus.value,
      page: 1,
      page_size: 50,
    })
    feedbackRows.value = (res.data.items || []).map((f: any) => ({
      _raw: f,
      target_system: f.target_system,
      feedback_type: f.feedback_type,
      dispatch_status: f.dispatch_status,
      source_result_id: f.source_result_id,
      created_display: f.created_at?.substring(0, 19).replace('T', ' ') || '',
      dispatched_display: f.dispatched_at?.substring(0, 19).replace('T', ' ') || '',
      dispatch_error: f.dispatch_error || '',
    }))
  } catch (e) { console.warn(e) }
}

async function loadSchedules() {
  try {
    const res = await qualityApi.listSchedules()
    schedules.value = (res.data.data || []).map((s: any) => ({
      _raw: s,
      id: s.id,
      rule_id: s.rule_id,
      schedule_name: s.schedule_name,
      schedule_cron: s.schedule_cron,
      target_dataset: s.target_dataset || '',
      is_active_display: s.is_active ? 'Y' : 'N',
      last_display: s.last_run_at?.substring(0, 19).replace('T', ' ') || '-',
      next_display: s.next_run_at?.substring(0, 19).replace('T', ' ') || '-',
    }))
  } catch (e) { console.warn(e) }
}

async function refreshAll() {
  await Promise.all([loadSummary(), loadTrend(), loadRuleFailures(), loadResults(), loadFeedback(), loadSchedules()])
}

// ── 액션 버튼 ──
async function runCatalogAll() {
  try {
    await qualityApi.executeCheck()
    message.success('카탈로그 전량 검증 완료')
    await refreshAll()
  } catch (e: any) { message.error(e?.response?.data?.detail || '실패') }
}

async function runDistributionAll() {
  try {
    const res = await qualityApi.checkDistributionAll()
    message.success(res.data.message || '유통 전량 검증 dispatch')
    setTimeout(() => refreshAll(), 3000)
  } catch (e: any) { message.error(e?.response?.data?.detail || '실패') }
}

async function runCompliance() {
  try {
    await qualityApi.runComplianceCheck()
    message.success('용어 준수 검사 완료')
    await refreshAll()
  } catch (e: any) { message.error(e?.response?.data?.detail || '실패') }
}

async function dispatchNow() {
  try {
    await qualityApi.dispatchAiFeedbackNow()
    message.success('AI 피드백 일괄 발송 dispatch 완료')
    setTimeout(() => refreshAll(), 2000)
  } catch (e: any) { message.error(e?.response?.data?.detail || '실패') }
}

onMounted(() => {
  refreshAll()
})
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';
@use '../../../styles/variables' as *;

.quality-dashboard {
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: $spacing-md;
    margin-bottom: $spacing-lg;
  }

  .kpi-card {
    background: $white;
    border: 1px solid $border-color;
    border-radius: $radius-lg;
    padding: $spacing-lg;
    display: flex;
    gap: $spacing-md;
    align-items: center;

    .kpi-icon {
      font-size: 28px;
      color: $primary;
      flex-shrink: 0;
    }
    .kpi-body { flex: 1; }
    .kpi-label {
      font-size: $font-size-xs;
      color: $text-secondary;
      margin-bottom: 2px;
    }
    .kpi-value {
      font-size: 24px;
      font-weight: 700;
      color: $text-primary;
      .unit {
        font-size: $font-size-md;
        font-weight: 500;
        color: $text-secondary;
        margin-left: 2px;
      }
    }
    .kpi-sub { font-size: 11px; color: $text-muted; }
    &.good { border-left: 3px solid $success; }
    &.warn { border-left: 3px solid $warning; .kpi-icon { color: $warning; } }
    &.danger { border-left: 3px solid $error; .kpi-icon { color: $error; } }
  }

  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
    .action-group { display: flex; gap: $spacing-xs; }
  }

  .chart-row {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: $spacing-md;
    margin-bottom: $spacing-lg;
  }

  .chart-card {
    background: $white;
    border: 1px solid $border-color;
    border-radius: $radius-lg;
    padding: $spacing-md $spacing-lg;
    min-height: 230px;
    display: flex;
    flex-direction: column;

    .chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: $spacing-sm;
      h3 { font-size: $font-size-md; font-weight: 600; margin: 0; }
      .chart-meta { font-size: $font-size-xs; color: $text-muted; }
    }

    .trend-svg {
      width: 100%;
      height: 160px;
    }

    .trend-axis {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: $text-muted;
      margin-top: 4px;
    }

    .empty-note {
      color: $text-muted;
      text-align: center;
      padding: $spacing-xl 0;
      font-size: $font-size-sm;
    }

    .bar-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
      li {
        display: grid;
        grid-template-columns: 100px 1fr auto;
        gap: $spacing-sm;
        align-items: center;
        font-size: $font-size-xs;
      }
      .bar-label {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: $text-secondary;
      }
      .bar-wrap {
        background: $bg-light;
        height: 10px;
        border-radius: 5px;
        overflow: hidden;
      }
      .bar-fill {
        background: linear-gradient(90deg, $warning, $error);
        height: 100%;
      }
      .bar-value {
        white-space: nowrap;
        color: $text-muted;
      }
    }
  }

  .section {
    background: $white;
    border: 1px solid $border-color;
    border-radius: $radius-lg;
    padding: $spacing-md $spacing-lg;
    margin-bottom: $spacing-lg;

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-sm;
      h3 {
        font-size: $font-size-md;
        font-weight: 600;
        margin: 0;
        display: inline-flex;
        gap: 6px;
        align-items: center;
      }
      .tabs { display: flex; gap: 2px; }
      .tab-btn {
        border: 1px solid $border-color;
        background: $white;
        padding: 4px 10px;
        font-size: $font-size-xs;
        cursor: pointer;
        &:first-child { border-radius: $radius-sm 0 0 $radius-sm; }
        &:last-child { border-radius: 0 $radius-sm $radius-sm 0; }
        &.active {
          background: $primary;
          color: $white;
          border-color: $primary;
        }
      }
    }
  }

  .payload-pre {
    background: #1f2428;
    color: #e1e4e8;
    border-radius: $radius-md;
    padding: $spacing-md;
    font-size: 11px;
    font-family: 'JetBrains Mono', 'D2Coding', monospace;
    overflow: auto;
    max-height: 360px;
  }

  :deep(.btn-xs) {
    font-size: 11px;
    padding: 2px 8px;
    line-height: 1.3;
  }

  // 태블릿 대응
  @media (max-width: 1279px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
    .chart-row { grid-template-columns: 1fr; }
  }
}
</style>
