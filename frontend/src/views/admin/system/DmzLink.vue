<template>
  <div class="admin-page">
    <div class="page-header"><h2>DMZ 연계</h2><p class="page-desc">DMZ/FA망 간 데이터 연계 및 보안 게이트웨이를 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">연계 채널 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'DMZ_연계')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 채널 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">채널 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">채널명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">방향</span><span class="info-value">{{ detailData.direction }}</span></div>
          <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol }}</span></div>
          <div class="modal-info-item"><span class="info-label">보안 등급</span><span class="info-value">{{ detailData.security }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
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
import { SafetyOutlined, SwapOutlined, CheckCircleOutlined, ApiOutlined, FileExcelOutlined, EditOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: SwapOutlined, label: '활성 채널', value: '5', color: '#0066CC' },
  { icon: SafetyOutlined, label: '보안 상태', value: '정상', color: '#28A745' },
  { icon: ApiOutlined, label: '일 전송량', value: '1.2 TB', color: '#9b59b6' },
  { icon: CheckCircleOutlined, label: '성공률', value: '99.8%', color: '#FFC107' },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '채널명', field: 'name', flex: 2 },
  { headerName: '방향', field: 'direction', width: 100 },
  { headerName: '프로토콜', field: 'protocol', width: 90 },
  { headerName: '보안 등급', field: 'security', width: 90 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: 'FA망 → 데이터허브 (실시간)', direction: 'FA → IT', protocol: 'SFTP/TLS', security: '1등급', status: '활성' },
  { name: '데이터허브 → 공공데이터포털', direction: 'IT → 외부', protocol: 'REST/HTTPS', security: '2등급', status: '활성' },
  { name: 'IoT Gateway → 데이터허브', direction: 'OT → IT', protocol: 'MQTT/TLS', security: '1등급', status: '활성' },
  { name: 'GIS 서버 → 데이터허브', direction: 'IT → IT', protocol: 'WFS/HTTPS', security: '2등급', status: '점검 중' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.dmzLinks()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.link_name || r.name || '',
        direction: r.transfer_direction || r.direction || '',
        protocol: r.link_type || r.protocol || '',
        security: r.security || '-',
        status: r.is_active === true ? '활성' : r.is_active === false ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DmzLink: API call failed, using mock data', e)
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
