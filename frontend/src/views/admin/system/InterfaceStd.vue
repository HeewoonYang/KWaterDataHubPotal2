<template>
  <div class="admin-page">
    <div class="page-header"><h2>표준 인터페이스</h2><p class="page-desc">시스템 간 연계 인터페이스 표준 정의 및 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">인터페이스 목록 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '인터페이스_목록')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 인터페이스 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">인터페이스 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">인터페이스명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol }}</span></div>
          <div class="modal-info-item"><span class="info-label">연계 시스템</span><span class="info-value">{{ detailData.target }}</span></div>
          <div class="modal-info-item"><span class="info-label">방향</span><span class="info-value">{{ detailData.direction }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 인터페이스 등록 팝업 -->
    <AdminModal :visible="showRegister" title="인터페이스 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">인터페이스명</label><input placeholder="인터페이스명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">프로토콜</label><select><option>REST</option><option>Kafka</option><option>OAuth2</option><option>WFS/WMS</option><option>gRPC</option></select></div>
          <div class="modal-form-group"><label class="required">방향</label><select><option>양방향</option><option>송신</option><option>수신</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">연계 시스템</label><input placeholder="연계 대상 시스템명" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="3" placeholder="인터페이스 설명"></textarea></div>
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
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '인터페이스명', field: 'name', flex: 2 },
  { headerName: '프로토콜', field: 'protocol', width: 90 },
  { headerName: '연계 시스템', field: 'target', flex: 1 },
  { headerName: '방향', field: 'direction', width: 80 },
  { headerName: '상태', field: 'status', width: 70 },
]
const rows = ref([
  { name: 'OpenMetadata 카탈로그 동기화', protocol: 'REST', target: 'OpenMetadata', direction: '양방향', status: '활성' },
  { name: 'Kafka 이벤트 수신', protocol: 'Kafka', target: 'Kafka Broker', direction: '수신', status: '활성' },
  { name: '오아시스 SSO 인증', protocol: 'OAuth2', target: 'K-water SSO', direction: '송신', status: '활성' },
  { name: '공공데이터포털 연계', protocol: 'REST', target: '공공데이터포털', direction: '송신', status: '활성' },
  { name: 'GIS 공간정보 수집', protocol: 'WFS/WMS', target: 'GIS Server', direction: '수신', status: '점검 중' },
])

onMounted(async () => {
  try {
    const res = await adminSystemApi.interfaces()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.interface_name || r.name || '',
        protocol: r.interface_type || r.protocol || '',
        target: r.target_system || r.source_system || r.target || '',
        direction: r.schedule_type || r.direction || '',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'MAINTENANCE' ? '점검 중' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('InterfaceStd: API call failed, using mock data', e)
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
