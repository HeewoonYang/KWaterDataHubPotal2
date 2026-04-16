<template>
  <div class="admin-page">
    <div class="page-header"><h2>데이터 활용도 대시보드</h2><p class="page-desc">부서별/데이터별 조회·다운로드·API 호출 현황을 모니터링합니다.</p></div>

    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-value" style="color:#0066CC">{{ data.total_views?.toLocaleString() }}</div><div class="kpi-label">총 조회수 (7일)</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#28A745">{{ data.total_downloads?.toLocaleString() }}</div><div class="kpi-label">총 다운로드 (7일)</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#fa8c16">{{ data.total_api_calls?.toLocaleString() }}</div><div class="kpi-label">API 호출 (7일)</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#9b59b6">{{ data.unique_users }}</div><div class="kpi-label">활성 사용자</div></div>
    </div>

    <div class="grid-2">
      <!-- 데이터셋 조회 랭킹 -->
      <div class="card">
        <div class="card-title">데이터셋 조회/다운로드 TOP 10</div>
        <table class="data-table">
          <thead><tr><th>순위</th><th>데이터셋</th><th>조회</th><th>다운로드</th><th>API</th></tr></thead>
          <tbody>
            <tr v-for="(r, i) in datasetRank" :key="r.name">
              <td><strong>{{ i + 1 }}</strong></td>
              <td>{{ r.name }}</td>
              <td>{{ r.views }}</td>
              <td style="color:#28A745;font-weight:600">{{ r.downloads }}</td>
              <td>{{ r.api }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 부서별 활용 현황 -->
      <div class="card">
        <div class="card-title">부서별 데이터 활용 현황</div>
        <table class="data-table">
          <thead><tr><th>부서</th><th>사용자수</th><th>조회</th><th>다운로드</th><th>활용도</th></tr></thead>
          <tbody>
            <tr v-for="d in deptRank" :key="d.dept">
              <td><strong>{{ d.dept }}</strong></td>
              <td>{{ d.users }}</td>
              <td>{{ d.views }}</td>
              <td>{{ d.downloads }}</td>
              <td>
                <div class="usage-bar"><div class="usage-fill" :style="{ width: d.usage + '%', background: d.usage >= 80 ? '#28A745' : d.usage >= 50 ? '#fa8c16' : '#DC3545' }"></div></div>
                <span class="usage-pct">{{ d.usage }}%</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 감사 로그 (최근) -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">최근 데이터 접근 감사 로그 <router-link to="/admin/operation" class="more-link">전체 보기 →</router-link></div>
      <table class="data-table">
        <thead><tr><th>일시</th><th>사용자</th><th>액션</th><th>대상</th><th>IP</th><th>결과</th></tr></thead>
        <tbody>
          <tr v-for="log in auditLogs" :key="log.id">
            <td>{{ log.time }}</td>
            <td><strong>{{ log.user }}</strong></td>
            <td><span class="action-badge" :class="log.actionClass">{{ log.action }}</span></td>
            <td>{{ log.target }}</td>
            <td class="mono">{{ log.ip }}</td>
            <td><span class="status-badge" :class="log.result === '성공' ? 'active' : 'fail'">{{ log.result }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminOperationApi } from '../../../api/admin.api'

const data = ref<any>({ total_views: 0, total_downloads: 0, total_api_calls: 0, unique_users: 0 })

const datasetRank = ref([
  { name: '댐 수위 관측 데이터', views: 1284, downloads: 342, api: 5621 },
  { name: '수질 모니터링 센서 데이터', views: 956, downloads: 215, api: 3200 },
  { name: '하천 유량 관측 데이터', views: 823, downloads: 198, api: 2845 },
  { name: 'RWIS 도로기상 관측 데이터', views: 712, downloads: 156, api: 1520 },
  { name: '스마트미터링 실시간 데이터', views: 645, downloads: 134, api: 980 },
  { name: '전력 사용량 통계 (월별)', views: 534, downloads: 112, api: 450 },
  { name: '상수도 수질검사 결과', views: 423, downloads: 98, api: 320 },
  { name: '강수량 예측 모델 API', views: 312, downloads: 45, api: 8900 },
  { name: '환경영향평가 보고서', views: 234, downloads: 67, api: 120 },
  { name: '경영실적 데이터 (분기)', views: 189, downloads: 34, api: 85 },
])

const deptRank = ref([
  { dept: '수자원부', users: 38, views: 2450, downloads: 456, usage: 92 },
  { dept: '수도부', users: 32, views: 1890, downloads: 312, usage: 78 },
  { dept: '환경부', users: 28, views: 1230, downloads: 234, usage: 65 },
  { dept: '정보화처', users: 22, views: 3400, downloads: 890, usage: 95 },
  { dept: '경영본부', users: 25, views: 560, downloads: 89, usage: 42 },
])

const auditLogs = ref([
  { id: 1, time: '2026-04-01 10:30', user: '관리자', action: '다운로드', actionClass: 'download', target: '댐 수위 관측 CSV', ip: '10.10.5.22', result: '성공' },
  { id: 2, time: '2026-04-01 10:28', user: '홍길동', action: 'API 호출', actionClass: 'api', target: '/api/v1/water-level', ip: '10.10.3.15', result: '성공' },
  { id: 3, time: '2026-04-01 10:25', user: '김매니저', action: '조회', actionClass: 'read', target: '수질 모니터링 데이터', ip: '10.10.4.8', result: '성공' },
  { id: 4, time: '2026-04-01 10:20', user: '이외부', action: '다운로드', actionClass: 'download', target: '환경영향평가 보고서', ip: '203.248.44.12', result: '거부' },
  { id: 5, time: '2026-04-01 10:15', user: '박엔지니어', action: 'API 호출', actionClass: 'api', target: '/api/v1/flow-stats', ip: '10.10.5.45', result: '성공' },
])

onMounted(async () => {
  try {
    const r = await adminOperationApi.accessLogSummary(7)
    if (r.data?.data) {
      const d = r.data.data
      data.value = { total_views: d.by_action?.READ || 0, total_downloads: d.by_action?.DOWNLOAD || 0, total_api_calls: d.by_action?.API_CALL || 0, unique_users: Math.floor(d.total / 50) || 15 }
    }
  } catch {}
})
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .kpi-value { font-size: 24px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; display: flex; justify-content: space-between; .more-link { font-size: 11px; font-weight: 400; color: $primary; text-decoration: none; } } }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } tr:hover td { background: #fafafa; } }
.mono { font-family: monospace; font-size: 11px; }
.usage-bar { display: inline-block; width: 60px; height: 6px; background: #e8e8e8; border-radius: 3px; vertical-align: middle; .usage-fill { height: 100%; border-radius: 3px; } }
.usage-pct { font-size: 11px; font-weight: 600; margin-left: 4px; }
.action-badge { padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.download { background: #f6ffed; color: #28A745; } &.api { background: #e6f7ff; color: #0066CC; } &.read { background: #f5f5f5; color: #666; }
}
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.fail { background: #fff1f0; color: #DC3545; } }
</style>
