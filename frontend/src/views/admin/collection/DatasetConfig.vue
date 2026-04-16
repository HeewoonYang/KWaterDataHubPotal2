<template>
  <div class="admin-page">
    <div class="page-header"><h2>데이터셋 구성</h2><p class="page-desc">수집 대상 데이터셋을 정의하고 구성합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">데이터셋 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 데이터셋 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '데이터셋_설정')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 데이터셋 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="xl" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">데이터셋 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스 유형</span><span class="info-value">{{ detailData.sourceType }}</span></div>
          <div class="modal-info-item"><span class="info-label">테이블/토픽</span><span class="info-value">{{ detailData.table }}</span></div>
          <div class="modal-info-item"><span class="info-label">컬럼 수</span><span class="info-value">{{ detailData.columns }}개</span></div>
          <div class="modal-info-item"><span class="info-label">수집 주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>

      <!-- ETL 컬럼 매핑 편집기 (REQ-DHUB-005-002-002) -->
      <div class="modal-section">
        <div class="modal-section-title">
          ETL 컬럼 매핑 ({{ mapping.length }}건)
          <span class="modal-section-right">
            <button class="btn btn-xs btn-outline" @click="addMappingRow"><PlusOutlined /> 매핑 추가</button>
            <button class="btn btn-xs btn-outline" @click="autoMapByName" title="원천명과 타깃명이 같은 컬럼 자동 매핑"><BulbOutlined /> 자동 매핑</button>
          </span>
        </div>
        <div class="mapping-help">
          원천 컬럼을 타깃 컬럼으로 변환하는 규칙을 정의합니다. 변환식 예: <code>UPPER(col)</code>, <code>SUBSTR(col,1,10)</code>, <code>CAST(col AS NUMERIC)</code>, <code>COALESCE(col, '미상')</code>
        </div>
        <table class="mapping-table">
          <thead>
            <tr>
              <th style="width:30px;">#</th>
              <th>원천 컬럼</th>
              <th>원천 타입</th>
              <th></th>
              <th>타깃 컬럼</th>
              <th>타깃 타입</th>
              <th>변환식 (선택)</th>
              <th>NULL 허용</th>
              <th style="width:60px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in mapping" :key="idx">
              <td>{{ idx + 1 }}</td>
              <td><input v-model="m.source" placeholder="src_col" class="map-input" /></td>
              <td>
                <select v-model="m.source_type" class="map-input">
                  <option value="">-</option>
                  <option v-for="t in dataTypes" :key="t" :value="t">{{ t }}</option>
                </select>
              </td>
              <td style="text-align:center;color:#999;">→</td>
              <td><input v-model="m.target" placeholder="tgt_col" class="map-input" /></td>
              <td>
                <select v-model="m.target_type" class="map-input">
                  <option value="">-</option>
                  <option v-for="t in dataTypes" :key="t" :value="t">{{ t }}</option>
                </select>
              </td>
              <td><input v-model="m.transform" placeholder="(없음)" class="map-input mono" /></td>
              <td style="text-align:center;"><input type="checkbox" v-model="m.nullable" /></td>
              <td>
                <button class="btn btn-xs btn-outline" @click="moveUp(idx)" :disabled="idx === 0"><CaretUpOutlined /></button>
                <button class="btn btn-xs btn-danger" @click="removeMappingRow(idx)"><CloseOutlined /></button>
              </td>
            </tr>
            <tr v-if="!mapping.length">
              <td colspan="9" style="text-align:center;color:#888;padding:24px;">매핑이 없습니다. [매핑 추가] 버튼으로 시작하세요.</td>
            </tr>
          </tbody>
        </table>
        <div class="mapping-preview" v-if="mapping.length">
          <div class="sub-title">생성될 매핑 JSON 미리보기</div>
          <pre class="json-preview">{{ JSON.stringify(mappingJson, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <button class="btn btn-primary" @click="saveMapping"><SaveOutlined /> 매핑 저장</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 데이터셋 추가 팝업 -->
    <AdminModal :visible="showRegister" title="데이터셋 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">데이터셋명</label><input placeholder="데이터셋명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소스 유형</label><select><option>Oracle DB</option><option>Kafka</option><option>GIS API</option><option>CSV</option><option>REST API</option></select></div>
          <div class="modal-form-group"><label class="required">수집 주기</label><select><option>실시간</option><option>10분</option><option>1시간</option><option>일 1회</option><option>월 1회</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">테이블/토픽</label><input placeholder="테이블명 또는 토픽명" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="데이터셋 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, computed, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  PlusOutlined, FileExcelOutlined, SaveOutlined, BulbOutlined, CloseOutlined, CaretUpOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})

// ETL 매핑 편집기 (REQ-DHUB-005-002-002)
interface MappingRow {
  source: string
  source_type: string
  target: string
  target_type: string
  transform: string
  nullable: boolean
}
const mapping = ref<MappingRow[]>([])
const dataTypes = ['VARCHAR', 'TEXT', 'INTEGER', 'BIGINT', 'NUMERIC', 'DATE', 'TIMESTAMP', 'BOOLEAN', 'JSONB', 'UUID']

const mappingJson = computed(() => mapping.value.filter(m => m.source || m.target).map(m => ({
  source: m.source, source_type: m.source_type || undefined,
  target: m.target, target_type: m.target_type || undefined,
  transform: m.transform || undefined, nullable: m.nullable,
})))

function loadMappingFromConfig(cfg: any) {
  const raw = cfg?.column_mapping
  if (Array.isArray(raw)) {
    mapping.value = raw.map((m: any) => ({
      source: m.source || '', source_type: m.source_type || '',
      target: m.target || '', target_type: m.target_type || '',
      transform: m.transform || '', nullable: !!m.nullable,
    }))
  } else if (raw && typeof raw === 'object') {
    // 객체 형태 {srcCol: tgtCol} → 배열 변환
    mapping.value = Object.entries(raw).map(([s, t]) => ({
      source: s, source_type: '', target: String(t), target_type: '', transform: '', nullable: false,
    }))
  } else {
    mapping.value = []
  }
}

function addMappingRow() {
  mapping.value.push({ source: '', source_type: '', target: '', target_type: '', transform: '', nullable: true })
}
function removeMappingRow(i: number) { mapping.value.splice(i, 1) }
function moveUp(i: number) {
  if (i === 0) return
  const [item] = mapping.value.splice(i, 1)
  mapping.value.splice(i - 1, 0, item)
}
function autoMapByName() {
  for (const m of mapping.value) {
    if (m.source && !m.target) m.target = m.source.toLowerCase()
    if (m.source && !m.source_type) m.source_type = 'VARCHAR'
    if (m.target && !m.target_type) m.target_type = m.source_type || 'VARCHAR'
  }
  message.success('자동 매핑이 적용되었습니다.')
}
async function saveMapping() {
  const cfgId = detailData.value?._raw?.id
  if (!cfgId) {
    message.warning('이 행은 mock 데이터입니다. 실제 데이터셋 구성에서만 저장됩니다.')
    return
  }
  try {
    await adminCollectionApi.updateDatasetConfig(cfgId, { column_mapping: mappingJson.value })
    message.success('컬럼 매핑이 저장되었습니다.')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '저장 실패')
  }
}

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '데이터셋명', field: 'name', flex: 1.5, minWidth: 150 },
  { headerName: '소스 유형', field: 'sourceType', flex: 0.7, minWidth: 80 },
  { headerName: '테이블/토픽', field: 'table', flex: 1, minWidth: 120 },
  { headerName: '컬럼 수', field: 'columns', flex: 0.5, minWidth: 60 },
  { headerName: '수집 주기', field: 'schedule', flex: 0.6, minWidth: 70 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { name: '댐 수위 관측 데이터', sourceType: 'Oracle DB', table: 'TM_DAM_LEVEL', columns: 12, schedule: '10분', status: '활성' },
  { name: '수질 모니터링 센서', sourceType: 'Kafka', table: 'iot.water-quality', columns: 18, schedule: '실시간', status: '활성' },
  { name: '상수도 관로 GIS', sourceType: 'GIS API', table: '/wfs/pipeline', columns: 24, schedule: '일 1회', status: '활성' },
  { name: '전력 사용량 통계', sourceType: 'CSV', table: '/data/power/*.csv', columns: 8, schedule: '월 1회', status: '활성' },
  { name: '하천 유량 관측', sourceType: 'REST API', table: '/api/river/flow', columns: 10, schedule: '1시간', status: '일시정지' },
])


onMounted(async () => {
  try {
    const res = await adminCollectionApi.datasetConfigs()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.dataset_name || r.name || '',
        sourceType: r.source_name || r.sourceType || '',
        table: r.source_table || r.table || '',
        columns: r.columns || '-',
        schedule: r.schedule || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'PAUSED' ? '일시정지' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('DatasetConfig: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  loadMappingFromConfig(event.data?._raw)
  showDetail.value = true
}
function handleRegister() { message.success("등록되었습니다."); showRegister.value = false }
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }

/* ETL 매핑 편집기 */
.modal-section-right { float: right; display: inline-flex; gap: 4px; }
.mapping-help { font-size: 11px; color: #666; background: #f5f7fa; padding: 6px 10px; border-radius: 4px; margin-bottom: 8px;
  code { background: #fff; border: 1px solid #d9d9d9; padding: 1px 4px; margin: 0 2px; border-radius: 2px; font-size: 10px; }
}
.mapping-table { width: 100%; font-size: 11px; border-collapse: collapse;
  th { background: #f5f7fa; padding: 6px; border-bottom: 2px solid #e8e8e8; text-align: left; font-weight: 600; }
  td { padding: 4px 6px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
}
.map-input { width: 100%; padding: 3px 6px; border: 1px solid #d9d9d9; border-radius: 3px; font-size: 11px; height: 24px;
  &.mono { font-family: monospace; }
}
.mapping-preview { margin-top: 12px; }
.sub-title { font-size: 11px; font-weight: 700; color: #4a5568; margin-bottom: 4px; }
.json-preview { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; font-size: 10px; max-height: 180px; overflow: auto; margin: 0; }
.btn-danger { background: #fff1f0 !important; color: #DC3545 !important; border: 1px solid #ffa39e !important; padding: 3px 6px !important; }
</style>
