<template>
  <div class="admin-page">
    <div class="page-header"><h2>역할 관리</h2><p class="page-desc">사용자 역할과 권한 매핑을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">역할 목록 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 역할 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '역할_목록')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 역할 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">역할 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">역할명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">코드</span><span class="info-value">{{ detailData.code }}</span></div>
          <div class="modal-info-item"><span class="info-label">설명</span><span class="info-value">{{ detailData.desc }}</span></div>
          <div class="modal-info-item"><span class="info-label">사용자 수</span><span class="info-value">{{ detailData.userCount }}명</span></div>
          <div class="modal-info-item"><span class="info-label">관리자 포털</span><span class="info-value">{{ detailData.adminAccess }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge badge-success">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 역할 추가 팝업 -->
    <AdminModal :visible="showRegister" title="역할 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">역할명</label><input placeholder="역할명 입력" /></div>
          <div class="modal-form-group"><label class="required">코드</label><input placeholder="역할 코드 (예: ADMIN)" /></div>
        </div>
        <div class="modal-form-group"><label class="required">설명</label><textarea rows="2" placeholder="역할 설명 입력"></textarea></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">관리자 포털 접근</label><select><option>전체</option><option>부분</option><option>없음</option></select></div>
          <div class="modal-form-group"><label>상태</label><select><option>활성</option><option>비활성</option></select></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 추가</button>
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
  { headerName: '역할명', field: 'name', flex: 1 },
  { headerName: '코드', field: 'code', width: 100 },
  { headerName: '설명', field: 'desc', flex: 2 },
  { headerName: '사용자 수', field: 'userCount', width: 90 },
  { headerName: '관리자 포털', field: 'adminAccess', width: 100 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: '시스템 관리자', code: 'ADMIN', desc: '모든 메뉴 접근 가능, 시스템 전체 관리', userCount: 3, adminAccess: '전체', status: '활성' },
  { name: '데이터 관리자', code: 'MANAGER', desc: '데이터 관련 메뉴 관리, 사용자 관리 제외', userCount: 8, adminAccess: '부분', status: '활성' },
  { name: '내부 사용자', code: 'INTERNAL', desc: '사용자 포털 전체 이용', userCount: 245, adminAccess: '없음', status: '활성' },
  { name: '외부 사용자', code: 'EXTERNAL', desc: '카탈로그 조회, 유통 데이터 신청', userCount: 52, adminAccess: '없음', status: '활성' },
])

onMounted(async () => {
  try {
    const res = await adminUserApi.roles()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.role_name || r.name || '',
        code: r.role_code || r.code || '',
        desc: r.description || r.desc || '',
        userCount: r.user_count != null ? r.user_count : (r.userCount || 0),
        adminAccess: r.can_access_admin === true ? '전체' : r.can_access_admin === false ? '없음' : (r.adminAccess || '없음'),
        status: r.status || '활성',
      }))
    }
  } catch (e) {
    console.warn('RoleManage: API call failed, using mock data', e)
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
