<template>
  <div class="admin-page">
    <div class="page-header"><h2>원본DB 설정</h2><p class="page-desc">DB 복제 원본 데이터베이스 연결 정보를 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">원본DB <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> DB 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '원본DB')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- DB 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">원본DB 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">DB명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">DBMS</span><span class="info-value">{{ detailData.dbms }}</span></div>
          <div class="modal-info-item"><span class="info-label">호스트</span><span class="info-value">{{ detailData.host }}</span></div>
          <div class="modal-info-item"><span class="info-label">포트</span><span class="info-value">{{ detailData.port }}</span></div>
          <div class="modal-info-item"><span class="info-label">스키마</span><span class="info-value">{{ detailData.schema }}</span></div>
          <div class="modal-info-item"><span class="info-label">연결 상태</span><span class="info-value"><span class="badge" :class="detailData.status === '연결됨' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- DB 등록 팝업 -->
    <AdminModal :visible="showRegister" title="DB 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">DB명</label><input placeholder="DB명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">DBMS</label><select><option>Oracle</option><option>MySQL</option><option>MSSQL</option><option>PostgreSQL</option><option>MongoDB</option></select></div>
          <div class="modal-form-group"><label class="required">포트</label><input placeholder="포트 번호" /></div>
        </div>
        <div class="modal-form-group"><label class="required">호스트</label><input placeholder="호스트 IP" /></div>
        <div class="modal-form-group"><label class="required">스키마</label><input placeholder="스키마명" /></div>
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
  { headerName: 'DB명', field: 'name', flex: 1 },
  { headerName: 'DBMS', field: 'dbms', width: 90 },
  { headerName: '호스트', field: 'host', flex: 1 },
  { headerName: '포트', field: 'port', width: 65 },
  { headerName: '스키마', field: 'schema', width: 100 },
  { headerName: '연결 상태', field: 'status', width: 90 },
]
const rows = ref([
  { name: '수자원관리DB', dbms: 'Oracle', host: '10.10.1.100', port: '1521', schema: 'WATER_MGMT', status: '연결됨' },
  { name: '경영정보DB', dbms: 'MySQL', host: '10.10.2.50', port: '3306', schema: 'BIZ_INFO', status: '연결됨' },
  { name: '환경모니터링DB', dbms: 'MSSQL', host: '10.10.3.30', port: '1433', schema: 'ENV_MONITOR', status: '연결됨' },
  { name: 'IoT센서DB', dbms: 'MongoDB', host: '10.10.4.10', port: '27017', schema: 'iot_sensors', status: '연결됨' },
])

onMounted(async () => {
  try {
    const res = await adminCollectionApi.dataSources()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.source_name || r.name || '',
        dbms: r.source_type || r.db_type || r.dbms || '',
        host: r.connection_host || r.host || '',
        port: r.connection_port ? String(r.connection_port) : (r.port || ''),
        schema: r.connection_db || r.schema || '',
        status: r.last_test_result === 'SUCCESS' ? '연결됨' : r.status === 'ACTIVE' ? '연결됨' : (r.status || '연결됨'),
      }))
    }
  } catch (e) {
    console.warn('DbSource: API call failed, using mock data', e)
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
