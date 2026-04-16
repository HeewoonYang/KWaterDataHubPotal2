<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>단어사전</h2>
      <p class="page-desc">K-water 표준 단어사전을 조회하고 관리합니다.</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>상태</label><select v-model="filterStatus"><option value="">전체</option><option value="ACTIVE">활성</option><option value="INACTIVE">비활성</option></select></div>
        <div class="filter-group"><label>속성분류</label><select v-model="filterClassifier"><option value="">전체</option><option>식별자</option><option>명칭</option><option>수치</option><option>코드</option><option>일시</option><option>내용</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="searchText" placeholder="단어명/영문명 검색" @keyup.enter="loadData" /></div>
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
    <AdminModal :visible="showModal" :title="editId ? '단어 수정' : '단어 등록'" @close="closeModal">
      <div class="modal-form">
        <div class="form-row"><label>단어명 *</label><input v-model="form.word_name" /></div>
        <div class="form-row"><label>영문명 *</label><input v-model="form.english_name" /></div>
        <div class="form-row"><label>영문의미</label><input v-model="form.english_meaning" /></div>
        <div class="form-row"><label>속성분류어</label><input v-model="form.attr_classifier" /></div>
        <div class="form-row"><label>동의어</label><input v-model="form.synonyms" /></div>
        <div class="form-row"><label>설명</label><textarea v-model="form.description" rows="3"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" @click="closeModal">취소</button>
        <button class="btn btn-primary" @click="saveWord">{{ editId ? '수정' : '등록' }}</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { BookOutlined, CheckCircleOutlined, StopOutlined, FileTextOutlined, SearchOutlined, PlusOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '@/components/AdminModal.vue'
import { wordApi, importExportApi } from '@/api/standard.api'
import type { StdWord } from '@/types/standard'

ModuleRegistry.registerModules([AllCommunityModule])

const searchText = ref('')
const filterStatus = ref('')
const filterClassifier = ref('')
const total = ref(0)
const rowData = ref<StdWord[]>([])
const showModal = ref(false)
const editId = ref<number | null>(null)
const form = ref({ word_name: '', english_name: '', english_meaning: '', attr_classifier: '', synonyms: '', description: '' })

const stats = ref<{ icon: Component; label: string; value: string; color: string }[]>([
  { icon: BookOutlined, label: '전체 단어', value: '0', color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '활성', value: '0', color: '#28A745' },
  { icon: StopOutlined, label: '비활성', value: '0', color: '#DC3545' },
  { icon: FileTextOutlined, label: '속성분류', value: '6종', color: '#FFC107' },
])

const defCol = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '단어명', field: 'word_name', flex: 2, minWidth: 150 },
  { headerName: '영문명', field: 'english_name', flex: 1.5, minWidth: 120 },
  { headerName: '영문의미', field: 'english_meaning', flex: 2, minWidth: 150 },
  { headerName: '속성분류어', field: 'attr_classifier', flex: 0.7, minWidth: 90 },
  { headerName: '동의어', field: 'synonyms', flex: 1, minWidth: 100 },
  { headerName: '상태', field: 'status', flex: 0.6, minWidth: 70 },
])

async function loadData() {
  try {
    const res = await wordApi.list({ page: 1, page_size: 1000, search: searchText.value, status: filterStatus.value })
    rowData.value = res.data.items
    total.value = res.data.total
    stats.value[0].value = total.value.toLocaleString()
    stats.value[1].value = rowData.value.filter(w => w.status === 'ACTIVE').length.toLocaleString()
    stats.value[2].value = rowData.value.filter(w => w.status === 'INACTIVE').length.toLocaleString()
  } catch { /* API 미연결 시 빈 데이터 */ }
}

function onRowClick(event: any) {
  const data = event.data as StdWord
  editId.value = data.id
  form.value = { word_name: data.word_name, english_name: data.english_name, english_meaning: data.english_meaning || '', attr_classifier: data.attr_classifier || '', synonyms: data.synonyms || '', description: data.description || '' }
  showModal.value = true
}

async function saveWord() {
  try {
    if (editId.value) {
      await wordApi.update(editId.value, form.value)
    } else {
      await wordApi.create(form.value)
    }
    closeModal()
    loadData()
  } catch (e) { console.error(e) }
}

function closeModal() {
  showModal.value = false
  editId.value = null
  form.value = { word_name: '', english_name: '', english_meaning: '', attr_classifier: '', synonyms: '', description: '' }
}

async function exportExcel() {
  try {
    const res = await importExportApi.exportExcel('word')
    const url = URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = 'std_word_export.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { console.error(e) }
}

onMounted(loadData)
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';</style>
