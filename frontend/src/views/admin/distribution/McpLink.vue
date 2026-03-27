<template>
  <div class="admin-page">
    <div class="page-header"><h2>MCP 연동</h2><p class="page-desc">MCP(Model Context Protocol) 서버 연동 및 AI 데이터 유통을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">MCP 서버 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 서버 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'MCP_서버')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- MCP 서버 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">MCP 서버 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">서버명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">Endpoint</span><span class="info-value">{{ detailData.endpoint }}</span></div>
          <div class="modal-info-item"><span class="info-label">Tool 수</span><span class="info-value">{{ detailData.tools }}개</span></div>
          <div class="modal-info-item"><span class="info-label">연결 상태</span><span class="info-value"><span class="badge" :class="detailData.status === '연결됨' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">최근 호출</span><span class="info-value">{{ detailData.lastCall }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 서버 등록 팝업 -->
    <AdminModal :visible="showRegister" title="서버 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">서버명</label><input placeholder="MCP 서버명 입력" /></div>
        <div class="modal-form-group"><label class="required">Endpoint</label><input placeholder="http://mcp.example.com" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="서버 설명"></textarea></div>
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
import { adminDistributionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { sortable: true, resizable: true, flex: 1, minWidth: 80 }
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '서버명', field: 'name', flex: 2 },
  { headerName: 'Endpoint', field: 'endpoint', flex: 2 },
  { headerName: 'Tool 수', field: 'tools', width: 75 },
  { headerName: '연결 상태', field: 'status', width: 90 },
  { headerName: '최근 호출', field: 'lastCall', width: 120 },
]
const rows = ref([
  { name: '데이터허브 MCP Server', endpoint: 'http://mcp.datahub.kwater.or.kr', tools: 12, status: '연결됨', lastCall: '2026-03-25 09:30' },
  { name: '수질분석 MCP Server', endpoint: 'http://mcp-wq.datahub.kwater.or.kr', tools: 5, status: '연결됨', lastCall: '2026-03-25 09:15' },
  { name: 'GIS MCP Server', endpoint: 'http://mcp-gis.datahub.kwater.or.kr', tools: 3, status: '점검 중', lastCall: '2026-03-24 18:00' },
])

onMounted(async () => {
  try {
    const res = await adminDistributionApi.mcpConfigs()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.mcp_name || r.name || '',
        endpoint: r.server_url || r.endpoint || '',
        tools: r.tools || '-',
        status: r.status === 'ACTIVE' ? '연결됨' : r.status === 'MAINTENANCE' ? '점검 중' : (r.status || '-'),
        lastCall: r.lastCall || '-',
      }))
    }
  } catch (e) {
    console.warn('McpLink: API call failed, using mock data', e)
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
