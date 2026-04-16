<template>
  <div class="admin-page">
    <div class="page-header"><h2>사용자 공통</h2><p class="page-desc">비밀번호 정책, 세션 관리 등 사용자 공통 설정을 관리합니다.</p></div>

    <div v-if="loading" class="loading-placeholder">설정을 불러오는 중...</div>

    <template v-else>
      <!-- ═══ 고정 + 커스텀 카테고리 카드 ═══ -->
      <div class="settings-cards">
        <!-- 고정 4개 카드 -->
        <div class="setting-card" v-for="section in sections" :key="section.key">
          <div class="setting-header">
            <span class="setting-header-left"><component :is="section.icon" /> {{ section.title }}</span>
            <button class="btn-edit" @click="openEdit(section.key)"><EditOutlined /> 편집</button>
          </div>
          <div class="setting-items">
            <div v-for="item in section.keys" :key="item.key" class="setting-item">
              <span class="setting-label">{{ item.label }}</span>
              <span class="setting-value">{{ displayValue(item.key, settings[item.key]) }}</span>
            </div>
          </div>
        </div>

        <!-- 커스텀 카테고리 카드들 -->
        <div class="setting-card" v-for="cat in customCategories" :key="cat.category_key">
          <div class="setting-header">
            <span class="setting-header-left"><AppstoreOutlined /> {{ cat.category_name }}</span>
            <div class="setting-header-actions">
              <button class="btn-edit" @click="openAddCustomSetting(cat.category_key)"><PlusOutlined /> 항목</button>
              <button class="btn-edit btn-delete" @click="handleDeleteCategory(cat.category_key)"><DeleteOutlined /></button>
            </div>
          </div>
          <div class="setting-items">
            <div v-if="!cat.items || cat.items.length === 0" class="setting-item empty-hint">
              <span class="setting-label">항목이 없습니다. "항목" 버튼으로 추가하세요.</span>
            </div>
            <div v-for="item in cat.items" :key="item.id" class="setting-item">
              <span class="setting-label">{{ item.name }}</span>
              <span class="setting-value">
                {{ item.value }}
                <button class="btn-inline-delete" @click="handleDeleteCustomSetting(item.id)" title="삭제"><CloseOutlined /></button>
              </span>
            </div>
          </div>
        </div>

        <!-- 카테고리 추가 버튼 카드 -->
        <div class="setting-card add-card" @click="showCategoryModal = true">
          <div class="add-card-content"><PlusCircleOutlined class="add-icon" /><span>카테고리 추가</span></div>
        </div>
      </div>

      <!-- ═══ 보안 규칙 관리 ═══ -->
      <div class="table-section">
        <div class="table-header">
          <span class="table-count"><SafetyOutlined /> 보안 규칙 <strong>{{ securityRules.length }}</strong>건</span>
          <div class="table-actions">
            <button class="btn btn-primary btn-sm" @click="openRuleModal(null)"><PlusOutlined /> 규칙 추가</button>
            <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(ruleCols, securityRules, '보안_규칙')"><FileExcelOutlined /></button>
          </div>
        </div>
        <div class="ag-grid-wrapper">
          <AgGridVue class="ag-theme-alpine" :rowData="securityRules" :columnDefs="ruleCols" :defaultColDef="defCol"
            :tooltipShowDelay="0" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRuleRowClick" />
        </div>
      </div>
    </template>

    <!-- ═══ 모달: 고정 설정 편집 ═══ -->
    <AdminModal :visible="!!editSection" :title="editTitle" size="md" @close="editSection = null">
      <div class="modal-form" v-if="editSection">
        <div class="modal-form-group" v-for="item in currentSectionItems" :key="item.key">
          <label>{{ item.label }}</label>
          <input v-if="item.type === 'NUMBER'" type="number" min="1" v-model="editForm[item.key]" />
          <select v-else-if="item.type === 'BOOLEAN'" v-model="editForm[item.key]">
            <option value="true">활성</option>
            <option value="false">비활성</option>
          </select>
          <select v-else-if="item.options" v-model="editForm[item.key]">
            <option v-for="opt in item.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <input v-else type="text" v-model="editForm[item.key]" />
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" :disabled="saving" @click="handleSave"><SaveOutlined /> {{ saving ? '저장 중...' : '저장' }}</button>
        <button class="btn btn-outline" @click="editSection = null">취소</button>
      </template>
    </AdminModal>

    <!-- ═══ 모달: 보안 규칙 추가/편집 ═══ -->
    <AdminModal :visible="showRuleModal" :title="ruleForm.id ? '보안 규칙 수정' : '보안 규칙 추가'" size="md" @close="showRuleModal = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">규칙 유형</label>
          <select v-model="ruleForm.rule_type" :disabled="!!ruleForm.id">
            <option value="">선택</option>
            <option value="IP_WHITELIST">IP 화이트리스트</option>
            <option value="ACCESS_TIME">접속 허용 시간대</option>
            <option value="PASSWORD_PATTERN">비밀번호 금지 패턴</option>
            <option value="SESSION_LIMIT">세션 제한</option>
          </select>
        </div>
        <div class="modal-form-group">
          <label class="required">규칙명</label>
          <input v-model="ruleForm.rule_name" placeholder="예: 본사 IP 대역" />
        </div>
        <div class="modal-form-group">
          <label class="required">값</label>
          <input v-model="ruleForm.value" :placeholder="rulePlaceholder" />
          <small class="form-hint">{{ ruleHint }}</small>
        </div>
        <div class="modal-form-group">
          <label>설명</label>
          <textarea v-model="ruleForm.description" rows="2" placeholder="규칙 설명 (선택)"></textarea>
        </div>
        <div class="modal-form-group" v-if="ruleForm.id">
          <label>상태</label>
          <select v-model="ruleForm.is_active">
            <option :value="true">활성</option>
            <option :value="false">비활성</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" :disabled="saving" @click="handleSaveRule"><SaveOutlined /> 저장</button>
        <button v-if="ruleForm.id" class="btn btn-danger" @click="handleDeleteRule"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showRuleModal = false">취소</button>
      </template>
    </AdminModal>

    <!-- ═══ 모달: 카테고리 추가 ═══ -->
    <AdminModal :visible="showCategoryModal" title="설정 카테고리 추가" size="sm" @close="showCategoryModal = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">카테고리명</label>
          <input v-model="newCategoryName" placeholder="예: 감사 설정, 외부 연동" />
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" :disabled="saving || !newCategoryName.trim()" @click="handleCreateCategory"><PlusOutlined /> 생성</button>
        <button class="btn btn-outline" @click="showCategoryModal = false">취소</button>
      </template>
    </AdminModal>

    <!-- ═══ 모달: 커스텀 설정 항목 추가 ═══ -->
    <AdminModal :visible="showCustomSettingModal" title="설정 항목 추가" size="sm" @close="showCustomSettingModal = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">항목명</label>
          <input v-model="customSettingForm.setting_name" placeholder="예: 최대 재시도 횟수" />
        </div>
        <div class="modal-form-group">
          <label class="required">값</label>
          <input v-model="customSettingForm.setting_value" placeholder="설정 값" />
        </div>
        <div class="modal-form-group">
          <label>값 유형</label>
          <select v-model="customSettingForm.setting_type">
            <option value="STRING">텍스트</option>
            <option value="NUMBER">숫자</option>
            <option value="BOOLEAN">활성/비활성</option>
          </select>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" :disabled="saving || !customSettingForm.setting_name.trim()" @click="handleCreateCustomSetting"><PlusOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showCustomSettingModal = false">취소</button>
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
  LockOutlined, ClockCircleOutlined, SafetyOutlined, MailOutlined, EditOutlined, SaveOutlined,
  PlusOutlined, PlusCircleOutlined, DeleteOutlined, CloseOutlined, FileExcelOutlined, AppstoreOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const loading = ref(true)
const saving = ref(false)
const settings = reactive<Record<string, string>>({})
const editSection = ref<string | null>(null)
const editForm = reactive<Record<string, string>>({})

// ── 보안 규칙 ──
const securityRules = ref<any[]>([])
const showRuleModal = ref(false)
const ruleForm = reactive<any>({ id: null, rule_type: '', rule_name: '', value: '', description: '', is_active: true })

// ── 커스텀 카테고리 ──
const customCategories = ref<any[]>([])
const showCategoryModal = ref(false)
const newCategoryName = ref('')
const showCustomSettingModal = ref(false)
const customSettingForm = reactive({ category_key: '', setting_name: '', setting_value: '', setting_type: 'STRING' })

// ── AG Grid ──
const defCol = { ...baseDefaultColDef }
const RULE_TYPE_MAP: Record<string, string> = {
  IP_WHITELIST: 'IP 화이트리스트', ACCESS_TIME: '접속 허용 시간대',
  PASSWORD_PATTERN: '비밀번호 금지 패턴', SESSION_LIMIT: '세션 제한',
}
const ruleCols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 50 },
  { headerName: '규칙 유형', field: 'rule_type', flex: 1, minWidth: 130, valueFormatter: (p: any) => RULE_TYPE_MAP[p.value] || p.value },
  { headerName: '규칙명', field: 'rule_name', flex: 1.5 },
  { headerName: '값', field: 'value', flex: 2 },
  { headerName: '상태', field: 'is_active', flex: 0.5, minWidth: 70, cellRenderer: (p: any) => p.value ? '활성' : '비활성' },
  { headerName: '설명', field: 'description', flex: 1.5 },
])

// ── 고정 섹션 정의 ──
interface SettingItem { key: string; label: string; type: 'NUMBER' | 'BOOLEAN' | 'STRING'; options?: { value: string; label: string }[] }
interface Section { key: string; title: string; icon: any; keys: SettingItem[] }

const sections: Section[] = [
  {
    key: 'password', title: '비밀번호 정책', icon: LockOutlined,
    keys: [
      { key: 'user.password.min_length', label: '최소 길이', type: 'NUMBER' },
      { key: 'user.password.complexity', label: '복잡도', type: 'STRING', options: [
        { value: 'UPPER_LOWER_NUMBER_SPECIAL', label: '대/소문자+숫자+특수문자' },
        { value: 'UPPER_LOWER_NUMBER', label: '대/소문자+숫자' },
        { value: 'LOWER_NUMBER', label: '소문자+숫자' },
      ]},
      { key: 'user.password.change_cycle_days', label: '변경 주기(일)', type: 'NUMBER' },
      { key: 'user.password.reuse_limit', label: '재사용 제한(개)', type: 'NUMBER' },
    ],
  },
  {
    key: 'session', title: '세션 관리', icon: ClockCircleOutlined,
    keys: [
      { key: 'user.session.timeout_minutes', label: '세션 타임아웃(분)', type: 'NUMBER' },
      { key: 'user.session.max_devices', label: '동시 접속 디바이스', type: 'NUMBER' },
      { key: 'user.session.auto_logout', label: '자동 로그아웃', type: 'BOOLEAN' },
    ],
  },
  {
    key: 'security', title: '보안 설정', icon: SafetyOutlined,
    keys: [
      { key: 'user.security.login_fail_lock_count', label: '로그인 실패 잠금 횟수', type: 'NUMBER' },
      { key: 'user.security.login_fail_lock_minutes', label: '잠금 시간(분)', type: 'NUMBER' },
      { key: 'user.security.ip_access_control', label: 'IP 접근 제어', type: 'BOOLEAN' },
      { key: 'user.security.two_factor_auth', label: '2단계 인증', type: 'STRING', options: [
        { value: 'REQUIRED', label: '필수' }, { value: 'OPTIONAL', label: '선택적' }, { value: 'DISABLED', label: '비활성' },
      ]},
    ],
  },
  {
    key: 'notification', title: '알림 설정', icon: MailOutlined,
    keys: [
      { key: 'user.notification.signup_approval', label: '가입 승인 알림', type: 'STRING', options: [
        { value: 'EMAIL_PORTAL', label: '이메일+포털' }, { value: 'EMAIL', label: '이메일만' }, { value: 'PORTAL', label: '포털만' },
      ]},
      { key: 'user.notification.password_expiry_days', label: '비밀번호 만료 사전 알림(일)', type: 'NUMBER' },
      { key: 'user.notification.account_expiry_days', label: '계정 만료 사전 알림(일)', type: 'NUMBER' },
    ],
  },
]

const DEFAULTS: Record<string, string> = {
  'user.password.min_length': '8', 'user.password.complexity': 'UPPER_LOWER_NUMBER_SPECIAL',
  'user.password.change_cycle_days': '90', 'user.password.reuse_limit': '5',
  'user.session.timeout_minutes': '30', 'user.session.max_devices': '3', 'user.session.auto_logout': 'true',
  'user.security.login_fail_lock_count': '5', 'user.security.login_fail_lock_minutes': '30',
  'user.security.ip_access_control': 'true', 'user.security.two_factor_auth': 'OPTIONAL',
  'user.notification.signup_approval': 'EMAIL_PORTAL', 'user.notification.password_expiry_days': '7',
  'user.notification.account_expiry_days': '14',
}

const DISPLAY_MAP: Record<string, Record<string, string>> = {
  'user.password.complexity': { UPPER_LOWER_NUMBER_SPECIAL: '대/소문자+숫자+특수문자', UPPER_LOWER_NUMBER: '대/소문자+숫자', LOWER_NUMBER: '소문자+숫자' },
  'user.session.auto_logout': { true: '활성', false: '비활성' },
  'user.security.ip_access_control': { true: '활성', false: '비활성' },
  'user.security.two_factor_auth': { REQUIRED: '필수', OPTIONAL: '선택적', DISABLED: '비활성' },
  'user.notification.signup_approval': { EMAIL_PORTAL: '이메일+포털', EMAIL: '이메일만', PORTAL: '포털만' },
}

const UNIT_MAP: Record<string, string> = {
  'user.password.min_length': '자 이상', 'user.password.change_cycle_days': '일', 'user.password.reuse_limit': '개',
  'user.session.timeout_minutes': '분', 'user.session.max_devices': '개 디바이스',
  'user.security.login_fail_lock_count': '회', 'user.security.login_fail_lock_minutes': '분',
  'user.notification.password_expiry_days': '일 전', 'user.notification.account_expiry_days': '일 전',
}

function displayValue(key: string, raw: string | undefined): string {
  const val = raw ?? DEFAULTS[key] ?? ''
  if (DISPLAY_MAP[key]?.[val]) return DISPLAY_MAP[key][val]
  if (UNIT_MAP[key]) return `${val}${UNIT_MAP[key]}`
  return val
}

// ── 고정 설정 편집 ──
const editTitle = computed(() => { const s = sections.find(s => s.key === editSection.value); return s ? `${s.title} 편집` : '' })
const currentSectionItems = computed(() => sections.find(s => s.key === editSection.value)?.keys ?? [])

function openEdit(sectionKey: string) {
  const sec = sections.find(s => s.key === sectionKey)
  if (!sec) return
  for (const item of sec.keys) editForm[item.key] = settings[item.key] ?? DEFAULTS[item.key] ?? ''
  editSection.value = sectionKey
}

async function handleSave() {
  saving.value = true
  try {
    const sec = sections.find(s => s.key === editSection.value)
    if (!sec) return
    const payload: Record<string, string> = {}
    for (const item of sec.keys) payload[item.key] = String(editForm[item.key])
    await adminUserApi.updateCommonSettings({ settings: payload })
    Object.assign(settings, payload)
    message.success('설정이 저장되었습니다')
    editSection.value = null
  } catch (e) { message.error('설정 저장에 실패했습니다') }
  finally { saving.value = false }
}

// ── 보안 규칙 ──
const rulePlaceholder = computed(() => {
  const map: Record<string, string> = {
    IP_WHITELIST: '10.10.0.0/16', ACCESS_TIME: '09:00~18:00',
    PASSWORD_PATTERN: 'kwater, password, 1234', SESSION_LIMIT: 'ADMIN:5, INTERNAL:3',
  }
  return map[ruleForm.rule_type] || '값 입력'
})
const ruleHint = computed(() => {
  const map: Record<string, string> = {
    IP_WHITELIST: 'CIDR 표기법 (예: 10.10.0.0/16, 192.168.1.0/24)',
    ACCESS_TIME: '시작~종료 (24시간, 예: 09:00~18:00)',
    PASSWORD_PATTERN: '금지 문자열을 쉼표(,)로 구분',
    SESSION_LIMIT: '역할코드:세션수 형태로 쉼표 구분',
  }
  return map[ruleForm.rule_type] || ''
})

function openRuleModal(row: any | null) {
  if (row) {
    Object.assign(ruleForm, { id: row.id, rule_type: row.rule_type, rule_name: row.rule_name, value: row.value, description: row.description || '', is_active: row.is_active ?? true })
  } else {
    Object.assign(ruleForm, { id: null, rule_type: '', rule_name: '', value: '', description: '', is_active: true })
  }
  showRuleModal.value = true
}

function onRuleRowClick(event: any) { openRuleModal(event.data) }

async function handleSaveRule() {
  if (!ruleForm.rule_type || !ruleForm.rule_name || !ruleForm.value) {
    message.warning('필수 항목을 입력하세요'); return
  }
  saving.value = true
  try {
    if (ruleForm.id) {
      await adminUserApi.updateSecurityRule(ruleForm.id, {
        rule_name: ruleForm.rule_name, value: ruleForm.value, is_active: ruleForm.is_active, description: ruleForm.description,
      })
      message.success('보안 규칙이 수정되었습니다')
    } else {
      await adminUserApi.createSecurityRule({
        rule_type: ruleForm.rule_type, rule_name: ruleForm.rule_name, value: ruleForm.value, description: ruleForm.description,
      })
      message.success('보안 규칙이 추가되었습니다')
    }
    showRuleModal.value = false
    await loadData()
  } catch (e) { message.error('보안 규칙 저장에 실패했습니다') }
  finally { saving.value = false }
}

async function handleDeleteRule() {
  if (!ruleForm.id) return
  saving.value = true
  try {
    await adminUserApi.deleteSecurityRule(ruleForm.id)
    message.success('보안 규칙이 삭제되었습니다')
    showRuleModal.value = false
    await loadData()
  } catch (e) { message.error('삭제에 실패했습니다') }
  finally { saving.value = false }
}

// ── 커스텀 카테고리 ──
async function handleCreateCategory() {
  if (!newCategoryName.value.trim()) return
  saving.value = true
  try {
    await adminUserApi.createCustomCategory({ category_name: newCategoryName.value.trim() })
    message.success('카테고리가 생성되었습니다')
    newCategoryName.value = ''
    showCategoryModal.value = false
    await loadData()
  } catch (e: any) { message.error(e?.response?.data?.detail || '카테고리 생성에 실패했습니다') }
  finally { saving.value = false }
}

async function handleDeleteCategory(catKey: string) {
  if (!confirm(`'${catKey}' 카테고리를 삭제하시겠습니까? 소속 항목도 모두 삭제됩니다.`)) return
  try {
    await adminUserApi.deleteCustomCategory(catKey)
    message.success('카테고리가 삭제되었습니다')
    await loadData()
  } catch (e) { message.error('카테고리 삭제에 실패했습니다') }
}

function openAddCustomSetting(catKey: string) {
  Object.assign(customSettingForm, { category_key: catKey, setting_name: '', setting_value: '', setting_type: 'STRING' })
  showCustomSettingModal.value = true
}

async function handleCreateCustomSetting() {
  if (!customSettingForm.setting_name.trim()) return
  saving.value = true
  try {
    await adminUserApi.createCustomSetting(customSettingForm)
    message.success('설정 항목이 추가되었습니다')
    showCustomSettingModal.value = false
    await loadData()
  } catch (e) { message.error('설정 항목 추가에 실패했습니다') }
  finally { saving.value = false }
}

async function handleDeleteCustomSetting(settingId: string) {
  try {
    await adminUserApi.deleteCustomSetting(settingId)
    message.success('설정 항목이 삭제되었습니다')
    await loadData()
  } catch (e) { message.error('삭제에 실패했습니다') }
}

// ── 데이터 로드 ──
async function loadData() {
  try {
    const res = await adminUserApi.commonSettings()
    const data = res.data.data
    if (data) {
      Object.assign(settings, data.password_policy, data.session_management, data.security_settings, data.notification_settings)
      securityRules.value = data.security_rules || []
      customCategories.value = data.custom_categories || []
    }
  } catch (e) {
    console.warn('UserCommon: API 호출 실패, 기본값 사용', e)
    Object.assign(settings, DEFAULTS)
  }
}

onMounted(async () => {
  await loadData()
  loading.value = false
})
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';
@use '../../../styles/variables' as *;

.loading-placeholder { text-align: center; padding: 60px 0; color: $text-muted; font-size: $font-size-sm; }

.settings-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: $spacing-lg; margin-bottom: $spacing-lg; }

.setting-card { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden; }

.setting-header {
  padding: $spacing-md $spacing-lg; background: #4a6a8a; color: $white; font-size: $font-size-sm; font-weight: 600;
  display: flex; align-items: center; justify-content: space-between;
  .setting-header-left { display: flex; align-items: center; gap: $spacing-sm; }
  .setting-header-actions { display: flex; gap: 4px; }
}

.btn-edit {
  background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.4); color: $white;
  padding: 4px 12px; border-radius: $radius-sm; font-size: 12px; cursor: pointer;
  display: flex; align-items: center; gap: 4px; transition: all $transition-fast;
  &:hover { background: rgba(255, 255, 255, 0.3); }
  &.btn-delete { padding: 4px 8px; &:hover { background: rgba(255, 80, 80, 0.5); } }
}

.setting-items { padding: $spacing-sm 0; }

.setting-item {
  display: flex; justify-content: space-between; align-items: center; padding: $spacing-sm $spacing-lg;
  border-bottom: 1px solid #f5f5f5;
  &:last-child { border-bottom: none; }
  &.empty-hint { justify-content: center; .setting-label { color: $text-muted; font-style: italic; } }
}

.setting-label { font-size: $font-size-sm; color: $text-secondary; }
.setting-value { font-size: $font-size-sm; font-weight: 600; color: $text-primary; display: flex; align-items: center; gap: 6px; }

.btn-inline-delete {
  background: none; border: none; color: #ccc; cursor: pointer; font-size: 11px; padding: 2px;
  &:hover { color: #e74c3c; }
}

.add-card {
  border: 2px dashed $border-color; cursor: pointer; display: flex; align-items: center; justify-content: center;
  min-height: 120px; transition: all $transition-fast;
  &:hover { border-color: $primary; background: rgba(66, 133, 244, 0.03); }
  .add-card-content { display: flex; flex-direction: column; align-items: center; gap: $spacing-sm; color: $text-muted; font-size: $font-size-sm; }
  .add-icon { font-size: 28px; color: $primary; }
}

.modal-form { display: flex; flex-direction: column; gap: $spacing-md; }

.modal-form-group {
  display: flex; flex-direction: column; gap: $spacing-xs;
  label { font-size: $font-size-sm; font-weight: 600; color: $text-secondary;
    &.required::before { content: "* "; color: #e74c3c; }
  }
  input, select, textarea {
    padding: 8px 12px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm;
    outline: none; background: $white; font-family: inherit;
    &:focus { border-color: $primary; box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.1); }
  }
  input[type="number"] { max-width: 200px; }
  .form-hint { font-size: 11px; color: $text-muted; }
}

.btn-danger {
  background: #e74c3c; color: $white; border: none; padding: 8px 16px; border-radius: $radius-sm;
  cursor: pointer; font-size: $font-size-sm; display: flex; align-items: center; gap: 4px;
  &:hover { background: #c0392b; }
}

:deep(.ag-row) { cursor: pointer; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) { .settings-cards { grid-template-columns: 1fr; } }
</style>
