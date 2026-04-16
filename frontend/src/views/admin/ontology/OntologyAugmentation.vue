<template>
  <div class="admin-page">
    <div class="page-header"><h2>온톨로지 메타 증강*</h2><p class="page-desc">수집 데이터의 DDL, 프로시저, 비정형 문서에서 메타데이터를 추출하여 그래프DB를 구축합니다.</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-icon" style="background:#e6f7ff;color:#0066CC"><CodeOutlined /></div><div class="kpi-body"><div class="kpi-value">156</div><div class="kpi-label">DDL 추출</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f6ffed;color:#28A745"><FunctionOutlined /></div><div class="kpi-body"><div class="kpi-value">89</div><div class="kpi-label">프로시저 매핑</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#f9f0ff;color:#9b59b6"><FileTextOutlined /></div><div class="kpi-body"><div class="kpi-value">42</div><div class="kpi-label">문서 인제스트</div></div></div>
      <div class="kpi-card"><div class="kpi-icon" style="background:#fff7e6;color:#fa8c16"><NodeIndexOutlined /></div><div class="kpi-body"><div class="kpi-value">12,450</div><div class="kpi-label">그래프 노드</div></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">전체 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '온톨로지메타증강')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- Graph DB 연결 상태 -->
    <div class="card" style="margin-top:16px;">
      <div class="card-title">Graph DB 연결 상태</div>
      <div class="graph-status">
        <span class="graph-host">Neo4j Cluster (10.0.10.20:7687)</span>
        <span class="status-badge active">연결됨</span>
      </div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.sourceName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">소스 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">소스유형</span><span class="info-value">{{ detailData.sourceType }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스명</span><span class="info-value">{{ detailData.sourceName }}</span></div>
          <div class="modal-info-item"><span class="info-label">원천시스템</span><span class="info-value">{{ detailData.sourceSystem }}</span></div>
          <div class="modal-info-item"><span class="info-label">추출상태</span><span class="info-value">{{ detailData.extractStatus }}</span></div>
          <div class="modal-info-item"><span class="info-label">노드수</span><span class="info-value">{{ detailData.nodeCount }}</span></div>
          <div class="modal-info-item"><span class="info-label">관계수</span><span class="info-value">{{ detailData.relCount }}</span></div>
          <div class="modal-info-item"><span class="info-label">최종처리</span><span class="info-value">{{ detailData.lastProcessed }}</span></div>
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
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { CodeOutlined, FunctionOutlined, FileTextOutlined, NodeIndexOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 45 },
  { headerName: '소스유형', field: 'sourceType', flex: 0.6, minWidth: 75 },
  { headerName: '소스명', field: 'sourceName', flex: 1.2, minWidth: 150 },
  { headerName: '원천시스템', field: 'sourceSystem', flex: 1, minWidth: 120 },
  { headerName: '추출상태', field: 'extractStatus', flex: 0.5, minWidth: 65 },
  { headerName: '노드수', field: 'nodeCount', flex: 0.6, minWidth: 70 },
  { headerName: '관계수', field: 'relCount', flex: 0.6, minWidth: 70 },
  { headerName: '최종처리', field: 'lastProcessed', flex: 0.7, minWidth: 90 },
])
const rows = ref([
  { sourceType: 'DDL', sourceName: '수질DB 테이블 정의', sourceSystem: 'Oracle (수질)', extractStatus: '완료', nodeCount: '2,340', relCount: '4,120', lastProcessed: '2026-04-05' },
  { sourceType: 'DDL', sourceName: '운영통합DB 테이블 정의', sourceSystem: 'Oracle (운영통합)', extractStatus: '완료', nodeCount: '1,890', relCount: '3,450', lastProcessed: '2026-04-05' },
  { sourceType: 'PROCEDURE', sourceName: '자산ERP 업무쿼리', sourceSystem: 'Tibero (자산)', extractStatus: '완료', nodeCount: '3,120', relCount: '5,680', lastProcessed: '2026-04-04' },
  { sourceType: 'PROCEDURE', sourceName: '시설 뷰 테이블 정의', sourceSystem: 'SAP HANA (시설)', extractStatus: '진행중', nodeCount: '890', relCount: '1,200', lastProcessed: '2026-04-06' },
  { sourceType: 'MANUAL', sourceName: '수자원관리 매뉴얼', sourceSystem: '-', extractStatus: '완료', nodeCount: '1,560', relCount: '2,340', lastProcessed: '2026-04-03' },
  { sourceType: 'GUIDELINE', sourceName: '댐 안전관리 지침', sourceSystem: '-', extractStatus: '대기', nodeCount: '0', relCount: '0', lastProcessed: '-' },
])

onMounted(() => {})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { display: flex; align-items: center; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.kpi-body { .kpi-value { font-size: 22px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px; .card-title { font-weight: 700; font-size: 13px; margin-bottom: 10px; } }
.graph-status { display: flex; align-items: center; gap: 12px; font-size: 13px; .graph-host { font-family: monospace; font-size: 12px; color: #555; } }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } }
:deep(.ag-row) { cursor: pointer; }
</style>
