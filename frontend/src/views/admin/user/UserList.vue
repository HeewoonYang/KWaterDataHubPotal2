<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>내부 사용자 관리</h2>
      <p class="page-desc">K-water 내부 사용자 계정을 조회하고 관리합니다.</p>
    </div>

    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>부서</label><select v-model="filterDept"><option value="">전체</option><option value="water">수자원부</option><option value="supply">수도부</option><option value="env">환경부</option><option value="it">정보화처</option></select></div>
        <div class="filter-group"><label>역할</label><select v-model="filterRole"><option value="">전체</option><option value="ADMIN">관리자</option><option value="MANAGER">매니저</option><option value="INTERNAL">일반</option></select></div>
        <div class="filter-group"><label>상태</label><select v-model="filterStatus"><option value="">전체</option><option value="active">활성</option><option value="inactive">비활성</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input type="text" v-model="searchText" placeholder="이름, 사번 검색" /></div>
        <div class="filter-actions"><button class="btn btn-primary"><SearchOutlined /> 조회</button><button class="btn btn-outline"><ReloadOutlined /> 초기화</button></div>
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
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="columnDefs" :defaultColDef="defaultColDef" :pagination="true" :paginationPageSize="10" :rowSelection="'multiple'" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 사용자 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailUser.name + ' 사용자 상세'" size="lg" @close="showDetail = false">
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">총 로그인</div><div class="stat-number">{{ detailUser.loginCount || 245 }}</div></div>
        <div class="modal-stat-card success"><div class="stat-title">데이터 조회</div><div class="stat-number">{{ detailUser.queryCount || 1280 }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">다운로드</div><div class="stat-number">{{ detailUser.downloadCount || 35 }}</div></div>
        <div class="modal-stat-card info"><div class="stat-title">API 호출</div><div class="stat-number">{{ detailUser.apiCount || 4500 }}</div></div>
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
          <div class="modal-info-item"><span class="info-label">최근 로그인</span><span class="info-value">{{ detailUser.lastLogin }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailUser.status === '활성' ? 'badge-success' : 'badge-muted'">{{ detailUser.status }}</span></span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">최근 활동 이력</div>
        <table class="modal-table">
          <thead><tr><th>번호</th><th>일시</th><th>활동</th><th>대상</th><th>IP</th></tr></thead>
          <tbody>
            <tr><td class="text-center">1</td><td>2026-03-25 09:00</td><td>로그인</td><td>사용자포털</td><td>10.10.5.22</td></tr>
            <tr><td class="text-center">2</td><td>2026-03-25 09:05</td><td>데이터 조회</td><td>댐 수위 관측 데이터</td><td>10.10.5.22</td></tr>
            <tr><td class="text-center">3</td><td>2026-03-25 09:12</td><td>다운로드</td><td>수질 모니터링 CSV</td><td>10.10.5.22</td></tr>
            <tr><td class="text-center">4</td><td>2026-03-24 16:45</td><td>로그아웃</td><td>사용자포털</td><td>10.10.5.22</td></tr>
            <tr><td class="text-center">5</td><td>2026-03-24 14:30</td><td>API 호출</td><td>/api/v1/datasets</td><td>10.10.5.22</td></tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 사용자 등록 팝업 -->
    <AdminModal :visible="showRegister" title="내부 사용자 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">사번</label><input placeholder="사번 입력" /></div>
          <div class="modal-form-group"><label class="required">이름</label><input placeholder="이름 입력" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">부서</label><select><option>수자원부</option><option>수도부</option><option>환경부</option><option>정보화처</option></select></div>
          <div class="modal-form-group"><label class="required">직급</label><select><option>사원</option><option>대리</option><option>과장</option><option>부장</option><option>처장</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">이메일</label><input placeholder="email@kwater.or.kr" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">역할</label><select><option>INTERNAL (일반)</option><option>MANAGER (매니저)</option><option>ADMIN (관리자)</option></select></div>
          <div class="modal-form-group"><label>전화번호</label><input placeholder="전화번호" /></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { SearchOutlined, ReloadOutlined, PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const filterDept = ref(''), filterRole = ref(''), filterStatus = ref(''), searchText = ref('')
const showDetail = ref(false), showRegister = ref(false)
const detailUser = ref<any>({})

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const columnDefs: ColDef[] = [
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, maxWidth: 40, flex: 0, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '사번', field: 'empNo', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '이름', field: 'name', flex: 1, minWidth: 100 },
  { headerName: '부서', field: 'department', flex: 1, minWidth: 100 },
  { headerName: '직급', field: 'position', width: 80, maxWidth: 80, flex: 0 },
  { headerName: '역할', field: 'role', width: 80, maxWidth: 80, flex: 0 },
  { headerName: '이메일', field: 'email', flex: 1.5, minWidth: 160 },
  { headerName: '최근 로그인', field: 'lastLogin', flex: 1, minWidth: 130 },
  { headerName: '상태', field: 'status', width: 65, maxWidth: 65, flex: 0 },
]
const rowData = ref([
  { empNo: '20210001', name: '관리자', department: '정보화처', position: '처장', role: 'ADMIN', email: 'admin@kwater.or.kr', lastLogin: '2026-03-25 09:00', status: '활성' },
  { empNo: '20210015', name: '김매니저', department: '수자원부', position: '과장', role: 'MANAGER', email: 'manager@kwater.or.kr', lastLogin: '2026-03-25 08:30', status: '활성' },
  { empNo: '20220032', name: '홍길동', department: '수도부', position: '대리', role: 'INTERNAL', email: 'user@kwater.or.kr', lastLogin: '2026-03-24 16:45', status: '활성' },
  { empNo: '20220048', name: '이영희', department: '환경부', position: '사원', role: 'INTERNAL', email: 'lee@kwater.or.kr', lastLogin: '2026-03-24 14:20', status: '활성' },
  { empNo: '20190087', name: '박철수', department: '수자원부', position: '부장', role: 'MANAGER', email: 'park@kwater.or.kr', lastLogin: '2026-03-23 11:10', status: '활성' },
  { empNo: '20230012', name: '정미경', department: '정보화처', position: '사원', role: 'INTERNAL', email: 'jung@kwater.or.kr', lastLogin: '2026-03-22 09:30', status: '비활성' },
])

onMounted(async () => {
  try {
    const res = await adminUserApi.users()
    const items = res.data.items
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        empNo: r.employee_no || r.empNo || '',
        name: r.name || '',
        department: r.department_name || r.department || '',
        position: r.position || '',
        role: r.role_code || r.role || '',
        email: r.email || '',
        lastLogin: r.last_login_at ? String(r.last_login_at).replace('T', ' ').substring(0, 16) : (r.lastLogin || '-'),
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'INACTIVE' ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('UserList: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailUser.value = event.data
  showDetail.value = true
}
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
