<template>
  <div class="admin-page">
    <div class="page-header"><h2>기관 연계</h2><p class="page-desc">외부 기관 데이터 연계 수집을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">기관 연계 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 연계 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '기관_연계')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 기관 연계 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.org + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">연계 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">기관명</span><span class="info-value">{{ detailData.org }}</span></div>
          <div class="modal-info-item"><span class="info-label">연계 데이터</span><span class="info-value">{{ detailData.data }}</span></div>
          <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol }}</span></div>
          <div class="modal-info-item"><span class="info-label">수집 주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 수집</span><span class="info-value">{{ detailData.lastSync }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 연계 등록 팝업 -->
    <AdminModal :visible="showRegister" title="연계 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">기관명</label><input placeholder="기관명 입력" /></div>
        <div class="modal-form-group"><label class="required">연계 데이터</label><input placeholder="연계 데이터 설명" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">프로토콜</label><select><option>REST API</option><option>SOAP</option><option>SFTP</option></select></div>
          <div class="modal-form-group"><label class="required">수집 주기</label><select><option>실시간</option><option>30분</option><option>1시간</option><option>일 1회</option></select></div>
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
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '기관명', field: 'org', flex: 1 },
  { headerName: '연계 데이터', field: 'data', flex: 2 },
  { headerName: '프로토콜', field: 'protocol', width: 90 },
  { headerName: '수집 주기', field: 'schedule', width: 90 },
  { headerName: '최근 수집', field: 'lastSync', width: 120 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { org: '기상청', data: '강수량/기온 관측 데이터', protocol: 'REST API', schedule: '1시간', lastSync: '2026-03-25 09:00', status: '활성' },
  { org: '환경부', data: '수질 측정 결과', protocol: 'SOAP', schedule: '일 1회', lastSync: '2026-03-25 06:00', status: '활성' },
  { org: '국토부', data: '하천 유량 정보', protocol: 'REST API', schedule: '30분', lastSync: '2026-03-25 09:30', status: '활성' },
  { org: '행안부', data: '재난 안전 데이터', protocol: 'SFTP', schedule: '일 1회', lastSync: '2026-03-25 01:00', status: '점검 중' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.externalAgencies()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        org: r.agency_name || r.org || '',
        data: r.agency_code || r.data || '',
        protocol: r.protocol || '',
        schedule: r.schedule || '-',
        lastSync: r.lastSync || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'MAINTENANCE' ? '점검 중' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('ExternalLink: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
