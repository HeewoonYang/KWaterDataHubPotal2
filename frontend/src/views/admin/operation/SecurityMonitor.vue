<template>
  <div class="admin-page">
    <div class="page-header"><h2>보안 모니터링</h2><p class="page-desc">비정상 접근 탐지, 로그인 실패, 계정 잠금 현황 및 로그 보관정책을 관리합니다.</p></div>

    <!-- 보안 점수 카드 -->
    <div class="stats-row">
      <div class="stat-card"><div class="stat-value" :style="{ color: data.security_score >= 90 ? '#28A745' : data.security_score >= 80 ? '#fa8c16' : '#DC3545' }">{{ data.security_score }}</div><div class="stat-label">보안 점수</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#DC3545">{{ data.denied_today }}</div><div class="stat-label">오늘 접근 거부</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#fa8c16">{{ data.login_fail_today }}</div><div class="stat-label">오늘 로그인 실패</div></div>
      <div class="stat-card"><div class="stat-value" style="color:#DC3545">{{ data.locked_accounts }}</div><div class="stat-label">잠긴 계정</div></div>
    </div>

    <!-- 트렌드 + 누적 -->
    <div class="grid-2">
      <div class="card"><div class="card-title">7일 보안 이벤트 트렌드</div>
        <table class="data-table"><thead><tr><th>날짜</th><th>접근 거부</th></tr></thead>
          <tbody><tr v-for="t in data.trend || []" :key="t.date"><td>{{ t.date }}</td><td :style="{ color: t.denied > 0 ? '#DC3545' : '#28A745', fontWeight: 600 }">{{ t.denied }}</td></tr></tbody>
        </table>
      </div>
      <div class="card"><div class="card-title">7일 누적</div>
        <div class="summary-grid">
          <div class="summary-item"><span class="s-label">접근 거부</span><span class="s-value" style="color:#DC3545">{{ data.denied_7d }}</span></div>
          <div class="summary-item"><span class="s-label">로그인 실패</span><span class="s-value" style="color:#fa8c16">{{ data.login_fail_7d }}</span></div>
          <div class="summary-item"><span class="s-label">잠긴 계정</span><span class="s-value" style="color:#DC3545">{{ data.locked_accounts }}</span></div>
        </div>
      </div>
    </div>

    <!-- 로그 보관정책 관리 -->
    <div class="card" style="margin-top:16px">
      <div class="card-title-row">
        <span class="card-title">로그 보관정책 관리</span>
        <span class="card-desc">보관기한이 만료된 로그를 조회하고 정리할 수 있습니다.</span>
      </div>
      <table class="data-table retention-table">
        <thead>
          <tr>
            <th>로그 유형</th>
            <th>설명</th>
            <th>보관기한 (일)</th>
            <th>전체 건수</th>
            <th>만료 건수</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in retention.policies || []" :key="p.log_type">
            <td class="log-type-cell">
              <DatabaseOutlined v-if="p.log_type === 'ACCESS_LOG'" />
              <LoginOutlined v-else-if="p.log_type === 'LOGIN_HISTORY'" />
              <SearchOutlined v-else-if="p.log_type === 'AI_QUERY_LOG'" />
              <HistoryOutlined v-else />
              <span>{{ p.log_type_name }}</span>
            </td>
            <td class="desc-cell">{{ p.description }}</td>
            <td>
              <div class="retention-edit">
                <input
                  v-if="editingType === p.log_type"
                  v-model.number="editDays"
                  type="number"
                  min="30"
                  class="retention-input"
                  @keyup.enter="saveRetention(p.log_type)"
                  @keyup.escape="editingType = ''"
                />
                <span v-else class="retention-days">{{ p.retention_days }}일</span>
                <button v-if="editingType === p.log_type" class="btn-sm btn-primary" @click="saveRetention(p.log_type)">저장</button>
                <button v-if="editingType === p.log_type" class="btn-sm btn-default" @click="editingType = ''">취소</button>
                <button v-else class="btn-sm btn-default" @click="startEdit(p)">
                  <EditOutlined /> 변경
                </button>
              </div>
            </td>
            <td class="num-cell">{{ (p.total_count || 0).toLocaleString() }}</td>
            <td class="num-cell">
              <span :style="{ color: p.expired_count > 0 ? '#DC3545' : '#28A745', fontWeight: 600 }">
                {{ (p.expired_count || 0).toLocaleString() }}
              </span>
            </td>
            <td>
              <button
                class="btn-sm btn-danger"
                :disabled="!p.expired_count || p.expired_count === 0 || cleaningType === p.log_type"
                @click="cleanupLogs(p)"
              >
                <DeleteOutlined />
                {{ cleaningType === p.log_type ? '삭제 중...' : '만료 로그 삭제' }}
              </button>
            </td>
          </tr>
          <tr v-if="!retention.policies || retention.policies.length === 0">
            <td colspan="6" style="text-align:center;color:#999;padding:20px">로그 보관정책을 불러오는 중...</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminOperationApi } from '../../../api/admin.api'
import {
  DatabaseOutlined, LoginOutlined, SearchOutlined, HistoryOutlined,
  EditOutlined, DeleteOutlined,
} from '@ant-design/icons-vue'

// 보안 대시보드
const data = ref<any>({ security_score: 0, denied_today: 0, login_fail_today: 0, locked_accounts: 0, denied_7d: 0, login_fail_7d: 0, trend: [] })

// 로그 보관정책
const retention = ref<any>({ policies: [] })
const editingType = ref('')
const editDays = ref(365)
const cleaningType = ref('')

async function loadSecurityDashboard() {
  try {
    const r = await adminOperationApi.securityDashboard()
    if (r.data?.data) data.value = r.data.data
  } catch {}
}

async function loadRetention() {
  try {
    const r = await adminOperationApi.logRetention()
    if (r.data?.data) retention.value = r.data.data
  } catch {}
}

function startEdit(policy: any) {
  editingType.value = policy.log_type
  editDays.value = policy.retention_days
}

async function saveRetention(logType: string) {
  if (editDays.value < 30) {
    alert('보관기한은 최소 30일 이상이어야 합니다.')
    return
  }
  try {
    await adminOperationApi.updateLogRetention(logType, editDays.value)
    editingType.value = ''
    await loadRetention()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '보관기한 변경 실패')
  }
}

async function cleanupLogs(policy: any) {
  if (!confirm(`[${policy.log_type_name}] 만료 로그 ${(policy.expired_count || 0).toLocaleString()}건을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) return
  cleaningType.value = policy.log_type
  try {
    const r = await adminOperationApi.cleanupLogs(policy.log_type)
    alert(r.data?.message || '삭제 완료')
    await loadRetention()
  } catch (e: any) {
    alert(e?.response?.data?.detail || '로그 삭제 실패')
  } finally {
    cleaningType.value = ''
  }
}

onMounted(() => {
  loadSecurityDashboard()
  loadRetention()
})
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center;
  .stat-value { font-size: 28px; font-weight: 800; }
  .stat-label { font-size: 12px; color: #999; }
}
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px;
  .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; }
}
.card-title-row { display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px;
  .card-title { font-weight: 700; font-size: 14px; }
  .card-desc { font-size: 12px; color: #999; }
}
.data-table { width: 100%; font-size: 12px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; }
}
.summary-grid { display: flex; flex-direction: column; gap: 12px; padding: 10px 0; }
.summary-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f5f5f5;
  .s-label { font-size: 13px; color: #666; }
  .s-value { font-size: 20px; font-weight: 800; }
}

/* 로그 보관정책 */
.retention-table {
  th:nth-child(3), th:nth-child(4), th:nth-child(5) { text-align: center; }
  td.num-cell { text-align: center; font-variant-numeric: tabular-nums; }
  td.desc-cell { color: #666; max-width: 280px; }
  td.log-type-cell { display: flex; align-items: center; gap: 6px; font-weight: 600; color: #333; }
}
.retention-edit { display: flex; align-items: center; gap: 6px; justify-content: center; }
.retention-input { width: 70px; padding: 3px 6px; border: 1px solid #1890ff; border-radius: 4px; text-align: center; font-size: 12px;
  &:focus { outline: none; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
}
.retention-days { font-weight: 600; color: #1890ff; }

.btn-sm { padding: 3px 8px; font-size: 11px; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer; background: #fff; display: inline-flex; align-items: center; gap: 3px; white-space: nowrap;
  &:hover { border-color: #1890ff; color: #1890ff; }
  &:disabled { opacity: 0.4; cursor: not-allowed; &:hover { border-color: #d9d9d9; color: inherit; } }
}
.btn-primary { background: #1890ff; color: #fff; border-color: #1890ff; &:hover { background: #40a9ff; color: #fff; } }
.btn-danger { color: #DC3545; border-color: #DC3545; &:hover { background: #DC3545; color: #fff; } &:disabled:hover { background: #fff; color: #DC3545; } }
.btn-default { &:hover { border-color: #1890ff; color: #1890ff; } }

@media (max-width: 1279px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .grid-2 { grid-template-columns: 1fr; }
}
</style>
