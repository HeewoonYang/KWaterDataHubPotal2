<template>
  <div class="admin-page">
    <div class="page-header"><h2>클라우드 구성</h2><p class="page-desc">클라우드 인프라 리소스 현황 및 구성을 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">클라우드 리소스 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '클라우드_리소스')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 리소스 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">리소스 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">리소스명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">사양</span><span class="info-value">{{ detailData.spec }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge badge-success">{{ detailData.status }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">가용률</span><span class="info-value">{{ detailData.availability }}</span></div>
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
import { CloudOutlined, HddOutlined, ClusterOutlined, ApiOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: CloudOutlined, label: 'VM 인스턴스', value: '12', color: '#0066CC' },
  { icon: HddOutlined, label: '스토리지 (TB)', value: '48', color: '#28A745' },
  { icon: ClusterOutlined, label: 'K8s 노드', value: '8', color: '#9b59b6' },
  { icon: ApiOutlined, label: '네트워크 VPC', value: '3', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '리소스명', field: 'name', flex: 2 },
  { headerName: '유형', field: 'type', width: 100 },
  { headerName: '사양', field: 'spec', flex: 1 },
  { headerName: '상태', field: 'status', width: 80 },
  { headerName: '가용률', field: 'availability', width: 80 },
]
const rows = ref([
  { name: 'datahub-web-01', type: 'VM', spec: '8 vCPU / 32GB RAM', status: '운영 중', availability: '99.9%' },
  { name: 'datahub-web-02', type: 'VM', spec: '8 vCPU / 32GB RAM', status: '운영 중', availability: '99.8%' },
  { name: 'datahub-api-01', type: 'VM', spec: '16 vCPU / 64GB RAM', status: '운영 중', availability: '99.9%' },
  { name: 'datahub-db-master', type: 'VM', spec: '32 vCPU / 128GB RAM', status: '운영 중', availability: '99.99%' },
  { name: 'datahub-k8s-node-01', type: 'K8s', spec: '16 vCPU / 64GB RAM', status: '운영 중', availability: '99.9%' },
  { name: 'datahub-storage-01', type: 'Storage', spec: 'NFS 20TB', status: '운영 중', availability: '99.99%' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.cloud()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.resource_name || r.name || '',
        type: r.resource_type || r.type || '',
        spec: r.resource_id || r.region || r.spec || '',
        status: r.status === 'RUNNING' ? '운영 중' : r.status === 'ACTIVE' ? '운영 중' : (r.status || '-'),
        availability: r.availability || '-',
      }))
    }
  } catch (e) {
    console.warn('CloudConfig: API call failed, using mock data', e)
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
