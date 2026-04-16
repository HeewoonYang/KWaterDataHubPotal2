<template>
  <div class="admin-page">
    <div class="page-header"><h2>도메인 수집현황*</h2><p class="page-desc">원천 DB의 전체 테이블에서 수집 대상 테이블/컬럼을 선택하고 관리합니다.</p></div>

    <!-- 도메인/DB 선택 -->
    <div class="domain-selector">
      <div class="selector-row">
        <div class="selector-group">
          <label>도메인 선택</label>
          <select v-model="selectedDomain" @change="onDomainChange">
            <option v-for="d in domainList" :key="d.key" :value="d.key">{{ d.label }}</option>
          </select>
        </div>
        <div class="domain-meta" v-if="currentDomain">
          <span class="meta-item"><DatabaseOutlined /> {{ currentDomain.dbms }}</span>
          <span class="meta-item"><LinkOutlined /> {{ currentDomain.host }}</span>
          <span class="meta-item"><TableOutlined /> {{ currentDomain.schema }}</span>
        </div>
      </div>
      <div class="domain-summary" v-if="currentDomain">
        <div class="summary-chips">
          <span class="chip chip-total"><TableOutlined /> 총 테이블 <strong>{{ currentDomain.totalTables }}</strong></span>
          <span class="chip chip-collect"><CheckCircleOutlined /> 수집 <strong>{{ collectedTables.length }}</strong></span>
          <span class="chip chip-exclude"><StopOutlined /> 미수집 <strong>{{ excludedTables.length }}</strong></span>
        </div>
      </div>
    </div>

    <!-- 수집 대상 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count section-title collected"><CheckCircleOutlined /> 수집 대상 테이블 <strong>{{ collectedTables.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(collectCols, collectedTables, '수집_테이블')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="collectedTables" :columnDefs="collectCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="15" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onCollectedRowClick" :getRowStyle="getCollectedRowStyle" :rowSelection="'multiple'" @grid-ready="(p: any) => collectGridApi = p.api" /></div>
    </div>

    <!-- 이동 화살표 + 저장 -->
    <div class="transfer-bar">
      <button class="btn btn-sm btn-outline transfer-btn" title="선택 테이블을 미수집으로 이동" @click="moveToExcluded"><DownOutlined /> 수집 제외</button>
      <button class="btn btn-sm btn-primary transfer-btn" title="선택 테이블을 수집으로 이동" @click="moveToCollected"><UpOutlined /> 수집 추가</button>
      <div style="flex:1"></div>
      <button class="btn btn-sm btn-success" :class="{ 'btn-pulse': configChanged }" @click="saveAllConfig"><SaveOutlined /> 설정 저장{{ configChanged ? ' *' : '' }}</button>
    </div>

    <!-- 미수집 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count section-title excluded"><StopOutlined /> 미수집 테이블 <strong>{{ excludedTables.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(excludeCols, excludedTables, '미수집_테이블')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="excludedTables" :columnDefs="excludeCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onExcludedRowClick" :getRowStyle="getExcludedRowStyle" :rowSelection="'multiple'" @grid-ready="(p: any) => excludeGridApi = p.api" /></div>
    </div>

    <!-- 컬럼 수집여부 설정 팝업 -->
    <AdminModal :visible="showColumnModal" :title="selectedTable?.tableName + ' 컬럼 수집 설정'" size="lg" @close="showColumnModal = false">
      <div class="column-modal-header">
        <div class="column-modal-info">
          <span class="badge" :class="selectedTable?._isCollected ? 'badge-success' : 'badge-muted'">{{ selectedTable?._isCollected ? '수집중' : '미수집' }}</span>
          <span style="font-size:12px;color:#666;">전체 {{ selectedColumns.length }}개 컬럼 / 수집 <strong style="color:#28A745">{{ selectedColumns.filter((c: any) => c.isCollected).length }}</strong>개 / 제외 <strong style="color:#DC3545">{{ selectedColumns.filter((c: any) => !c.isCollected).length }}</strong>개</span>
        </div>
        <div class="column-modal-actions">
          <button class="btn btn-xs btn-outline" @click="selectAllCols(true)"><CheckSquareOutlined /> 전체선택</button>
          <button class="btn btn-xs btn-outline" @click="selectAllCols(false)"><BorderOutlined /> 전체해제</button>
        </div>
      </div>
      <div class="ag-grid-wrapper" style="margin-top:10px;"><AgGridVue class="ag-theme-alpine" :rowData="selectedColumns" :columnDefs="columnCols" :defaultColDef="defCol" :pagination="false" domLayout="autoHeight" :tooltipShowDelay="0" /></div>
      <template #footer>
        <button class="btn btn-primary" @click="saveColumnConfig"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="showColumnModal = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 수집추가/제외 확인 모달 -->
    <AdminModal :visible="showActionModal" :title="actionModalTitle" size="sm" @close="showActionModal = false">
      <p style="font-size:13px;white-space:pre-line;line-height:1.8;">{{ actionModalMsg }}</p>
      <template #footer>
        <button class="btn btn-primary" @click="confirmAction"><CheckOutlined /> 확인</button>
        <button class="btn btn-outline" @click="showActionModal = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  DatabaseOutlined, LinkOutlined, TableOutlined, CheckCircleOutlined, StopOutlined,
  FileExcelOutlined, CheckSquareOutlined, BorderOutlined,
  SaveOutlined, CheckOutlined, DownOutlined, UpOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const route = useRoute()
const defCol = { ...baseDefaultColDef }

// ===== 도메인 선택 =====
const domainList = [
  { key: '시설', label: '시설 (SAP HANA)' },
  { key: '자산', label: '자산 (Tibero)' },
  { key: '운영통합', label: '운영통합 (Oracle)' },
  { key: '수질통합', label: '수질통합 (Oracle)' },
  { key: '관망', label: '관망 (Oracle)' },
]
const selectedDomain = ref('시설')
const selectedTable = ref<any>(null)
const showColumnModal = ref(false)
const showActionModal = ref(false)
const actionModalTitle = ref('')
const actionModalMsg = ref('')
const pendingAction = ref<any>(null)

// ===== 도메인 메타 정보 =====
interface DomainMeta {
  dbms: string; host: string; schema: string; totalTables: number; note: string
  tables: TableInfo[]
}
interface TableInfo {
  tableName: string; description: string; totalCols: number; collectCols?: number
  rowCount: string; lastCollected?: string; isCollected: boolean
  excludeReason?: string; columns: ColumnInfo[]
}
interface ColumnInfo {
  colName: string; dataType: string; description: string
  nullable: string; isPk: string; isCollected: boolean
}

const domainData: Record<string, DomainMeta> = {
  '수질통합': {
    dbms: 'Oracle 19c', host: '10.10.1.100:1521', schema: 'WATER_QUALITY', totalTables: 28,
    note: '수질통합 고유업무만 수집. 계측DB·운영통합DB와의 조인 테이블은 제외하여 순수 수질 데이터만 PG에 적재',
    tables: [
      { tableName: 'WQ_MEASURE_DATA', description: '수질 측정 데이터 (원본)', totalCols: 18, collectCols: 16, rowCount: '1,245,000', lastCollected: '2026-04-07 05:12', isCollected: true, columns: [
        { colName: 'MEASURE_ID', dataType: 'NUMBER(12)', description: '측정 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'SITE_ID', dataType: 'VARCHAR2(20)', description: '측정소 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'MEASURE_DT', dataType: 'DATE', description: '측정 일시', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'PH_VALUE', dataType: 'NUMBER(5,2)', description: 'pH 수치', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'DO_VALUE', dataType: 'NUMBER(5,2)', description: '용존산소(DO)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'BOD_VALUE', dataType: 'NUMBER(5,2)', description: '생물화학적산소요구량(BOD)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'COD_VALUE', dataType: 'NUMBER(5,2)', description: '화학적산소요구량(COD)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'SS_VALUE', dataType: 'NUMBER(5,2)', description: '부유물질(SS)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'TN_VALUE', dataType: 'NUMBER(5,2)', description: '총질소(TN)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'TP_VALUE', dataType: 'NUMBER(5,2)', description: '총인(TP)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'TEMP_VALUE', dataType: 'NUMBER(4,1)', description: '수온', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'TURBIDITY', dataType: 'NUMBER(6,2)', description: '탁도', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'CONDUCTIVITY', dataType: 'NUMBER(6,2)', description: '전기전도도', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'CHLOROPHYLL', dataType: 'NUMBER(5,2)', description: '클로로필-a', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'MEASURE_METHOD', dataType: 'VARCHAR2(10)', description: '측정방법 코드', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'QUALITY_FLAG', dataType: 'CHAR(1)', description: '품질 플래그', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'ETL_BATCH_ID', dataType: 'NUMBER(10)', description: 'ETL 배치 ID (내부용)', nullable: 'Y', isPk: 'N', isCollected: false },
        { colName: 'SYS_UPDATE_DT', dataType: 'DATE', description: '시스템 수정일 (내부용)', nullable: 'Y', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_SITE_INFO', description: '수질 측정소 기본정보', totalCols: 14, collectCols: 14, rowCount: '3,200', lastCollected: '2026-04-07 05:12', isCollected: true, columns: [
        { colName: 'SITE_ID', dataType: 'VARCHAR2(20)', description: '측정소 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'SITE_NAME', dataType: 'VARCHAR2(100)', description: '측정소명', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'REGION_CODE', dataType: 'VARCHAR2(10)', description: '지역코드', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'LATITUDE', dataType: 'NUMBER(10,7)', description: '위도', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'LONGITUDE', dataType: 'NUMBER(10,7)', description: '경도', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'WQ_STANDARD', description: '수질 환경 기준치 정의', totalCols: 12, collectCols: 12, rowCount: '850', lastCollected: '2026-04-01 05:00', isCollected: true, columns: [
        { colName: 'STD_ID', dataType: 'NUMBER(6)', description: '기준 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'ITEM_CODE', dataType: 'VARCHAR2(10)', description: '항목코드', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'STD_GRADE', dataType: 'VARCHAR2(5)', description: '등급 (Ia~VI)', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'MIN_VALUE', dataType: 'NUMBER(8,2)', description: '하한값', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'MAX_VALUE', dataType: 'NUMBER(8,2)', description: '상한값', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'WQ_ALERT_LOG', description: '수질 이상 알림 이력', totalCols: 10, collectCols: 10, rowCount: '12,400', lastCollected: '2026-04-07 05:12', isCollected: true, columns: [
        { colName: 'ALERT_ID', dataType: 'NUMBER(12)', description: '알림 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'SITE_ID', dataType: 'VARCHAR2(20)', description: '측정소 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ALERT_TYPE', dataType: 'VARCHAR2(20)', description: '알림 유형', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ALERT_DT', dataType: 'DATE', description: '발생일시', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'WQ_SAMPLE_RESULT', description: '시료 채취 분석 결과', totalCols: 22, collectCols: 20, rowCount: '456,000', lastCollected: '2026-04-07 05:12', isCollected: true, columns: [
        { colName: 'SAMPLE_ID', dataType: 'NUMBER(12)', description: '시료 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'SITE_ID', dataType: 'VARCHAR2(20)', description: '측정소 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'SAMPLE_DT', dataType: 'DATE', description: '채취일시', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ANALYSIS_RESULT', dataType: 'CLOB', description: '분석결과 JSON', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'WQ_INSPECTOR', description: '수질 검사원 정보', totalCols: 8, collectCols: 8, rowCount: '280', lastCollected: '2026-04-01 05:00', isCollected: true, columns: [
        { colName: 'INSPECTOR_ID', dataType: 'VARCHAR2(10)', description: '검사원 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'INSPECTOR_NAME', dataType: 'VARCHAR2(50)', description: '검사원명', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'DEPT_CODE', dataType: 'VARCHAR2(10)', description: '부서코드', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'WQ_PROCESS_LOG', description: '정수 처리 공정 이력', totalCols: 16, collectCols: 14, rowCount: '890,000', lastCollected: '2026-04-07 05:12', isCollected: true, columns: [
        { colName: 'LOG_ID', dataType: 'NUMBER(12)', description: '로그 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PLANT_ID', dataType: 'VARCHAR2(10)', description: '정수장 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'PROCESS_DT', dataType: 'DATE', description: '처리일시', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'CHLORINE_DOSAGE', dataType: 'NUMBER(6,3)', description: '염소 투입량', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      // 미수집 테이블 (조인/중복)
      { tableName: 'WQ_RT_SENSOR_LINK', description: '실시간 센서 연동 테이블 (계측DB 조인)', totalCols: 8, rowCount: '-', isCollected: false, excludeReason: '계측DB 조인 테이블', columns: [
        { colName: 'SENSOR_ID', dataType: 'VARCHAR2(20)', description: '센서 ID', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'RT_MEASURE_ID', dataType: 'NUMBER(12)', description: '실시간 측정 ID (계측DB FK)', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_OPS_FACILITY_MAP', description: '운영통합 시설 매핑 (운영통합DB 조인)', totalCols: 6, rowCount: '-', isCollected: false, excludeReason: '운영통합DB 중복', columns: [
        { colName: 'WQ_SITE_ID', dataType: 'VARCHAR2(20)', description: '수질 측정소 ID', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'OPS_FACILITY_ID', dataType: 'VARCHAR2(20)', description: '운영통합 시설 ID (FK)', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_PIPE_QUALITY_JOIN', description: '관망 수질 연계 (관망DB 조인)', totalCols: 10, rowCount: '-', isCollected: false, excludeReason: '관망DB 조인 테이블', columns: [
        { colName: 'PIPE_ID', dataType: 'VARCHAR2(20)', description: '관망 ID (관망DB FK)', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'QUALITY_POINT_ID', dataType: 'VARCHAR2(20)', description: '수질 포인트 ID', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_HDAPS_RESERVOIR', description: '수력발전 저수지 수질 연계 (HDAPS 조인)', totalCols: 8, rowCount: '-', isCollected: false, excludeReason: '계측DB(HDAPS) 조인', columns: [
        { colName: 'RESERVOIR_ID', dataType: 'VARCHAR2(10)', description: '저수지 ID (HDAPS FK)', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'WQ_GRADE', dataType: 'VARCHAR2(5)', description: '수질 등급', nullable: 'Y', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_ERP_BUDGET_LINK', description: '자산ERP 예산 연계 (ERP DB 조인)', totalCols: 6, rowCount: '-', isCollected: false, excludeReason: '자산ERP 조인 테이블', columns: [
        { colName: 'BUDGET_ID', dataType: 'VARCHAR2(20)', description: '예산항목 ID (ERP FK)', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'WQ_PROJECT_ID', dataType: 'VARCHAR2(20)', description: '수질 사업 ID', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_GIOS_GROUND_LINK', description: '지하수 수질 연계 (GIOS 조인)', totalCols: 7, rowCount: '-', isCollected: false, excludeReason: '계측DB(GIOS) 조인', columns: [
        { colName: 'GROUND_WELL_ID', dataType: 'VARCHAR2(20)', description: '관정 ID (GIOS FK)', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'WQ_SAMPLE_ID', dataType: 'NUMBER(12)', description: '수질 시료 ID', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_ETL_WORK_LOG', description: 'ETL 작업 로그 (내부 관리용)', totalCols: 12, rowCount: '-', isCollected: false, excludeReason: '내부 ETL 관리 테이블', columns: [
        { colName: 'WORK_ID', dataType: 'NUMBER(12)', description: '작업 ID', nullable: 'N', isPk: 'Y', isCollected: false },
        { colName: 'BATCH_DT', dataType: 'DATE', description: '배치 일시', nullable: 'N', isPk: 'N', isCollected: false },
      ]},
      { tableName: 'WQ_TEMP_STAGING', description: '임시 스테이징 테이블', totalCols: 20, rowCount: '-', isCollected: false, excludeReason: '임시 테이블', columns: [
        { colName: 'STAGING_ID', dataType: 'NUMBER(12)', description: '스테이징 ID', nullable: 'N', isPk: 'Y', isCollected: false },
      ]},
    ],
  },
  '운영통합': {
    dbms: 'Oracle 19c', host: '10.10.1.110:1521', schema: 'OPS_INTG', totalTables: 22,
    note: '운영통합 고유업무만 수집. 수질/관망/계측DB와의 조인 테이블은 제외',
    tables: [
      { tableName: 'OPS_FACILITY_STATUS', description: '시설 운영 현황', totalCols: 20, collectCols: 18, rowCount: '856,000', lastCollected: '2026-04-07 04:35', isCollected: true, columns: [
        { colName: 'FACILITY_ID', dataType: 'VARCHAR2(20)', description: '시설 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'FACILITY_NAME', dataType: 'VARCHAR2(100)', description: '시설명', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'OP_STATUS', dataType: 'VARCHAR2(10)', description: '운영상태', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'OP_DATE', dataType: 'DATE', description: '운영일', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'OPS_ALARM_HISTORY', description: '운영 알람 이력', totalCols: 14, collectCols: 14, rowCount: '234,000', lastCollected: '2026-04-07 04:35', isCollected: true, columns: [
        { colName: 'ALARM_ID', dataType: 'NUMBER(12)', description: '알람 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'FACILITY_ID', dataType: 'VARCHAR2(20)', description: '시설 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ALARM_DT', dataType: 'DATE', description: '발생일시', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ALARM_TYPE', dataType: 'VARCHAR2(20)', description: '알람 유형', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'OPS_MAINTENANCE', description: '유지보수 이력', totalCols: 16, collectCols: 16, rowCount: '45,600', lastCollected: '2026-04-06 04:30', isCollected: true, columns: [
        { colName: 'MAINT_ID', dataType: 'NUMBER(12)', description: '유지보수 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'FACILITY_ID', dataType: 'VARCHAR2(20)', description: '시설 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'MAINT_TYPE', dataType: 'VARCHAR2(20)', description: '유지보수 유형', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'OPS_DAILY_REPORT', description: '일일 운영보고', totalCols: 18, collectCols: 16, rowCount: '128,000', lastCollected: '2026-04-07 04:35', isCollected: true, columns: [
        { colName: 'REPORT_ID', dataType: 'NUMBER(12)', description: '보고 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'REPORT_DT', dataType: 'DATE', description: '보고일', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'OPS_ENERGY_USAGE', description: '에너지 사용량', totalCols: 12, collectCols: 12, rowCount: '365,000', lastCollected: '2026-04-07 04:35', isCollected: true, columns: [
        { colName: 'USAGE_ID', dataType: 'NUMBER(12)', description: '사용량 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'FACILITY_ID', dataType: 'VARCHAR2(20)', description: '시설 ID', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      // 미수집
      { tableName: 'OPS_WQ_JOINT_VIEW', description: '수질 연동 뷰 (수질DB 조인)', totalCols: 12, rowCount: '-', isCollected: false, excludeReason: '수질DB 조인 테이블', columns: [] },
      { tableName: 'OPS_RT_SENSOR_MAP', description: '실시간 센서 매핑 (계측DB 조인)', totalCols: 8, rowCount: '-', isCollected: false, excludeReason: '계측DB 조인 테이블', columns: [] },
      { tableName: 'OPS_PIPE_STATUS_LINK', description: '관망 상태 연동 (관망DB 조인)', totalCols: 10, rowCount: '-', isCollected: false, excludeReason: '관망DB 조인 테이블', columns: [] },
      { tableName: 'OPS_ETL_LOG', description: 'ETL 처리 로그', totalCols: 8, rowCount: '-', isCollected: false, excludeReason: '내부 ETL 관리 테이블', columns: [] },
    ],
  },
  '관망': {
    dbms: 'Oracle 19c', host: '10.10.1.120:1521', schema: 'PIPE_NET', totalTables: 18,
    note: '관망 고유업무만 수집. 수질/운영통합/계측DB와의 조인 테이블은 제외',
    tables: [
      { tableName: 'PIPE_NETWORK', description: '관망 네트워크 정보', totalCols: 24, collectCols: 22, rowCount: '128,000', lastCollected: '2026-04-07 03:15', isCollected: true, columns: [
        { colName: 'PIPE_ID', dataType: 'VARCHAR2(20)', description: '관망 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PIPE_TYPE', dataType: 'VARCHAR2(10)', description: '관종', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'DIAMETER', dataType: 'NUMBER(6)', description: '구경(mm)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'LENGTH_M', dataType: 'NUMBER(8,2)', description: '연장(m)', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'INSTALL_DT', dataType: 'DATE', description: '매설일', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'PIPE_PRESSURE', description: '관압 측정 데이터', totalCols: 10, collectCols: 10, rowCount: '2,340,000', lastCollected: '2026-04-07 03:15', isCollected: true, columns: [
        { colName: 'PRESS_ID', dataType: 'NUMBER(12)', description: '측정 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PIPE_ID', dataType: 'VARCHAR2(20)', description: '관망 ID', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'PRESSURE_VAL', dataType: 'NUMBER(6,2)', description: '관압(kgf/cm2)', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'PIPE_LEAK_LOG', description: '누수 탐지 이력', totalCols: 14, collectCols: 14, rowCount: '8,900', lastCollected: '2026-04-06 03:10', isCollected: true, columns: [
        { colName: 'LEAK_ID', dataType: 'NUMBER(12)', description: '누수 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PIPE_ID', dataType: 'VARCHAR2(20)', description: '관망 ID', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'PIPE_GIS_DATA', description: '관망 GIS 공간정보', totalCols: 8, collectCols: 8, rowCount: '128,000', lastCollected: '2026-04-07 03:15', isCollected: true, columns: [
        { colName: 'PIPE_ID', dataType: 'VARCHAR2(20)', description: '관망 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'GEOM', dataType: 'SDO_GEOMETRY', description: '공간정보', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      // 미수집
      { tableName: 'PIPE_WQ_SAMPLING', description: '관망 수질 샘플링 (수질DB 조인)', totalCols: 10, rowCount: '-', isCollected: false, excludeReason: '수질DB 조인 테이블', columns: [] },
      { tableName: 'PIPE_OPS_REPAIR', description: '운영통합 보수 연동 (운영통합DB 조인)', totalCols: 8, rowCount: '-', isCollected: false, excludeReason: '운영통합DB 조인 테이블', columns: [] },
      { tableName: 'PIPE_METER_LINK', description: '스마트미터 연동 (계측DB 조인)', totalCols: 6, rowCount: '-', isCollected: false, excludeReason: '계측DB(스마트미터) 조인', columns: [] },
    ],
  },
  '자산': {
    dbms: 'Tibero 7', host: '10.10.2.50:8629', schema: 'ASSET_ERP', totalTables: 35,
    note: 'ERP DB는 테이블간 연결관계가 없어 개발자가 개발한 업무쿼리로 연결관계를 확인하여 1·2차 가공 후 수집DB에 적재',
    tables: [
      { tableName: 'ASSET_MASTER', description: '자산 마스터 (1차 가공)', totalCols: 30, collectCols: 28, rowCount: '45,600', lastCollected: '2026-04-07 04:10', isCollected: true, columns: [
        { colName: 'ASSET_NO', dataType: 'VARCHAR(20)', description: '자산번호 (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'ASSET_NAME', dataType: 'VARCHAR(200)', description: '자산명', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ASSET_CLASS', dataType: 'VARCHAR(10)', description: '자산분류', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'ACQUIRE_DT', dataType: 'DATE', description: '취득일', nullable: 'Y', isPk: 'N', isCollected: true },
        { colName: 'ACQUIRE_AMT', dataType: 'NUMBER(15,2)', description: '취득가액', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'ASSET_LIFECYCLE', description: '자산 라이프사이클 (2차 가공)', totalCols: 18, collectCols: 18, rowCount: '128,000', lastCollected: '2026-04-07 04:10', isCollected: true, columns: [
        { colName: 'LIFECYCLE_ID', dataType: 'NUMBER(12)', description: '라이프사이클 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'ASSET_NO', dataType: 'VARCHAR(20)', description: '자산번호', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'ASSET_DEPRECIATION', description: '감가상각 이력', totalCols: 14, collectCols: 14, rowCount: '234,000', lastCollected: '2026-04-07 04:10', isCollected: true, columns: [
        { colName: 'DEPR_ID', dataType: 'NUMBER(12)', description: '감가상각 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'ASSET_NO', dataType: 'VARCHAR(20)', description: '자산번호', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'ASSET_MAINTENANCE', description: '자산 유지보수 이력 (업무쿼리 조인)', totalCols: 16, collectCols: 16, rowCount: '89,000', lastCollected: '2026-04-06 04:05', isCollected: true, columns: [
        { colName: 'MAINT_ID', dataType: 'NUMBER(12)', description: '유지보수 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'ASSET_NO', dataType: 'VARCHAR(20)', description: '자산번호', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      // 미수집
      { tableName: 'BKPF', description: 'SAP 전표 헤더 (ERP 원본)', totalCols: 45, rowCount: '-', isCollected: false, excludeReason: 'ERP 원본 (업무쿼리 가공 필요)', columns: [] },
      { tableName: 'BSEG', description: 'SAP 전표 항목 (ERP 원본)', totalCols: 60, rowCount: '-', isCollected: false, excludeReason: 'ERP 원본 (업무쿼리 가공 필요)', columns: [] },
      { tableName: 'ANLA', description: '고정자산 마스터 (ERP 원본)', totalCols: 55, rowCount: '-', isCollected: false, excludeReason: 'ERP 원본 (1차 가공 → ASSET_MASTER)', columns: [] },
      { tableName: 'ANLZ', description: '자산 시간종속 데이터 (ERP 원본)', totalCols: 30, rowCount: '-', isCollected: false, excludeReason: 'ERP 원본 (2차 가공 → ASSET_LIFECYCLE)', columns: [] },
      { tableName: 'ERP_HR_LINK', description: '인사 연동 테이블', totalCols: 12, rowCount: '-', isCollected: false, excludeReason: '인사 업무 영역 (수집 범위 외)', columns: [] },
    ],
  },
  '시설': {
    dbms: 'SAP HANA 2.0', host: '10.10.3.30:30015', schema: 'FACILITY', totalTables: 24,
    note: '원본 테이블로는 의미파악이 힘들어 뷰(View) 테이블을 봐야 업무에 활용할 인사이트를 도출할 수 있음',
    tables: [
      { tableName: 'V_PLANT_STATUS', description: '정수장 현황 (뷰)', totalCols: 18, collectCols: 18, rowCount: '2,800', lastCollected: '2026-04-06 22:10', isCollected: true, columns: [
        { colName: 'PLANT_ID', dataType: 'NVARCHAR(10)', description: '정수장 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PLANT_NAME', dataType: 'NVARCHAR(100)', description: '정수장명', nullable: 'N', isPk: 'N', isCollected: true },
        { colName: 'CAPACITY', dataType: 'DECIMAL(10,2)', description: '시설용량(톤/일)', nullable: 'Y', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'V_EQUIP_HISTORY', description: '설비 이력 (뷰)', totalCols: 22, collectCols: 20, rowCount: '156,000', lastCollected: '2026-04-06 22:10', isCollected: true, columns: [
        { colName: 'EQUIP_ID', dataType: 'NVARCHAR(20)', description: '설비 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'PLANT_ID', dataType: 'NVARCHAR(10)', description: '정수장 ID', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      { tableName: 'V_MAINT_SCHEDULE', description: '정비 일정 (뷰)', totalCols: 14, collectCols: 14, rowCount: '34,500', lastCollected: '2026-04-06 22:10', isCollected: true, columns: [
        { colName: 'SCHEDULE_ID', dataType: 'NVARCHAR(20)', description: '일정 ID (PK)', nullable: 'N', isPk: 'Y', isCollected: true },
        { colName: 'EQUIP_ID', dataType: 'NVARCHAR(20)', description: '설비 ID', nullable: 'N', isPk: 'N', isCollected: true },
      ]},
      // 미수집 (원본 테이블)
      { tableName: 'EQUI', description: 'SAP PM 설비 마스터 (원본)', totalCols: 80, rowCount: '-', isCollected: false, excludeReason: '원본 테이블 (뷰로 가공하여 수집)', columns: [] },
      { tableName: 'IFLO', description: 'SAP PM 기능위치 (원본)', totalCols: 65, rowCount: '-', isCollected: false, excludeReason: '원본 테이블 (뷰로 가공하여 수집)', columns: [] },
      { tableName: 'AUFK', description: 'SAP 오더 헤더 (원본)', totalCols: 90, rowCount: '-', isCollected: false, excludeReason: '원본 테이블 (뷰로 가공하여 수집)', columns: [] },
      { tableName: 'AFIH', description: 'PM 유지보수 오더 헤더 (원본)', totalCols: 50, rowCount: '-', isCollected: false, excludeReason: '원본 테이블 (뷰로 가공하여 수집)', columns: [] },
      { tableName: 'MARA', description: 'SAP 자재 마스터 (원본)', totalCols: 120, rowCount: '-', isCollected: false, excludeReason: '원본 테이블 (수집 범위 외)', columns: [] },
    ],
  },
}

const currentDomain = computed(() => domainData[selectedDomain.value] || null)
const allTables = computed(() => currentDomain.value?.tables || [])
const collectedTables = computed(() => allTables.value.filter(t => t.isCollected))
const excludedTables = computed(() => allTables.value.filter(t => !t.isCollected))
const selectedColumns = computed(() => selectedTable.value?.columns || [])

function onDomainChange() {
  selectedTable.value = null
}

// ===== 수집 테이블 그리드 =====
const collectGridApi = ref<any>(null)
const excludeGridApi = ref<any>(null)

const collectCols: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, minWidth: 36, flex: 0, sortable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 40 },
  { headerName: '테이블명', field: 'tableName', flex: 1.5, minWidth: 160, cellStyle: { fontFamily: 'monospace', fontWeight: '600' } },
  { headerName: '설명', field: 'description', flex: 2, minWidth: 180 },
  { headerName: '전체컬럼', field: 'totalCols', flex: 0.5, minWidth: 60, cellStyle: { textAlign: 'center' } },
  { headerName: '수집컬럼', field: 'collectCols', flex: 0.5, minWidth: 60, cellStyle: { textAlign: 'center' } },
  { headerName: '건수', field: 'rowCount', flex: 0.7, minWidth: 80, cellStyle: { textAlign: 'right' } },
  { headerName: '최근수집', field: 'lastCollected', flex: 1, minWidth: 130 },
])

const excludeCols: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, minWidth: 36, flex: 0, sortable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 40 },
  { headerName: '테이블명', field: 'tableName', flex: 1.5, minWidth: 160, cellStyle: { fontFamily: 'monospace', fontWeight: '600' } },
  { headerName: '설명', field: 'description', flex: 2, minWidth: 180 },
  { headerName: '전체컬럼', field: 'totalCols', flex: 0.5, minWidth: 60, cellStyle: { textAlign: 'center' } },
  { headerName: '제외사유', field: 'excludeReason', flex: 1.5, minWidth: 160 },
])

const columnCols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 35 },
  { headerName: '컬럼명', field: 'colName', flex: 1.2, minWidth: 140, cellStyle: { fontFamily: 'monospace', fontWeight: '600' } },
  { headerName: '데이터타입', field: 'dataType', flex: 1, minWidth: 120, cellStyle: { fontFamily: 'monospace', fontSize: '11px' } },
  { headerName: '설명', field: 'description', flex: 1.5, minWidth: 160 },
  { headerName: 'NULL', field: 'nullable', flex: 0.3, minWidth: 40, cellStyle: { textAlign: 'center' } },
  { headerName: 'PK', field: 'isPk', flex: 0.3, minWidth: 35, cellStyle: { textAlign: 'center' } },
  { headerName: '수집', field: 'isCollected', flex: 0.4, minWidth: 50, cellRenderer: (params: any) => {
    const checked = params.value ? 'checked' : ''
    return `<input type="checkbox" ${checked} style="cursor:pointer;width:16px;height:16px;" />`
  }, cellStyle: { textAlign: 'center', cursor: 'pointer' },
    onCellClicked: (params: any) => {
      params.data.isCollected = !params.data.isCollected
      params.api.refreshCells({ rowNodes: [params.node], force: true })
    }
  },
])

function getCollectedRowStyle(params: any) {
  if (params.node.rowIndex === selectedTable.value?._rowIdx && selectedTable.value?._isCollected) {
    return { background: '#e6f7ff' }
  }
  return undefined
}

function getExcludedRowStyle(params: any) {
  if (params.node.rowIndex === selectedTable.value?._rowIdx && !selectedTable.value?._isCollected) {
    return { background: '#fff7e6' }
  }
  return undefined
}

function onCollectedRowClick(event: any) {
  selectedTable.value = { ...event.data, _isCollected: true, _rowIdx: event.rowIndex }
  showColumnModal.value = true
}

function onExcludedRowClick(event: any) {
  selectedTable.value = { ...event.data, _isCollected: false, _rowIdx: event.rowIndex }
  showColumnModal.value = true
}

function selectAllCols(val: boolean) {
  if (selectedTable.value?.columns) {
    selectedTable.value.columns.forEach((c: ColumnInfo) => { c.isCollected = val })
  }
}

function saveColumnConfig() {
  const total = selectedTable.value?.columns?.length || 0
  const selected = selectedTable.value?.columns?.filter((c: ColumnInfo) => c.isCollected).length || 0
  if (selectedTable.value?._isCollected && selected === 0) {
    message.warning('수집중인 테이블은 최소 1개 이상의 컬럼을 수집해야 합니다.')
    return
  }
  // PK 컬럼 수집 해제 체크
  const uncheckedPks = selectedTable.value?.columns?.filter((c: ColumnInfo) => c.isPk === 'Y' && !c.isCollected)
  if (uncheckedPks && uncheckedPks.length > 0) {
    message.warning(`PK 컬럼(${uncheckedPks.map((c: ColumnInfo) => c.colName).join(', ')})은 수집 해제할 수 없습니다.`)
    uncheckedPks.forEach((c: ColumnInfo) => { c.isCollected = true })
    return
  }
  // collectCols 업데이트
  if (selectedTable.value) {
    selectedTable.value.collectCols = selected
    // 원본 테이블 데이터도 업데이트
    const orig = allTables.value.find(t => t.tableName === selectedTable.value.tableName)
    if (orig) orig.collectCols = selected
  }
  message.success(`${selectedTable.value.tableName}: ${selected}/${total} 컬럼 수집 설정이 저장되었습니다.`)
  showColumnModal.value = false
}

// ===== 수집 ↔ 미수집 이동 =====
const configChanged = ref(false)

function moveToExcluded() {
  if (!collectGridApi.value) return
  const selected = collectGridApi.value.getSelectedRows()
  if (selected.length === 0) { message.warning('수집 제외할 테이블을 선택하세요.'); return }
  // 유효성: 데이터가 있는 테이블이면 경고 모달
  const hasData = selected.filter((t: any) => t.rowCount && t.rowCount !== '0' && t.rowCount !== '-')
  if (hasData.length > 0) {
    pendingAction.value = { type: 'exclude', tables: selected }
    actionModalTitle.value = '수집 제외 확인'
    actionModalMsg.value = `다음 테이블에 이미 수집된 데이터가 있습니다.\n\n${hasData.map((t: any) => `• ${t.tableName} (${t.rowCount}건)`).join('\n')}\n\n수집을 제외하면 신규 데이터가 수집되지 않습니다.\n계속하시겠습니까?`
    showActionModal.value = true
    return
  }
  doExclude(selected)
}

function doExclude(tables: any[]) {
  tables.forEach((t: any) => {
    t.isCollected = false
    t.excludeReason = t.excludeReason || '수동 제외'
  })
  configChanged.value = true
  message.success(`${tables.length}개 테이블을 미수집으로 이동했습니다. [설정 저장]을 눌러 반영하세요.`)
  if (collectGridApi.value) collectGridApi.value.deselectAll()
}

function moveToCollected() {
  if (!excludeGridApi.value) return
  const selected = excludeGridApi.value.getSelectedRows()
  if (selected.length === 0) { message.warning('수집 추가할 테이블을 선택하세요.'); return }
  selected.forEach((t: any) => {
    t.isCollected = true
    t.excludeReason = undefined
    if (!t.collectCols) t.collectCols = t.totalCols
    if (!t.lastCollected) t.lastCollected = '-'
    if (!t.rowCount || t.rowCount === '-') t.rowCount = '0'
    if (t.columns) t.columns.forEach((c: ColumnInfo) => { c.isCollected = true })
  })
  configChanged.value = true
  message.success(`${selected.length}개 테이블을 수집 대상에 추가했습니다. [설정 저장]을 눌러 반영하세요.`)
  if (excludeGridApi.value) excludeGridApi.value.deselectAll()
}

function saveAllConfig() {
  if (!configChanged.value) {
    message.info('변경된 내용이 없습니다.')
    return
  }
  // 유효성 체크: 수집 테이블이 0개
  if (collectedTables.value.length === 0) {
    message.error('최소 1개 이상의 테이블을 수집 대상으로 설정하세요.')
    return
  }
  // 유효성 체크: 수집 컬럼 0개인 테이블
  const invalid = collectedTables.value.filter(t => t.collectCols === 0)
  if (invalid.length > 0) {
    message.error(`${invalid.map(t => t.tableName).join(', ')} 테이블의 수집 컬럼이 0개입니다. 최소 1개 이상의 컬럼을 선택하세요.`)
    return
  }
  configChanged.value = false
  message.success(`${selectedDomain.value} 도메인: 수집 ${collectedTables.value.length}개 / 미수집 ${excludedTables.value.length}개 테이블 설정이 저장되었습니다.`)
}

function confirmAction() {
  if (pendingAction.value?.type === 'exclude') {
    doExclude(pendingAction.value.tables)
  }
  showActionModal.value = false
  pendingAction.value = null
}

// 초기화: URL 쿼리 파라미터로 도메인 선택
onMounted(() => {
  const q = route.query.domain as string
  if (q && domainData[q]) {
    selectedDomain.value = q
  }
})
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }

.domain-selector {
  background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; margin-bottom: 16px;
}
.selector-row {
  display: flex; align-items: center; gap: 20px; margin-bottom: 12px;
  .selector-group {
    display: flex; align-items: center; gap: 8px;
    label { font-size: 13px; font-weight: 600; white-space: nowrap; }
    select { padding: 6px 12px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; min-width: 200px; }
  }
}
.domain-meta {
  display: flex; gap: 16px; font-size: 12px; color: #666;
  .meta-item { display: flex; align-items: center; gap: 4px; }
}
.domain-summary {
  display: flex; flex-direction: column; gap: 8px;
}
.summary-chips {
  display: flex; gap: 12px;
  .chip {
    display: flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 20px; font-size: 12px;
    strong { font-size: 14px; }
    &.chip-total { background: #f0f0f0; color: #333; }
    &.chip-collect { background: #f6ffed; color: #28A745; }
    &.chip-exclude { background: #fff1f0; color: #DC3545; }
  }
}
.domain-note {
  padding: 8px 12px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 6px;
  font-size: 12px; color: #ad6800; display: flex; align-items: flex-start; gap: 6px; line-height: 1.5;
}
.section-title {
  font-size: 13px !important; font-weight: 700 !important;
  &.collected { color: #28A745; }
  &.excluded { color: #DC3545; }
}

// 컬럼 모달
.column-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  .badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; margin-right: 8px; &.badge-success { background: #f6ffed; color: #28A745; } &.badge-muted { background: #f5f5f5; color: #999; } }
}
.column-modal-info { display: flex; align-items: center; }
.column-modal-actions { display: flex; gap: 6px; }

// 이동 바
.transfer-bar {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px; margin: 12px 0;
  background: #f8f9fb; border: 1px solid #e8e8e8; border-radius: 8px;
  .transfer-btn { display: flex; align-items: center; gap: 4px; }
}
.btn-success { background: #28A745 !important; color: #fff !important; border-color: #28A745 !important; &:hover { background: #218838 !important; } }
.btn-pulse { animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(40,167,69,0.4); } 50% { box-shadow: 0 0 0 6px rgba(40,167,69,0); } }
.btn-xs { padding: 3px 8px !important; font-size: 11px !important; }

@media (max-width: 1279px) {
  .selector-row { flex-direction: column; align-items: flex-start; }
  .domain-meta { flex-wrap: wrap; }
}
</style>
