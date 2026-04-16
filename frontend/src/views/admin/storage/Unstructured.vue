<template>
  <div class="admin-page">
    <div class="page-header"><h2>비정형 저장소</h2><p class="page-desc">비정형 데이터(파일, 이미지, 문서) 저장소를 관리합니다.</p></div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label"><div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div><div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">저장소 버킷 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 버킷 생성</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '비정형_저장소')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 버킷 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">버킷 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">버킷명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.type }}</span></div>
          <div class="modal-info-item"><span class="info-label">파일 수</span><span class="info-value">{{ detailData.files }}</span></div>
          <div class="modal-info-item"><span class="info-label">용량</span><span class="info-value">{{ detailData.size }}</span></div>
          <div class="modal-info-item"><span class="info-label">보존 정책</span><span class="info-value">{{ detailData.retention }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-danger" @click="handleDelete"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 버킷 생성 팝업 -->
    <AdminModal :visible="showRegister" title="버킷 생성" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">버킷명</label><input v-model="regForm.storage_name" placeholder="버킷명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">유형</label><select v-model="regForm.storage_type"><option>문서</option><option>GIS</option><option>이미지</option><option>로그파일</option></select></div>
          <div class="modal-form-group"><label class="required">버킷 경로</label><input v-model="regForm.bucket_name" placeholder="버킷 경로 입력" /></div>
        </div>
        <div class="modal-form-group"><label>용량(GB)</label><input v-model="regForm.total_capacity_gb" type="number" placeholder="총 용량(GB)" /></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 생성</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'

import { ref, reactive, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { FolderOutlined, FileOutlined, PictureOutlined, CloudOutlined, PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminStorageApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const defCol = { ...baseDefaultColDef }
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: FolderOutlined, label: '총 버킷', value: '8', color: '#0066CC' },
  { icon: FileOutlined, label: '총 파일 수', value: '45,230', color: '#28A745' },
  { icon: CloudOutlined, label: '사용 용량', value: '12.5 TB', color: '#9b59b6' },
  { icon: PictureOutlined, label: '이미지/GIS', value: '8,450', color: '#FFC107' },
]
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '버킷명', field: 'name', flex: 2 },
  { headerName: '유형', field: 'type', width: 100 },
  { headerName: '파일 수', field: 'files', width: 80 },
  { headerName: '용량', field: 'size', width: 90 },
  { headerName: '보존 정책', field: 'retention', width: 110 },
  { headerName: '상태', field: 'status', width: 70 },
])
const rows = ref([
  { name: 'datahub-documents', type: '문서(PDF/HWP)', files: '12,500', size: '3.5 TB', retention: '영구보관', status: '활성' },
  { name: 'datahub-gis-data', type: 'GIS (SHP/GeoJSON)', files: '5,200', size: '4.2 TB', retention: '영구보관', status: '활성' },
  { name: 'datahub-images', type: '이미지(위성/CCTV)', files: '3,250', size: '2.8 TB', retention: '3년', status: '활성' },
  { name: 'datahub-logs', type: '로그파일', files: '24,280', size: '2.0 TB', retention: '1년', status: '활성' },
])

const regForm = reactive({ storage_name: '', storage_type: '문서', bucket_name: '', total_capacity_gb: '' })

async function loadData() {
  try {
    const res = await adminStorageApi.unstructured()
    const items = res.data.data
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        name: r.storage_name || r.bucket_name || r.name || '',
        type: r.storage_type || r.type || '',
        files: r.files || '-',
        size: r.total_capacity_gb != null ? r.total_capacity_gb + ' GB' : (r.size || '-'),
        retention: r.retention || '-',
        status: r.status === 'ACTIVE' ? '활성' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('Unstructured: API call failed, using mock data', e)
  }
}

onMounted(() => loadData())

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

async function handleRegister() {
  try {
    await adminStorageApi.createUnstructured(regForm)
    message.success('등록되었습니다.')
    showRegister.value = false
    Object.assign(regForm, { storage_name: '', storage_type: '문서', bucket_name: '', total_capacity_gb: '' })
    await loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.message || '등록에 실패했습니다.')
  }
}

async function handleDelete() {
  const id = detailData.value._raw?.id || detailData.value.id
  if (!id) { message.error('삭제할 항목의 ID를 찾을 수 없습니다.'); return }
  try {
    await adminStorageApi.deleteUnstructured(id)
    message.success('삭제되었습니다.')
    showDetail.value = false
    await loadData()
  } catch (e: any) {
    message.error(e?.response?.data?.message || '삭제에 실패했습니다.')
  }
}
</script>
<style lang="scss" scoped>@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
