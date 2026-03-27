<template>
  <div class="admin-page">
    <div class="page-header"><h2>분류체계 연동</h2><p class="page-desc">데이터관리포털 분류체계와 동기화 현황을 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">연동 현황 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm"><SyncOutlined /> 동기화</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '품질_연동')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 연동 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.category + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">연동 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">분류체계</span><span class="info-value">{{ detailData.category }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터허브 코드</span><span class="info-value">{{ detailData.hubCode }}</span></div>
          <div class="modal-info-item"><span class="info-label">관리포털 코드</span><span class="info-value">{{ detailData.portalCode }}</span></div>
          <div class="modal-info-item"><span class="info-label">동기화 상태</span><span class="info-value"><span class="badge" :class="detailData.status === '일치' ? 'badge-success' : 'badge-danger'">{{ detailData.status }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">최근 동기화</span><span class="info-value">{{ detailData.lastSync }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
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
import { LinkOutlined, CheckCircleOutlined, SyncOutlined, WarningOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { classificationApi } from '../../../api/standard.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: LinkOutlined, label: '연동 항목', value: '48', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '동기화 완료', value: '45', color: '#28A745' },
  { icon: WarningOutlined, label: '불일치', value: '3', color: '#DC3545' },
  { icon: SyncOutlined, label: '최근 동기화', value: '03-25 06:00', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '분류체계', field: 'category', flex: 2 },
  { headerName: '데이터허브 코드', field: 'hubCode', flex: 1 },
  { headerName: '관리포털 코드', field: 'portalCode', flex: 1 },
  { headerName: '동기화 상태', field: 'status', width: 100 },
  { headerName: '최근 동기화', field: 'lastSync', width: 120 },
]
const rows = ref([
  { category: '수자원 > 댐 > 수위', hubCode: 'WR-DAM-LV', portalCode: 'WR-DAM-LV', status: '일치', lastSync: '2026-03-25 06:00' },
  { category: '환경 > 수질 > IoT센서', hubCode: 'EN-WQ-IOT', portalCode: 'EN-WQ-IOT', status: '일치', lastSync: '2026-03-25 06:00' },
  { category: '시설 > 관로 > GIS', hubCode: 'FA-PP-GIS', portalCode: 'FA-PL-GIS', status: '불일치', lastSync: '2026-03-24 06:00' },
])

onMounted(async () => {
  try {
    const res = await classificationApi.getSyncStatus()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items
    }
  } catch (e) {
    console.warn('QualityLink: API call failed, using mock data', e)
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
