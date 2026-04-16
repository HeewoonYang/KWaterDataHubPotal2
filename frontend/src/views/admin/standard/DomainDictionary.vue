<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>도메인사전</h2>
      <p class="page-desc">K-water 표준 도메인사전을 조회하고 관리합니다.</p>
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
        <div class="filter-group"><label>데이터유형</label><select v-model="filterType"><option value="">전체</option><option>NUMERIC</option><option>VARCHAR</option><option>CHAR</option><option>TIMESTAMP</option><option>DATE</option><option>CLOB</option><option>BLOB</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="searchText" placeholder="도메인명/코드 검색" @keyup.enter="loadData" /></div>
        <div class="filter-actions"><button class="btn btn-primary" @click="loadData"><SearchOutlined /> 조회</button></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ total }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-success" @click="showModal = true"><PlusOutlined /> 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportExcel"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="defCol" :pagination="true" :paginationPageSize="20" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>
    <AdminModal :visible="showModal" :title="editId ? '도메인 수정' : '도메인 등록'" @close="closeModal">
      <div class="modal-form">
        <div class="form-row"><label>도메인그룹 *</label><input v-model="form.domain_group" /></div>
        <div class="form-row"><label>도메인명 *</label><input v-model="form.domain_name" /></div>
        <div class="form-row"><label>도메인코드 *</label><input v-model="form.domain_code" /></div>
        <div class="form-row"><label>데이터유형 *</label><select v-model="form.data_type"><option>NUMERIC</option><option>VARCHAR</option><option>CHAR</option><option>TIMESTAMP</option><option>DATE</option><option>CLOB</option><option>BLOB</option></select></div>
        <div class="form-row"><label>길이</label><input type="number" v-model.number="form.length" /></div>
        <div class="form-row"><label>소수점</label><input type="number" v-model.number="form.decimal_places" /></div>
        <div class="form-row"><label>설명</label><textarea v-model="form.description" rows="3"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" @click="closeModal">취소</button>
        <button class="btn btn-primary" @click="saveDomain">{{ editId ? '수정' : '등록' }}</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { DatabaseOutlined, AppstoreOutlined, NumberOutlined, FontSizeOutlined, SearchOutlined, PlusOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '@/components/AdminModal.vue'
import { domainApi, importExportApi } from '@/api/standard.api'
import type { StdDomain } from '@/types/standard'

ModuleRegistry.registerModules([AllCommunityModule])

const searchText = ref('')
const filterGroup = ref('')
const filterType = ref('')
const total = ref(0)
const rowData = ref<StdDomain[]>([])
const showModal = ref(false)
const editId = ref<number | null>(null)
const domainGroups = ['범주', '식별자', '수치값', '텍스트', '이름', '기타', '날짜', '주소', '등급', '분류', '상태']
const form = ref({ domain_group: '', domain_name: '', domain_code: '', data_type: 'VARCHAR', length: 0, decimal_places: 0, description: '' })

const stats = ref<{ icon: Component; label: string; value: string; color: string }[]>([
  { icon: DatabaseOutlined, label: '전체 도메인', value: '0', color: '#0066CC' },
  { icon: AppstoreOutlined, label: '그룹 수', value: '11', color: '#28A745' },
  { icon: NumberOutlined, label: 'NUMERIC', value: '0', color: '#6F42C1' },
  { icon: FontSizeOutlined, label: 'VARCHAR', value: '0', color: '#FFC107' },
])

const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '도메인그룹', field: 'domain_group', flex: 0.7, minWidth: 90 },
  { headerName: '도메인명', field: 'domain_name', flex: 2, minWidth: 150 },
  { headerName: '도메인코드', field: 'domain_code', flex: 1.5, minWidth: 120 },
  { headerName: '데이터유형', field: 'data_type', flex: 0.7, minWidth: 90 },
  { headerName: '길이', field: 'length', flex: 0.5, minWidth: 60 },
  { headerName: '소수점', field: 'decimal_places', flex: 0.5, minWidth: 60 },
  { headerName: '설명', field: 'description', flex: 2, minWidth: 150 },
])

async function loadData() {
  try {
    const res = await domainApi.list({ page: 1, page_size: 1000, search: searchText.value })
    rowData.value = res.data.items
    total.value = res.data.total
    stats.value[0].value = total.value.toLocaleString()
    stats.value[2].value = rowData.value.filter(d => d.data_type === 'NUMERIC').length.toLocaleString()
    stats.value[3].value = rowData.value.filter(d => d.data_type === 'VARCHAR').length.toLocaleString()
  } catch { /* API 미연결 시 빈 데이터 */ }
}

function onRowClick(event: any) {
  const data = event.data as StdDomain
  editId.value = data.id
  form.value = { domain_group: data.domain_group, domain_name: data.domain_name, domain_code: data.domain_code, data_type: data.data_type, length: data.length || 0, decimal_places: data.decimal_places || 0, description: data.description || '' }
  showModal.value = true
}

async function saveDomain() {
  try {
    if (editId.value) { await domainApi.update(editId.value, form.value) }
    else { await domainApi.create(form.value) }
    closeModal()
    loadData()
  } catch (e) { console.error(e) }
}

function closeModal() { showModal.value = false; editId.value = null; form.value = { domain_group: '', domain_name: '', domain_code: '', data_type: 'VARCHAR', length: 0, decimal_places: 0, description: '' } }

async function exportExcel() {
  try { const res = await importExportApi.exportExcel('domain'); const url = URL.createObjectURL(new Blob([res.data])); const a = document.createElement('a'); a.href = url; a.download = 'std_domain_export.xlsx'; a.click(); URL.revokeObjectURL(url) } catch (e) { console.error(e) }
}

onMounted(loadData)
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';</style>
