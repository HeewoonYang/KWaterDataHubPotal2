<template>
  <div class="admin-page">
    <div class="page-header"><h2>외부 사용자</h2><p class="page-desc">외부 기관 사용자 계정을 관리합니다.</p></div>
    <div class="search-filter"><div class="filter-row">
      <div class="filter-group"><label>기관</label><select><option value="">전체</option><option>환경부</option><option>기상청</option><option>국토부</option></select></div>
      <div class="filter-group"><label>상태</label><select><option value="">전체</option><option>활성</option><option>대기</option><option>만료</option></select></div>
      <div class="filter-group search-group"><label>검색</label><input placeholder="이름/기관 검색" /></div>
      <div class="filter-actions"><button class="btn btn-primary btn-sm">조회</button></div>
    </div></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">외부 사용자 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '외부_사용자')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 외부 사용자 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 사용자 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">이름</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">기관</span><span class="info-value">{{ detailData.org }}</span></div>
          <div class="modal-info-item"><span class="info-label">이메일</span><span class="info-value">{{ detailData.email }}</span></div>
          <div class="modal-info-item"><span class="info-label">권한</span><span class="info-value">{{ detailData.role }}</span></div>
          <div class="modal-info-item"><span class="info-label">가입일</span><span class="info-value">{{ detailData.joinDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">만료일</span><span class="info-value">{{ detailData.expireDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : detailData.status === '대기' ? 'badge-warning' : 'badge-muted'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 외부 사용자 등록 팝업 -->
    <AdminModal :visible="showRegister" title="외부 사용자 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">이름</label><input placeholder="이름 입력" /></div>
          <div class="modal-form-group"><label class="required">기관</label><select><option>환경부</option><option>기상청</option><option>국토부</option><option>기타</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">이메일</label><input placeholder="email@example.go.kr" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">권한</label><select><option>외부사용자</option><option>외부관리자</option></select></div>
          <div class="modal-form-group"><label class="required">만료일</label><input type="date" /></div>
        </div>
        <div class="modal-form-group"><label>비고</label><textarea rows="2" placeholder="비고 입력"></textarea></div>
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
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '이름', field: 'name', width: 100 },
  { headerName: '기관', field: 'org', flex: 1 },
  { headerName: '이메일', field: 'email', flex: 1 },
  { headerName: '권한', field: 'role', width: 100 },
  { headerName: '가입일', field: 'joinDate', width: 110 },
  { headerName: '만료일', field: 'expireDate', width: 110 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '이외부', org: '환경부', email: 'lee@me.go.kr', role: '외부사용자', joinDate: '2026-01-15', expireDate: '2026-07-15', status: '활성' },
  { name: '박기상', org: '기상청', email: 'park@kma.go.kr', role: '외부사용자', joinDate: '2026-02-10', expireDate: '2026-08-10', status: '활성' },
  { name: '최국토', org: '국토부', email: 'choi@molit.go.kr', role: '외부사용자', joinDate: '2026-03-01', expireDate: '2026-09-01', status: '대기' },
])

onMounted(async () => {
  try {
    const res = await adminUserApi.users({ user_type: 'EXTERNAL' })
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.name || '',
        org: r.department_name || r.org || '',
        email: r.email || '',
        role: r.role_code || r.role || '외부사용자',
        joinDate: r.joinDate || '-',
        expireDate: r.expireDate || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'PENDING' ? '대기' : r.status === 'EXPIRED' ? '만료' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('ExternalUser: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
