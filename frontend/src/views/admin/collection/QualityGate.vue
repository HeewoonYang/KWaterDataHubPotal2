<template>
  <div class="admin-page">
    <div class="page-header"><h2>수집 품질 게이트웨이*</h2><p class="page-desc">수집 단계에서 이상치/결측값을 감지하여 격리하고, 품질 검증 룰을 관리합니다.</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-value" style="color:#28A745">{{ passCount }}</div><div class="kpi-label">통과</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#fa8c16">{{ quarantineCount }}</div><div class="kpi-label">격리 (검토필요)</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#DC3545">{{ rejectCount }}</div><div class="kpi-label">거부</div></div>
      <div class="kpi-card"><div class="kpi-value">{{ rules.length }}</div><div class="kpi-label">검증 룰</div></div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">격리된 데이터 (Quarantine)</div>
        <div v-for="q in quarantined" :key="q.id" class="quarantine-item">
          <div class="q-info"><strong>{{ q.dataset }}</strong><span class="q-reason">{{ q.reason }}</span><span class="q-time">{{ q.detected }}</span></div>
          <div class="q-actions">
            <button class="btn btn-xs btn-success" @click="q.status = 'approved'; passCount++; quarantineCount--">승인</button>
            <button class="btn btn-xs btn-danger" @click="q.status = 'rejected'; rejectCount++; quarantineCount--">거부</button>
          </div>
        </div>
        <div v-if="quarantined.length === 0" class="empty-msg">격리 항목 없음</div>
      </div>
      <div class="card">
        <div class="card-title">품질 검증 룰 <button class="btn btn-xs btn-primary" style="float:right" @click="showAddRule = true"><PlusOutlined /> 추가</button></div>
        <table class="data-table">
          <thead><tr><th>룰명</th><th>대상</th><th>조건</th><th>상태</th></tr></thead>
          <tbody>
            <tr v-for="r in rules" :key="r.name"><td><strong>{{ r.name }}</strong></td><td>{{ r.target }}</td><td class="mono">{{ r.condition }}</td>
              <td><span class="status-badge" :class="r.active ? 'active' : 'inactive'">{{ r.active ? '활성' : '비활성' }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <AdminModal :visible="showAddRule" title="품질 검증 룰 추가" size="md" @close="showAddRule = false">
      <div class="form-group"><label>룰명</label><input v-model="ruleForm.rule_name" type="text" placeholder="예: 수위 이상치 탐지" /></div>
      <div class="form-group"><label>대상 컬럼</label><input v-model="ruleForm.target_column" type="text" placeholder="예: WATER_LV" /></div>
      <div class="form-group"><label>검증 조건</label><input v-model="ruleForm.condition" type="text" placeholder="예: value > 0 AND value < 300" /></div>
      <div class="form-group"><label>위반 시 처리</label><select v-model="ruleForm.severity"><option value="QUARANTINE">격리 (Quarantine)</option><option value="REJECT">거부 (Reject)</option><option value="WARNING">경고 (Warning)</option></select></div>
      <template #footer><button class="btn btn-primary" @click="addRule">추가</button><button class="btn btn-outline" @click="showAddRule = false">취소</button></template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import { qualityApi } from '../../../api/standard.api'
import AdminModal from '../../../components/AdminModal.vue'
const showAddRule = ref(false)

const ruleForm = reactive({
  rule_name: '',
  target_column: '',
  condition: '',
  severity: 'WARNING',
})

async function loadData() {
  try {
    const res = await qualityApi.listRules()
    if (res.data?.data && res.data.data.length > 0) {
      rules.value = res.data.data.map((item: any) => ({
        name: item.rule_name || item.name,
        target: item.target_column || item.target,
        condition: item.condition,
        active: item.is_active !== false,
        _raw: item,
      }))
    }
  } catch (e) {
    console.warn('품질 룰 데이터 로드 실패, mock 데이터 사용:', e)
  }
}

async function addRule() {
  try {
    await qualityApi.createRule(ruleForm)
    showAddRule.value = false
    message.success('룰이 추가되었습니다.')
    Object.assign(ruleForm, { rule_name: '', target_column: '', condition: '', severity: 'WARNING' })
    await loadData()
  } catch (e: any) {
    message.error('룰 추가 실패: ' + (e?.response?.data?.message || e.message))
  }
}
const passCount = ref(1245)
const quarantineCount = ref(3)
const rejectCount = ref(1)
const quarantined = ref([
  { id: 1, dataset: '수위관측 시계열', reason: 'WATER_LV = -999 (이상치)', detected: '2026-04-01 08:30', status: 'pending' },
  { id: 2, dataset: '수질 센서 데이터', reason: 'pH = 15.2 (범위 초과: 0~14)', detected: '2026-04-01 07:15', status: 'pending' },
  { id: 3, dataset: '전력 사용량', reason: 'METER_ID = NULL (필수값 누락)', detected: '2026-03-31 23:45', status: 'pending' },
])
const rules = ref([
  { name: '수위 범위 검증', target: 'WATER_LV', condition: 'value >= 0 AND value <= 300', active: true },
  { name: 'pH 범위 검증', target: 'PH', condition: 'value >= 0 AND value <= 14', active: true },
  { name: '필수 ID 검증', target: '*_ID', condition: 'NOT NULL', active: true },
  { name: '온도 이상치', target: 'TEMP_C', condition: 'value >= -30 AND value <= 50', active: true },
  { name: '유량 음수 검증', target: 'FLOW_RATE', condition: 'value >= 0', active: false },
])

onMounted(() => { loadData() })
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .kpi-value { font-size: 24px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; } }
.quarantine-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f0f0;
  .q-info { display: flex; flex-direction: column; gap: 2px; font-size: 12px; .q-reason { color: #DC3545; font-size: 11px; } .q-time { color: #999; font-size: 10px; } }
  .q-actions { display: flex; gap: 4px; }
}
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } }
.mono { font-family: monospace; font-size: 10px; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.inactive { background: #f5f5f5; color: #999; } }
.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }
.btn-success { border-color: #28A745 !important; color: #28A745 !important; }
.btn-danger { border-color: #DC3545 !important; color: #DC3545 !important; }
.empty-msg { text-align: center; color: #999; padding: 20px; font-size: 12px; }
.form-group { margin-bottom: 12px; label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; } input, select { width: 100%; padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; box-sizing: border-box; } }
</style>
