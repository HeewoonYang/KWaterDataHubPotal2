<template>
  <div class="admin-page">
    <div class="page-header"><h2>표준 인터페이스</h2><p class="page-desc">시스템 간 연계 인터페이스 표준 정의 및 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">인터페이스 목록 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="openRegister"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '인터페이스_목록')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 인터페이스 상세/수정 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.interface_name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">인터페이스 정보</div>
        <template v-if="!isEditing">
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">인터페이스코드</span><span class="info-value">{{ detailData.interface_code }}</span></div>
            <div class="modal-info-item"><span class="info-label">인터페이스명</span><span class="info-value">{{ detailData.interface_name }}</span></div>
            <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.interface_type }}</span></div>
            <div class="modal-info-item"><span class="info-label">프로토콜</span><span class="info-value">{{ detailData.protocol }}</span></div>
            <div class="modal-info-item"><span class="info-label">송신 시스템</span><span class="info-value">{{ detailData.source_system || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">수신 시스템</span><span class="info-value">{{ detailData.target_system || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">엔드포인트</span><span class="info-value">{{ detailData.endpoint_url || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">데이터 포맷</span><span class="info-value">{{ detailData.data_format || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">스케줄 유형</span><span class="info-value">{{ detailData.schedule_type || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">스케줄 CRON</span><span class="info-value">{{ detailData.schedule_cron || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">타임아웃</span><span class="info-value">{{ detailData.timeout_ms ? detailData.timeout_ms + 'ms' : '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">재시도</span><span class="info-value">{{ detailData.retry_count ?? '-' }}회</span></div>
            <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'">{{ detailData.status === 'ACTIVE' ? '활성' : detailData.status }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">설명</span><span class="info-value">{{ detailData.description || '-' }}</span></div>
          </div>
        </template>
        <template v-else>
          <div class="modal-form">
            <div class="modal-form-row">
              <div class="modal-form-group"><label class="required">인터페이스명</label><input v-model="editForm.interface_name" /></div>
              <div class="modal-form-group"><label class="required">유형</label><select v-model="editForm.interface_type"><option v-for="t in ifTypes" :key="t" :value="t">{{ t }}</option></select></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>프로토콜</label><select v-model="editForm.protocol"><option v-for="p in protocols" :key="p" :value="p">{{ p }}</option></select></div>
              <div class="modal-form-group"><label>데이터 포맷</label><select v-model="editForm.data_format"><option v-for="f in dataFormats" :key="f" :value="f">{{ f }}</option></select></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>송신 시스템</label><input v-model="editForm.source_system" /></div>
              <div class="modal-form-group"><label>수신 시스템</label><input v-model="editForm.target_system" /></div>
            </div>
            <div class="modal-form-group"><label>엔드포인트 URL</label><input v-model="editForm.endpoint_url" placeholder="https://..." /></div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>스케줄 유형</label><select v-model="editForm.schedule_type"><option v-for="s in scheduleTypes" :key="s" :value="s">{{ s }}</option></select></div>
              <div class="modal-form-group" v-if="editForm.schedule_type === 'BATCH'"><label>CRON 표현식</label><input v-model="editForm.schedule_cron" placeholder="0 */6 * * *" /></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>타임아웃(ms)</label><input type="number" v-model.number="editForm.timeout_ms" /></div>
              <div class="modal-form-group"><label>재시도 횟수</label><input type="number" v-model.number="editForm.retry_count" min="0" max="10" /></div>
            </div>
            <div class="modal-form-row">
              <div class="modal-form-group"><label>상태</label><select v-model="editForm.status"><option value="ACTIVE">활성</option><option value="INACTIVE">비활성</option><option value="MAINTENANCE">점검 중</option></select></div>
            </div>
            <div class="modal-form-group"><label>설명</label><textarea v-model="editForm.description" rows="2"></textarea></div>
          </div>
        </template>
      </div>
      <!-- 실행 이력 -->
      <div class="modal-section" v-if="!isEditing">
        <div class="modal-section-title">실행 이력</div>
        <div class="ag-grid-wrapper" v-if="logRows.length > 0"><AgGridVue class="ag-theme-alpine" :rowData="logRows" :columnDefs="logCols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="5" domLayout="autoHeight" /></div>
        <div v-else class="empty-text">실행 이력이 없습니다.</div>
      </div>
      <template #footer>
        <template v-if="!isEditing">
          <button class="btn btn-outline" @click="handleTest" :disabled="testing"><ApiOutlined /> {{ testing ? '테스트 중...' : '연결 테스트' }}</button>
          <button class="btn btn-primary" @click="startEdit"><EditOutlined /> 수정</button>
          <button class="btn btn-danger" @click="handleDelete"><DeleteOutlined /> 삭제</button>
          <button class="btn btn-outline" @click="showDetail = false">닫기</button>
        </template>
        <template v-else>
          <button class="btn btn-primary" @click="handleSaveEdit"><SaveOutlined /> 저장</button>
          <button class="btn btn-outline" @click="isEditing = false">취소</button>
        </template>
      </template>
    </AdminModal>

    <!-- 인터페이스 등록 팝업 -->
    <AdminModal :visible="showRegister" title="인터페이스 등록" size="lg" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">인터페이스명</label><input v-model="regForm.interface_name" placeholder="인터페이스명 입력" /></div>
          <div class="modal-form-group"><label class="required">유형</label><select v-model="regForm.interface_type"><option v-for="t in ifTypes" :key="t" :value="t">{{ t }}</option></select></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>프로토콜</label><select v-model="regForm.protocol"><option v-for="p in protocols" :key="p" :value="p">{{ p }}</option></select></div>
          <div class="modal-form-group"><label>데이터 포맷</label><select v-model="regForm.data_format"><option v-for="f in dataFormats" :key="f" :value="f">{{ f }}</option></select></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>송신 시스템</label><input v-model="regForm.source_system" placeholder="송신 시스템명" /></div>
          <div class="modal-form-group"><label>수신 시스템</label><input v-model="regForm.target_system" placeholder="수신 시스템명" /></div>
        </div>
        <div class="modal-form-group"><label>엔드포인트 URL</label><input v-model="regForm.endpoint_url" placeholder="https://api.example.com/v1/..." /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>스케줄 유형</label><select v-model="regForm.schedule_type"><option v-for="s in scheduleTypes" :key="s" :value="s">{{ s }}</option></select></div>
          <div class="modal-form-group" v-if="regForm.schedule_type === 'BATCH'"><label>CRON 표현식</label><input v-model="regForm.schedule_cron" placeholder="0 */6 * * *" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>타임아웃(ms)</label><input type="number" v-model.number="regForm.timeout_ms" /></div>
          <div class="modal-form-group"><label>재시도 횟수</label><input type="number" v-model.number="regForm.retry_count" min="0" max="10" /></div>
        </div>
        <div class="modal-form-group"><label>설명</label><textarea v-model="regForm.description" rows="2" placeholder="인터페이스 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'

import { ref, reactive, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminSystemApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const ifTypes = ['REST', 'SOAP', 'KAFKA', 'FILE', 'DB_LINK', 'gRPC', 'WFS/WMS']
const protocols = ['HTTP', 'HTTPS', 'TCP', 'MQ', 'WSS']
const dataFormats = ['JSON', 'XML', 'CSV', 'BINARY']
const scheduleTypes = ['REALTIME', 'BATCH', 'EVENT']

const showDetail = ref(false), showRegister = ref(false), isEditing = ref(false), testing = ref(false)
const detailData = ref<any>({})
const editForm = reactive<any>({})
const logRows = ref<any[]>([])

const initRegForm = () => ({
  interface_name: '', interface_type: 'REST', protocol: 'HTTPS', data_format: 'JSON',
  source_system: '', target_system: '', endpoint_url: '',
  schedule_type: 'REALTIME', schedule_cron: '', timeout_ms: 30000, retry_count: 3, description: '',
})
const regForm = reactive(initRegForm())

const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 45 },
  { headerName: '인터페이스코드', field: 'interface_code', width: 110 },
  { headerName: '인터페이스명', field: 'interface_name', flex: 1.5 },
  { headerName: '유형', field: 'interface_type', width: 80 },
  { headerName: '송신', field: 'source_system', flex: 1 },
  { headerName: '수신', field: 'target_system', flex: 1 },
  { headerName: '엔드포인트', field: 'endpoint_url', flex: 1.5 },
  { headerName: '스케줄', field: 'schedule_type', width: 80 },
  { headerName: '상태', field: '_status_label', width: 70 },
])

const logCols = withHeaderTooltips([
  { headerName: '실행일시', field: 'started_at', width: 140 },
  { headerName: '유형', field: 'execution_type', width: 70 },
  { headerName: '상태', field: 'status', width: 70 },
  { headerName: '소요시간', field: 'duration_label', width: 80 },
  { headerName: '전체건수', field: 'total_records', width: 75 },
  { headerName: '성공', field: 'success_records', width: 60 },
  { headerName: '오류', field: 'error_records', width: 60 },
  { headerName: '오류메시지', field: 'error_message', flex: 1 },
])

const rows = ref<any[]>([])

async function loadData() {
  try {
    const res = await adminSystemApi.interfaces()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        ...r,
        _status_label: r.status === 'ACTIVE' ? '활성' : r.status === 'MAINTENANCE' ? '점검 중' : r.status === 'INACTIVE' ? '비활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('InterfaceStd: API call failed, using mock data', e)
    rows.value = [
      { interface_code: 'IF-A001', interface_name: 'OpenMetadata 카탈로그 동기화', interface_type: 'REST', source_system: '데이터허브', target_system: 'OpenMetadata', endpoint_url: '/api/v1/metadata/sync', schedule_type: 'BATCH', status: 'ACTIVE', _status_label: '활성' },
      { interface_code: 'IF-A002', interface_name: 'Kafka 이벤트 수신', interface_type: 'KAFKA', source_system: 'Kafka Broker', target_system: '데이터허브', endpoint_url: '', schedule_type: 'REALTIME', status: 'ACTIVE', _status_label: '활성' },
    ]
  }
}

onMounted(() => loadData())

function openRegister() {
  Object.assign(regForm, initRegForm())
  showRegister.value = true
}

async function onRowClick(event: any) {
  const row = event.data
  if (row.id) {
    try {
      const res = await adminSystemApi.getInterface(row.id)
      detailData.value = res.data.data
    } catch { detailData.value = row }
  } else {
    detailData.value = row
  }
  isEditing.value = false
  showDetail.value = true
  loadLogs()
}

async function loadLogs() {
  logRows.value = []
  const id = detailData.value?.id
  if (!id) return
  try {
    const res = await adminSystemApi.interfaceLogs(id, { page_size: 20 })
    const items = res.data.items || []
    logRows.value = items.map((l: any) => ({
      ...l,
      started_at: l.started_at ? String(l.started_at).replace('T', ' ').substring(0, 19) : '-',
      duration_label: l.duration_ms != null ? (l.duration_ms >= 1000 ? (l.duration_ms / 1000).toFixed(1) + 's' : l.duration_ms + 'ms') : '-',
    }))
  } catch { /* no logs */ }
}

function startEdit() {
  const d = detailData.value
  Object.assign(editForm, {
    interface_name: d.interface_name, interface_type: d.interface_type, protocol: d.protocol,
    data_format: d.data_format, source_system: d.source_system, target_system: d.target_system,
    endpoint_url: d.endpoint_url, schedule_type: d.schedule_type, schedule_cron: d.schedule_cron,
    timeout_ms: d.timeout_ms, retry_count: d.retry_count, status: d.status, description: d.description,
  })
  isEditing.value = true
}

async function handleSaveEdit() {
  const id = detailData.value?.id
  if (!id) return
  try {
    await adminSystemApi.updateInterface(id, { ...editForm })
    message.success('수정되었습니다.')
    isEditing.value = false
    showDetail.value = false
    await loadData()
  } catch { message.error('수정에 실패했습니다.') }
}

async function handleRegister() {
  if (!regForm.interface_name.trim()) { message.warning('인터페이스명을 입력해주세요.'); return }
  try {
    await adminSystemApi.createInterface({ ...regForm })
    message.success('등록되었습니다.')
    showRegister.value = false
    await loadData()
  } catch { message.error('등록에 실패했습니다.') }
}

async function handleDelete() {
  const id = detailData.value?.id
  if (!id) { message.warning('삭제할 수 없습니다.'); return }
  try {
    await adminSystemApi.deleteInterface(id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    await loadData()
  } catch { message.error('삭제에 실패했습니다.') }
}

async function handleTest() {
  const id = detailData.value?.id
  if (!id) { message.warning('연결 테스트를 실행할 수 없습니다.'); return }
  testing.value = true
  try {
    const res = await adminSystemApi.testInterface(id)
    message.success(res.data.message || '연결 테스트 성공')
    await loadLogs()
  } catch { message.error('연결 테스트에 실패했습니다.') }
  finally { testing.value = false }
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
.empty-text { padding: 20px; text-align: center; color: #999; font-size: 13px; }
</style>
