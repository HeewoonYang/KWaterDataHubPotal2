<template>
  <div class="admin-page">
    <div class="page-header"><h2>기능 검토</h2><p class="page-desc">시스템 기능 최적화 및 개선 사항을 관리합니다.</p></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">검토 항목 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 항목 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '최적화_검토')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 검토 항목 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.item + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">검토 항목 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">검토 항목</span><span class="info-value">{{ detailData.item }}</span></div>
          <div class="modal-info-item"><span class="info-label">분류</span><span class="info-value">{{ detailData.category }}</span></div>
          <div class="modal-info-item"><span class="info-label">우선순위</span><span class="info-value">{{ detailData.priority }}</span></div>
          <div class="modal-info-item"><span class="info-label">담당자</span><span class="info-value">{{ detailData.assignee }}</span></div>
          <div class="modal-info-item"><span class="info-label">진행 상태</span><span class="info-value"><span class="badge" :class="detailData.status === '완료' ? 'badge-success' : detailData.status === '진행 중' ? 'badge-info' : 'badge-warning'">{{ detailData.status }}</span></span></div>
          <div class="modal-info-item"><span class="info-label">기한</span><span class="info-value">{{ detailData.deadline }}</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 항목 추가 팝업 -->
    <AdminModal :visible="showRegister" title="항목 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">검토 항목</label><input v-model="regForm.title" placeholder="검토 항목 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">분류</label><select v-model="regForm.event_type"><option>성능</option><option>UI/UX</option><option>수집</option><option>보안</option></select></div>
          <div class="modal-form-group"><label class="required">우선순위</label><select v-model="regForm.severity"><option value="HIGH">높음</option><option value="MEDIUM">중간</option><option value="LOW">낮음</option></select></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">담당자</label><input v-model="regAssignee" placeholder="담당자" /></div>
          <div class="modal-form-group"><label class="required">기한</label><input v-model="regDeadline" type="date" /></div>
        </div>
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

import { ref, reactive, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminOperationApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '검토 항목', field: 'item', flex: 2 },
  { headerName: '분류', field: 'category', width: 100 },
  { headerName: '우선순위', field: 'priority', width: 80 },
  { headerName: '담당자', field: 'assignee', width: 90 },
  { headerName: '진행 상태', field: 'status', width: 90 },
  { headerName: '기한', field: 'deadline', width: 110 },
])
const rows = ref([
  { item: 'AG Grid 대용량 데이터 가상화', category: '성능', priority: '높음', assignee: '관리자', status: '완료', deadline: '2026-03-15' },
  { item: 'API 응답 캐싱 전략 개선', category: '성능', priority: '높음', assignee: '김매니저', status: '진행 중', deadline: '2026-04-01' },
  { item: '대시보드 차트 렌더링 최적화', category: 'UI/UX', priority: '중간', assignee: '관리자', status: '진행 중', deadline: '2026-04-15' },
  { item: 'Kafka Consumer 병렬화', category: '수집', priority: '높음', assignee: '김매니저', status: '대기', deadline: '2026-05-01' },
  { item: '접근 제어 정책 엔진 개선', category: '보안', priority: '중간', assignee: '관리자', status: '대기', deadline: '2026-05-15' },
])

const regForm = reactive({ event_type: '성능', severity: 'MEDIUM', title: '', description: '' })
const regAssignee = ref('')
const regDeadline = ref('')

async function loadData() {
  try {
    const res = await adminOperationApi.systemEvents()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        item: r.title || r.item || '',
        category: r.event_type || r.category || '',
        priority: r.severity || r.priority || '',
        assignee: r.assignee || '-',
        status: r.resolved_at ? '완료' : (r.status || '대기'),
        deadline: r.occurred_at ? String(r.occurred_at).substring(0, 10) : (r.deadline || '-'),
      }))
    }
  } catch (e) {
    console.warn('Optimize: API call failed, using mock data', e)
  }
}

onMounted(() => loadData())

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

async function handleRegister() {
  try {
    const payload = {
      ...regForm,
      description: [regAssignee.value ? `담당자: ${regAssignee.value}` : '', regDeadline.value ? `기한: ${regDeadline.value}` : ''].filter(Boolean).join(', ') || regForm.description,
    }
    await adminOperationApi.createSystemEvent(payload)
    message.success('등록되었습니다.')
    showRegister.value = false
    Object.assign(regForm, { event_type: '성능', severity: 'MEDIUM', title: '', description: '' })
    regAssignee.value = ''
    regDeadline.value = ''
    await loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.message || '등록에 실패했습니다.')
  }
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
