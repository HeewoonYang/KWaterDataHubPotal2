<template>
  <div class="download-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">데이터 다운로드</span>
    </nav>

    <div class="page-header"><h2>데이터 다운로드</h2><p>승인된 데이터를 원하는 포맷으로 다운로드합니다.</p></div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>포맷</label><select v-model="f1"><option value="">전체</option><option>CSV</option><option>JSON</option><option>Excel</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="f2" placeholder="데이터셋명 검색" /></div>
        <div class="filter-actions"><button class="btn btn-primary" @click="fetchDownloads"><SearchOutlined /> 조회</button></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">다운로드 가능 <strong>{{ rows.length }}</strong>건</span></div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { SearchOutlined } from '@ant-design/icons-vue'
import { userApi, distributionApi } from '../../api/portal.api'
ModuleRegistry.registerModules([AllCommunityModule])
const f1 = ref(''), f2 = ref('')
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '데이터셋', field: 'name', flex: 2, minWidth: 200 },
  { headerName: '포맷', field: 'format', width: 70, maxWidth: 70, flex: 0 },
  { headerName: '크기', field: 'size', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '승인일', field: 'approvedDate', width: 110, maxWidth: 110, flex: 0 },
  { headerName: '만료일', field: 'expireDate', width: 110, maxWidth: 110, flex: 0 },
  { headerName: '다운로드', field: 'downloads', width: 85, maxWidth: 85, flex: 0 },
]

// Fallback mock data
const defaultRows = [
  { id: '1', name: '댐 수위 관측 데이터 (2026-Q1)', format: 'CSV', size: '245 MB', approvedDate: '2026-03-20', expireDate: '2026-06-20', downloads: 3 },
  { id: '2', name: '수질 모니터링 센서 데이터', format: 'JSON', size: '1.2 GB', approvedDate: '2026-03-18', expireDate: '2026-09-18', downloads: 1 },
  { id: '3', name: '전력 사용량 통계 (월별)', format: 'Excel', size: '8.5 MB', approvedDate: '2026-03-15', expireDate: '2026-06-15', downloads: 5 },
  { id: '4', name: '하천 유량 관측 데이터', format: 'CSV', size: '580 MB', approvedDate: '2026-03-10', expireDate: '2026-06-10', downloads: 2 },
]

const rows = ref(defaultRows)

async function fetchDownloads() {
  try {
    const params: Record<string, any> = { page: 1, page_size: 20 }
    if (f1.value) params.format = f1.value
    if (f2.value) params.keyword = f2.value
    const res = await userApi.downloadHistory(params)
    if (res.data?.items?.length) {
      rows.value = res.data.items.map((item: any) => ({
        id: item.id,
        name: item.dataset_name || '',
        format: item.download_format || '',
        size: item.file_size_bytes ? `${(item.file_size_bytes / 1048576).toFixed(1)} MB` : '-',
        approvedDate: item.downloaded_at ? item.downloaded_at.substring(0, 10) : '',
        expireDate: '',
        downloads: 1,
      }))
    }
  } catch (e) {
    console.error('다운로드 목록 조회 실패:', e)
  }
}

async function downloadFile(id: string, format: string) {
  try {
    const res = await distributionApi.downloadFile(id, format)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `dataset_${id}.${format.toLowerCase()}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    console.error('파일 다운로드 실패:', e)
  }
}

onMounted(() => { fetchDownloads() })

defineExpose({ downloadFile })
</script>
<style lang="scss" scoped>
@use '../../styles/variables' as *;
.download-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.search-filter { background: #f5f7fa; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; }
.filter-row { display: flex; align-items: flex-end; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: $spacing-xs; label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; } select, input { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 130px; background: $white; } &.search-group { flex: 1; input { width: 100%; } } }
.filter-actions { display: flex; gap: $spacing-sm; }
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.ag-grid-wrapper { :deep(.ag-theme-alpine) { --ag-header-background-color: #4a6a8a; --ag-header-foreground-color: #fff; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; font-family: $font-family; } :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; color: #fff; } :deep(.ag-header-cell) { color: #fff; } }
</style>
