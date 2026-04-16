<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>공간정보 수집</h2>
      <p class="page-desc">ArcGIS · GeoServer · GeoJSON · Oracle Spatial 등 표준 공간정보 소스 수집 설정을 관리합니다.</p>
    </div>

    <div class="table-section">
      <div class="table-header">
        <span class="table-count">공간정보 소스 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="openCreate"><PlusOutlined /> 소스 추가</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '공간정보_수집')">
            <FileExcelOutlined />
          </button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="rows"
          :columnDefs="cols"
          :defaultColDef="defCol"
          :pagination="true"
          :paginationPageSize="10"
          domLayout="autoHeight"
          :tooltipShowDelay="0"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- 상세 팝업 (탭) -->
    <AdminModal :visible="showDetail" :title="(detail.config_name || '상세') + ' 상세'" size="lg" @close="showDetail = false">
      <div class="spatial-tabs">
        <button :class="['tab-btn', { active: tab === 'info' }]" @click="tab = 'info'">기본정보</button>
        <button :class="['tab-btn', { active: tab === 'layers' }]" @click="tab = 'layers'">레이어 ({{ detail.layers?.length || 0 }})</button>
        <button :class="['tab-btn', { active: tab === 'history' }]" @click="tab = 'history'">수집이력 ({{ detail.recent_history?.length || 0 }})</button>
      </div>

      <div v-show="tab === 'info'" class="modal-section">
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">소스명</span><span class="info-value">{{ detail.config_name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스시스템</span><span class="info-value">{{ detail.source_system || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터유형</span><span class="info-value">{{ detail.spatial_data_type || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">좌표계</span><span class="info-value">{{ detail.coordinate_system || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">URL</span><span class="info-value">{{ detail.source_url || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">PostGIS 스키마</span><span class="info-value">{{ detail.target_schema || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">PostGIS 테이블</span><span class="info-value">{{ detail.target_table || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detail.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'">{{ detail.status === 'ACTIVE' ? '활성' : (detail.status || '-') }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">최근 수집</span><span class="info-value">{{ formatDt(detail.last_collected_at) }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 상태</span><span class="info-value">{{ detail.last_status || '-' }}</span></div>
          <div class="modal-info-item"><span class="info-label">피처 수</span><span class="info-value">{{ detail.feature_count || 0 }}</span></div>
          <div v-if="detail.last_error_message" class="modal-info-item" style="grid-column: 1 / -1;">
            <span class="info-label">최근 에러</span><span class="info-value" style="color:#d32f2f">{{ detail.last_error_message }}</span>
          </div>
        </div>
      </div>

      <div v-show="tab === 'layers'" class="modal-section">
        <div v-if="!detail.layers?.length" class="empty-state">등록된 레이어가 없습니다. "레이어 탐색" 버튼으로 자동 탐색을 실행하세요.</div>
        <div v-else class="ag-grid-wrapper">
          <AgGridVue
            class="ag-theme-alpine"
            :rowData="detail.layers"
            :columnDefs="layerCols"
            :defaultColDef="defCol"
            domLayout="autoHeight"
          />
        </div>
      </div>

      <div v-show="tab === 'history'" class="modal-section">
        <div v-if="!detail.recent_history?.length" class="empty-state">수집 이력이 없습니다. "즉시 수집" 버튼으로 실행하세요.</div>
        <div v-else class="ag-grid-wrapper">
          <AgGridVue
            class="ag-theme-alpine"
            :rowData="detail.recent_history"
            :columnDefs="historyCols"
            :defaultColDef="defCol"
            domLayout="autoHeight"
          />
        </div>
      </div>

      <template #footer>
        <button class="btn btn-outline" @click="handleTest"><ApiOutlined /> 연결 테스트</button>
        <button class="btn btn-outline" @click="handleDiscover"><SearchOutlined /> 레이어 탐색</button>
        <button class="btn btn-outline" @click="handleRun"><PlayCircleOutlined /> 즉시 수집</button>
        <button class="btn btn-primary" @click="openEdit"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" style="color:#d32f2f" @click="handleDelete"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 등록/수정 팝업 -->
    <AdminModal :visible="showForm" :title="formMode === 'create' ? '공간정보 소스 추가' : '공간정보 소스 수정'" size="lg" @close="showForm = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">소스명</label>
          <input v-model="form.config_name" placeholder="예: 상수도 관로 네트워크" />
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">소스시스템</label>
            <select v-model="form.source_system">
              <option value="">선택</option>
              <option v-for="opt in sourceSystems" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>데이터유형</label>
            <select v-model="form.spatial_data_type">
              <option value="">선택</option>
              <option value="GIS">GIS</option>
              <option value="SATELLITE">위성</option>
              <option value="LIDAR">LiDAR</option>
              <option value="DRONE">드론</option>
            </select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label>좌표계</label>
            <select v-model="form.coordinate_system">
              <option value="">선택</option>
              <option value="EPSG:5186">EPSG:5186 (중부원점 TM)</option>
              <option value="EPSG:5179">EPSG:5179 (한국 UTM-K)</option>
              <option value="EPSG:4326">EPSG:4326 (WGS84)</option>
              <option value="EPSG:3857">EPSG:3857 (Web Mercator)</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>상태</label>
            <select v-model="form.status">
              <option value="ACTIVE">활성</option>
              <option value="INACTIVE">비활성</option>
            </select>
          </div>
        </div>
        <div class="modal-form-group">
          <label>소스 URL</label>
          <input v-model="form.source_url" placeholder="https://example.com/arcgis/rest/services/..." />
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label>PostGIS 스키마</label>
            <input v-model="form.target_schema" placeholder="spatial_gis" />
          </div>
          <div class="modal-form-group">
            <label>PostGIS 테이블</label>
            <input v-model="form.target_table" placeholder="예: water_pipeline" />
          </div>
        </div>
        <div class="modal-form-group">
          <label>인증 유형</label>
          <select v-model="authType" @change="syncAuth">
            <option value="NONE">없음</option>
            <option value="BASIC">Basic (ID/PW)</option>
            <option value="TOKEN">토큰</option>
          </select>
        </div>
        <div v-if="authType === 'BASIC'" class="modal-form-row">
          <div class="modal-form-group"><label>사용자</label><input v-model="authUser" /></div>
          <div class="modal-form-group"><label>비밀번호</label><input v-model="authPass" type="password" /></div>
        </div>
        <div v-if="authType === 'TOKEN'" class="modal-form-group">
          <label>토큰</label><input v-model="authToken" />
        </div>
        <div class="modal-form-group">
          <label>이벤트 트리거</label>
          <select v-model="eventType" @change="syncEvent">
            <option value="">사용 안 함</option>
            <option value="FILE_UPLOAD">파일 업로드</option>
            <option value="KAFKA">Kafka</option>
            <option value="API">API</option>
          </select>
        </div>
        <div v-if="eventType" class="modal-form-group">
          <label>토픽/경로</label>
          <input v-model="eventTopic" placeholder="spatial.ingest 또는 /uploads/gis/" />
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleSave"><SaveOutlined /> {{ formMode === 'create' ? '추가' : '저장' }}</button>
        <button class="btn btn-outline" @click="showForm = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, reactive, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined,
  DeleteOutlined, ApiOutlined, SearchOutlined, PlayCircleOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'

ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const showForm = ref(false)
const tab = ref<'info' | 'layers' | 'history'>('info')
const formMode = ref<'create' | 'edit'>('create')

const detail = ref<any>({ layers: [], recent_history: [] })
const form = reactive<any>({
  config_name: '', source_system: '', spatial_data_type: '',
  coordinate_system: '', status: 'ACTIVE', source_url: '',
  target_schema: 'spatial_gis', target_table: '',
  auth_config: null, event_trigger_config: null,
})
const authType = ref<'NONE' | 'BASIC' | 'TOKEN'>('NONE')
const authUser = ref('')
const authPass = ref('')
const authToken = ref('')
const eventType = ref('')
const eventTopic = ref('')

const sourceSystems = [
  { value: 'ARCGIS_REST', label: 'ArcGIS REST' },
  { value: 'GEOSERVER_WFS', label: 'GeoServer WFS' },
  { value: 'GEOSERVER_WMS', label: 'GeoServer WMS' },
  { value: 'GEOJSON_URL', label: 'GeoJSON URL' },
  { value: 'ORACLE_SPATIAL', label: 'Oracle Spatial' },
  { value: 'SHAPEFILE', label: 'Shapefile (MinIO)' },
]

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '소스명', field: 'config_name', flex: 1.5, minWidth: 150 },
  { headerName: '소스시스템', field: 'source_system', flex: 0.9, minWidth: 120 },
  { headerName: '좌표계', field: 'coordinate_system', flex: 0.7, minWidth: 100 },
  { headerName: '대상테이블', field: 'target_table', flex: 1, minWidth: 120 },
  { headerName: '최근 수집', field: 'last_collected_at_fmt', flex: 0.9, minWidth: 140 },
  { headerName: '상태', field: 'status_label', flex: 0.5, minWidth: 70 },
])
const layerCols: ColDef[] = withHeaderTooltips([
  { headerName: '레이어명', field: 'layer_name', flex: 1.5, minWidth: 140 },
  { headerName: '지오메트리', field: 'geometry_type', flex: 0.8, minWidth: 100 },
  { headerName: 'SRID', field: 'srid', flex: 0.5, minWidth: 70 },
  { headerName: '피처수', field: 'feature_count', flex: 0.7, minWidth: 80 },
  { headerName: '활성', field: 'is_enabled', flex: 0.4, minWidth: 60, valueFormatter: (p: any) => p.value ? 'Y' : 'N' },
])
const historyCols: ColDef[] = withHeaderTooltips([
  { headerName: '시작시각', field: 'started_at', flex: 1, minWidth: 140, valueFormatter: (p: any) => formatDt(p.value) },
  { headerName: '종료시각', field: 'ended_at', flex: 1, minWidth: 140, valueFormatter: (p: any) => formatDt(p.value) },
  { headerName: '상태', field: 'status', flex: 0.6, minWidth: 80 },
  { headerName: '트리거', field: 'triggered_by', flex: 0.6, minWidth: 80 },
  { headerName: '피처수', field: 'feature_count', flex: 0.6, minWidth: 80 },
  { headerName: '무효수', field: 'invalid_feature_count', flex: 0.6, minWidth: 80 },
])

const rows = ref<any[]>([])

function formatDt(v: any) {
  if (!v) return '-'
  try { return String(v).replace('T', ' ').substring(0, 16) } catch { return String(v) }
}

async function reload() {
  try {
    const res = await adminCollectionApi.spatialConfigs()
    const items = res.data.data || []
    rows.value = items.map((r: any) => ({
      ...r,
      last_collected_at_fmt: formatDt(r.last_collected_at),
      status_label: r.status === 'ACTIVE' ? '활성' : (r.status || '-'),
    }))
  } catch (e) {
    console.warn('SpatialCollect: list API failed', e)
    rows.value = []
  }
}

async function onRowClick(event: any) {
  const id = event.data?.id
  if (!id) return
  try {
    const res = await adminCollectionApi.spatialConfigDetail(id)
    detail.value = res.data.data || event.data
    tab.value = 'info'
    showDetail.value = true
  } catch (e) {
    message.error('상세 정보를 불러오지 못했습니다.')
  }
}

function openCreate() {
  formMode.value = 'create'
  Object.assign(form, {
    config_name: '', source_system: '', spatial_data_type: '',
    coordinate_system: '', status: 'ACTIVE', source_url: '',
    target_schema: 'spatial_gis', target_table: '',
    auth_config: null, event_trigger_config: null,
  })
  authType.value = 'NONE'; authUser.value = ''; authPass.value = ''; authToken.value = ''
  eventType.value = ''; eventTopic.value = ''
  showForm.value = true
}

function openEdit() {
  formMode.value = 'edit'
  Object.assign(form, detail.value)
  const a = detail.value.auth_config || {}
  authType.value = a.auth_type || 'NONE'
  authUser.value = a.username || ''; authPass.value = ''; authToken.value = ''
  const e = detail.value.event_trigger_config || {}
  eventType.value = e.trigger_type || ''; eventTopic.value = e.topic_or_path || ''
  showDetail.value = false
  showForm.value = true
}

function syncAuth() {
  if (authType.value === 'NONE') form.auth_config = { auth_type: 'NONE' }
}
function syncEvent() {
  if (!eventType.value) form.event_trigger_config = { enabled: false }
}

function buildPayload() {
  const payload: any = { ...form }
  payload.auth_config = {
    auth_type: authType.value,
    ...(authType.value === 'BASIC' ? { username: authUser.value, password_enc: authPass.value } : {}),
    ...(authType.value === 'TOKEN' ? { token_enc: authToken.value } : {}),
  }
  payload.event_trigger_config = eventType.value
    ? { enabled: true, trigger_type: eventType.value, topic_or_path: eventTopic.value }
    : { enabled: false }
  return payload
}

async function handleSave() {
  if (!form.config_name) { message.error('소스명은 필수입니다.'); return }
  if (!form.source_system) { message.error('소스시스템은 필수입니다.'); return }
  try {
    const payload = buildPayload()
    if (formMode.value === 'create') {
      await adminCollectionApi.createSpatialConfig(payload)
      message.success('공간정보 소스가 등록되었습니다.')
    } else {
      await adminCollectionApi.updateSpatialConfig(detail.value.id, payload)
      message.success('공간정보 소스가 수정되었습니다.')
    }
    showForm.value = false
    await reload()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '저장에 실패했습니다.')
  }
}

async function handleDelete() {
  if (!detail.value.id) return
  if (!confirm(`"${detail.value.config_name}" 소스를 삭제하시겠습니까?`)) return
  try {
    await adminCollectionApi.deleteSpatialConfig(detail.value.id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    await reload()
  } catch {
    message.error('삭제에 실패했습니다.')
  }
}

async function handleTest() {
  if (!detail.value.id) return
  try {
    const res = await adminCollectionApi.testSpatialConnection(detail.value.id)
    const d = res.data.data
    d.success ? message.success(d.message) : message.error(d.message)
  } catch { message.error('연결 테스트에 실패했습니다.') }
}

async function handleDiscover() {
  if (!detail.value.id) return
  try {
    const res = await adminCollectionApi.discoverSpatialLayers(detail.value.id)
    const d = res.data.data
    message.info(d.message)
    if (d.layers) {
      detail.value.layers = d.layers
      tab.value = 'layers'
    }
  } catch { message.error('레이어 탐색에 실패했습니다.') }
}

async function handleRun() {
  if (!detail.value.id) return
  try {
    const res = await adminCollectionApi.runSpatialCollection(detail.value.id)
    const d = res.data.data
    if (d.success) {
      message.success(d.message)
      const r = await adminCollectionApi.spatialConfigDetail(detail.value.id)
      detail.value = r.data.data
      tab.value = 'history'
    } else {
      message.error(d.message)
    }
  } catch { message.error('수집 실행에 실패했습니다.') }
}

onMounted(reload)
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';

:deep(.ag-row) { cursor: pointer; }

.spatial-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 16px;

  .tab-btn {
    padding: 10px 18px;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    cursor: pointer;
    font-size: 14px;
    color: #666;

    &:hover { color: #1976d2; }
    &.active { color: #1976d2; border-bottom-color: #1976d2; font-weight: 600; }
  }
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
}

@media (max-width: 1279px) {
  .modal-form-row { grid-template-columns: 1fr; }
}
</style>
