<template>
  <div class="mydata-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">내 데이터</span>
    </nav>

    <div class="page-header"><h2>내 데이터</h2><p>즐겨찾기, 최근 조회, 다운로드 이력을 관리합니다.</p></div>
    <div class="data-tabs">
      <button :class="{ active: tab === 'favorites' }" @click="tab = 'favorites'"><StarFilled /> 즐겨찾기 ({{ favorites.length }})</button>
      <button :class="{ active: tab === 'recent' }" @click="tab = 'recent'"><EyeOutlined /> 최근 조회 ({{ recent.length }})</button>
      <button :class="{ active: tab === 'downloads' }" @click="tab = 'downloads'"><DownloadOutlined /> 다운로드 이력 ({{ downloads.length }})</button>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">전체 <strong>{{ currentData.length }}</strong>건</span><div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(currentCols, currentData, '나의_데이터')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="currentData" :columnDefs="currentCols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../utils/exportExcel'
import { ref, computed, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { StarFilled, EyeOutlined, DownloadOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import { userApi } from '../../api/portal.api'
ModuleRegistry.registerModules([AllCommunityModule])
const tab = ref('favorites')
const favCols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋명', field: 'name', flex: 2, minWidth: 200 },
  { headerName: '유형', field: 'type', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '등급', field: 'grade', width: 65, maxWidth: 65, flex: 0 },
  { headerName: '추가일', field: 'date', width: 110, maxWidth: 110, flex: 0 },
]
const recentCols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋명', field: 'name', flex: 2, minWidth: 200 },
  { headerName: '유형', field: 'type', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '조회 일시', field: 'date', flex: 1, minWidth: 140 },
]
const dlCols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋명', field: 'name', flex: 2, minWidth: 200 },
  { headerName: '포맷', field: 'format', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '크기', field: 'size', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '다운로드일', field: 'date', width: 110, maxWidth: 110, flex: 0 },
]

// Fallback mock data
const defaultFavorites = [
  { name: '댐 수위 관측 데이터', type: 'DB', grade: 'L3', date: '2026-03-25' },
  { name: '수질 모니터링 센서 데이터', type: 'IoT', grade: 'L2', date: '2026-03-24' },
  { name: '강수량 예측 API', type: 'API', grade: 'L3', date: '2026-03-23' },
  { name: '하천 유량 관측 데이터', type: 'DB', grade: 'L2', date: '2026-03-20' },
]
const defaultRecent = [
  { name: '상수도 관로 GIS 데이터', type: 'GIS', date: '2026-03-25 14:30' },
  { name: '전력 사용량 통계', type: 'CSV', date: '2026-03-25 11:20' },
  { name: '댐 수위 관측 데이터', type: 'DB', date: '2026-03-24 16:45' },
  { name: '하천 유량 관측 데이터', type: 'DB', date: '2026-03-24 10:15' },
  { name: '수질 모니터링 센서 데이터', type: 'IoT', date: '2026-03-23 09:30' },
]
const defaultDownloads = [
  { name: '전력 사용량 통계 (월별)', format: 'CSV', size: '8.5 MB', date: '2026-03-25' },
  { name: '상수도 수질검사 결과', format: 'JSON', size: '42 MB', date: '2026-03-23' },
  { name: '댐 수위 관측 (2026-Q1)', format: 'CSV', size: '245 MB', date: '2026-03-20' },
]

const favorites = ref(defaultFavorites)
const recent = ref(defaultRecent)
const downloads = ref(defaultDownloads)

onMounted(async () => {
  try {
    const [favRes, recentRes, dlRes] = await Promise.all([
      userApi.favorites({ page: 1, page_size: 20 }),
      userApi.recentViews({ page: 1, page_size: 20 }),
      userApi.downloadHistory({ page: 1, page_size: 20 }),
    ])
    if (favRes.data?.items) favorites.value = favRes.data.items
    if (recentRes.data?.items) recent.value = recentRes.data.items
    if (dlRes.data?.items) downloads.value = dlRes.data.items
  } catch (e) {
    console.error('내 데이터 조회 실패:', e)
  }
})

const currentData = computed<any[]>(() => tab.value === 'favorites' ? favorites.value : tab.value === 'recent' ? recent.value : downloads.value)
const currentCols = computed(() => tab.value === 'favorites' ? favCols : tab.value === 'recent' ? recentCols : dlCols)
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.mydata-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.data-tabs { display: flex; gap: $spacing-sm; button { padding: 8px 18px; border: 1px solid $border-color; border-radius: $radius-md; background: $white; font-size: $font-size-sm; color: $text-secondary; display: flex; align-items: center; gap: 6px; cursor: pointer; &:hover { border-color: $primary; color: $primary; } &.active { background: $primary; color: $white; border-color: $primary; } } }
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.table-actions { display: flex; align-items: center; gap: $spacing-sm; }
.btn-excel { background: none; border: 1px solid #2e7d32; color: #2e7d32; width: 32px; height: 32px; border-radius: $radius-md; font-size: 18px; display: flex; align-items: center; justify-content: center; &:hover { background: #2e7d32; color: $white; } }
.ag-grid-wrapper { :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; font-family: $font-family; } :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; } :deep(.ag-header-cell) { color: #fff; } }
</style>
