<template>
  <div class="admin-page">
    <div class="page-header"><h2>유통 통계</h2><p class="page-desc">데이터 유통 현황 통계 및 리포트를 조회합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">월별 유통 현황</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '유통_통계')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 월별 유통 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.month + ' 유통 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">월별 유통 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">월</span><span class="info-value">{{ detailData.month }}</span></div>
          <div class="modal-info-item"><span class="info-label">유통 건수</span><span class="info-value">{{ detailData.total }}</span></div>
          <div class="modal-info-item"><span class="info-label">다운로드</span><span class="info-value">{{ detailData.downloads }}</span></div>
          <div class="modal-info-item"><span class="info-label">API 호출</span><span class="info-value">{{ detailData.apiCalls }}</span></div>
          <div class="modal-info-item"><span class="info-label">신규 신청</span><span class="info-value">{{ detailData.requests }}건</span></div>
          <div class="modal-info-item"><span class="info-label">승인</span><span class="info-value">{{ detailData.approved }}건</span></div>
          <div class="modal-info-item"><span class="info-label">반려</span><span class="info-value">{{ detailData.rejected }}건</span></div>
          <div class="modal-info-item"><span class="info-label">활성 사용자</span><span class="info-value">{{ detailData.users }}명</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { BarChartOutlined, DownloadOutlined, ApiOutlined, UserOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: BarChartOutlined, label: '월 유통 건수', value: '38,500', color: '#0066CC' },
  { icon: DownloadOutlined, label: '월 다운로드', value: '2,340', color: '#28A745' },
  { icon: ApiOutlined, label: '월 API 호출', value: '1.45M', color: '#9b59b6' },
  { icon: UserOutlined, label: '월 활성 사용자', value: '156', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: '월', field: 'month', width: 90 },
  { headerName: '유통 건수', field: 'total', width: 100 },
  { headerName: '다운로드', field: 'downloads', width: 90 },
  { headerName: 'API 호출', field: 'apiCalls', width: 100 },
  { headerName: '신규 신청', field: 'requests', width: 90 },
  { headerName: '승인', field: 'approved', width: 70 },
  { headerName: '반려', field: 'rejected', width: 70 },
  { headerName: '활성 사용자', field: 'users', width: 90 },
]
const rows = ref([
  { month: '2026-03', total: '38,500', downloads: '2,340', apiCalls: '1,450K', requests: 45, approved: 42, rejected: 3, users: 156 },
  { month: '2026-02', total: '35,200', downloads: '2,100', apiCalls: '1,320K', requests: 38, approved: 36, rejected: 2, users: 142 },
  { month: '2026-01', total: '32,800', downloads: '1,950', apiCalls: '1,180K', requests: 32, approved: 30, rejected: 2, users: 135 },
  { month: '2025-12', total: '28,500', downloads: '1,680', apiCalls: '980K', requests: 28, approved: 27, rejected: 1, users: 128 },
  { month: '2025-11', total: '30,100', downloads: '1,820', apiCalls: '1,050K', requests: 35, approved: 33, rejected: 2, users: 130 },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.stats()
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        month: r.stat_date || r.month || '',
        total: r.view_count != null ? r.view_count.toLocaleString() : (r.total || '-'),
        downloads: r.download_count != null ? r.download_count.toLocaleString() : (r.downloads || '-'),
        apiCalls: r.api_call_count != null ? r.api_call_count.toLocaleString() : (r.apiCalls || '-'),
        requests: r.requests || '-',
        approved: r.approved || '-',
        rejected: r.rejected || '-',
        users: r.unique_users != null ? r.unique_users : (r.users || '-'),
      }))
    }
  } catch (e) {
    console.warn('DistStats: API call failed, using mock data', e)
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
