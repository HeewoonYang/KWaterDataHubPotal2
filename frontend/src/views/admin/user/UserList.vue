<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>조직 및 사용자 관리</h2>
      <p class="page-desc">K-water 조직 구조와 소속 사용자를 조회하고 관리합니다.</p>
    </div>

    <div class="org-user-layout">
      <!-- 좌측: 조직 트리 -->
      <div class="org-tree-panel">
        <div class="panel-header">
          <span class="panel-title"><ApartmentOutlined /> 조직도</span>
          <button class="btn-icon" title="새로고침" @click="loadOrgTree"><ReloadOutlined /></button>
        </div>
        <div class="tree-search">
          <input type="text" v-model="orgSearch" placeholder="부서 검색" />
        </div>
        <div class="tree-container">
          <div class="tree-node root" :class="{ active: !selectedOrg }" @click="selectOrg(null)">
            <BankOutlined /> K-water 전체
            <span class="node-count">{{ totalUserCount }}</span>
          </div>
          <template v-for="dept in filteredOrgTree" :key="dept.code">
            <div class="tree-node level-1" :class="{ active: selectedOrg?.code === dept.code, expanded: dept.expanded }" @click="selectOrg(dept)">
              <span class="expand-icon" @click.stop="dept.expanded = !dept.expanded">
                <CaretRightOutlined v-if="!dept.expanded && dept.children?.length" />
                <CaretDownOutlined v-if="dept.expanded && dept.children?.length" />
                <span v-if="!dept.children?.length" style="width:14px;display:inline-block"></span>
              </span>
              <FolderOutlined /> {{ dept.name }}
              <span class="node-count">{{ dept.userCount }}</span>
            </div>
            <template v-if="dept.expanded && dept.children">
              <div v-for="sub in dept.children" :key="sub.code" class="tree-node level-2" :class="{ active: selectedOrg?.code === sub.code }" @click="selectOrg(sub)">
                <TeamOutlined /> {{ sub.name }}
                <span class="node-count">{{ sub.userCount }}</span>
              </div>
            </template>
          </template>
        </div>
      </div>

      <!-- 우측: 사용자 목록 -->
      <div class="user-list-panel">
        <div class="panel-header">
          <span class="panel-title">
            <template v-if="selectedOrg">{{ selectedOrg.name }}</template>
            <template v-else>전체</template>
            소속 사용자
          </span>
        </div>

        <div class="search-filter compact">
          <div class="filter-row">
            <div class="filter-group"><label>역할</label><select v-model="filterRole"><option value="">전체</option><option value="ADMIN">관리자</option><option value="MANAGER">매니저</option><option value="INTERNAL">일반</option></select></div>
            <div class="filter-group"><label>상태</label><select v-model="filterStatus"><option value="">전체</option><option value="active">활성</option><option value="inactive">비활성</option><option value="suspended">정지</option></select></div>
            <div class="filter-group search-group"><label>검색</label><input type="text" v-model="searchText" placeholder="이름, 사번, 이메일 검색" @keyup.enter="loadUsers" /></div>
            <div class="filter-actions">
              <button class="btn btn-primary" @click="loadUsers"><SearchOutlined /> 조회</button>
              <button class="btn btn-outline" @click="resetFilter"><ReloadOutlined /> 초기화</button>
            </div>
          </div>
        </div>

        <div class="table-section">
          <div class="table-header">
            <span class="table-count">전체 <strong>{{ rowData.length }}</strong>건</span>
            <div class="table-actions">
              <button class="btn btn-success" @click="showRegister = true"><PlusOutlined /> 등록</button>
              <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, rowData, '사용자_목록')"><FileExcelOutlined /></button>
            </div>
          </div>
          <div class="ag-grid-wrapper">
            <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="columnDefs" :defaultColDef="defaultColDef" :tooltipShowDelay="0" :pagination="true" :paginationPageSize="15" :rowSelection="'multiple'" domLayout="autoHeight" @row-clicked="onRowClick" />
          </div>
        </div>
      </div>
    </div>

    <!-- 사용자 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailUser.name + ' 사용자 상세'" size="lg" @close="showDetail = false">
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">총 로그인</div><div class="stat-number">{{ detailUser.loginCount || 0 }}</div></div>
        <div class="modal-stat-card success"><div class="stat-title">데이터 조회</div><div class="stat-number">{{ detailUser.queryCount || 0 }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">다운로드</div><div class="stat-number">{{ detailUser.downloadCount || 0 }}</div></div>
        <div class="modal-stat-card info"><div class="stat-title">API 호출</div><div class="stat-number">{{ detailUser.apiCount || 0 }}</div></div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">사번</span><span class="info-value">{{ detailUser.empNo }}</span></div>
          <div class="modal-info-item"><span class="info-label">이름</span><span class="info-value">{{ detailUser.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">부서</span><span class="info-value">{{ detailUser.department }}</span></div>
          <div class="modal-info-item"><span class="info-label">직급</span><span class="info-value">{{ detailUser.position }}</span></div>
          <div class="modal-info-item"><span class="info-label">역할</span><span class="info-value">{{ detailUser.role }}</span></div>
          <div class="modal-info-item"><span class="info-label">이메일</span><span class="info-value">{{ detailUser.email }}</span></div>
          <div class="modal-info-item"><span class="info-label">전화번호</span><span class="info-value">{{ detailUser.phone || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 로그인</span><span class="info-value">{{ detailUser.lastLogin }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailUser.status === '활성' ? 'badge-success' : detailUser.status === '정지' ? 'badge-danger' : 'badge-muted'">{{ detailUser.status }}</span></span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">최근 활동 이력</div>
        <table class="modal-table">
          <thead><tr><th>번호</th><th>일시</th><th>활동</th><th>대상</th><th>IP</th></tr></thead>
          <tbody>
            <tr v-for="(act, idx) in detailUser.activities || []" :key="idx">
              <td class="text-center">{{ Number(idx) + 1 }}</td>
              <td>{{ act.datetime }}</td>
              <td>{{ act.action }}</td>
              <td>{{ act.target }}</td>
              <td>{{ act.ip }}</td>
            </tr>
            <tr v-if="!detailUser.activities?.length"><td colspan="5" class="text-center" style="color:#999">활동 이력이 없습니다.</td></tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-warning" @click="handleResetPassword"><ReloadOutlined /> 비밀번호 초기화</button>
        <button class="btn btn-primary" @click="openEditMode"><EditOutlined /> 수정</button>
        <button class="btn btn-danger" @click="handleDeleteUser"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 사용자 등록 팝업 -->
    <AdminModal :visible="showRegister" title="내부 사용자 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">사번</label><input v-model="registerForm.empNo" placeholder="사번 입력" /></div>
          <div class="modal-form-group"><label class="required">이름</label><input v-model="registerForm.name" placeholder="이름 입력" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">부서</label>
            <select v-model="registerForm.deptCode">
              <option value="">선택</option>
              <option v-for="d in flatOrgList" :key="d.code" :value="d.code">{{ d.name }}</option>
            </select>
          </div>
          <div class="modal-form-group"><label class="required">직급</label>
            <select v-model="registerForm.position">
              <option value="">선택</option>
              <option>사원</option><option>대리</option><option>과장</option><option>부장</option><option>처장</option>
            </select>
          </div>
        </div>
        <div class="modal-form-group"><label class="required">이메일</label><input v-model="registerForm.email" placeholder="email@kwater.or.kr" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">역할</label>
            <select v-model="registerForm.roleCode">
              <option value="INTERNAL">INTERNAL (일반)</option>
              <option value="MANAGER">MANAGER (매니저)</option>
              <option value="ADMIN">ADMIN (관리자)</option>
            </select>
          </div>
          <div class="modal-form-group"><label>전화번호</label><input v-model="registerForm.phone" placeholder="전화번호" /></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, computed, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  SearchOutlined, ReloadOutlined, PlusOutlined, FileExcelOutlined,
  EditOutlined, SaveOutlined, DeleteOutlined, ApartmentOutlined, BankOutlined,
  FolderOutlined, TeamOutlined, CaretRightOutlined, CaretDownOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

// ── 조직 트리 ──
interface OrgNode {
  code: string
  name: string
  parentCode?: string
  userCount: number
  expanded?: boolean
  children?: OrgNode[]
}

const orgSearch = ref('')
const selectedOrg = ref<OrgNode | null>(null)
const orgTree = ref<OrgNode[]>([
  {
    code: 'EXEC', name: '경영본부', userCount: 25, expanded: false,
    children: [
      { code: 'EXEC-HR', name: '인사처', userCount: 12 },
      { code: 'EXEC-FIN', name: '재무처', userCount: 13 },
    ],
  },
  {
    code: 'WATER', name: '수자원부', userCount: 38, expanded: false,
    children: [
      { code: 'WATER-DAM', name: '댐관리처', userCount: 15 },
      { code: 'WATER-RIVER', name: '하천관리처', userCount: 12 },
      { code: 'WATER-PLAN', name: '수자원기획처', userCount: 11 },
    ],
  },
  {
    code: 'SUPPLY', name: '수도부', userCount: 32, expanded: false,
    children: [
      { code: 'SUPPLY-NET', name: '관망관리처', userCount: 16 },
      { code: 'SUPPLY-QUAL', name: '수질관리처', userCount: 16 },
    ],
  },
  {
    code: 'ENV', name: '환경부', userCount: 28, expanded: false,
    children: [
      { code: 'ENV-ECO', name: '환경생태처', userCount: 14 },
      { code: 'ENV-SAFE', name: '안전관리처', userCount: 14 },
    ],
  },
  {
    code: 'IT', name: '정보화처', userCount: 22, expanded: false,
    children: [
      { code: 'IT-DEV', name: '정보개발팀', userCount: 10 },
      { code: 'IT-INFRA', name: '인프라운영팀', userCount: 7 },
      { code: 'IT-DATA', name: '데이터관리팀', userCount: 5 },
    ],
  },
])

const totalUserCount = computed(() => orgTree.value.reduce((s: number, d) => s + d.userCount, 0))

const filteredOrgTree = computed(() => {
  if (!orgSearch.value) return orgTree.value
  const kw = orgSearch.value.toLowerCase()
  return orgTree.value.filter(d =>
    d.name.toLowerCase().includes(kw) ||
    d.children?.some(c => c.name.toLowerCase().includes(kw))
  ).map(d => ({ ...d, expanded: true }))
})

const flatOrgList = computed(() => {
  const list: { code: string; name: string }[] = []
  orgTree.value.forEach(d => {
    list.push({ code: d.code, name: d.name })
    d.children?.forEach(c => list.push({ code: c.code, name: `  ${d.name} > ${c.name}` }))
  })
  return list
})

function selectOrg(org: OrgNode | null) {
  selectedOrg.value = org
  loadUsers()
}

async function loadOrgTree() {
  try {
    const res = await adminUserApi.orgTree()
    if (res.data?.data?.length) {
      // API에서 flat 리스트로 오므로 트리 구조 유지하면서 userCount 업데이트
      const apiData = res.data.data as { code: string; name: string; userCount: number }[]
      const countMap: Record<string, number> = {}
      apiData.forEach(d => { countMap[d.code] = d.userCount })
      orgTree.value.forEach(dept => {
        if (countMap[dept.code] !== undefined) dept.userCount = countMap[dept.code]
        dept.children?.forEach(sub => {
          if (countMap[sub.code] !== undefined) sub.userCount = countMap[sub.code]
        })
      })
    }
  } catch (e) {
    console.warn('조직 트리 API 호출 실패:', e)
  }
  orgSearch.value = ''
  selectedOrg.value = null
}

// ── 사용자 목록 ──
const filterRole = ref(''), filterStatus = ref(''), searchText = ref('')
const showDetail = ref(false), showRegister = ref(false)
const detailUser = ref<any>({})
const registerForm = ref({ empNo: '', name: '', deptCode: '', position: '', email: '', roleCode: 'INTERNAL', phone: '' })

const defaultColDef = { ...baseDefaultColDef }
const columnDefs: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, flex: 0, width: 40, minWidth: 40, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '사번', field: 'empNo', flex: 0.7, minWidth: 90 },
  { headerName: '이름', field: 'name', flex: 1, minWidth: 90 },
  { headerName: '부서', field: 'department', flex: 1.2, minWidth: 100 },
  { headerName: '직급', field: 'position', flex: 0.5, minWidth: 75 },
  { headerName: '역할', field: 'role', flex: 0.6, minWidth: 80 },
  { headerName: '이메일', field: 'email', flex: 1.5, minWidth: 150 },
  { headerName: '최근 로그인', field: 'lastLogin', flex: 1, minWidth: 130 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 65 },
])

const rowData = ref([
  { empNo: '20210001', name: '관리자', department: '정보화처', position: '처장', role: 'ADMIN', email: 'admin@kwater.or.kr', lastLogin: '2026-03-25 09:00', status: '활성' },
  { empNo: '20210015', name: '김매니저', department: '수자원부', position: '과장', role: 'MANAGER', email: 'manager@kwater.or.kr', lastLogin: '2026-03-25 08:30', status: '활성' },
  { empNo: '20220032', name: '홍길동', department: '수도부', position: '대리', role: 'INTERNAL', email: 'user@kwater.or.kr', lastLogin: '2026-03-24 16:45', status: '활성' },
  { empNo: '20220048', name: '이영희', department: '환경부', position: '사원', role: 'INTERNAL', email: 'lee@kwater.or.kr', lastLogin: '2026-03-24 14:20', status: '활성' },
  { empNo: '20190087', name: '박철수', department: '수자원부', position: '부장', role: 'MANAGER', email: 'park@kwater.or.kr', lastLogin: '2026-03-23 11:10', status: '활성' },
  { empNo: '20230012', name: '정미경', department: '정보화처', position: '사원', role: 'INTERNAL', email: 'jung@kwater.or.kr', lastLogin: '2026-03-22 09:30', status: '비활성' },
])

function resetFilter() {
  filterRole.value = ''
  filterStatus.value = ''
  searchText.value = ''
  loadUsers()
}

async function loadUsers() {
  try {
    const params: Record<string, any> = { user_type: 'INTERNAL' }
    if (selectedOrg.value) params.department_code = selectedOrg.value.code
    if (filterRole.value) params.role = filterRole.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchText.value) params.search = searchText.value

    const res = await adminUserApi.users(params)
    const items = res.data.items
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        empNo: r.employee_no || '',
        name: r.name || '',
        department: r.department_name || '',
        position: r.position || '',
        role: r.role_code || '',
        email: r.email || '',
        lastLogin: r.last_login_at ? String(r.last_login_at).replace('T', ' ').substring(0, 16) : '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'SUSPENDED' ? '정지' : r.status === 'INACTIVE' ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('UserList: API call failed, using mock data', e)
  }
}

onMounted(() => {
  loadUsers()
})

function onRowClick(event: any) {
  detailUser.value = {
    ...event.data,
    activities: [
      { datetime: '2026-03-25 09:00', action: '로그인', target: '사용자포털', ip: '10.10.5.22' },
      { datetime: '2026-03-25 09:05', action: '데이터 조회', target: '댐 수위 관측 데이터', ip: '10.10.5.22' },
      { datetime: '2026-03-25 09:12', action: '다운로드', target: '수질 모니터링 CSV', ip: '10.10.5.22' },
    ],
  }
  showDetail.value = true
}

async function handleRegister() {
  if (!registerForm.value.empNo || !registerForm.value.name || !registerForm.value.email) {
    message.warning('필수 항목을 입력해주세요.')
    return
  }
  try {
    const deptName = flatOrgList.value.find(d => d.code === registerForm.value.deptCode)?.name?.trim() || ''
    await adminUserApi.createUser({
      login_id: registerForm.value.empNo,
      password: 'kwater1234!',
      name: registerForm.value.name,
      email: registerForm.value.email,
      user_type: 'INTERNAL',
      employee_no: registerForm.value.empNo,
      department_code: registerForm.value.deptCode,
      department_name: deptName,
      position: registerForm.value.position,
      role_code: registerForm.value.roleCode,
    })
    message.success('사용자가 등록되었습니다. 초기 비밀번호: kwater1234!')
    showRegister.value = false
    registerForm.value = { empNo: '', name: '', deptCode: '', position: '', email: '', roleCode: 'INTERNAL', phone: '' }
    loadUsers()
  } catch (e: any) {
    message.error('등록에 실패했습니다: ' + (e.response?.data?.detail || e.message))
  }
}

function openEditMode() {
  const raw = detailUser.value._raw
  if (!raw?.id) {
    message.warning('API 데이터가 필요합니다. 목록을 새로고침 후 다시 시도해주세요.')
    return
  }
  const newRole = prompt('역할 변경 (ADMIN, MANAGER, INTERNAL):', detailUser.value.role)
  if (newRole && ['ADMIN', 'MANAGER', 'INTERNAL', 'EXTERNAL'].includes(newRole)) {
    adminUserApi.updateUser(raw.id, { role_code: newRole }).then(() => {
      message.success('역할이 변경되었습니다.')
      showDetail.value = false
      loadUsers()
    }).catch((e: any) => message.error('수정 실패: ' + (e.response?.data?.detail || e.message)))
  }
}

async function handleDeleteUser() {
  const raw = detailUser.value._raw
  if (!raw?.id) return
  if (!confirm(`${detailUser.value.name} 사용자를 삭제하시겠습니까?`)) return
  try {
    await adminUserApi.deleteUser(raw.id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    loadUsers()
  } catch (e: any) {
    message.error('삭제 실패: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleResetPassword() {
  const raw = detailUser.value._raw
  if (!raw?.id) return
  if (!confirm(`${detailUser.value.name}의 비밀번호를 초기화하시겠습니까?`)) return
  try {
    const res = await adminUserApi.resetPassword(raw.id)
    message.success(res.data?.message || '비밀번호가 초기화되었습니다.')
  } catch (e: any) {
    message.error('초기화 실패: ' + (e.response?.data?.detail || e.message))
  }
}
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';

.org-user-layout {
  display: flex;
  gap: 16px;
  min-height: 600px;
}

.org-tree-panel {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  display: flex;
  flex-direction: column;

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #e8e8e8;
    .panel-title { font-weight: 600; font-size: 14px; display: flex; align-items: center; gap: 6px; }
  }

  .tree-search {
    padding: 8px 12px;
    border-bottom: 1px solid #f0f0f0;
    input {
      width: 100%;
      padding: 6px 10px;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      font-size: 13px;
      &:focus { outline: none; border-color: #1890ff; }
    }
  }

  .tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }

  .tree-node {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    cursor: pointer;
    font-size: 13px;
    color: #333;
    transition: background 0.15s;
    &:hover { background: #f5f5f5; }
    &.active { background: #e6f7ff; color: #1890ff; font-weight: 600; }
    &.root { font-weight: 600; font-size: 14px; padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }
    &.level-1 { padding-left: 16px; }
    &.level-2 { padding-left: 42px; font-size: 12.5px; color: #555; }
    .node-count {
      margin-left: auto;
      font-size: 11px;
      color: #999;
      background: #f5f5f5;
      padding: 1px 6px;
      border-radius: 10px;
    }
    .expand-icon { display: inline-flex; width: 14px; font-size: 10px; color: #999; }
  }

  .btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    color: #999;
    font-size: 14px;
    padding: 4px;
    &:hover { color: #1890ff; }
  }
}

.user-list-panel {
  flex: 1;
  min-width: 0;

  .panel-header {
    margin-bottom: 12px;
    .panel-title { font-weight: 600; font-size: 15px; }
  }

  .search-filter.compact {
    margin-bottom: 12px;
    .filter-row { flex-wrap: wrap; }
  }
}

:deep(.ag-row) { cursor: pointer; }

@media (max-width: 1279px) {
  .org-user-layout { flex-direction: column; }
  .org-tree-panel {
    width: 100%;
    min-width: 100%;
    max-height: 300px;
  }
}
</style>
