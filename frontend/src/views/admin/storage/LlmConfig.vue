<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>LLM/T2SQL 설정*</h2>
      <p class="page-desc">자연어 질의를 SQL로 변환하는 LLM 모델을 설정하고 테스트합니다.</p>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">LLM 모델 <strong>{{ rows.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 모델 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, 'LLM_모델_목록')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- T2SQL 테스트 -->
    <div class="table-section" style="margin-top: 16px;">
      <div class="table-header"><span class="table-count">T2SQL 테스트</span></div>
      <div style="padding: 16px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px;">
        <div style="display: flex; gap: 8px; margin-bottom: 12px;">
          <input v-model="testQuery" placeholder="자연어 질의 입력" style="flex: 1; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px;" />
          <button class="btn btn-primary btn-sm" @click="runTest"><ThunderboltOutlined /> SQL 변환 테스트</button>
        </div>
        <pre v-if="showResult" style="background: #f5f5f5; padding: 14px; border-radius: 6px; font-size: 12px; line-height: 1.6; overflow-x: auto; margin: 0;"><code>{{ sqlResult }}</code></pre>
      </div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.modelName + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">LLM 모델 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">모델명</span><span class="info-value">{{ detailData.modelName }}</span></div>
          <div class="modal-info-item"><span class="info-label">프로바이더</span><span class="info-value">{{ detailData.provider }}</span></div>
          <div class="modal-info-item"><span class="info-label">API 엔드포인트</span><span class="info-value">{{ detailData.apiEndpoint }}</span></div>
          <div class="modal-info-item"><span class="info-label">버전</span><span class="info-value">{{ detailData.version }}</span></div>
          <div class="modal-info-item"><span class="info-label">토큰한도</span><span class="info-value">{{ detailData.tokenLimit }}</span></div>
          <div class="modal-info-item"><span class="info-label">기본모델</span><span class="info-value">{{ detailData.isDefault }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 등록 팝업 -->
    <AdminModal :visible="showRegister" title="LLM 모델 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">모델명</label><input v-model="regForm.modelName" placeholder="모델명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">프로바이더</label><select v-model="regForm.provider"><option>OpenAI</option><option>Anthropic</option><option>Self-hosted</option></select></div>
          <div class="modal-form-group"><label class="required">버전</label><input v-model="regForm.version" placeholder="모델 버전" /></div>
        </div>
        <div class="modal-form-group"><label class="required">API 엔드포인트</label><input v-model="regForm.apiEndpoint" placeholder="https://api.example.com/v1" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label>토큰한도</label><input v-model="regForm.tokenLimit" placeholder="128,000" /></div>
          <div class="modal-form-group"><label>기본모델</label><select v-model="regForm.isDefault"><option>Y</option><option>N</option></select></div>
        </div>
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
import { ref, reactive } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }

const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '모델명', field: 'modelName', flex: 1.2, minWidth: 120 },
  { headerName: '프로바이더', field: 'provider', flex: 0.8, minWidth: 90 },
  { headerName: 'API 엔드포인트', field: 'apiEndpoint', flex: 1.5, minWidth: 180 },
  { headerName: '버전', field: 'version', flex: 1.2, minWidth: 140 },
  { headerName: '토큰한도', field: 'tokenLimit', flex: 0.7, minWidth: 80 },
  { headerName: '기본모델', field: 'isDefault', flex: 0.5, minWidth: 60 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rows = ref([
  { modelName: 'GPT-4o', provider: 'OpenAI', apiEndpoint: 'https://api.openai.com/v1', version: 'gpt-4o-2024-08-06', tokenLimit: '128,000', isDefault: 'Y', status: '활성' },
  { modelName: 'Claude Sonnet 4', provider: 'Anthropic', apiEndpoint: 'https://api.anthropic.com/v1', version: 'claude-sonnet-4-20250514', tokenLimit: '200,000', isDefault: 'N', status: '활성' },
  { modelName: 'Local LLM (vLLM)', provider: 'Self-hosted', apiEndpoint: 'http://10.0.20.10:8000/v1', version: 'Qwen2.5-72B', tokenLimit: '32,768', isDefault: 'N', status: '비활성' },
])

const testQuery = ref('')
const showResult = ref(false)
const sqlResult = `SELECT site_name, AVG(water_level) as avg_level\nFROM collect_wq.water_level_data\nWHERE measure_dt >= '2026-01-01'\nGROUP BY site_name\nORDER BY avg_level DESC`

function runTest() {
  if (!testQuery.value) { message.warning('자연어 질의를 입력하세요.'); return }
  showResult.value = true
  message.success('SQL 변환이 완료되었습니다.')
}

const regForm = reactive({ modelName: '', provider: 'OpenAI', apiEndpoint: '', version: '', tokenLimit: '', isDefault: 'N' })

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

function handleRegister() {
  if (!regForm.modelName || !regForm.apiEndpoint) { message.warning('필수 항목을 입력하세요.'); return }
  rows.value.push({ ...regForm, status: '활성' })
  message.success('등록되었습니다.')
  showRegister.value = false
  Object.assign(regForm, { modelName: '', provider: 'OpenAI', apiEndpoint: '', version: '', tokenLimit: '', isDefault: 'N' })
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
