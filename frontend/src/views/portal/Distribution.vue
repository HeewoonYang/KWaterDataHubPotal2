<template>
  <div class="dist-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">유통 데이터 목록</span>
    </nav>

    <div class="page-header">
      <h2>유통 데이터 목록</h2>
      <p>유통 가능한 데이터셋을 조회하고 신청하세요.</p>
    </div>

    <!-- 검색/필터 -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group">
          <label>분류</label>
          <select v-model="filterCategory">
            <option value="">전체</option>
            <option value="water">수자원</option>
            <option value="supply">수도</option>
            <option value="env">환경</option>
            <option value="mgmt">경영</option>
          </select>
        </div>
        <div class="filter-group">
          <label>데이터 등급</label>
          <select v-model="filterGrade">
            <option value="">전체</option>
            <option value="3">L3 (공개)</option>
            <option value="2">L2 (내부공유)</option>
          </select>
        </div>
        <div class="filter-group">
          <label>포맷</label>
          <select v-model="filterFormat">
            <option value="">전체</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="api">API</option>
          </select>
        </div>
        <div class="filter-group search-group">
          <label>검색</label>
          <input type="text" v-model="searchText" placeholder="데이터셋명 검색" />
        </div>
        <div class="filter-actions">
          <button class="btn btn-primary" @click="onSearch"><SearchOutlined /> 조회</button>
          <button class="btn btn-outline" @click="onReset"><ReloadOutlined /> 초기화</button>
        </div>
      </div>
    </div>

    <!-- AG Grid 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ distData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-primary"><ShoppingCartOutlined /> 일괄 신청</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, distData, '데이터_유통')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="distData"
          :columnDefs="columnDefs"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="10"
          :rowSelection="'multiple'"
          domLayout="autoHeight"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../utils/exportExcel'
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  SearchOutlined,
  ReloadOutlined,
  ShoppingCartOutlined,
  FileExcelOutlined,
} from '@ant-design/icons-vue'
import { distributionApi } from '../../api/portal.api'

ModuleRegistry.registerModules([AllCommunityModule])

const filterCategory = ref('')
const filterGrade = ref('')
const filterFormat = ref('')
const searchText = ref('')

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }

const columnDefs: ColDef[] = [
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, maxWidth: 40, flex: 0, sortable: false, resizable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋명', field: 'name', flex: 2, minWidth: 200 },
  { headerName: '분류', field: 'category', width: 80, maxWidth: 80, flex: 0 },
  { headerName: '등급', field: 'gradeLabel', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '포맷', field: 'format', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '건수', field: 'rows', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '제공기관', field: 'provider', flex: 1, minWidth: 100 },
  { headerName: '갱신일', field: 'updated', flex: 1, minWidth: 110 },
  { headerName: '상태', field: 'status', width: 70, maxWidth: 70, flex: 0 },
]

// Fallback mock data
const defaultDistData = [
  { id: 1, name: '댐 수위 관측 데이터 (실시간)', category: '수자원', gradeLabel: 'L3', format: 'API', rows: '1.2억건', provider: '수자원부', updated: '2026-03-25', status: '활성' },
  { id: 2, name: '상수도 수질검사 결과', category: '수도', gradeLabel: 'L2', format: 'CSV', rows: '52만건', provider: '수도부', updated: '2026-03-24', status: '활성' },
  { id: 3, name: '하천 유량 관측 데이터', category: '수자원', gradeLabel: 'L3', format: 'JSON', rows: '5,200만건', provider: '수자원부', updated: '2026-03-24', status: '활성' },
  { id: 4, name: '전력 사용량 통계 (월별)', category: '경영', gradeLabel: 'L3', format: 'CSV', rows: '15,600건', provider: '경영부', updated: '2026-03-23', status: '활성' },
  { id: 5, name: '상수관로 GIS 데이터', category: '수도', gradeLabel: 'L2', format: 'JSON', rows: '320만건', provider: '수도부', updated: '2026-03-22', status: '활성' },
  { id: 6, name: '강수량 예측 API', category: '환경', gradeLabel: 'L3', format: 'API', rows: 'API', provider: '환경부', updated: '2026-03-25', status: '활성' },
  { id: 7, name: '환경영향평가 보고서', category: '환경', gradeLabel: 'L2', format: 'CSV', rows: '8,200건', provider: '환경부', updated: '2026-03-20', status: '비활성' },
]

const distData = ref(defaultDistData)

async function fetchData() {
  try {
    const params: Record<string, any> = { page: 1, page_size: 20 }
    if (filterCategory.value) params.category = filterCategory.value
    if (filterGrade.value) params.grade = filterGrade.value
    if (filterFormat.value) params.format = filterFormat.value
    if (searchText.value) params.keyword = searchText.value
    const res = await distributionApi.datasets(params)
    if (res.data?.items?.length) {
      distData.value = res.data.items.map((item: any) => ({
        id: item.id,
        name: item.distribution_name || item.dataset_name || '',
        category: item.classification_name || '',
        gradeLabel: item.grade_code || '',
        format: (item.allowed_formats && item.allowed_formats[0]) || '',
        rows: item.download_count ? `${item.download_count}건` : '-',
        provider: item.owner_department || '',
        updated: '',
        status: item.is_downloadable ? '활성' : '비활성',
      }))
    }
  } catch (e) {
    console.error('유통 데이터 조회 실패:', e)
  }
}

onMounted(() => { fetchData() })

function onSearch() { fetchData() }
function onReset() { filterCategory.value = ''; filterGrade.value = ''; filterFormat.value = ''; searchText.value = ''; fetchData() }
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.dist-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  p { font-size: $font-size-sm; color: $text-muted; }
}
.search-filter { background: #f5f7fa; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; }
.filter-row { display: flex; align-items: flex-end; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group {
  display: flex; flex-direction: column; gap: $spacing-xs;
  label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; }
  select, input { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 130px; background: $white; outline: none; &:focus { border-color: $primary; } }
  &.search-group { flex: 1; input { width: 100%; } }
}
.filter-actions { display: flex; gap: $spacing-sm; }

.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.table-actions { display: flex; align-items: center; gap: $spacing-sm; }
.btn-excel {
  background: none; border: 1px solid #2e7d32; color: #2e7d32; width: 32px; height: 32px; border-radius: $radius-md; font-size: 18px; display: flex; align-items: center; justify-content: center; transition: all $transition-fast;
  &:hover { background: #2e7d32; color: $white; }
}

.ag-grid-wrapper {
  :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; --ag-row-border-color: #f0f0f0; --ag-selected-row-background-color: #e8f0fe; font-family: $font-family; }
  :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; }
  :deep(.ag-header-cell) { color: #fff; }
}

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .filter-row { flex-direction: column; align-items: stretch; }
}
</style>
