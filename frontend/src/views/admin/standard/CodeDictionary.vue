<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>코드사전</h2>
      <p class="page-desc">K-water 표준 코드사전을 조회하고 관리합니다. (총 139,520건)</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>코드그룹</label><input v-model="filterGroup" placeholder="코드그룹 필터" /></div>
        <div class="filter-group"><label>시스템명</label><input v-model="filterSystem" placeholder="시스템명 필터" /></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="searchText" placeholder="코드ID/코드명 검색" @keyup.enter="loadData" /></div>
        <div class="filter-actions"><button class="btn btn-primary" @click="loadData"><SearchOutlined /> 조회</button></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ total.toLocaleString() }}</strong>건 ({{ page }}/{{ totalPages }} 페이지)</span>
        <div class="table-actions">
          <button class="btn btn-success" @click="showModal = true"><PlusOutlined /> 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportExcel"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="50" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
      <div class="pagination-bar">
        <button class="btn btn-secondary" :disabled="page <= 1" @click="page--; loadData()">이전</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-secondary" :disabled="page >= totalPages" @click="page++; loadData()">다음</button>
      </div>
    </div>
    <AdminModal :visible="showModal" :title="editId ? '코드 수정' : '코드 등록'" @close="closeModal">
      <div class="modal-form">
        <div class="form-row"><label>코드그룹 *</label><input v-model="form.code_group" /></div>
        <div class="form-row"><label>코드그룹명 *</label><input v-model="form.code_group_name" /></div>
        <div class="form-row"><label>코드ID *</label><input v-model="form.code_id" /></div>
        <div class="form-row"><label>코드값</label><input v-model="form.code_value" /></div>
        <div class="form-row"><label>코드값명</label><input v-model="form.code_value_name" /></div>
        <div class="form-row"><label>시스템명</label><input v-model="form.system_name" /></div>
        <div class="form-row"><label>부모코드명</label><input v-model="form.parent_code_name" /></div>
        <div class="form-row"><label>설명</label><textarea v-model="form.description" rows="3"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" @click="closeModal">취소</button>
        <button class="btn btn-primary" @click="saveCode">{{ editId ? '수정' : '등록' }}</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { TagsOutlined, ClusterOutlined, ApartmentOutlined, BarcodeOutlined, SearchOutlined, PlusOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '@/components/AdminModal.vue'
import { codeApi, importExportApi } from '@/api/standard.api'
import type { StdCode } from '@/types/standard'

ModuleRegistry.registerModules([AllCommunityModule])

const searchText = ref('')
const filterGroup = ref('')
const filterSystem = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 50
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)
const rowData = ref<StdCode[]>([])
const showModal = ref(false)
const editId = ref<number | null>(null)
const form = ref({ code_group: '', code_group_name: '', code_id: '', code_value: '', code_value_name: '', system_name: '', parent_code_name: '', description: '' })

const stats = ref<{ icon: Component; label: string; value: string; color: string }[]>([
  { icon: TagsOutlined, label: '전체 코드', value: '0', color: '#0066CC' },
  { icon: ClusterOutlined, label: '코드그룹', value: '43', color: '#28A745' },
  { icon: ApartmentOutlined, label: '계층 코드', value: '0', color: '#6F42C1' },
  { icon: BarcodeOutlined, label: '시스템', value: '0', color: '#FFC107' },
])

const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 60, flex: 0 },
  { headerName: '코드그룹', field: 'code_group', width: 90, maxWidth: 100, flex: 0 },
  { headerName: '코드그룹명', field: 'code_group_name', flex: 1.5, minWidth: 130 },
  { headerName: '코드ID', field: 'code_id', flex: 1, minWidth: 100 },
  { headerName: '코드값', field: 'code_value', width: 80, maxWidth: 100, flex: 0 },
  { headerName: '코드값명', field: 'code_value_name', flex: 1.5, minWidth: 130 },
  { headerName: '시스템', field: 'system_name', width: 80, maxWidth: 100, flex: 0 },
  { headerName: '부모코드', field: 'parent_code_name', width: 100, maxWidth: 120, flex: 0 },
  { headerName: '정렬', field: 'sort_order', width: 55, maxWidth: 55, flex: 0 },
]

async function loadData() {
  try {
    const res = await codeApi.list({ page: page.value, page_size: pageSize, search: searchText.value })
    rowData.value = res.data.items
    total.value = res.data.total
    stats.value[0].value = total.value.toLocaleString()
  } catch { /* API 미연결 */ }
}

function onRowClick(event: any) {
  const data = event.data as StdCode
  editId.value = data.id
  form.value = { code_group: data.code_group, code_group_name: data.code_group_name, code_id: data.code_id, code_value: data.code_value || '', code_value_name: data.code_value_name || '', system_name: data.system_name || '', parent_code_name: data.parent_code_name || '', description: data.description || '' }
  showModal.value = true
}

async function saveCode() {
  try {
    if (editId.value) { await codeApi.update(editId.value, form.value) }
    else { await codeApi.create(form.value) }
    closeModal()
    loadData()
  } catch (e) { console.error(e) }
}

function closeModal() { showModal.value = false; editId.value = null; form.value = { code_group: '', code_group_name: '', code_id: '', code_value: '', code_value_name: '', system_name: '', parent_code_name: '', description: '' } }

async function exportExcel() {
  try { const res = await importExportApi.exportExcel('code'); const url = URL.createObjectURL(new Blob([res.data])); const a = document.createElement('a'); a.href = url; a.download = 'std_code_export.xlsx'; a.click(); URL.revokeObjectURL(url) } catch (e) { console.error(e) }
}

onMounted(loadData)
</script>
<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
.pagination-bar { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; }
</style>
