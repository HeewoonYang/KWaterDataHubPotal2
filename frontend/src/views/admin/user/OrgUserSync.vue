<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>조직/사용자 동기화</h2>
      <p class="page-desc">ERP 인사정보 시스템과 K-water 조직/사용자 데이터를 동기화합니다.</p>
    </div>

    <!-- 동기화 현황 카드 -->
    <div class="sync-summary-cards">
      <div class="summary-card">
        <div class="card-icon primary"><SyncOutlined /></div>
        <div class="card-body">
          <div class="card-label">최근 동기화</div>
          <div class="card-value">{{ lastSyncTime }}</div>
        </div>
        <div class="card-badge" :class="lastSyncStatus === '성공' ? 'success' : 'danger'">{{ lastSyncStatus }}</div>
      </div>
      <div class="summary-card">
        <div class="card-icon success"><TeamOutlined /></div>
        <div class="card-body">
          <div class="card-label">동기화 사용자</div>
          <div class="card-value">{{ syncStats.totalUsers }}명</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon warning"><ApartmentOutlined /></div>
        <div class="card-body">
          <div class="card-label">동기화 부서</div>
          <div class="card-value">{{ syncStats.totalDepts }}개</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon info"><ClockCircleOutlined /></div>
        <div class="card-body">
          <div class="card-label">자동 동기화</div>
          <div class="card-value">{{ autoSyncEnabled ? '매일 06:00' : '비활성' }}</div>
        </div>
      </div>
    </div>

    <!-- 동기화 설정 및 실행 -->
    <div class="sync-config-section">
      <div class="section-header">
        <span class="section-title"><SettingOutlined /> 동기화 설정</span>
      </div>
      <div class="config-grid">
        <div class="config-item">
          <label>ERP 연동 시스템</label>
          <div class="config-value">
            <span class="badge badge-success">연결됨</span>
            K-water ERP (SAP HR) - {{ erpEndpoint }}
          </div>
        </div>
        <div class="config-item">
          <label>동기화 범위</label>
          <div class="config-value">
            <label class="checkbox-label"><input type="checkbox" v-model="syncScope.org" /> 조직(부서) 정보</label>
            <label class="checkbox-label"><input type="checkbox" v-model="syncScope.user" /> 사용자(인사) 정보</label>
            <label class="checkbox-label"><input type="checkbox" v-model="syncScope.position" /> 직급/직위 정보</label>
          </div>
        </div>
        <div class="config-item">
          <label>자동 동기화</label>
          <div class="config-value">
            <label class="checkbox-label"><input type="checkbox" v-model="autoSyncEnabled" /> 사용</label>
            <template v-if="autoSyncEnabled">
              <select v-model="autoSyncSchedule" class="inline-select">
                <option value="daily_06">매일 06:00</option>
                <option value="daily_00">매일 00:00</option>
                <option value="hourly">매 1시간</option>
                <option value="weekly">매주 월요일 06:00</option>
              </select>
            </template>
          </div>
        </div>
        <div class="config-item">
          <label>충돌 처리 정책</label>
          <div class="config-value">
            <select v-model="conflictPolicy" class="inline-select">
              <option value="erp_priority">ERP 우선 (ERP 데이터로 덮어쓰기)</option>
              <option value="hub_priority">허브 우선 (허브 데이터 유지)</option>
              <option value="manual">수동 확인 (충돌 건 별도 검토)</option>
            </select>
          </div>
        </div>
      </div>
      <div class="config-actions">
        <button class="btn btn-primary" :disabled="syncing" @click="runSync">
          <SyncOutlined :spin="syncing" /> {{ syncing ? '동기화 중...' : '수동 동기화 실행' }}
        </button>
        <button class="btn btn-outline" @click="runDryRun">
          <EyeOutlined /> 사전 점검 (Dry Run)
        </button>
        <button class="btn btn-outline" @click="saveConfig">
          <SaveOutlined /> 설정 저장
        </button>
      </div>
    </div>

    <!-- 동기화 이력 -->
    <div class="table-section">
      <div class="table-header">
        <span class="section-title"><HistoryOutlined /> 동기화 이력</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(historyColDefs, historyData, '동기화이력')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="historyData" :columnDefs="historyColDefs" :defaultColDef="defaultColDef" :tooltipShowDelay="0" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onHistoryClick" />
      </div>
    </div>

    <!-- 동기화 상세 결과 팝업 -->
    <AdminModal :visible="showSyncDetail" :title="'동기화 상세 - ' + syncDetailData.syncTime" size="lg" @close="showSyncDetail = false">
      <div class="modal-stats">
        <div class="modal-stat-card success"><div class="stat-title">신규 추가</div><div class="stat-number">{{ syncDetailData.added }}</div></div>
        <div class="modal-stat-card primary"><div class="stat-title">정보 변경</div><div class="stat-number">{{ syncDetailData.updated }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">퇴직/비활성</div><div class="stat-number">{{ syncDetailData.deactivated }}</div></div>
        <div class="modal-stat-card danger"><div class="stat-title">오류</div><div class="stat-number">{{ syncDetailData.errors }}</div></div>
      </div>
      <div class="modal-section" v-if="syncDetailData.changes?.length">
        <div class="modal-section-title">변경 상세 내역</div>
        <table class="modal-table">
          <thead><tr><th>구분</th><th>사번</th><th>이름</th><th>변경 항목</th><th>변경 전</th><th>변경 후</th></tr></thead>
          <tbody>
            <tr v-for="(ch, idx) in syncDetailData.changes" :key="idx">
              <td><span class="badge" :class="ch.type === '신규' ? 'badge-success' : ch.type === '변경' ? 'badge-primary' : 'badge-warning'">{{ ch.type }}</span></td>
              <td>{{ ch.empNo }}</td>
              <td>{{ ch.name }}</td>
              <td>{{ ch.field }}</td>
              <td>{{ ch.before || '-' }}</td>
              <td>{{ ch.after }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showSyncDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import {
  SyncOutlined, TeamOutlined, ApartmentOutlined, ClockCircleOutlined,
  SettingOutlined, EyeOutlined, SaveOutlined, HistoryOutlined, FileExcelOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

// ── 동기화 현황 ──
const lastSyncTime = ref('2026-03-27 06:00:12')
const lastSyncStatus = ref('성공')
const syncStats = ref({ totalUsers: 1245, totalDepts: 48 })

// ── 설정 ──
const erpEndpoint = ref('https://erp.kwater.or.kr/api/hr')
const autoSyncEnabled = ref(true)
const autoSyncSchedule = ref('daily_06')
const conflictPolicy = ref('erp_priority')
const syncScope = ref({ org: true, user: true, position: true })
const syncing = ref(false)

// ── 동기화 실행 ──
async function runSync() {
  syncing.value = true
  try {
    const res = await adminUserApi.runOrgSync(false)
    lastSyncTime.value = new Date().toISOString().replace('T', ' ').substring(0, 19)
    lastSyncStatus.value = '성공'
    const d = res.data?.data || {}
    message.success(`동기화 완료: 신규 ${d.added || 0}건, 변경 ${d.updated || 0}건, 비활성 ${d.deactivated || 0}건`)
  } catch {
    lastSyncStatus.value = '실패'
    message.error('동기화 실행 중 오류가 발생했습니다.')
  } finally {
    syncing.value = false
  }
}

async function runDryRun() {
  try {
    const res = await adminUserApi.runOrgSync(true)
    const dd = res.data?.data || {}
    message.info(`사전 점검 완료: 신규 ${dd.added || 0}건, 변경 ${dd.updated || 0}건, 비활성 ${dd.deactivated || 0}건 예상`)
  } catch {
    message.error('사전 점검 중 오류가 발생했습니다.')
  }
}

function saveConfig() {
  message.success('동기화 설정이 저장되었습니다.')
}

// ── 동기화 이력 그리드 ──
const defaultColDef = { ...baseDefaultColDef }
const historyColDefs = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '동기화 일시', field: 'syncTime', flex: 1.5, minWidth: 140 },
  { headerName: '실행 유형', field: 'triggerType', flex: 0.8, minWidth: 80 },
  { headerName: '범위', field: 'scope', flex: 1, minWidth: 90 },
  { headerName: '신규', field: 'added', flex: 0.5, minWidth: 50, cellStyle: { color: '#52c41a', fontWeight: 600 } },
  { headerName: '변경', field: 'updated', flex: 0.5, minWidth: 50, cellStyle: { color: '#1890ff', fontWeight: 600 } },
  { headerName: '비활성', field: 'deactivated', flex: 0.6, minWidth: 55, cellStyle: { color: '#faad14', fontWeight: 600 } },
  { headerName: '오류', field: 'errors', flex: 0.5, minWidth: 50, cellStyle: { color: '#ff4d4f', fontWeight: 600 } },
  { headerName: '소요시간', field: 'duration', flex: 0.7, minWidth: 65 },
  { headerName: '결과', field: 'status', flex: 0.6, minWidth: 55 },
  { headerName: '실행자', field: 'executor', flex: 0.7, minWidth: 60 },
])

const historyData = ref([
  { syncTime: '2026-03-27 06:00:12', triggerType: '자동', scope: '조직+사용자', added: 2, updated: 8, deactivated: 1, errors: 0, duration: '12초', status: '성공', executor: 'SYSTEM' },
  { syncTime: '2026-03-26 06:00:08', triggerType: '자동', scope: '조직+사용자', added: 0, updated: 3, deactivated: 0, errors: 0, duration: '10초', status: '성공', executor: 'SYSTEM' },
  { syncTime: '2026-03-25 14:22:45', triggerType: '수동', scope: '사용자', added: 5, updated: 15, deactivated: 2, errors: 1, duration: '18초', status: '부분성공', executor: '관리자' },
  { syncTime: '2026-03-25 06:00:10', triggerType: '자동', scope: '조직+사용자', added: 1, updated: 6, deactivated: 0, errors: 0, duration: '11초', status: '성공', executor: 'SYSTEM' },
  { syncTime: '2026-03-24 06:00:15', triggerType: '자동', scope: '조직+사용자', added: 0, updated: 2, deactivated: 0, errors: 0, duration: '9초', status: '성공', executor: 'SYSTEM' },
  { syncTime: '2026-03-23 06:00:09', triggerType: '자동', scope: '조직+사용자', added: 3, updated: 11, deactivated: 1, errors: 0, duration: '14초', status: '성공', executor: 'SYSTEM' },
  { syncTime: '2026-03-22 10:15:33', triggerType: '수동', scope: '조직', added: 2, updated: 4, deactivated: 0, errors: 0, duration: '5초', status: '성공', executor: '관리자' },
  { syncTime: '2026-03-21 06:00:11', triggerType: '자동', scope: '조직+사용자', added: 0, updated: 1, deactivated: 0, errors: 0, duration: '8초', status: '성공', executor: 'SYSTEM' },
])

// ── 상세 팝업 ──
const showSyncDetail = ref(false)
const syncDetailData = ref<any>({})

function onHistoryClick(event: any) {
  const row = event.data
  syncDetailData.value = {
    syncTime: row.syncTime,
    added: row.added,
    updated: row.updated,
    deactivated: row.deactivated,
    errors: row.errors,
    changes: [
      { type: '신규', empNo: '20260015', name: '김신입', field: '계정 생성', before: '', after: 'ACTIVE' },
      { type: '신규', empNo: '20260016', name: '박신입', field: '계정 생성', before: '', after: 'ACTIVE' },
      { type: '변경', empNo: '20220032', name: '홍길동', field: '부서', before: '수도부', after: '수자원부' },
      { type: '변경', empNo: '20210015', name: '김매니저', field: '직급', before: '대리', after: '과장' },
      { type: '변경', empNo: '20220048', name: '이영희', field: '이메일', before: 'lee_old@kwater.or.kr', after: 'lee@kwater.or.kr' },
      { type: '비활성', empNo: '20180042', name: '최퇴직', field: '계정 상태', before: 'ACTIVE', after: 'WITHDRAWN' },
    ],
  }
  showSyncDetail.value = true
}
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';

.sync-summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  position: relative;

  .card-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    &.primary { background: #e6f7ff; color: #1890ff; }
    &.success { background: #f6ffed; color: #52c41a; }
    &.warning { background: #fffbe6; color: #faad14; }
    &.info { background: #f0f5ff; color: #2f54eb; }
  }

  .card-body {
    .card-label { font-size: 12px; color: #999; }
    .card-value { font-size: 18px; font-weight: 700; color: #333; }
  }

  .card-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 600;
    &.success { background: #f6ffed; color: #52c41a; }
    &.danger { background: #fff2f0; color: #ff4d4f; }
  }
}

.sync-config-section {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;

  .section-header {
    margin-bottom: 16px;
    .section-title { font-weight: 600; font-size: 15px; display: flex; align-items: center; gap: 6px; }
  }
}

.config-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.config-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  > label {
    width: 130px;
    min-width: 130px;
    font-weight: 600;
    font-size: 13px;
    color: #555;
    padding-top: 4px;
  }
  .config-value {
    flex: 1;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    font-size: 13px;
  }
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  cursor: pointer;
  input[type="checkbox"] { accent-color: #1890ff; }
}

.inline-select {
  padding: 4px 8px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 13px;
}

.config-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.section-title {
  font-weight: 600;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge-primary { background: #e6f7ff; color: #1890ff; }
.badge-danger { background: #fff2f0; color: #ff4d4f; }

:deep(.ag-row) { cursor: pointer; }

@media (max-width: 1279px) {
  .sync-summary-cards { grid-template-columns: repeat(2, 1fr); }
  .config-item {
    flex-direction: column;
    gap: 6px;
    > label { width: auto; }
  }
}
</style>
