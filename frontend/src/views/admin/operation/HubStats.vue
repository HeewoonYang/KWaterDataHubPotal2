<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>허브 통계</h2>
      <p class="page-desc">데이터허브 이용 현황 및 관리 통계를 확인합니다.</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>

    <!-- 차트 영역 (플레이스홀더) -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title"><BarChartOutlined /> 월별 데이터 수집량</div>
        <div class="chart-placeholder">
          <div class="bar-group">
            <div v-for="m in monthData" :key="m.month" class="bar-item">
              <div class="bar" :style="{ height: m.value + '%' }"></div>
              <span>{{ m.month }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title"><PieChartOutlined /> 데이터 유형별 분포</div>
        <div class="chart-placeholder donut">
          <svg viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e0e0e0" stroke-width="18" />
            <circle cx="60" cy="60" r="50" fill="none" stroke="#0066CC" stroke-width="18" stroke-dasharray="100 214" stroke-dashoffset="0" />
            <circle cx="60" cy="60" r="50" fill="none" stroke="#28A745" stroke-width="18" stroke-dasharray="80 234" stroke-dashoffset="-100" />
            <circle cx="60" cy="60" r="50" fill="none" stroke="#FFC107" stroke-width="18" stroke-dasharray="60 254" stroke-dashoffset="-180" />
            <circle cx="60" cy="60" r="50" fill="none" stroke="#9b59b6" stroke-width="18" stroke-dasharray="74 240" stroke-dashoffset="-240" />
          </svg>
          <div class="donut-legend">
            <span><i style="background:#0066CC"></i> DB (32%)</span>
            <span><i style="background:#28A745"></i> IoT (26%)</span>
            <span><i style="background:#FFC107"></i> API (19%)</span>
            <span><i style="background:#9b59b6"></i> 파일 (23%)</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 최근 활동 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">최근 이용 현황 <strong>{{ rowData.length }}</strong>건</span>
        <div class="table-actions"><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '허브_통계')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="{ sortable: true, resizable: true, flex: 1, minWidth: 80 }" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 이용 현황 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.date + ' 이용 현황 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">일별 이용 현황</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">일자</span><span class="info-value">{{ detailData.date }}</span></div>
          <div class="modal-info-item"><span class="info-label">수집 건수</span><span class="info-value">{{ detailData.collected }}</span></div>
          <div class="modal-info-item"><span class="info-label">정제 건수</span><span class="info-value">{{ detailData.cleansed }}</span></div>
          <div class="modal-info-item"><span class="info-label">유통 건수</span><span class="info-value">{{ detailData.distributed }}</span></div>
          <div class="modal-info-item"><span class="info-label">API 호출</span><span class="info-value">{{ detailData.apiCalls }}</span></div>
          <div class="modal-info-item"><span class="info-label">다운로드</span><span class="info-value">{{ detailData.downloads }}</span></div>
          <div class="modal-info-item"><span class="info-label">활성 사용자</span><span class="info-value">{{ detailData.activeUsers }}명</span></div>
          <div class="modal-info-item"><span class="info-label">오류 건수</span><span class="info-value">{{ detailData.errors }}건</span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { BarChartOutlined, PieChartOutlined, DatabaseOutlined, TeamOutlined, CloudDownloadOutlined, ApiOutlined, FileExcelOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminOperationApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false)
const detailData = ref<any>({})
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: DatabaseOutlined, label: '총 데이터셋', value: '1,247', color: '#0066CC' },
  { icon: TeamOutlined, label: '월 활성 사용자', value: '156', color: '#28A745' },
  { icon: CloudDownloadOutlined, label: '월 다운로드', value: '2,340', color: '#9b59b6' },
  { icon: ApiOutlined, label: 'API 호출 (월)', value: '1.45M', color: '#FFC107' },
]
const monthData = [
  { month: '10월', value: 55 }, { month: '11월', value: 62 }, { month: '12월', value: 48 },
  { month: '1월', value: 72 }, { month: '2월', value: 68 }, { month: '3월', value: 85 },
]
const cols: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 50, maxWidth: 50, flex: 0 },
  { headerName: '일자', field: 'date', width: 110, maxWidth: 110, flex: 0 },
  { headerName: '수집 건수', field: 'collected', width: 100, maxWidth: 100, flex: 0 },
  { headerName: '정제 건수', field: 'cleansed', width: 100, maxWidth: 100, flex: 0 },
  { headerName: '유통 건수', field: 'distributed', width: 100, maxWidth: 100, flex: 0 },
  { headerName: 'API 호출', field: 'apiCalls', width: 100, maxWidth: 100, flex: 0 },
  { headerName: '다운로드', field: 'downloads', width: 90, maxWidth: 90, flex: 0 },
  { headerName: '활성 사용자', field: 'activeUsers', width: 95, maxWidth: 95, flex: 0 },
  { headerName: '오류 건수', field: 'errors', width: 85, maxWidth: 85, flex: 0 },
]
const rowData = ref([
  { date: '2026-03-25', collected: '48,320', cleansed: '47,800', distributed: '12,500', apiCalls: '52,100', downloads: 85, activeUsers: 42, errors: 3 },
  { date: '2026-03-24', collected: '45,100', cleansed: '44,600', distributed: '11,200', apiCalls: '48,700', downloads: 72, activeUsers: 38, errors: 1 },
  { date: '2026-03-23', collected: '42,800', cleansed: '42,300', distributed: '10,800', apiCalls: '45,200', downloads: 65, activeUsers: 35, errors: 5 },
  { date: '2026-03-22', collected: '39,500', cleansed: '39,000', distributed: '9,500', apiCalls: '41,800', downloads: 58, activeUsers: 32, errors: 2 },
  { date: '2026-03-21', collected: '44,200', cleansed: '43,800', distributed: '11,000', apiCalls: '47,500', downloads: 78, activeUsers: 40, errors: 0 },
])

onMounted(async () => {
  try {
    const res = await adminOperationApi.hubStats()
    const items = res.data.items
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        date: r.stat_date || r.date || '',
        collected: r.total_datasets != null ? r.total_datasets.toLocaleString() : (r.collected || '-'),
        cleansed: r.cleansed || '-',
        distributed: r.total_downloads != null ? r.total_downloads.toLocaleString() : (r.distributed || '-'),
        apiCalls: r.total_api_calls != null ? r.total_api_calls.toLocaleString() : (r.apiCalls || '-'),
        downloads: r.total_downloads != null ? r.total_downloads : (r.downloads || '-'),
        activeUsers: r.active_users != null ? r.active_users : (r.activeUsers || '-'),
        errors: r.errors || 0,
      }))
    }
  } catch (e) {
    console.warn('HubStats: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
</script>
<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }

.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: $spacing-lg; }
.chart-card { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-xl; box-shadow: $shadow-sm; }
.chart-title { font-size: $font-size-md; font-weight: 600; margin-bottom: $spacing-lg; display: flex; align-items: center; gap: $spacing-sm; }
.chart-placeholder { height: 200px; }
.bar-group { display: flex; align-items: flex-end; justify-content: space-around; height: 180px; }
.bar-item { display: flex; flex-direction: column; align-items: center; gap: $spacing-sm; flex: 1; }
.bar { width: 30px; background: linear-gradient(180deg, $primary, $primary-light); border-radius: 3px 3px 0 0; transition: height 0.3s; }
.bar-item span { font-size: $font-size-xs; color: $text-muted; }
.donut { display: flex; align-items: center; gap: $spacing-xl; }
.donut svg { width: 140px; height: 140px; transform: rotate(-90deg); }
.donut-legend { display: flex; flex-direction: column; gap: $spacing-sm; }
.donut-legend span { font-size: $font-size-sm; color: $text-secondary; display: flex; align-items: center; gap: $spacing-sm; }
.donut-legend i { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .chart-row { grid-template-columns: 1fr; }
}
</style>
