<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>용어사전</h2>
      <p class="page-desc">K-water 표준 용어사전을 조회하고 관리합니다. (총 41,724건)</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>도메인그룹</label><select v-model="filterGroup"><option value="">전체</option><option v-for="g in domainGroups" :key="g">{{ g }}</option></select></div>
        <div class="filter-group"><label>데이터유형</label><select v-model="filterType"><option value="">전체</option><option>VARCHAR</option><option>NUMERIC</option><option>CHAR</option><option>DATE</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="searchText" placeholder="용어명/영문명 검색" @keyup.enter="loadData" /></div>
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
    <AdminModal :visible="showModal" :title="editId ? '용어 수정' : '용어 등록'" @close="closeModal">
      <div class="modal-form">
        <div class="form-row"><label>용어명 *</label><input v-model="form.term_name" /></div>
        <div class="form-row"><label>영문명 *</label><input v-model="form.english_name" /></div>
        <div class="form-row"><label>영문의미</label><input v-model="form.english_meaning" /></div>
        <div class="form-row"><label>도메인코드</label><input v-model="form.domain_code" /></div>
        <div class="form-row"><label>도메인그룹</label><input v-model="form.domain_group" /></div>
        <div class="form-row"><label>데이터유형</label><select v-model="form.data_type"><option>VARCHAR</option><option>NUMERIC</option><option>CHAR</option><option>DATE</option><option>CLOB</option><option>TIMESTAMP</option></select></div>
        <div class="form-row"><label>길이</label><input type="number" v-model.number="form.length" /></div>
        <div class="form-row"><label>설명</label><textarea v-model="form.description" rows="3"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" @click="closeModal">취소</button>
        <button class="btn btn-primary" @click="saveTerm">{{ editId ? '수정' : '등록' }}</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { ProfileOutlined, DatabaseOutlined, FontSizeOutlined, NumberOutlined, SearchOutlined, PlusOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '@/components/AdminModal.vue'
import { termApi, importExportApi } from '@/api/standard.api'
import type { StdTerm } from '@/types/standard'

ModuleRegistry.registerModules([AllCommunityModule])

const searchText = ref('')
const filterGroup = ref('')
const filterType = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = 50
const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)
const rowData = ref<StdTerm[]>([])
const showModal = ref(false)
const editId = ref<number | null>(null)
const domainGroups = ['등급', '상태', '수량', '확인', 'ID', '날짜', '금액', '수치값', '이름', '시설']
const form = ref({ term_name: '', english_name: '', english_meaning: '', domain_code: '', domain_group: '', data_type: 'VARCHAR', length: 0, description: '' })

const stats = ref<{ icon: Component; label: string; value: string; color: string }[]>([
  { icon: ProfileOutlined, label: '전체 용어', value: '0', color: '#0066CC' },
  { icon: DatabaseOutlined, label: '도메인 분류', value: '3,891', color: '#28A745' },
  { icon: FontSizeOutlined, label: 'VARCHAR', value: '0', color: '#6F42C1' },
  { icon: NumberOutlined, label: 'NUMERIC', value: '0', color: '#FFC107' },
])

const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 60, flex: 0 },
  { headerName: '용어명', field: 'term_name', flex: 2, minWidth: 180 },
  { headerName: '영문명', field: 'english_name', flex: 1.5, minWidth: 120 },
  { headerName: '도메인코드', field: 'domain_code', flex: 1, minWidth: 100 },
  { headerName: '도메인그룹', field: 'domain_group', width: 100, maxWidth: 110, flex: 0 },
  { headerName: '데이터유형', field: 'data_type', width: 90, maxWidth: 100, flex: 0 },
  { headerName: '길이', field: 'length', width: 60, maxWidth: 60, flex: 0 },
  { headerName: '소수점', field: 'decimal_places', width: 65, maxWidth: 65, flex: 0 },
]

async function loadData() {
  try {
    const res = await termApi.list({ page: page.value, page_size: pageSize, search: searchText.value })
    rowData.value = res.data.items
    total.value = res.data.total
    stats.value[0].value = total.value.toLocaleString()
  } catch { /* API 미연결 */ }
}

function onRowClick(event: any) {
  const data = event.data as StdTerm
  editId.value = data.id
  form.value = { term_name: data.term_name, english_name: data.english_name, english_meaning: data.english_meaning || '', domain_code: data.domain_code || '', domain_group: data.domain_group || '', data_type: data.data_type || 'VARCHAR', length: data.length || 0, description: data.description || '' }
  showModal.value = true
}

async function saveTerm() {
  try {
    if (editId.value) { await termApi.update(editId.value, form.value) }
    else { await termApi.create(form.value) }
    closeModal()
    loadData()
  } catch (e) { console.error(e) }
}

function closeModal() { showModal.value = false; editId.value = null; form.value = { term_name: '', english_name: '', english_meaning: '', domain_code: '', domain_group: '', data_type: 'VARCHAR', length: 0, description: '' } }

async function exportExcel() {
  try { const res = await importExportApi.exportExcel('term'); const url = URL.createObjectURL(new Blob([res.data])); const a = document.createElement('a'); a.href = url; a.download = 'std_term_export.xlsx'; a.click(); URL.revokeObjectURL(url) } catch (e) { console.error(e) }
}

onMounted(loadData)
</script>
<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
.pagination-bar { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; }
</style>
