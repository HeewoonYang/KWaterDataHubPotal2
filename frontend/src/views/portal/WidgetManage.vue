<template>
  <div class="admin-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">&gt;</span>
      <span class="current">위젯 관리</span>
    </nav>

    <div class="page-header">
      <h2>위젯 관리*</h2>
      <p class="page-desc">대시보드 위젯 템플릿을 등록하고 관리합니다.</p>
    </div>

    <!-- KPI Cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background:#0066CC"><AppstoreOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ rowData.length }}</span><span class="stat-label">총 위젯 수</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#28A745"><FundOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ rowData.filter(r => r.cat === 'kpi').length }}</span><span class="stat-label">KPI 위젯</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#9b59b6"><BarChartOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ rowData.filter(r => r.cat === 'chart').length }}</span><span class="stat-label">차트 위젯</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:#17a2b8"><GlobalOutlined /></div>
        <div class="stat-info"><span class="stat-value">{{ rowData.filter(r => r.dataLevel === 'public').length }}</span><span class="stat-label">공개 위젯</span></div>
      </div>
    </div>

    <!-- Search / Filter -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group">
          <label>카테고리</label>
          <select v-model="filterCat">
            <option value="">전체</option>
            <option value="kpi">KPI</option>
            <option value="card">카드</option>
            <option value="list">리스트</option>
            <option value="chart">차트</option>
          </select>
        </div>
        <div class="filter-group">
          <label>데이터등급</label>
          <select v-model="filterLevel">
            <option value="">전체</option>
            <option value="public">공개</option>
            <option value="internal">내부</option>
            <option value="restricted">제한</option>
            <option value="confidential">기밀</option>
          </select>
        </div>
        <div class="filter-group search-group">
          <label>검색</label>
          <input type="text" v-model="searchText" placeholder="위젯명, 설명 검색" />
        </div>
        <div class="filter-actions">
          <button class="btn btn-primary" @click="applyFilter"><SearchOutlined /> 조회</button>
          <button class="btn btn-outline" @click="resetFilter"><ReloadOutlined /> 초기화</button>
        </div>
      </div>
    </div>

    <!-- AG Grid -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ filteredData.length }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-success" @click="showRegister = true"><PlusOutlined /> 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(columnDefs, filteredData, '위젯_목록')"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="filteredData"
          :columnDefs="columnDefs"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="10"
          domLayout="autoHeight"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- Detail Modal -->
    <AdminModal :visible="showDetail" :title="detailItem.name + ' 위젯 상세'" size="lg" @close="showDetail = false">
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">카테고리</div><div class="stat-number" style="font-size:16px">{{ catLabel(detailItem.cat) }}</div></div>
        <div class="modal-stat-card success"><div class="stat-title">데이터등급</div><div class="stat-number" style="font-size:16px">{{ levelLabel(detailItem.dataLevel) }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">접근역할</div><div class="stat-number" style="font-size:16px">{{ typeof detailItem.roles === 'string' ? detailItem.roles : (detailItem.roles || []).join(', ') }}</div></div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">위젯 ID</span><span class="info-value">{{ detailItem.id }}</span></div>
          <div class="modal-info-item"><span class="info-label">위젯명</span><span class="info-value">{{ detailItem.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">카테고리</span><span class="info-value">{{ catLabel(detailItem.cat) }}</span></div>
          <div class="modal-info-item"><span class="info-label">데이터등급</span><span class="info-value">{{ levelLabel(detailItem.dataLevel) }}</span></div>
          <div class="modal-info-item"><span class="info-label">접근역할</span><span class="info-value">{{ typeof detailItem.roles === 'string' ? detailItem.roles : (detailItem.roles || []).join(', ') }}</span></div>
          <div class="modal-info-item"><span class="info-label">색상</span><span class="info-value"><span class="color-circle" :style="{ background: detailItem.color }"></span> {{ detailItem.color }}</span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">설명</div>
        <p style="font-size:14px;color:#333">{{ detailItem.desc }}</p>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- Register Modal -->
    <AdminModal :visible="showRegister" title="위젯 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">위젯명</label><input placeholder="위젯명 입력" /></div>
          <div class="modal-form-group"><label class="required">카테고리</label>
            <select><option>KPI</option><option>카드</option><option>리스트</option><option>차트</option></select>
          </div>
        </div>
        <div class="modal-form-group"><label class="required">설명</label><textarea rows="3" placeholder="위젯 설명 입력"></textarea></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">데이터등급</label>
            <select><option>공개(public)</option><option>내부(internal)</option><option>제한(restricted)</option><option>기밀(confidential)</option></select>
          </div>
          <div class="modal-form-group"><label>접근역할</label>
            <select><option>all</option><option>ADMIN</option><option>MANAGER</option><option>INTERNAL</option></select>
          </div>
        </div>
        <div class="modal-form-group"><label>색상코드</label><input placeholder="#0066CC" /></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRegister = false"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  SearchOutlined, ReloadOutlined, PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined,
  AppstoreOutlined, FundOutlined, BarChartOutlined, GlobalOutlined,
} from '@ant-design/icons-vue'

import AdminModal from '../../components/AdminModal.vue'
import { exportGridToExcel } from '../../utils/exportExcel'

ModuleRegistry.registerModules([AllCommunityModule])

const searchText = ref('')
const filterCat = ref('')
const filterLevel = ref('')
const showDetail = ref(false)
const showRegister = ref(false)
const detailItem = ref<any>({})

const defaultColDef = { sortable: true, resizable: true, flex: 1, minWidth: 80 }

const columnDefs: ColDef[] = [
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 55, resizable: false },
  { headerName: '위젯명', field: 'name', flex: 1.5, minWidth: 160,
    cellRenderer: (params: any) => {
      const catSymbols: Record<string, string> = { kpi: 'K', card: 'C', list: 'L', chart: 'G' }
      const colors: Record<string, string> = { kpi: '#1677ff', card: '#fa8c16', list: '#13c2c2', chart: '#722ed1' }
      const c = colors[params.data.cat] || '#666'
      const sym = catSymbols[params.data.cat] || '?'
      return `<span style="display:flex;align-items:center;gap:6px"><span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:4px;background:${c}15;color:${c};font-size:11px;font-weight:700;">${sym}</span><span style="font-weight:600">${params.value}</span></span>`
    }
  },
  { headerName: '카테고리', field: 'cat', width: 110,
    cellRenderer: (params: any) => {
      const map: Record<string, string> = { kpi: '#0066CC', card: '#28A745', list: '#FFC107', chart: '#9b59b6' }
      const label: Record<string, string> = { kpi: 'KPI', card: '카드', list: '리스트', chart: '차트' }
      const c = map[params.value] || '#666'
      return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:${c}1a;color:${c}">${label[params.value] || params.value}</span>`
    }
  },
  { headerName: '설명', field: 'desc', flex: 2, minWidth: 200 },
  { headerName: '접근역할', field: 'rolesLabel', width: 130,
    cellRenderer: (params: any) => {
      return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:#e3f2fd;color:#1565c0">${params.value}</span>`
    }
  },
  { headerName: '데이터등급', field: 'dataLevel', width: 115,
    cellRenderer: (params: any) => {
      const colors: Record<string, string> = { public: '#28A745', internal: '#0066CC', restricted: '#FFC107', confidential: '#DC3545' }
      const labels: Record<string, string> = { public: '공개', internal: '내부', restricted: '제한', confidential: '기밀' }
      const c = colors[params.value] || '#666'
      return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;background:${c}1a;color:${c}">${labels[params.value] || params.value}</span>`
    }
  },
  { headerName: '색상', field: 'color', width: 85,
    cellRenderer: (params: any) => `<span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:${params.value};border:1px solid #ddd;vertical-align:middle"></span>`
  },
  { headerName: '관리', width: 100, sortable: false,
    cellRenderer: () => `<button style="padding:3px 10px;border:1px solid #0066CC;color:#0066CC;border-radius:4px;font-size:12px;background:#fff;cursor:pointer">상세</button>`
  },
]

const rowData = ref([
  // KPI (10)
  { id: 'W001', icon: 'BarChartOutlined', name: '총 데이터셋', cat: 'kpi', desc: '데이터허브에 등록된 전체 데이터셋 수', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#0066CC' },
  { id: 'W002', icon: 'LineChartOutlined', name: '오늘 수집건수', cat: 'kpi', desc: '금일 수집 완료된 데이터 건수', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#28A745' },
  { id: 'W003', icon: 'StockOutlined', name: '오늘 적재건수', cat: 'kpi', desc: '금일 적재 완료된 데이터 건수', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#17a2b8' },
  { id: 'W004', icon: 'TeamOutlined', name: '활성 사용자', cat: 'kpi', desc: '현재 접속 중인 사용자 수', roles: 'all', rolesLabel: 'all', dataLevel: 'internal', color: '#9b59b6' },
  { id: 'W005', icon: 'SaveOutlined', name: '저장 용량', cat: 'kpi', desc: '전체 스토리지 사용량', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#e67e22' },
  { id: 'W006', icon: 'CheckCircleOutlined', name: '품질 점수', cat: 'kpi', desc: '전체 데이터 품질 평균 점수', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#2ecc71' },
  { id: 'W007', icon: 'RocketOutlined', name: 'API 호출량', cat: 'kpi', desc: '금일 API 호출 총 건수', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#3498db' },
  { id: 'W008', icon: 'FileTextOutlined', name: '신청 대기', cat: 'kpi', desc: '승인 대기 중인 데이터 신청 건수', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#FFC107' },
  { id: 'W009', icon: 'BellOutlined', name: '알림 건수', cat: 'kpi', desc: '미확인 알림 건수', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#e74c3c' },
  { id: 'W010', icon: 'ToolOutlined', name: '시스템 상태', cat: 'kpi', desc: '주요 시스템 가동률', roles: ['ADMIN'], rolesLabel: 'ADMIN', dataLevel: 'restricted', color: '#34495e' },
  // 카드 (8)
  { id: 'W011', icon: 'FileOutlined', name: '최근 등록 데이터', cat: 'card', desc: '최근 등록된 데이터셋 카드', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#0066CC' },
  { id: 'W012', icon: 'StarOutlined', name: '인기 데이터셋', cat: 'card', desc: '다운로드 상위 데이터셋', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#FFC107' },
  { id: 'W013', icon: 'BookOutlined', name: '공지사항', cat: 'card', desc: '최신 공지사항 요약', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#6c757d' },
  { id: 'W014', icon: 'SearchOutlined', name: 'AI 검색 현황', cat: 'card', desc: 'AI 검색 이용 통계 카드', roles: ['ADMIN','MANAGER','INTERNAL'], rolesLabel: 'ADMIN,MANAGER,INTERNAL', dataLevel: 'internal', color: '#9b59b6' },
  { id: 'W015', icon: 'ToolOutlined', name: '수집 상태 요약', cat: 'card', desc: '데이터 수집 파이프라인 상태', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#28A745' },
  { id: 'W016', icon: 'SearchOutlined', name: '품질 검사 요약', cat: 'card', desc: '최근 품질 검사 결과 카드', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#17a2b8' },
  { id: 'W017', icon: 'GlobalOutlined', name: '외부 연계 현황', cat: 'card', desc: '외부 기관 데이터 연계 상태', roles: ['ADMIN'], rolesLabel: 'ADMIN', dataLevel: 'restricted', color: '#e67e22' },
  { id: 'W018', icon: 'BulbOutlined', name: '추천 데이터셋', cat: 'card', desc: 'AI 기반 맞춤 데이터 추천', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#3498db' },
  // 리스트 (6)
  { id: 'W019', icon: 'FileTextOutlined', name: '데이터 신청 목록', cat: 'list', desc: '최근 데이터 신청 내역 리스트', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#0066CC' },
  { id: 'W020', icon: 'EditOutlined', name: '수집 이력', cat: 'list', desc: '최근 데이터 수집 이력 리스트', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#28A745' },
  { id: 'W021', icon: 'LockOutlined', name: '접근 로그', cat: 'list', desc: '최근 데이터 접근 로그', roles: ['ADMIN'], rolesLabel: 'ADMIN', dataLevel: 'restricted', color: '#DC3545' },
  { id: 'W022', icon: 'MessageOutlined', name: 'QnA 최신글', cat: 'list', desc: '최신 QnA 게시글 목록', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#6c757d' },
  { id: 'W023', icon: 'SettingOutlined', name: '시스템 로그', cat: 'list', desc: '최근 시스템 이벤트 로그', roles: ['ADMIN'], rolesLabel: 'ADMIN', dataLevel: 'confidential', color: '#34495e' },
  { id: 'W024', icon: 'InboxOutlined', name: '다운로드 이력', cat: 'list', desc: '최근 데이터 다운로드 내역', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#e67e22' },
  // 차트 (6)
  { id: 'W025', icon: 'BarChartOutlined', name: '수집/적재 현황 차트', cat: 'chart', desc: '일별 수집/적재 건수 추이 차트', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#0066CC' },
  { id: 'W026', icon: 'PieChartOutlined', name: '분류별 현황 차트', cat: 'chart', desc: '데이터 분류별 비율 파이 차트', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#FFC107' },
  { id: 'W027', icon: 'LineChartOutlined', name: '다운로드 순위 차트', cat: 'chart', desc: '인기 데이터셋 다운로드 순위', roles: 'all', rolesLabel: 'all', dataLevel: 'public', color: '#28A745' },
  { id: 'W028', icon: 'StockOutlined', name: 'API 사용량 차트', cat: 'chart', desc: '일별 API 호출 추이 차트', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#9b59b6' },
  { id: 'W029', icon: 'LineChartOutlined', name: '저장소 사용량 차트', cat: 'chart', desc: '스토리지 영역별 사용량 차트', roles: ['ADMIN'], rolesLabel: 'ADMIN', dataLevel: 'restricted', color: '#e74c3c' },
  { id: 'W030', icon: 'StockOutlined', name: '품질 추이 차트', cat: 'chart', desc: '월별 데이터 품질 점수 추이', roles: ['ADMIN','MANAGER'], rolesLabel: 'ADMIN,MANAGER', dataLevel: 'internal', color: '#17a2b8' },
])

const filteredData = computed(() => {
  let data = rowData.value
  if (filterCat.value) data = data.filter(r => r.cat === filterCat.value)
  if (filterLevel.value) data = data.filter(r => r.dataLevel === filterLevel.value)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    data = data.filter(r => r.name.toLowerCase().includes(q) || r.desc.toLowerCase().includes(q))
  }
  return data
})

function catLabel(cat: string) {
  const map: Record<string, string> = { kpi: 'KPI', card: '카드', list: '리스트', chart: '차트' }
  return map[cat] || cat
}

function levelLabel(level: string) {
  const map: Record<string, string> = { public: '공개', internal: '내부', restricted: '제한', confidential: '기밀' }
  return map[level] || level
}

function applyFilter() { /* filters are reactive via computed */ }
function resetFilter() { filterCat.value = ''; filterLevel.value = ''; searchText.value = '' }

function onRowClick(event: any) {
  detailItem.value = event.data
  showDetail.value = true
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.admin-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header {
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  .page-desc { font-size: $font-size-sm; color: $text-muted; }
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

.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: $spacing-md; }
.stat-card {
  background: $white; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; display: flex; align-items: center; gap: $spacing-md; box-shadow: $shadow-sm;
  .stat-icon { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: $white; flex-shrink: 0; }
  .stat-info { flex: 1; display: flex; flex-direction: column; }
  .stat-value { font-size: $font-size-xl; font-weight: 700; }
  .stat-label { font-size: $font-size-xs; color: $text-muted; }
}

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
:deep(.ag-row) { cursor: pointer; }

.color-circle { display: inline-block; width: 16px; height: 16px; border-radius: 50%; border: 1px solid #ddd; vertical-align: middle; margin-right: 6px; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
  .filter-row { flex-direction: column; align-items: stretch; }
}
</style>
