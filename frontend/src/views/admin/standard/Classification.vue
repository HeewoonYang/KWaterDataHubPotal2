<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>분류 등록</h2>
      <p class="page-desc">데이터 분류 체계(대/중/소분류)를 등록·수정하고 표준 단어/용어/코드/도메인과 연동합니다. K-water 데이터 관리포털과의 정기 동기화를 지원합니다.</p>
    </div>

    <!-- 연동 현황 패널 -->
    <div class="sync-panel">
      <div class="sync-panel-main">
        <div class="sync-status-group">
          <span class="sync-label">연동 상태</span>
          <span class="sync-badge" :class="`sync-badge-${syncSettings.enabled ? (lastSync.status || 'ready') : 'disabled'}`">
            <span class="sync-dot"></span>
            {{ syncStateText }}
          </span>
        </div>
        <div class="sync-meta">
          <div class="sync-meta-item">
            <CloudServerOutlined />
            <span class="sync-meta-label">연계 대상</span>
            <span class="sync-meta-value">K-water 데이터 관리포털</span>
            <span class="sync-chip sync-chip-tbd">연계방식 협의중</span>
          </div>
          <div class="sync-meta-item">
            <ScheduleOutlined />
            <span class="sync-meta-label">동기화 주기</span>
            <span class="sync-meta-value">{{ scheduleText }}</span>
          </div>
          <div class="sync-meta-item">
            <ClockCircleOutlined />
            <span class="sync-meta-label">최근 동기화</span>
            <span class="sync-meta-value">{{ lastSync.at || '-' }}</span>
            <span v-if="lastSync.at" class="sync-chip" :class="`sync-chip-${lastSync.status}`">
              {{ lastSyncResultText }}
            </span>
          </div>
        </div>
      </div>
      <div class="sync-panel-actions">
        <button class="btn btn-sm btn-outline" @click="openHistory"><HistoryOutlined /> 동기화 이력</button>
        <button class="btn btn-sm btn-outline" @click="openSyncSettings"><SettingOutlined /> 연동 설정</button>
        <button class="btn btn-sm btn-primary" :disabled="syncing" @click="runSyncNow">
          <SyncOutlined :spin="syncing" /> {{ syncing ? '동기화 중...' : '지금 동기화' }}
        </button>
      </div>
    </div>

    <div class="table-section">
      <div class="table-header">
        <span class="table-count">분류 체계 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-filters">
          <label class="filter-chip">
            <input type="checkbox" v-model="filterOnlyMismatch" />
            미일치/신규만 보기
          </label>
        </div>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="openCreate"><PlusOutlined /> 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, filteredRows, '분류_체계')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          :tooltipShowDelay="0"
          class="ag-theme-alpine"
          :rowData="filteredRows"
          :columnDefs="cols"
          :defaultColDef="defCol"
          :pagination="true"
          :paginationPageSize="20"
          domLayout="autoHeight"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- 분류 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="`${detailRow.code || ''} 분류 상세`" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">분류 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">대분류</span><span class="info-value">{{ detailRow.category1 }}</span></div>
          <div class="modal-info-item"><span class="info-label">중분류</span><span class="info-value">{{ detailRow.category2 || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">소분류</span><span class="info-value">{{ detailRow.category3 || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">코드</span><span class="info-value">{{ detailRow.code }}</span></div>
          <div class="modal-info-item"><span class="info-label">레벨</span><span class="info-value">L{{ detailRow.level }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value">{{ detailRow.status }}</span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">연동 표준사전</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">단어</span><span class="info-value">{{ detailRow.std_word_name || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">용어</span><span class="info-value">{{ detailRow.std_term_name || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">도메인</span><span class="info-value">{{ detailRow.std_domain_name || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">코드</span><span class="info-value">{{ detailRow.std_code_name || '-' }}</span></div>
        </div>
        <div v-if="detailRow.description" class="modal-info-item" style="margin-top:8px;">
          <span class="info-label">설명</span>
          <span class="info-value">{{ detailRow.description }}</span>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">연결된 논리/물리 모델 ({{ linkedModels.length }}건)</div>
        <table class="modal-table" v-if="linkedModels.length">
          <thead><tr><th>유형</th><th>모델명</th><th>시스템</th><th>버전</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="m in linkedModels" :key="m.id">
              <td><span class="badge" :class="m.model_type === 'LOGICAL' ? 'badge-info' : 'badge-success'">{{ m.model_type }}</span></td>
              <td>{{ m.model_name }}</td>
              <td>{{ m.system_name || '-' }}</td>
              <td>{{ m.version || '-' }}</td>
              <td>{{ m.status }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#888; font-size:13px;">연결된 모델이 없습니다.</p>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">관리포털 연동 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">원천</span>
            <span class="info-value">
              <span class="badge" :class="detailRow.source === 'PORTAL' ? 'badge-info' : 'badge-default'">
                {{ detailRow.source === 'PORTAL' ? '관리포털' : 'LOCAL' }}
              </span>
            </span>
          </div>
          <div class="modal-info-item"><span class="info-label">관리포털 코드</span><span class="info-value">{{ detailRow.portal_code || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">동기화 상태</span>
            <span class="info-value">
              <span class="sync-chip" :class="`sync-chip-${detailRow.sync_status || 'ready'}`">
                {{ syncStatusLabel(detailRow.sync_status) }}
              </span>
            </span>
          </div>
          <div class="modal-info-item"><span class="info-label">최근 동기화</span><span class="info-value">{{ detailRow.synced_at || '-' }}</span></div>
        </div>
        <div class="modal-sub-title" style="margin-top:12px;">변경 이력</div>
        <table class="modal-table" v-if="itemHistory.length">
          <thead><tr><th style="width:140px;">일시</th><th style="width:90px;">유형</th><th style="width:90px;">원천</th><th style="width:90px;">상태</th><th>내용</th></tr></thead>
          <tbody>
            <tr v-for="h in itemHistory" :key="h.id">
              <td>{{ h.at }}</td>
              <td><span class="badge" :class="`badge-${h.changeType}`">{{ historyTypeLabel(h.changeType) }}</span></td>
              <td>{{ h.source === 'PORTAL' ? '관리포털' : 'LOCAL' }}</td>
              <td><span class="sync-chip" :class="`sync-chip-${h.status}`">{{ syncStatusLabel(h.status) }}</span></td>
              <td>{{ h.message || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else style="color:#888; font-size:13px;">변경 이력이 없습니다.</p>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="openEdit(detailRow)"><EditOutlined /> 수정</button>
        <button class="btn btn-danger" @click="handleDelete(detailRow)"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 분류 등록/수정 팝업 -->
    <AdminModal :visible="showForm" :title="editId ? '분류 수정' : '분류 등록'" size="md" @close="closeForm">
      <div class="modal-form">
        <div class="form-row">
          <label>레벨 *</label>
          <select v-model.number="form.level" @change="onLevelChange">
            <option :value="1">대분류 (L1)</option>
            <option :value="2">중분류 (L2)</option>
            <option :value="3">소분류 (L3)</option>
          </select>
        </div>
        <div class="form-row" v-if="form.level > 1">
          <label>상위분류 *</label>
          <select v-model.number="form.parent_id">
            <option :value="null">선택</option>
            <option v-for="p in parentCandidates" :key="p.id" :value="p.id">{{ p.name }} ({{ p.code }})</option>
          </select>
        </div>
        <div class="form-row">
          <label>분류명 *</label>
          <input v-model="form.name" placeholder="예: 수자원 / 댐 / 수위" />
        </div>
        <div class="form-row">
          <label>코드 *</label>
          <input v-model="form.code" placeholder="예: WR-DAM-LV" />
        </div>
        <div class="form-row">
          <label>설명</label>
          <textarea v-model="form.description" rows="2" placeholder="분류 설명"></textarea>
        </div>
        <div class="form-row">
          <label>정렬순서</label>
          <input v-model.number="form.sort_order" type="number" min="0" />
        </div>

        <div class="form-row">
          <label>표준 단어</label>
          <select v-model.number="form.std_word_id">
            <option :value="null">(연동 안 함)</option>
            <option v-for="w in stdWords" :key="w.id" :value="w.id">{{ w.word_name }} / {{ w.english_name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>표준 용어</label>
          <select v-model.number="form.std_term_id">
            <option :value="null">(연동 안 함)</option>
            <option v-for="t in stdTerms" :key="t.id" :value="t.id">{{ t.term_name }} / {{ t.english_name }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>표준 도메인</label>
          <select v-model.number="form.std_domain_id">
            <option :value="null">(연동 안 함)</option>
            <option v-for="d in stdDomains" :key="d.id" :value="d.id">{{ d.domain_name }} ({{ d.domain_code }})</option>
          </select>
        </div>
        <div class="form-row">
          <label>표준 코드</label>
          <select v-model.number="form.std_code_id">
            <option :value="null">(연동 안 함)</option>
            <option v-for="c in stdCodes" :key="c.id" :value="c.id">{{ c.code_group_name }} - {{ c.code_id }}</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleSave"><SaveOutlined /> {{ editId ? '수정' : '등록' }}</button>
        <button class="btn btn-outline" @click="closeForm">취소</button>
      </template>
    </AdminModal>

    <!-- 연동 설정 모달 -->
    <AdminModal :visible="showSyncSettings" title="데이터 관리포털 연동 설정" size="md" @close="showSyncSettings = false">
      <div class="modal-form">
        <div class="form-notice">
          <InfoCircleOutlined /> K-water 데이터 관리포털과의 실제 연계 스펙은 협의 중이며, 아래 설정은 스펙 확정 후 실제 동기화에 적용됩니다.
        </div>
        <div class="form-row">
          <label>연동 활성화</label>
          <label class="switch">
            <input type="checkbox" v-model="syncSettingsDraft.enabled" />
            <span>사용</span>
          </label>
        </div>
        <div class="form-row">
          <label>연계 방식</label>
          <select v-model="syncSettingsDraft.method">
            <option value="REST">REST API (관리포털 → 허브)</option>
            <option value="FILE">파일 연계 (CSV/Excel)</option>
            <option value="DBLINK">DB Link (직접 조회)</option>
            <option value="KAFKA">Kafka 이벤트 구독</option>
          </select>
        </div>
        <div class="form-row">
          <label>엔드포인트</label>
          <input v-model="syncSettingsDraft.endpoint" placeholder="예: https://mgmt-portal.kwater.or.kr/api/v1/classifications (협의 후 입력)" />
        </div>
        <div class="form-row">
          <label>인증 방식</label>
          <select v-model="syncSettingsDraft.authType">
            <option value="NONE">(없음)</option>
            <option value="APIKEY">API Key</option>
            <option value="OAUTH2">OAuth2 / JWT</option>
            <option value="MTLS">mTLS 상호인증</option>
          </select>
        </div>
        <div class="form-row" v-if="syncSettingsDraft.authType !== 'NONE'">
          <label>인증 토큰/키</label>
          <input v-model="syncSettingsDraft.authToken" type="password" placeholder="실제 값은 Secret/Vault 저장 권장" />
        </div>
        <div class="form-row">
          <label>동기화 주기</label>
          <select v-model="syncSettingsDraft.schedule">
            <option value="MANUAL">수동 (사용자 요청 시)</option>
            <option value="HOURLY">매시간</option>
            <option value="DAILY">매일</option>
            <option value="CUSTOM">사용자 정의 (Cron)</option>
          </select>
        </div>
        <div class="form-row" v-if="syncSettingsDraft.schedule === 'DAILY'">
          <label>실행 시각</label>
          <input v-model="syncSettingsDraft.dailyTime" type="time" />
        </div>
        <div class="form-row" v-if="syncSettingsDraft.schedule === 'CUSTOM'">
          <label>Cron 표현식</label>
          <input v-model="syncSettingsDraft.cron" placeholder="0 */1 * * *" />
        </div>
        <div class="form-row">
          <label>충돌 시 처리</label>
          <select v-model="syncSettingsDraft.conflictPolicy">
            <option value="PORTAL_WINS">관리포털 우선 (덮어쓰기)</option>
            <option value="LOCAL_WINS">로컬 우선 (건너뜀)</option>
            <option value="MANUAL">수동 병합 (알림)</option>
          </select>
        </div>
        <div class="form-row">
          <label>표준체계 자동 매핑</label>
          <label class="switch">
            <input type="checkbox" v-model="syncSettingsDraft.autoMapStandard" />
            <span>동기화 시 분류명/코드를 기준으로 단어·용어·도메인·코드 자동 매핑 시도</span>
          </label>
        </div>
        <div class="form-row">
          <label>삭제 처리</label>
          <select v-model="syncSettingsDraft.deletePolicy">
            <option value="SOFT">논리삭제 (is_deleted=true)</option>
            <option value="INACTIVE">비활성 처리</option>
            <option value="KEEP">유지 (이력만 기록)</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="saveSyncSettings"><SaveOutlined /> 설정 저장</button>
        <button class="btn btn-outline" @click="showSyncSettings = false">취소</button>
      </template>
    </AdminModal>

    <!-- 동기화 이력 모달 -->
    <AdminModal :visible="showHistory" title="분류체계 동기화 이력" size="lg" @close="showHistory = false">
      <div class="modal-section">
        <div class="sync-history-summary">
          <div class="summary-chip"><strong>{{ historySummary.total }}</strong> 총건수</div>
          <div class="summary-chip summary-chip-NEW"><strong>{{ historySummary.NEW }}</strong> 신규</div>
          <div class="summary-chip summary-chip-MATCH"><strong>{{ historySummary.MATCH }}</strong> 일치</div>
          <div class="summary-chip summary-chip-MISMATCH"><strong>{{ historySummary.MISMATCH }}</strong> 불일치</div>
          <div class="summary-chip summary-chip-DELETED"><strong>{{ historySummary.DELETED }}</strong> 삭제</div>
        </div>
        <table class="modal-table">
          <thead>
            <tr>
              <th style="width:140px;">일시</th>
              <th style="width:90px;">유형</th>
              <th style="width:110px;">분류코드</th>
              <th>분류명</th>
              <th style="width:90px;">원천</th>
              <th style="width:90px;">상태</th>
              <th>메시지</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in syncHistory" :key="h.id">
              <td>{{ h.at }}</td>
              <td><span class="badge" :class="`badge-${h.changeType}`">{{ historyTypeLabel(h.changeType) }}</span></td>
              <td>{{ h.code }}</td>
              <td>{{ h.name }}</td>
              <td>{{ h.source === 'PORTAL' ? '관리포털' : 'LOCAL' }}</td>
              <td><span class="sync-chip" :class="`sync-chip-${h.status}`">{{ syncStatusLabel(h.status) }}</span></td>
              <td>{{ h.message || '-' }}</td>
            </tr>
            <tr v-if="!syncHistory.length">
              <td colspan="7" style="text-align:center; color:#888; padding:24px;">동기화 이력이 없습니다.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showHistory = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import {
  PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined,
  CloudServerOutlined, ScheduleOutlined, ClockCircleOutlined, HistoryOutlined,
  SettingOutlined, SyncOutlined, InfoCircleOutlined,
} from '@ant-design/icons-vue'
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import {
  classificationApi, modelApi, wordApi, termApi, domainApi, codeApi,
} from '../../../api/standard.api'
import type { Classification, StdWord, StdTerm, StdDomain, StdCode, MetaModel } from '../../../types/standard'

ModuleRegistry.registerModules([AllCommunityModule])

// ── 상태 ──
const showDetail = ref(false)
const showForm = ref(false)
const showSyncSettings = ref(false)
const showHistory = ref(false)
const editId = ref<number | null>(null)
const detailRow = ref<any>({})
const linkedModels = ref<MetaModel[]>([])
const allClassifications = ref<Classification[]>([])
const filterOnlyMismatch = ref(false)
const syncing = ref(false)

const stdWords = ref<StdWord[]>([])
const stdTerms = ref<StdTerm[]>([])
const stdDomains = ref<StdDomain[]>([])
const stdCodes = ref<StdCode[]>([])

// ── 연동 설정 (로컬 보관, 백엔드 연계 스펙 확정 후 서버로 이관) ──
interface SyncSettings {
  enabled: boolean
  method: 'REST' | 'FILE' | 'DBLINK' | 'KAFKA'
  endpoint: string
  authType: 'NONE' | 'APIKEY' | 'OAUTH2' | 'MTLS'
  authToken: string
  schedule: 'MANUAL' | 'HOURLY' | 'DAILY' | 'CUSTOM'
  dailyTime: string
  cron: string
  conflictPolicy: 'PORTAL_WINS' | 'LOCAL_WINS' | 'MANUAL'
  autoMapStandard: boolean
  deletePolicy: 'SOFT' | 'INACTIVE' | 'KEEP'
}
const defaultSyncSettings = (): SyncSettings => ({
  enabled: false,
  method: 'REST',
  endpoint: '',
  authType: 'OAUTH2',
  authToken: '',
  schedule: 'DAILY',
  dailyTime: '02:00',
  cron: '0 */1 * * *',
  conflictPolicy: 'MANUAL',
  autoMapStandard: true,
  deletePolicy: 'SOFT',
})
const SYNC_SETTINGS_KEY = 'classification.syncSettings'
const LAST_SYNC_KEY = 'classification.lastSync'

const syncSettings = ref<SyncSettings>(defaultSyncSettings())
const syncSettingsDraft = reactive<SyncSettings>(defaultSyncSettings())
const lastSync = ref<{ at: string; status: string; message?: string }>({ at: '', status: 'ready' })

// 동기화 이력 (ClassificationSyncLog 연동 자리 — 현재는 데모 데이터)
interface HistoryItem {
  id: number
  at: string
  changeType: 'NEW' | 'UPDATE' | 'DELETE'
  code: string
  name: string
  source: 'PORTAL' | 'LOCAL'
  status: 'MATCH' | 'MISMATCH' | 'NEW' | 'DELETED' | 'ERROR'
  message?: string
  classificationId?: number
}
const syncHistory = ref<HistoryItem[]>([])

const form = reactive({
  level: 1 as 1 | 2 | 3,
  parent_id: null as number | null,
  name: '',
  code: '',
  description: '',
  sort_order: 0,
  std_word_id: null as number | null,
  std_term_id: null as number | null,
  std_domain_id: null as number | null,
  std_code_id: null as number | null,
})

// ── 그리드 컬럼 ──
const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '대분류', field: 'category1', flex: 1 },
  { headerName: '중분류', field: 'category2', flex: 1 },
  { headerName: '소분류', field: 'category3', flex: 1 },
  { headerName: '코드', field: 'code', width: 130 },
  { headerName: '표준단어', field: 'std_word_name', width: 120 },
  { headerName: '표준용어', field: 'std_term_name', width: 120 },
  { headerName: '도메인', field: 'std_domain_name', width: 110 },
  {
    headerName: '원천', field: 'source', width: 100,
    cellRenderer: (p: any) => {
      const v = p.value || 'LOCAL'
      const label = v === 'PORTAL' ? '관리포털' : 'LOCAL'
      const cls = v === 'PORTAL' ? 'badge badge-info' : 'badge badge-default'
      return `<span class="${cls}">${label}</span>`
    },
  },
  {
    headerName: '동기화', field: 'sync_status', width: 100,
    cellRenderer: (p: any) => {
      const v = p.value || 'ready'
      const labels: Record<string, string> = { MATCH: '일치', MISMATCH: '불일치', NEW: '신규', DELETED: '삭제', ERROR: '오류', ready: '-' }
      return `<span class="sync-chip sync-chip-${v}">${labels[v] || v}</span>`
    },
  },
  { headerName: '등록일', field: 'regDate', width: 110 },
])

// 평탄화된 그리드 rows (leaf 노드를 기준으로 대/중/소 경로 추적)
const rows = computed(() => {
  const byId = new Map<number, Classification>()
  allClassifications.value.forEach(c => byId.set(c.id, c))
  const items: any[] = []
  for (const c of allClassifications.value) {
    const path: Classification[] = []
    let cur: Classification | undefined = c
    while (cur) {
      path.unshift(cur)
      cur = cur.parent_id != null ? byId.get(cur.parent_id) : undefined
    }
    const meta = (c as any) // 백엔드 확장 필드 대비: source, portal_code, sync_status, synced_at
    items.push({
      id: c.id,
      level: c.level,
      parent_id: c.parent_id,
      name: c.name,
      code: c.code,
      status: c.status,
      description: c.description,
      std_word_id: c.std_word_id,
      std_term_id: c.std_term_id,
      std_domain_id: c.std_domain_id,
      std_code_id: c.std_code_id,
      std_word_name: c.std_word_name,
      std_term_name: c.std_term_name,
      std_domain_name: c.std_domain_name,
      std_code_name: c.std_code_name,
      source: meta.source || 'LOCAL',
      portal_code: meta.portal_code || null,
      sync_status: meta.sync_status || 'ready',
      synced_at: meta.synced_at || null,
      category1: path[0]?.name || '',
      category2: path[1]?.name || '',
      category3: path[2]?.name || '',
      regDate: c.created_at ? c.created_at.substring(0, 10) : '',
    })
  }
  return items
})

const filteredRows = computed(() => {
  if (!filterOnlyMismatch.value) return rows.value
  return rows.value.filter(r => ['MISMATCH', 'NEW', 'DELETED', 'ERROR'].includes(r.sync_status))
})

// ── 연동 현황 표시 ──
const syncStateText = computed(() => {
  if (!syncSettings.value.enabled) return '연동 비활성'
  if (syncing.value) return '동기화 중'
  switch (lastSync.value.status) {
    case 'SUCCESS': return '정상'
    case 'PARTIAL': return '부분 성공'
    case 'ERROR': return '오류'
    default: return '대기'
  }
})
const scheduleText = computed(() => {
  const s = syncSettings.value
  if (!s.enabled) return '미사용'
  switch (s.schedule) {
    case 'MANUAL': return '수동'
    case 'HOURLY': return '매시간'
    case 'DAILY': return `매일 ${s.dailyTime}`
    case 'CUSTOM': return `Cron: ${s.cron}`
    default: return '-'
  }
})
const lastSyncResultText = computed(() => {
  switch (lastSync.value.status) {
    case 'SUCCESS': return '성공'
    case 'PARTIAL': return '부분성공'
    case 'ERROR': return '실패'
    case 'ready': return '대기'
    default: return lastSync.value.status
  }
})
const historySummary = computed(() => {
  const s = { total: syncHistory.value.length, NEW: 0, MATCH: 0, MISMATCH: 0, DELETED: 0 }
  for (const h of syncHistory.value) {
    if (h.status in s) (s as any)[h.status] += 1
  }
  return s
})
const itemHistory = computed(() => {
  if (!detailRow.value?.id) return []
  return syncHistory.value.filter(h => h.classificationId === detailRow.value.id)
})

function syncStatusLabel(v?: string) {
  const labels: Record<string, string> = { MATCH: '일치', MISMATCH: '불일치', NEW: '신규', DELETED: '삭제', ERROR: '오류', SUCCESS: '성공', PARTIAL: '부분성공', ready: '대기' }
  return labels[v || 'ready'] || v
}
function historyTypeLabel(v?: string) {
  const labels: Record<string, string> = { NEW: '신규', UPDATE: '수정', DELETE: '삭제' }
  return labels[v || ''] || v
}

// 선택된 레벨의 상위 분류 후보 (level-1의 것들)
const parentCandidates = computed(() =>
  allClassifications.value.filter(c => c.level === form.level - 1)
)

// ── API ──
async function loadClassifications() {
  try {
    const res = await classificationApi.list('flat')
    allClassifications.value = res.data.data as Classification[]
  } catch (e) {
    console.error('classification list failed', e)
    allClassifications.value = []
  }
}

async function loadStdDictionaries() {
  try {
    const [w, t, d, c] = await Promise.all([
      wordApi.list({ page: 1, page_size: 1000 }),
      termApi.list({ page: 1, page_size: 1000 }),
      domainApi.list({ page: 1, page_size: 1000 }),
      codeApi.list({ page: 1, page_size: 1000 }),
    ])
    stdWords.value = w.data.items || []
    stdTerms.value = t.data.items || []
    stdDomains.value = d.data.items || []
    stdCodes.value = c.data.items || []
  } catch (e) {
    console.error('std dictionaries load failed', e)
  }
}

async function loadLinkedModels(classificationId: number) {
  try {
    const res = await modelApi.list({ classification_id: classificationId } as any)
    linkedModels.value = (res.data.data || []) as MetaModel[]
  } catch {
    linkedModels.value = []
  }
}

// ── 그리드 / 상세 ──
function onRowClick(event: any) {
  detailRow.value = event.data
  showDetail.value = true
  loadLinkedModels(event.data.id)
}

// ── 폼 ──
function resetForm() {
  form.level = 1
  form.parent_id = null
  form.name = ''
  form.code = ''
  form.description = ''
  form.sort_order = 0
  form.std_word_id = null
  form.std_term_id = null
  form.std_domain_id = null
  form.std_code_id = null
}

function openCreate() {
  editId.value = null
  resetForm()
  showForm.value = true
}

function openEdit(row: any) {
  editId.value = row.id
  form.level = row.level
  form.parent_id = row.parent_id ?? null
  form.name = row.name
  form.code = row.code
  form.description = row.description || ''
  form.sort_order = 0
  form.std_word_id = row.std_word_id ?? null
  form.std_term_id = row.std_term_id ?? null
  form.std_domain_id = row.std_domain_id ?? null
  form.std_code_id = row.std_code_id ?? null
  showDetail.value = false
  showForm.value = true
}

function onLevelChange() {
  form.parent_id = null
}

function closeForm() {
  showForm.value = false
  editId.value = null
}

async function handleSave() {
  if (!form.name.trim()) { message.error('분류명을 입력하세요'); return }
  if (!form.code.trim()) { message.error('코드를 입력하세요'); return }
  if (form.level > 1 && form.parent_id == null) { message.error('상위분류를 선택하세요'); return }

  const body: Partial<Classification> = {
    level: form.level,
    parent_id: form.level > 1 ? form.parent_id : null,
    name: form.name.trim(),
    code: form.code.trim(),
    description: form.description || undefined,
    sort_order: form.sort_order || 0,
    std_word_id: form.std_word_id,
    std_term_id: form.std_term_id,
    std_domain_id: form.std_domain_id,
    std_code_id: form.std_code_id,
  }

  try {
    if (editId.value) {
      await classificationApi.update(editId.value, body)
      message.success('수정되었습니다')
    } else {
      await classificationApi.create(body)
      message.success('등록되었습니다')
    }
    closeForm()
    await loadClassifications()
  } catch (e: any) {
    console.error(e)
    message.error(e?.response?.data?.detail || '저장에 실패했습니다')
  }
}

async function handleDelete(row: any) {
  if (!row?.id) return
  if (!window.confirm(`"${row.name}" 분류를 삭제하시겠습니까?`)) return
  try {
    await classificationApi.delete(row.id)
    message.success('삭제되었습니다')
    showDetail.value = false
    await loadClassifications()
  } catch (e: any) {
    console.error(e)
    message.error(e?.response?.data?.detail || '삭제에 실패했습니다')
  }
}

// ── 연동 설정 / 이력 핸들러 ──
function loadSyncSettingsFromStorage() {
  try {
    const raw = localStorage.getItem(SYNC_SETTINGS_KEY)
    if (raw) syncSettings.value = { ...defaultSyncSettings(), ...JSON.parse(raw) }
    const last = localStorage.getItem(LAST_SYNC_KEY)
    if (last) lastSync.value = JSON.parse(last)
  } catch {
    /* ignore */
  }
}

function openSyncSettings() {
  Object.assign(syncSettingsDraft, syncSettings.value)
  showSyncSettings.value = true
}

function saveSyncSettings() {
  syncSettings.value = { ...syncSettingsDraft }
  try {
    localStorage.setItem(SYNC_SETTINGS_KEY, JSON.stringify(syncSettings.value))
  } catch { /* ignore */ }
  showSyncSettings.value = false
  message.success('연동 설정이 저장되었습니다. (실제 동기화는 연계 스펙 확정 후 적용)')
}

function openHistory() {
  loadSyncHistory()
  showHistory.value = true
}

async function loadSyncHistory() {
  // 실제 연동 시: await classificationApi.getSyncStatus() → ClassificationSyncLog 조회
  // 현재는 연계 스펙 미확정으로 기존 항목을 기반으로 샘플 이력 생성 (없으면 빈 배열 유지)
  try {
    const res = await classificationApi.getSyncStatus()
    const logs = (res?.data?.data || res?.data || []) as any[]
    if (Array.isArray(logs) && logs.length) {
      syncHistory.value = logs.map((l, i) => ({
        id: l.id ?? i,
        at: l.synced_at || l.created_at || '',
        changeType: l.change_type || 'UPDATE',
        code: l.hub_code || l.portal_code || '',
        name: l.name || '',
        source: (l.source || 'PORTAL') as 'PORTAL' | 'LOCAL',
        status: l.sync_status || 'MATCH',
        message: l.message,
        classificationId: l.classification_id,
      }))
    }
  } catch {
    /* API 미구현/비활성 시 빈 이력 유지 */
  }
}

async function runSyncNow() {
  if (!syncSettings.value.enabled) {
    if (!window.confirm('연동이 비활성 상태입니다. 그래도 동기화를 시도하시겠습니까?')) return
  }
  syncing.value = true
  const startedAt = new Date().toISOString().replace('T', ' ').substring(0, 19)
  try {
    await classificationApi.triggerSync()
    lastSync.value = { at: startedAt, status: 'SUCCESS', message: '동기화 요청 완료' }
    message.success('동기화가 요청되었습니다.')
    await loadSyncHistory()
    await loadClassifications()
  } catch (e: any) {
    lastSync.value = {
      at: startedAt,
      status: 'ERROR',
      message: e?.response?.data?.detail || '동기화 실패 (연계 스펙 미확정 또는 서버 오류)',
    }
    message.warning('동기화 API가 아직 연결되어 있지 않습니다. 연계 스펙 확정 후 동작합니다.')
  } finally {
    try {
      localStorage.setItem(LAST_SYNC_KEY, JSON.stringify(lastSync.value))
    } catch { /* ignore */ }
    syncing.value = false
  }
}

onMounted(async () => {
  loadSyncSettingsFromStorage()
  await Promise.all([loadClassifications(), loadStdDictionaries(), loadSyncHistory()])
})
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.btn-danger {
  background: #DC3545;
  color: #fff;
  border: 1px solid #DC3545;
  &:hover { background: #c82333; }
}

/* ── 연동 현황 패널 ── */
.sync-panel {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 14px 18px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #f0f7ff 0%, #f7faff 100%);
  border: 1px solid #d6e4f5;
  border-radius: 8px;
  flex-wrap: wrap;
}
.sync-panel-main { flex: 1; min-width: 0; }
.sync-status-group {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.sync-label {
  font-size: 12px;
  color: #6a7a8c;
  font-weight: 600;
}
.sync-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.sync-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: currentColor;
}
.sync-badge-ready, .sync-badge-MATCH, .sync-badge-SUCCESS { background: #e6f7ec; color: #19974b; }
.sync-badge-disabled { background: #f0f1f3; color: #8a94a6; }
.sync-badge-ERROR { background: #fde9e9; color: #d93b3b; }
.sync-badge-PARTIAL { background: #fff4e5; color: #d98500; }

.sync-meta { display: flex; flex-wrap: wrap; gap: 18px 28px; }
.sync-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #4a5568;
}
.sync-meta-label { color: #8a94a6; font-size: 12px; }
.sync-meta-value { color: #2b3340; font-weight: 600; }

.sync-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  background: #eef1f5;
  color: #6a7a8c;
}
.sync-chip-tbd { background: #fff4e5; color: #c47700; }
.sync-chip-MATCH, .sync-chip-SUCCESS { background: #e6f7ec; color: #19974b; }
.sync-chip-MISMATCH, .sync-chip-PARTIAL { background: #fff4e5; color: #d98500; }
.sync-chip-NEW { background: #e6f0ff; color: #1e64d8; }
.sync-chip-DELETED { background: #fde9e9; color: #d93b3b; }
.sync-chip-ERROR { background: #fde9e9; color: #d93b3b; }
.sync-chip-ready { background: #eef1f5; color: #6a7a8c; }

.sync-panel-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

/* ── 필터칩 ── */
.table-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  margin-right: 12px;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #4a5568;
  cursor: pointer;
  input[type="checkbox"] { margin: 0; }
}

/* ── 설정 모달 ── */
.form-notice {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 10px 12px;
  margin-bottom: 14px;
  background: #fff8e6;
  border: 1px solid #ffe1a8;
  border-radius: 6px;
  font-size: 12px;
  color: #8a6100;
  line-height: 1.5;
}
.switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  input[type="checkbox"] { margin: 0; transform: scale(1.1); }
  span { font-size: 13px; color: #4a5568; }
}

/* ── 이력 요약 ── */
.sync-history-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.summary-chip {
  padding: 6px 12px;
  border-radius: 6px;
  background: #f0f1f3;
  color: #4a5568;
  font-size: 12px;
  strong { font-size: 14px; margin-right: 4px; color: #2b3340; }
}
.summary-chip-NEW { background: #e6f0ff; color: #1e64d8; strong { color: #1e64d8; } }
.summary-chip-MATCH { background: #e6f7ec; color: #19974b; strong { color: #19974b; } }
.summary-chip-MISMATCH { background: #fff4e5; color: #d98500; strong { color: #d98500; } }
.summary-chip-DELETED { background: #fde9e9; color: #d93b3b; strong { color: #d93b3b; } }

/* ── 배지 확장 ── */
.badge-NEW { background: #e6f0ff; color: #1e64d8; }
.badge-UPDATE { background: #fff4e5; color: #d98500; }
.badge-DELETE { background: #fde9e9; color: #d93b3b; }
.badge-default { background: #eef1f5; color: #6a7a8c; }

.modal-sub-title {
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
  margin-bottom: 6px;
}

/* ── 태블릿 대응 ── */
@media (max-width: 1279px) {
  .sync-panel { flex-direction: column; align-items: stretch; }
  .sync-panel-actions { justify-content: flex-end; }
  .sync-meta { gap: 8px 16px; }
}
</style>
