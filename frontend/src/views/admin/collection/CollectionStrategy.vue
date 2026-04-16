<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>수집 전략</h2>
      <p class="page-desc">데이터 수집 파이프라인을 설정하고 모니터링합니다.</p>
    </div>
    <div class="stat-cards">
      <div class="stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>수집 방식</label><select v-model="f1"><option value="">전체</option><option>배치</option><option>실시간</option><option>CDC</option></select></div>
        <div class="filter-group"><label>상태</label><select v-model="f2"><option value="">전체</option><option>실행중</option><option>중지</option><option>오류</option></select></div>
        <div class="filter-group search-group"><label>검색</label><input v-model="f3" placeholder="파이프라인명 검색" /></div>
        <div class="filter-actions"><button class="btn btn-primary"><SearchOutlined /> 조회</button></div>
      </div>
    </div>
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ rowData.length }}</strong>건</span>
        <div class="table-actions"><button class="btn btn-success" @click="showRegister = true"><PlusOutlined /> 파이프라인 추가</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rowData, '수집_파이프라인')"><FileExcelOutlined /></button></div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine" :rowData="rowData" :columnDefs="cols" :defaultColDef="defaultColDef" :pagination="true" :paginationPageSize="10" :rowSelection="'multiple'" domLayout="autoHeight" :tooltipShowDelay="0" @row-clicked="onRowClick" />
      </div>
    </div>

    <!-- 파이프라인 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">파이프라인 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">파이프라인명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">소스</span><span class="info-value">{{ detailData.source }}</span></div>
          <div class="modal-info-item"><span class="info-label">방식</span><span class="info-value">{{ detailData.method }}</span></div>
          <div class="modal-info-item"><span class="info-label">주기</span><span class="info-value">{{ detailData.schedule }}</span></div>
          <div class="modal-info-item"><span class="info-label">최근 수집</span><span class="info-value">{{ detailData.lastRun }}</span></div>
          <div class="modal-info-item"><span class="info-label">건수</span><span class="info-value">{{ detailData.count }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '실행중' ? 'badge-success' : detailData.status === '오류' ? 'badge-danger' : 'badge-warning'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 파이프라인 추가 팝업 -->
    <AdminModal :visible="showRegister" title="파이프라인 추가" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-group"><label class="required">파이프라인명</label><input placeholder="파이프라인명 입력" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">소스</label><input placeholder="소스 시스템" /></div>
          <div class="modal-form-group"><label class="required">방식</label><select><option>배치</option><option>실시간</option><option>CDC</option></select></div>
        </div>
        <div class="modal-form-group"><label class="required">주기</label><input placeholder="수집 주기" /></div>
        <div class="modal-form-group"><label>설명</label><textarea rows="2" placeholder="파이프라인 설명"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 추가</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { CloudSyncOutlined, PlayCircleOutlined, PauseCircleOutlined, ExclamationCircleOutlined, SearchOutlined, PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const f1 = ref(''), f2 = ref(''), f3 = ref('')
const stats: { icon: Component; label: string; value: string; color: string }[] = [
  { icon: CloudSyncOutlined, label: '전체 파이프라인', value: '32', color: '#0066CC' },
  { icon: PlayCircleOutlined, label: '실행중', value: '28', color: '#28A745' },
  { icon: PauseCircleOutlined, label: '중지', value: '2', color: '#FFC107' },
  { icon: ExclamationCircleOutlined, label: '오류', value: '2', color: '#DC3545' },
]
const defaultColDef = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, minWidth: 36, flex: 0, sortable: false },
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '파이프라인명', field: 'name', flex: 1.5, minWidth: 150 },
  { headerName: '소스', field: 'source', flex: 1, minWidth: 100 },
  { headerName: '방식', field: 'method', flex: 0.5, minWidth: 70 },
  { headerName: '주기', field: 'schedule', flex: 0.5, minWidth: 70 },
  { headerName: '최근 수집', field: 'lastRun', flex: 1, minWidth: 120 },
  { headerName: '건수', field: 'count', flex: 0.5, minWidth: 70 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 60 },
])
const rowData = ref([
  { name: '댐 수위 실시간 수집', source: 'IoT센서 (MQTT)', method: '실시간', schedule: '10초', lastRun: '2026-03-25 13:25', count: '1,200/일', status: '실행중' },
  { name: '수질 센서 데이터 수집', source: 'IoT센서 (REST)', method: '실시간', schedule: '1분', lastRun: '2026-03-25 13:24', count: '850/일', status: '실행중' },
  { name: 'ERP 인사 동기화', source: 'SAP ERP', method: '배치', schedule: '매일 06:00', lastRun: '2026-03-25 06:00', count: '3,200건', status: '실행중' },
  { name: '기상청 API 연동', source: '기상청 Open API', method: '배치', schedule: '매시 정각', lastRun: '2026-03-25 13:00', count: '24/일', status: '실행중' },
  { name: 'Oracle DB 복제 (수도)', source: 'Oracle 19c', method: 'CDC', schedule: '실시간', lastRun: '2026-03-25 13:25', count: '실시간', status: '오류' },
  { name: 'PostgreSQL 마이그레이션', source: 'PostgreSQL 15', method: '배치', schedule: '수동', lastRun: '2026-03-20 14:00', count: '52만건', status: '중지' },
  { name: '수질 중복제거 파이프라인', source: 'Oracle (수질)', method: '중복제거', schedule: '매일 05:00', lastRun: '2026-04-07 05:00', count: '45,200건', status: '실행중' },
  { name: '자산ERP 다단계 조인', source: 'Tibero (자산ERP)', method: '다단계조인', schedule: '매일 04:00', lastRun: '2026-04-07 04:00', count: '28,800건', status: '실행중' },
  { name: '시설 뷰추출 수집', source: 'SAP HANA (시설)', method: '뷰추출', schedule: '매일 22:00', lastRun: '2026-04-06 22:00', count: '15,600건', status: '실행중' },
])


onMounted(async () => {
  try {
    const res = await adminCollectionApi.strategies()
    const items = res.data.data
    if (items && items.length > 0) {
      rowData.value = items.map((r: any) => ({
        _raw: r,
        name: r.strategy_name || r.name || '',
        source: r.target_data_type || r.source || '',
        method: r.strategy_type || r.method || '',
        schedule: r.schedule || '-',
        lastRun: r.lastRun || '-',
        count: r.count || '-',
        status: r.is_active === true ? '실행중' : r.is_active === false ? '중지' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('CollectionStrategy: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}
function handleRegister() { message.success("등록되었습니다."); showRegister.value = false }
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
</style>
