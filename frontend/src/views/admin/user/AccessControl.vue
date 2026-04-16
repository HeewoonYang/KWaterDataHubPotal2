<template>
  <div class="admin-page">
    <div class="page-header"><h2>데이터 접근제어</h2><p class="page-desc">데이터 등급별 접근 정책 및 사용자 권한을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">접근 정책 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 정책 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '접근_정책')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :tooltipShowDelay="0" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 정책 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">정책 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">정책명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터 등급</span><span class="info-value">{{ detailData.grade }}</span></div>
          <div class="modal-info-item"><span class="info-label">대상 역할</span><span class="info-value">{{ detailData.roles }}</span></div>
          <div class="modal-info-item"><span class="info-label">접근 유형</span><span class="info-value">{{ detailData.accessType }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge badge-success">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 정책 추가 팝업 -->
    <AdminModal :visible="showRegister" title="접근 정책 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">정책명</label><input placeholder="정책명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">데이터 등급</label><select><option>L1 (비공개)</option><option>L2 (내부)</option><option>L3 (공개)</option></select></div>
          <div class="modal-form-group"><label class="required">접근 유형</label><select><option>읽기</option><option>읽기/쓰기</option><option>비식별화</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">대상 역할</label><input placeholder="대상 역할 (예: ADMIN, MANAGER)" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="정책 설명"></textarea></div>
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
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '정책명', field: 'name', flex: 2 },
  { headerName: '데이터 등급', field: 'grade', flex: 0.8, minWidth: 100 },
  { headerName: '대상 역할', field: 'roles', flex: 1 },
  { headerName: '접근 유형', field: 'accessType', flex: 0.8, minWidth: 110 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 70 },
])
const rows = ref([
  { name: 'L1 비공개 데이터 접근', grade: 'L1 (비공개)', roles: 'ADMIN', accessType: '읽기/쓰기', status: '활성' },
  { name: 'L2 내부공유 데이터', grade: 'L2 (내부)', roles: 'ADMIN, MANAGER, INTERNAL', accessType: '읽기', status: '활성' },
  { name: 'L3 공개 데이터', grade: 'L3 (공개)', roles: '전체', accessType: '읽기', status: '활성' },
  { name: '개인정보 마스킹', grade: 'L1', roles: 'INTERNAL, EXTERNAL', accessType: '비식별화', status: '활성' },
])


onMounted(async () => {
  try {
    const res = await adminUserApi.accessPolicies()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.policy_name || r.name || '',
        grade: r.grade_name || r.grade || '',
        roles: r.role_name || r.roles || '',
        accessType: r.requires_approval ? '승인 필요' : (r.accessType || '읽기'),
        status: r.status || '활성',
      }))
    }
  } catch (e) {
    console.warn('AccessControl: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
function handleRegister() { message.success("등록되었습니다."); showRegister.value = false }
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
