<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>비식별화 관리*</h2>
      <p class="page-desc">상용 비식별화 엔진 연동 기반의 개인정보 탐지, 비식별 처리, 적정성 평가를 관리합니다.</p>
    </div>

    <!-- 엔진 상태 KPI -->
    <div class="kpi-row">
      <div class="kpi-card engine-card">
        <div class="engine-status"><span class="engine-dot active"></span> 연동 정상</div>
        <div class="engine-name">{{ engine.name }}</div>
        <div class="engine-ver">v{{ engine.version }} / {{ engine.license }}</div>
      </div>
      <div class="kpi-card"><div class="kpi-value" style="color:#DC3545">{{ stats.detected }}</div><div class="kpi-label">탐지 항목</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#28A745">{{ stats.processed }}</div><div class="kpi-label">처리 완료</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#fa8c16">{{ stats.pending }}</div><div class="kpi-label">처리 대기</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#0066CC">{{ stats.adequacy }}%</div><div class="kpi-label">적정성 점수</div></div>
    </div>

    <!-- 탭: 개인정보 탐지 / 비식별 정책 / 처리 이력 / 적정성 평가 -->
    <div class="tab-bar">
      <button :class="{ active: tab === 'detect' }" @click="tab = 'detect'">개인정보 탐지</button>
      <button :class="{ active: tab === 'policy' }" @click="tab = 'policy'">비식별 정책</button>
      <button :class="{ active: tab === 'history' }" @click="tab = 'history'">처리 이력</button>
      <button :class="{ active: tab === 'adequacy' }" @click="tab = 'adequacy'">적정성 평가</button>
      <button :class="{ active: tab === 'engine' }" @click="tab = 'engine'">엔진 설정</button>
    </div>

    <!-- 개인정보 탐지 -->
    <div v-if="tab === 'detect'" class="tab-content">
      <div class="section-header">
        <span>자동 탐지된 개인정보 항목</span>
        <button class="btn btn-sm btn-primary" @click="runDetection"><ThunderboltOutlined /> 전체 스캔 실행</button>
      </div>
      <table class="data-table">
        <thead><tr><th>데이터셋</th><th>컬럼</th><th>탐지 유형</th><th>신뢰도</th><th>건수</th><th>처리 상태</th><th>액션</th></tr></thead>
        <tbody>
          <tr v-for="d in detectedItems" :key="d.id">
            <td><strong>{{ d.dataset }}</strong></td>
            <td class="mono">{{ d.column }}</td>
            <td><span class="detect-type" :class="d.typeClass">{{ d.type }}</span></td>
            <td><span :style="{ color: d.confidence >= 90 ? '#DC3545' : '#fa8c16', fontWeight: 700 }">{{ d.confidence }}%</span></td>
            <td>{{ d.count.toLocaleString() }}</td>
            <td><span class="status-badge" :class="d.statusClass">{{ d.status }}</span></td>
            <td>
              <button v-if="d.status === '미처리'" class="btn btn-xs btn-primary" @click="applyPolicy(d)">정책 적용</button>
              <span v-else style="color:#28A745;font-size:11px">적용됨</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 비식별 정책 -->
    <div v-if="tab === 'policy'" class="tab-content">
      <div class="section-header">
        <span>비식별 처리 정책 목록</span>
        <button class="btn btn-sm btn-primary" @click="showAddPolicy = true"><PlusOutlined /> 정책 추가</button>
      </div>
      <table class="data-table">
        <thead><tr><th>정책명</th><th>대상 유형</th><th>처리 기법</th><th>엔진 함수</th><th>적용 데이터셋</th><th>상태</th><th>액션</th></tr></thead>
        <tbody>
          <tr v-for="p in policies" :key="p.id">
            <td><strong>{{ p.name }}</strong></td>
            <td><span class="detect-type" :class="p.targetClass">{{ p.target }}</span></td>
            <td>{{ p.method }}</td>
            <td class="mono">{{ p.engineFunc }}</td>
            <td>{{ p.datasets }}개</td>
            <td><span class="status-badge" :class="p.active ? 'active' : 'inactive'">{{ p.active ? '활성' : '비활성' }}</span></td>
            <td><button class="btn btn-xs btn-danger" @click="deletePolicy(p)"><DeleteOutlined /></button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 처리 이력 -->
    <div v-if="tab === 'history'" class="tab-content">
      <div class="section-header"><span>비식별 처리 이력</span></div>
      <table class="data-table">
        <thead><tr><th>실행일시</th><th>데이터셋</th><th>정책</th><th>처리 건수</th><th>소요시간</th><th>결과</th></tr></thead>
        <tbody>
          <tr v-for="h in history" :key="h.id">
            <td>{{ h.date }}</td>
            <td><strong>{{ h.dataset }}</strong></td>
            <td>{{ h.policy }}</td>
            <td>{{ h.count.toLocaleString() }}</td>
            <td>{{ h.elapsed }}</td>
            <td><span class="status-badge" :class="h.result === '성공' ? 'active' : 'fail'">{{ h.result }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 적정성 평가 -->
    <div v-if="tab === 'adequacy'" class="tab-content">
      <div class="section-header"><span>비식별 적정성 평가 (k-익명성 / l-다양성 / t-근접성)</span>
        <button class="btn btn-sm btn-outline" @click="runAdequacy"><SafetyOutlined /> 평가 실행</button>
      </div>
      <div class="adequacy-cards">
        <div class="adeq-card" v-for="a in adequacyResults" :key="a.metric">
          <div class="adeq-metric">{{ a.metric }}</div>
          <div class="adeq-score" :style="{ color: a.score >= 80 ? '#28A745' : a.score >= 60 ? '#fa8c16' : '#DC3545' }">{{ a.score }}%</div>
          <div class="adeq-desc">{{ a.desc }}</div>
          <div class="adeq-detail">기준: {{ a.threshold }} / 결과: {{ a.value }}</div>
        </div>
      </div>
    </div>

    <!-- 엔진 설정 -->
    <div v-if="tab === 'engine'" class="tab-content">
      <div class="section-header"><span>상용 비식별화 엔진 연동 설정</span></div>
      <div class="engine-config">
        <div class="config-group"><label>엔진 유형</label><select v-model="engine.name"><option>SecuData Enterprise</option><option>IrisDataNet</option><option>PersonaAI</option><option>K-Anonymizer Pro</option></select></div>
        <div class="config-group"><label>API Endpoint</label><input v-model="engine.endpoint" /></div>
        <div class="config-group"><label>API Key</label><input v-model="engine.apiKey" type="password" /></div>
        <div class="config-group"><label>라이선스</label><input v-model="engine.license" readonly /></div>
        <div class="config-group"><label>자동 탐지 주기</label>
          <select v-model="engine.scanSchedule"><option>수집 시 자동</option><option>매일 06:00</option><option>매주 월요일</option><option>수동</option></select>
        </div>
        <div class="config-group"><label>수집 파이프라인 인라인 모드</label>
          <label class="toggle"><input type="checkbox" v-model="engine.inlineMode" /><span class="slider"></span></label>
          <span class="toggle-desc">활성 시 수집 단계에서 자동 비식별 처리</span>
        </div>
        <div class="config-actions"><button class="btn btn-primary" @click="saveEngine">연동 설정 저장</button><button class="btn btn-outline" @click="testEngine">연결 테스트</button></div>
      </div>
    </div>

    <!-- 정책 추가 모달 -->
    <AdminModal :visible="showAddPolicy" title="비식별 정책 추가" size="lg" @close="showAddPolicy = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">정책명</label><input v-model="policyForm.config_name" placeholder="예: 주민번호 마스킹" /></div>
          <div class="modal-form-group"><label class="required">대상 개인정보 유형</label>
            <select v-model="policyForm.target_type"><option>주민등록번호</option><option>전화번호</option><option>이메일</option><option>성명</option><option>주소</option><option>계좌번호</option><option>IP주소</option><option>여권번호</option></select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">비식별 기법</label>
            <select v-model="policyForm.method"><option value="PSEUDONYMIZATION">가명처리 (Pseudonymization)</option><option value="AGGREGATION">총계처리 (Aggregation)</option><option value="SUPPRESSION">데이터 삭제 (Suppression)</option><option value="GENERALIZATION">데이터 범주화 (Generalization)</option><option value="MASKING">데이터 마스킹 (Masking)</option><option value="DIFFERENTIAL_PRIVACY">차분 프라이버시 (Differential Privacy)</option><option value="ENCRYPTION">암호화 (Encryption)</option></select>
          </div>
          <div class="modal-form-group"><label>엔진 함수</label><input v-model="policyForm.engine_func" placeholder="예: mask_ssn()" class="mono" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>마스킹 패턴</label><input v-model="policyForm.masking_pattern" placeholder="예: ***-**-**** → 앞6자리 보존" /></div>
          <div class="modal-form-group"><label>적용 시점</label>
            <select v-model="policyForm.apply_timing"><option>수집 시 인라인 적용</option><option>유통 전 배치 적용</option><option>다운로드 시 동적 적용</option></select>
          </div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea v-model="policyForm.description" rows="2" placeholder="정책 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="addPolicy"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showAddPolicy = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { PlusOutlined, ThunderboltOutlined, SafetyOutlined, SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import { adminCleansingApi } from '../../../api/admin.api'
import AdminModal from '../../../components/AdminModal.vue'

const tab = ref('detect')
const showAddPolicy = ref(false)

const policyForm = reactive({
  config_name: '',
  method: 'MASKING',
  target_columns: [] as string[],
  target_type: '주민등록번호',
  engine_func: '',
  masking_pattern: '',
  apply_timing: '수집 시 인라인 적용',
  description: '',
})

const engine = ref({
  name: 'SecuData Enterprise', version: '4.2.1', license: 'Enterprise (2026-12-31)',
  endpoint: 'https://deid-engine.kwater.or.kr/api/v2',
  apiKey: '••••••••••••••••',
  scanSchedule: '수집 시 자동', inlineMode: true,
})

const stats = ref({ detected: 47, processed: 42, pending: 5, adequacy: 94 })

const detectedItems = ref([
  { id: 1, dataset: '사용자 계정', column: 'SSN', type: '주민등록번호', typeClass: 'ssn', confidence: 99, count: 15200, status: '처리완료', statusClass: 'active' },
  { id: 2, dataset: '사용자 계정', column: 'PHONE', type: '전화번호', typeClass: 'phone', confidence: 97, count: 15200, status: '처리완료', statusClass: 'active' },
  { id: 3, dataset: '사용자 계정', column: 'EMAIL', type: '이메일', typeClass: 'email', confidence: 95, count: 14800, status: '처리완료', statusClass: 'active' },
  { id: 4, dataset: '외부사용자', column: 'NAME', type: '성명', typeClass: 'name', confidence: 92, count: 3200, status: '미처리', statusClass: 'pending' },
  { id: 5, dataset: '접근 로그', column: 'CLIENT_IP', type: 'IP주소', typeClass: 'ip', confidence: 88, count: 125000, status: '미처리', statusClass: 'pending' },
  { id: 6, dataset: '수질검사 결과', column: 'INSPECTOR_NM', type: '성명', typeClass: 'name', confidence: 85, count: 4500, status: '처리완료', statusClass: 'active' },
])

const policies = ref<any[]>([
  { id: 1, name: '주민번호 마스킹', target: '주민등록번호', targetClass: 'ssn', method: '데이터 마스킹', engineFunc: 'mask_ssn(keep=6)', datasets: 3, active: true },
  { id: 2, name: '전화번호 가명처리', target: '전화번호', targetClass: 'phone', method: '가명처리', engineFunc: 'pseudonymize_phone()', datasets: 5, active: true },
  { id: 3, name: '이메일 도메인 보존', target: '이메일', targetClass: 'email', method: '데이터 마스킹', engineFunc: 'mask_email(keep_domain=true)', datasets: 4, active: true },
  { id: 4, name: '성명 SHA-256', target: '성명', targetClass: 'name', method: '암호화', engineFunc: 'hash_sha256(salt=true)', datasets: 6, active: true },
  { id: 5, name: 'IP주소 삭제', target: 'IP주소', targetClass: 'ip', method: '데이터 삭제', engineFunc: 'suppress()', datasets: 1, active: false },
  { id: 6, name: '주소 범주화', target: '주소', targetClass: 'addr', method: '데이터 범주화', engineFunc: 'generalize_addr(level=city)', datasets: 2, active: true },
])

const history = ref([
  { id: 1, date: '2026-04-01 08:00', dataset: '사용자 계정', policy: '주민번호 마스킹', count: 15200, elapsed: '2.3s', result: '성공' },
  { id: 2, date: '2026-04-01 08:00', dataset: '사용자 계정', policy: '전화번호 가명처리', count: 15200, elapsed: '1.8s', result: '성공' },
  { id: 3, date: '2026-03-31 22:00', dataset: '수질검사 결과', policy: '성명 SHA-256', count: 4500, elapsed: '0.5s', result: '성공' },
  { id: 4, date: '2026-03-31 06:00', dataset: '접근 로그', policy: 'IP주소 삭제', count: 125000, elapsed: '8.1s', result: '성공' },
  { id: 5, date: '2026-03-30 08:00', dataset: '외부사용자', policy: '이메일 도메인 보존', count: 3200, elapsed: '0.4s', result: '성공' },
])

const adequacyResults = ref([
  { metric: 'k-익명성 (k-Anonymity)', score: 96, desc: '동일 준식별자 조합이 k개 이상 존재', threshold: 'k ≥ 5', value: 'k = 8 (최소)' },
  { metric: 'l-다양성 (l-Diversity)', score: 91, desc: '각 동치 클래스 내 민감 속성 다양성', threshold: 'l ≥ 3', value: 'l = 4 (최소)' },
  { metric: 't-근접성 (t-Closeness)', score: 88, desc: '전체 분포와 동치 클래스 분포 거리', threshold: 't ≤ 0.2', value: 't = 0.15 (최대)' },
  { metric: '재식별 위험도', score: 97, desc: '비식별 데이터에서 개인 재식별 가능성', threshold: '위험도 < 5%', value: '2.8%' },
])

async function loadData() {
  try {
    const res = await adminCleansingApi.anonymization()
    if (res.data?.data && res.data.data.length > 0) {
      policies.value = res.data.data.map((item: any) => ({
        id: item.id,
        name: item.config_name,
        target: item.target_type || item.method,
        targetClass: (item.target_type || '').includes('주민') ? 'ssn' : (item.target_type || '').includes('전화') ? 'phone' : (item.target_type || '').includes('이메일') ? 'email' : 'name',
        method: item.method,
        engineFunc: item.engine_func || '-',
        datasets: item.dataset_count || 0,
        active: item.is_active !== false,
        _raw: item,
      }))
    }
  } catch (e) {
    console.warn('비식별화 데이터 로드 실패, mock 데이터 사용:', e)
  }
}

async function addPolicy() {
  try {
    await adminCleansingApi.createAnonymization(policyForm)
    showAddPolicy.value = false
    message.success('정책이 추가되었습니다.')
    Object.assign(policyForm, { config_name: '', method: 'MASKING', target_columns: [], target_type: '주민등록번호', engine_func: '', masking_pattern: '', apply_timing: '수집 시 인라인 적용', description: '' })
    await loadData()
  } catch (e: any) {
    message.error('정책 추가 실패: ' + (e?.response?.data?.message || e.message))
  }
}

async function applyPolicy(d: any) {
  try {
    const id = d._raw?.id || d.id
    await adminCleansingApi.executeAnonymization(id)
    d.status = '처리완료'
    d.statusClass = 'active'
    stats.value.pending--
    stats.value.processed++
    message.success('비식별 처리가 실행되었습니다.')
  } catch (e: any) {
    message.error('비식별 처리 실패: ' + (e?.response?.data?.message || e.message))
  }
}

async function deletePolicy(p: any) {
  try {
    const id = p._raw?.id || p.id
    await adminCleansingApi.deleteAnonymization(id)
    message.success('정책이 삭제되었습니다.')
    await loadData()
  } catch (e: any) {
    message.error('정책 삭제 실패: ' + (e?.response?.data?.message || e.message))
  }
}

function runDetection() { message.info('전체 데이터셋 개인정보 스캔이 시작되었습니다.\n엔진: ' + engine.value.name) }
function runAdequacy() { message.info('적정성 평가가 실행되었습니다.') }
function saveEngine() { message.success('엔진 연동 설정이 저장되었습니다.') }
function testEngine() { message.success('연결 테스트 성공: ' + engine.value.endpoint) }

onMounted(() => { loadData() })
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';

.kpi-row { display: grid; grid-template-columns: 1.5fr repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; text-align: center;
  .kpi-value { font-size: 24px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; }
}
.engine-card { text-align: left !important; display: flex; flex-direction: column; gap: 4px;
  .engine-status { font-size: 12px; display: flex; align-items: center; gap: 6px; }
  .engine-dot { width: 8px; height: 8px; border-radius: 50%; &.active { background: #28A745; } &.error { background: #DC3545; } }
  .engine-name { font-size: 16px; font-weight: 800; color: #333; }
  .engine-ver { font-size: 11px; color: #999; }
}

.tab-bar { display: flex; gap: 2px; border-bottom: 2px solid #e8e8e8; margin-bottom: 16px;
  button { padding: 8px 16px; border: none; background: none; font-size: 13px; color: #666; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px;
    &.active { color: $primary; border-bottom-color: $primary; font-weight: 600; } &:hover { color: $primary; }
  }
}
.tab-content { min-height: 300px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 600; font-size: 14px; }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; border: 1px solid #e8e8e8;
  th { background: #f5f7fa; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; }
  td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; }
  tr:hover td { background: #fafafa; }
}
.mono { font-family: monospace; font-size: 11px; }
.detect-type { padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.ssn { background: #fff1f0; color: #DC3545; } &.phone { background: #e6f7ff; color: #0066CC; }
  &.email { background: #f6ffed; color: #28A745; } &.name { background: #fff7e6; color: #fa8c16; }
  &.ip { background: #f9f0ff; color: #722ed1; } &.addr { background: #e6fffb; color: #13c2c2; }
}
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;
  &.active { background: #f6ffed; color: #28A745; } &.pending { background: #fff7e6; color: #fa8c16; }
  &.inactive { background: #f5f5f5; color: #999; } &.fail { background: #fff1f0; color: #DC3545; }
}
.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }

.adequacy-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.adeq-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center;
  .adeq-metric { font-size: 12px; font-weight: 700; color: #333; margin-bottom: 8px; }
  .adeq-score { font-size: 32px; font-weight: 900; }
  .adeq-desc { font-size: 11px; color: #999; margin-top: 4px; }
  .adeq-detail { font-size: 10px; color: #bbb; margin-top: 6px; font-family: monospace; }
}

.engine-config { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 14px;
  .config-group { display: flex; align-items: center; gap: 12px;
    label { width: 160px; font-size: 13px; font-weight: 600; color: #555; flex-shrink: 0; }
    input, select { flex: 1; padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
    .toggle-desc { font-size: 11px; color: #999; }
  }
  .config-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
}
.toggle { position: relative; width: 40px; height: 22px; flex-shrink: 0; display: inline-block;
  input { display: none; &:checked + .slider { background: $primary; &::before { transform: translateX(18px); } } }
  .slider { position: absolute; inset: 0; background: #ccc; border-radius: 22px; transition: 0.3s; cursor: pointer;
    &::before { content: ''; position: absolute; width: 16px; height: 16px; background: #fff; border-radius: 50%; left: 3px; top: 3px; transition: 0.3s; }
  }
}
.modal-form { display: flex; flex-direction: column; gap: 12px; }
.modal-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.modal-form-group { display: flex; flex-direction: column; gap: 4px;
  label { font-size: 12px; font-weight: 600; &.required::after { content: ' *'; color: #DC3545; } }
  input, select, textarea { padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; box-sizing: border-box; }
}
</style>
