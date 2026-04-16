<template>
  <div class="admin-page">
    <div class="page-header"><h2>역할 관리</h2><p class="page-desc">역할그룹별 역할과 화면별 CUD 권한을 관리합니다.</p></div>

    <!-- 역할그룹 카드 영역 -->
    <div class="role-groups">
      <div v-for="group in roleGroups" :key="group.code" class="role-group-card" :class="{ active: selectedGroup === group.code }">
        <div class="group-header" @click="selectedGroup = group.code">
          <component :is="group.icon" style="margin-right:6px" />
          <span class="group-title">{{ group.label }}</span>
          <span class="group-count">{{ getRolesByGroup(group.code).length }}개 역할</span>
        </div>
        <div class="group-roles">
          <div v-for="role in getRolesByGroup(group.code)" :key="role.id"
            class="role-item" :class="{ selected: selectedRole?.id === role.id }"
            @click="selectRole(role)">
            <div class="role-info">
              <span class="role-name">{{ role.role_name }}</span>
              <span class="role-code">{{ role.role_code }}</span>
            </div>
            <div class="role-meta">
              <span class="role-users"><TeamOutlined /> {{ role.user_count }}명</span>
              <span v-if="role.can_access_admin" class="badge badge-info">관리자</span>
            </div>
          </div>
        </div>
        <div class="group-actions">
          <button class="btn btn-xs btn-outline" @click="openAddRole(group.code)"><PlusOutlined /> 역할 추가</button>
        </div>
      </div>
    </div>

    <!-- 선택된 역할의 화면별 CUD 권한 매트릭스 -->
    <div v-if="selectedRole" class="table-section" style="margin-top:16px">
      <div class="table-header">
        <span class="table-count">
          <strong>{{ selectedRole.role_name }}</strong> 화면별 권한 ({{ permissionRows.length }}건)
        </span>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="savePermissions" :disabled="!isDirty"><SaveOutlined /> 저장</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(permCols, permissionRows, '화면권한_' + selectedRole.role_code)"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="permissionRows" :columnDefs="permCols"
          :defaultColDef="defCol" :tooltipShowDelay="0" :pagination="true" :paginationPageSize="20"
          domLayout="autoHeight" :getRowStyle="getRowStyle" @cell-value-changed="onCellChanged" />
      </div>
    </div>
    <div v-else class="empty-perm-area">
      <p>왼쪽에서 역할을 선택하면 화면별 CUD 권한을 설정할 수 있습니다.</p>
    </div>

    <!-- 역할 상세/수정 팝업 -->
    <AdminModal :visible="showDetail" :title="detailRole?.role_name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">역할 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">역할명</span><span class="info-value">{{ detailRole?.role_name }}</span></div>
          <div class="modal-info-item"><span class="info-label">코드</span><span class="info-value">{{ detailRole?.role_code }}</span></div>
          <div class="modal-info-item"><span class="info-label">역할그룹</span><span class="info-value">{{ getGroupLabel(detailRole?.role_group) }}</span></div>
          <div class="modal-info-item"><span class="info-label">설명</span><span class="info-value">{{ detailRole?.description }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용자 수</span><span class="info-value">{{ detailRole?.user_count }}명</span></div>
          <div class="modal-info-item"><span class="info-label">관리자접근</span><span class="info-value"><span :class="detailRole?.can_access_admin ? 'badge badge-success' : 'badge badge-default'">{{ detailRole?.can_access_admin ? '가능' : '불가' }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button v-if="!detailRole?.is_system_role" class="btn btn-danger btn-sm" @click="handleDeleteRole"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 역할 추가 팝업 -->
    <AdminModal :visible="showRegister" title="역할 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">역할명</label><input v-model="newRole.role_name" placeholder="역할명 입력" /></div>
          <div class="modal-form-group"><label class="required">역할코드</label><input v-model="newRole.role_code" placeholder="예: DATA_VIEWER" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">역할그룹</label>
            <select v-model="newRole.role_group">
              <option value="GENERAL">일반사용자</option>
              <option value="DATA_ADMIN">데이터관리자</option>
              <option value="SYS_ADMIN">시스템관리자</option>
              <option value="EXTERNAL">외부사용자</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>관리자 접근</label>
            <select v-model="newRole.can_access_admin">
              <option :value="true">가능</option>
              <option :value="false">불가</option>
            </select>
          </div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea v-model="newRole.description" rows="2" placeholder="역할 설명 입력"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'

import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, SaveOutlined, DeleteOutlined,
  SettingOutlined, TeamOutlined, DatabaseOutlined, GlobalOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

// ── 역할그룹 정의 ──
const roleGroups = [
  { code: 'GENERAL', label: '일반사용자', icon: TeamOutlined },
  { code: 'DATA_ADMIN', label: '데이터관리자', icon: DatabaseOutlined },
  { code: 'SYS_ADMIN', label: '시스템관리자', icon: SettingOutlined },
  { code: 'EXTERNAL', label: '외부사용자', icon: GlobalOutlined },
]

function getGroupLabel(code: string | undefined) {
  return roleGroups.find(g => g.code === code)?.label || code || ''
}

// ── 역할 데이터 ──
const allRoles = ref<any[]>([])
const selectedGroup = ref('GENERAL')
const selectedRole = ref<any>(null)
const showDetail = ref(false)
const showRegister = ref(false)
const detailRole = ref<any>(null)
const isDirty = ref(false)

const newRole = ref({ role_code: '', role_name: '', role_group: 'GENERAL', description: '', can_access_admin: false })

function getRolesByGroup(groupCode: string) {
  return allRoles.value.filter(r => r.role_group === groupCode)
}

function selectRole(role: any) {
  selectedRole.value = role
  isDirty.value = false
  loadScreenPermissions(role.id)
}

// ── 화면코드 & 권한 ──
const screenCodes = ref<any[]>([])
const permissionRows = ref<any[]>([])
const defCol = { ...baseDefaultColDef }

const permCols: ColDef[] = withHeaderTooltips([
  { headerName: '그룹', field: 'screen_group', flex: 0.8, minWidth: 100, rowGroup: false },
  { headerName: '화면명', field: 'screen_name', flex: 1.2, minWidth: 140 },
  { headerName: '화면코드', field: 'screen_code', flex: 0.8, minWidth: 100 },
  { headerName: '등록(C)', field: 'can_create', flex: 0.5, minWidth: 70, editable: true,
    cellDataType: 'boolean',
    cellRenderer: (p: any) => p.value ? '<span style="color:#52c41a;font-weight:bold">&#10004;</span>' : '<span style="color:#d9d9d9">&#10006;</span>',
    cellEditor: 'agCheckboxCellEditor',
  },
  { headerName: '수정(U)', field: 'can_update', flex: 0.5, minWidth: 70, editable: true,
    cellDataType: 'boolean',
    cellRenderer: (p: any) => p.value ? '<span style="color:#1890ff;font-weight:bold">&#10004;</span>' : '<span style="color:#d9d9d9">&#10006;</span>',
    cellEditor: 'agCheckboxCellEditor',
  },
  { headerName: '삭제(D)', field: 'can_delete', flex: 0.5, minWidth: 70, editable: true,
    cellDataType: 'boolean',
    cellRenderer: (p: any) => p.value ? '<span style="color:#ff4d4f;font-weight:bold">&#10004;</span>' : '<span style="color:#d9d9d9">&#10006;</span>',
    cellEditor: 'agCheckboxCellEditor',
  },
])

function getRowStyle(params: any) {
  const groupColors: Record<string, string> = {
    '시스템관리': '#fff7e6', '사용자관리': '#e6f7ff', '데이터표준': '#f6ffed',
    '데이터수집': '#fff0f6', '데이터정제': '#f9f0ff', '데이터저장': '#e6fffb',
    '데이터유통': '#fcffe6', '운영관리': '#fff1f0',
  }
  const bg = groupColors[params.data?.screen_group]
  return bg ? { backgroundColor: bg } : undefined
}

function onCellChanged() { isDirty.value = true }

async function loadScreenPermissions(roleId: string) {
  try {
    const [codesRes, permsRes] = await Promise.all([
      adminUserApi.screenCodes(),
      adminUserApi.screenPermissions(roleId),
    ])
    const codes = codesRes.data.data || []
    const perms = permsRes.data.data || []
    screenCodes.value = codes

    const permMap: Record<string, any> = {}
    for (const p of perms) { permMap[p.screen_code] = p }

    permissionRows.value = codes.map((sc: any) => {
      const existing = permMap[sc.screen_code]
      return {
        screen_code: sc.screen_code,
        screen_name: sc.screen_name,
        screen_group: sc.screen_group,
        can_create: existing?.can_create ?? false,
        can_update: existing?.can_update ?? false,
        can_delete: existing?.can_delete ?? false,
      }
    })
  } catch (e) {
    console.warn('loadScreenPermissions failed', e)
    permissionRows.value = []
  }
}

async function savePermissions() {
  if (!selectedRole.value) return
  try {
    await adminUserApi.updateScreenPermissions(selectedRole.value.id, {
      permissions: permissionRows.value.map(r => ({
        screen_code: r.screen_code,
        screen_name: r.screen_name,
        screen_group: r.screen_group,
        can_create: r.can_create,
        can_update: r.can_update,
        can_delete: r.can_delete,
      }))
    })
    isDirty.value = false
    message.success('화면별 권한이 저장되었습니다.')
  } catch (e) {
    message.error('권한 저장 실패')
  }
}

// ── 역할 CRUD ──
function openAddRole(groupCode: string) {
  newRole.value = { role_code: '', role_name: '', role_group: groupCode, description: '', can_access_admin: groupCode !== 'GENERAL' && groupCode !== 'EXTERNAL' }
  showRegister.value = true
}

async function handleRegister() {
  if (!newRole.value.role_code || !newRole.value.role_name) {
    message.warning('역할명과 코드를 입력하세요.')
    return
  }
  try {
    await adminUserApi.createRole(newRole.value)
    message.success('역할이 등록되었습니다.')
    showRegister.value = false
    await loadRoles()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '등록 실패')
  }
}

async function handleDeleteRole() {
  if (!detailRole.value) return
  try {
    await adminUserApi.deleteRole(detailRole.value.id)
    message.success('역할이 삭제되었습니다.')
    showDetail.value = false
    if (selectedRole.value?.id === detailRole.value.id) {
      selectedRole.value = null
      permissionRows.value = []
    }
    await loadRoles()
  } catch (e: any) {
    message.error(e.response?.data?.detail || '삭제 실패')
  }
}

async function loadRoles() {
  try {
    const res = await adminUserApi.roles()
    allRoles.value = (res.data.data || []).map((r: any) => ({
      ...r,
      role_group: r.role_group || 'GENERAL',
    }))
  } catch (e) {
    console.warn('loadRoles failed, using empty list', e)
    allRoles.value = []
  }
}

onMounted(() => {
  loadRoles()
})
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';

.role-groups {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 8px;

  @media (max-width: 1279px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.role-group-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;

  &.active { border-color: #1890ff; }

  .group-header {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;

    .group-title { flex: 1; }
    .group-count { font-size: 11px; color: #8c8c8c; font-weight: 400; }
  }

  .group-roles {
    padding: 6px;
    max-height: 200px;
    overflow-y: auto;
  }

  .role-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;

    &:hover { background: #f5f5f5; }
    &.selected { background: #e6f7ff; border-left: 3px solid #1890ff; }

    .role-info {
      display: flex;
      flex-direction: column;
      .role-name { font-weight: 500; }
      .role-code { font-size: 11px; color: #8c8c8c; }
    }
    .role-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: #8c8c8c;
    }
  }

  .group-actions {
    padding: 6px 10px 10px;
    text-align: center;
    .btn-xs { font-size: 11px; padding: 2px 10px; }
  }
}

.badge-info { background: #e6f7ff; color: #1890ff; border: 1px solid #91d5ff; padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.badge-default { background: #f5f5f5; color: #8c8c8c; padding: 1px 6px; border-radius: 3px; font-size: 11px; }

.empty-perm-area {
  margin-top: 16px;
  text-align: center;
  padding: 60px;
  background: #fafafa;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  color: #8c8c8c;
  font-size: 14px;
}

:deep(.ag-row) { cursor: pointer; }
</style>
