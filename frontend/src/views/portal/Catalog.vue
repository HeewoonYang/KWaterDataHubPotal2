<template>
  <div class="catalog-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">카탈로그 탐색</span>
    </nav>

    <div class="page-header">
      <h2>데이터 카탈로그</h2>
      <p>OpenMetadata 기반 데이터 카탈로그를 탐색하고 검색하세요.</p>
    </div>

    <!-- 검색 영역 -->
    <div class="search-area">
      <div class="search-input-wrap">
        <SearchOutlined class="search-icon" />
        <input type="text" v-model="searchQuery" placeholder="데이터셋명, 태그, 키워드로 검색" @keyup.enter="onSearch" />
      </div>
      <div class="filter-tags">
        <button v-for="tag in filterTags" :key="tag" class="tag-btn" :class="{ active: selectedTag === tag }" @click="selectedTag = selectedTag === tag ? '' : tag">
          {{ tag }}
        </button>
      </div>
    </div>

    <!-- 본문: 트리 + 목록 -->
    <div class="catalog-body">
      <!-- 좌측 분류 트리 -->
      <aside class="category-tree">
        <div class="tree-header">
          <AppstoreOutlined /> 분류체계
        </div>
        <ul class="tree-list">
          <li v-for="cat in categories" :key="cat.name" class="tree-item" :class="{ active: selectedCategory === cat.name }" @click="selectedCategory = cat.name">
            <FolderOutlined />
            <span>{{ cat.name }}</span>
            <span class="tree-count">{{ cat.count }}</span>
          </li>
        </ul>
      </aside>

      <!-- 우측 데이터셋 목록 -->
      <div class="dataset-list">
        <div class="list-header">
          <span class="result-count">전체 <strong>{{ sortedDatasets.length }}</strong>건</span>
          <div class="sort-group">
            <select v-model="sortBy">
              <option value="latest">최신순</option>
              <option value="name">이름순</option>
              <option value="popular">인기순</option>
            </select>
          </div>
        </div>

        <div class="dataset-cards">
          <div v-for="ds in sortedDatasets" :key="ds.id" class="dataset-card" :class="{ highlighted: highlightId === ds.id }" @click="openDetail(ds)">
            <div class="card-top">
              <span class="ds-type" :class="ds.type">{{ ds.typeLabel }}</span>
              <span class="ds-grade" :class="'grade-' + ds.grade">L{{ ds.grade }}</span>
            </div>
            <h4 class="ds-name">{{ ds.name }}</h4>
            <p class="ds-desc">{{ ds.description }}</p>
            <div class="ds-meta">
              <span><TableOutlined /> {{ ds.columns }}개 컬럼</span>
              <span><DatabaseOutlined /> {{ ds.rows }}</span>
              <span><ClockCircleOutlined /> {{ ds.updated }}</span>
            </div>
            <div class="ds-tags">
              <span v-for="tag in ds.tags" :key="tag" class="ds-tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 데이터셋 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name" size="xl" @close="showDetail = false">
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">유형</div><div class="stat-number">{{ detailData.typeLabel }}</div></div>
        <div class="modal-stat-card success"><div class="stat-title">등급</div><div class="stat-number">L{{ detailData.grade }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">컬럼</div><div class="stat-number">{{ detailData.columns }}개</div></div>
        <div class="modal-stat-card info"><div class="stat-title">데이터 건수</div><div class="stat-number">{{ detailData.rows }}</div></div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.typeLabel }}</span></div>
          <div class="modal-info-item"><span class="info-label">보안 등급</span><span class="info-value">L{{ detailData.grade }}</span></div>
          <div class="modal-info-item"><span class="info-label">최종 수정일</span><span class="info-value">{{ detailData.updated }}</span></div>
          <div class="modal-info-item"><span class="info-label">컬럼 수</span><span class="info-value">{{ detailData.columns }}개</span></div>
          <div class="modal-info-item"><span class="info-label">데이터 건수</span><span class="info-value">{{ detailData.rows }}</span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">설명</div>
        <p style="font-size:13px;color:#555;line-height:1.6;">{{ detailData.description }}</p>
      </div>
      <div class="modal-section" v-if="detailData.tags">
        <div class="modal-section-title">태그</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <span v-for="tag in detailData.tags" :key="tag" class="badge badge-info">{{ tag }}</span>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">컬럼 정보 (샘플)</div>
        <table class="modal-table">
          <thead><tr><th>번호</th><th>컬럼명</th><th>데이터 타입</th><th>설명</th><th>NULL 허용</th></tr></thead>
          <tbody>
            <tr v-for="(col, i) in sampleColumns" :key="i">
              <td class="text-center">{{ i + 1 }}</td><td>{{ col.name }}</td><td>{{ col.dataType }}</td><td>{{ col.desc }}</td><td class="text-center">{{ col.nullable }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="openRequestForm">데이터 신청</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 데이터 신청 팝업 -->
    <AdminModal :visible="showRequest" title="데이터 이용 신청" size="md" @close="showRequest = false">
      <div class="modal-section">
        <div class="modal-section-title">신청 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋</span><span class="info-value">{{ detailData.name || detailData.dataset_name }}</span></div>
          <div class="modal-info-item"><span class="info-label">등급</span><span class="info-value">L{{ detailData.grade }}</span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">신청 내용</div>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">사용 목적</label>
            <textarea v-model="requestForm.purpose" rows="3" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px;resize:vertical;" placeholder="데이터 사용 목적을 입력하세요"></textarea>
          </div>
          <div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">요청 포맷</label>
            <select v-model="requestForm.format" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px;">
              <option value="CSV">CSV</option><option value="JSON">JSON</option><option value="XLSX">Excel</option>
            </select>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="submitRequest">신청</button>
        <button class="btn btn-outline" @click="showRequest = false">취소</button>
      </template>
    </AdminModal>

    <!-- 신청 완료 알림 -->
    <AdminModal :visible="showRequestDone" title="신청 완료" size="sm" @close="showRequestDone = false">
      <div style="text-align:center;padding:20px;">
        <div style="font-size:40px;color:#28A745;margin-bottom:12px;">&#10003;</div>
        <p style="font-size:14px;color:#333;">데이터 이용 신청이 접수되었습니다.</p>
        <p style="font-size:12px;color:#888;">관리자 승인 후 이용 가능합니다.</p>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showRequestDone = false">확인</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  SearchOutlined,
  AppstoreOutlined,
  FolderOutlined,
  TableOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons-vue'
import AdminModal from '../../components/AdminModal.vue'
import { catalogApi, distributionApi } from '../../api/portal.api'

const route = useRoute()
const searchQuery = ref('')
const selectedTag = ref('')
const selectedCategory = ref('수자원')
const sortBy = ref('latest')
const showDetail = ref(false)
const detailData = ref<any>({})
const highlightId = ref<number | null>(null)
const showRequest = ref(false)
const showRequestDone = ref(false)
const requestForm = ref({ purpose: '', format: 'CSV' })

const sampleColumns = [
  { name: 'MEAS_DT', dataType: 'TIMESTAMP', desc: '측정 일시', nullable: 'N' },
  { name: 'DAM_CD', dataType: 'VARCHAR(10)', desc: '댐 코드', nullable: 'N' },
  { name: 'DAM_NM', dataType: 'VARCHAR(50)', desc: '댐 명칭', nullable: 'N' },
  { name: 'WATER_LV', dataType: 'NUMERIC(8,2)', desc: '수위 (m)', nullable: 'Y' },
  { name: 'INFLOW', dataType: 'NUMERIC(10,2)', desc: '유입량 (m³/s)', nullable: 'Y' },
  { name: 'OUTFLOW', dataType: 'NUMERIC(10,2)', desc: '방류량 (m³/s)', nullable: 'Y' },
  { name: 'STORAGE_RT', dataType: 'NUMERIC(5,2)', desc: '저수율 (%)', nullable: 'Y' },
]

const filterTags = ['전체', 'DB', 'IoT', 'GIS', 'API', 'CSV']

// Fallback mock data
const defaultCategories = [
  { name: '수자원', count: 423 },
  { name: '수도', count: 287 },
  { name: '환경', count: 215 },
  { name: '경영', count: 178 },
  { name: '공간정보', count: 89 },
  { name: '기타', count: 55 },
]

const defaultDatasets = [
  { id: 1, name: '댐 수위 관측 데이터', description: '전국 다목적댐 실시간 수위 관측 데이터 (10분 간격)', type: 'db', typeLabel: 'DB', grade: 3, columns: 12, rows: '1.2억건', updated: '2026-03-25', tags: ['수위', '댐', '실시간'] },
  { id: 2, name: '수질 모니터링 센서 데이터', description: 'IoT 센서 기반 수질 항목별 측정값 (pH, DO, BOD 등)', type: 'iot', typeLabel: 'IoT', grade: 2, columns: 18, rows: '8,500만건', updated: '2026-03-25', tags: ['수질', 'IoT', '센서'] },
  { id: 3, name: '상수도 관로 GIS 데이터', description: '전국 상수도 관로 네트워크 공간정보 데이터셋', type: 'gis', typeLabel: 'GIS', grade: 2, columns: 24, rows: '320만건', updated: '2026-03-24', tags: ['GIS', '관로', '상수도'] },
  { id: 4, name: '전력 사용량 통계 (월별)', description: 'K-water 사업장별 월별 전력 사용량 집계 데이터', type: 'csv', typeLabel: 'CSV', grade: 3, columns: 8, rows: '15,600건', updated: '2026-03-23', tags: ['전력', '통계', '월별'] },
  { id: 5, name: '강수량 예측 모델 API', description: '기상청 연동 강수량 예측 결과 REST API', type: 'api', typeLabel: 'API', grade: 3, columns: 6, rows: 'API', updated: '2026-03-25', tags: ['기상', 'API', '예측'] },
  { id: 6, name: '하천 유량 관측 데이터', description: '주요 하천 관측소별 유량 측정 데이터 (시간 단위)', type: 'db', typeLabel: 'DB', grade: 2, columns: 10, rows: '5,200만건', updated: '2026-03-24', tags: ['유량', '하천', '관측'] },
]

const categories = ref(defaultCategories)
const datasets = ref(defaultDatasets)

async function fetchDatasets() {
  try {
    const params: Record<string, any> = { page: 1, page_size: 20, sort: sortBy.value }
    if (selectedCategory.value) params.category = selectedCategory.value
    if (selectedTag.value && selectedTag.value !== '전체') params.data_format = selectedTag.value
    if (searchQuery.value) params.keyword = searchQuery.value
    const res = await catalogApi.list(params)
    if (res.data?.items?.length) {
      datasets.value = res.data.items.map((item: any) => ({
        id: item.id,
        name: item.dataset_name || item.name || '',
        description: item.description || '',
        type: (item.data_format || 'DB').toLowerCase(),
        typeLabel: item.data_format || 'DB',
        grade: parseInt(item.grade_code?.replace('L','') || '3'),
        columns: item.columns?.length || 0,
        rows: item.row_count ? (item.row_count > 100000000 ? `${(item.row_count/100000000).toFixed(1)}억건` : item.row_count > 10000 ? `${(item.row_count/10000).toFixed(0)}만건` : `${item.row_count.toLocaleString()}건`) : '-',
        updated: item.created_at?.substring(0, 10) || '',
        tags: item.tags || [],
      }))
    }
  } catch (e) {
    console.error('카탈로그 데이터 조회 실패:', e)
  }
}

async function fetchCategories() {
  try {
    const res = await catalogApi.categories()
    if (res.data?.data) categories.value = res.data.data
  } catch (e) {
    console.error('카테고리 조회 실패:', e)
  }
}

const sortedDatasets = computed(() => {
  const sorted = [...datasets.value]
  if (sortBy.value === 'latest') sorted.sort((a, b) => b.updated.localeCompare(a.updated))
  else if (sortBy.value === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name))
  return sorted
})

// Re-fetch when filters change
watch([selectedCategory, selectedTag, sortBy], () => { fetchDatasets() })

function openDetail(ds: any) {
  detailData.value = ds
  showDetail.value = true
}

function onSearch() {
  fetchDatasets()
}

function openRequestForm() {
  showRequest.value = true
  requestForm.value = { purpose: '', format: 'CSV' }
}

async function submitRequest() {
  try {
    await distributionApi.createRequest({
      dataset_ids: [detailData.value.id],
      request_type: 'DOWNLOAD',
      requested_format: requestForm.value.format,
      purpose: requestForm.value.purpose,
    })
    showRequest.value = false
    showDetail.value = false
    showRequestDone.value = true
  } catch (e) {
    console.error('데이터 신청 실패:', e)
    alert('신청에 실패했습니다. 다시 시도해주세요.')
  }
}

// URL 파라미터로 최신순 정렬 + 하이라이트 처리
onMounted(async () => {
  if (route.query.sort === 'latest') sortBy.value = 'latest'

  await Promise.all([fetchCategories(), fetchDatasets()])

  if (route.query.highlight) {
    const id = Number(route.query.highlight)
    highlightId.value = id
    const ds = datasets.value.find(d => d.id === id)
    if (ds) {
      detailData.value = ds
      showDetail.value = true
    }
    setTimeout(() => { highlightId.value = null }, 3000)
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.catalog-page { display: flex; flex-direction: column; gap: $spacing-lg; }
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

.search-area {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-lg; box-shadow: $shadow-sm;
}
.search-input-wrap {
  position: relative; margin-bottom: $spacing-md;
  .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: $text-muted; font-size: 16px; }
  input { width: 100%; padding: 10px 12px 10px 36px; border: 1px solid $border-color; border-radius: $radius-md; font-size: $font-size-md; outline: none; &:focus { border-color: $primary; } }
}
.filter-tags { display: flex; gap: $spacing-sm; flex-wrap: wrap; }
.tag-btn {
  padding: 4px 12px; border: 1px solid $border-color; border-radius: 16px; font-size: $font-size-xs; background: $white; color: $text-secondary; cursor: pointer;
  &:hover { border-color: $primary; color: $primary; }
  &.active { background: $primary; color: $white; border-color: $primary; }
}

.catalog-body { display: flex; gap: $spacing-lg; }

.category-tree {
  width: 200px; flex-shrink: 0; background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden;
}
.tree-header {
  padding: $spacing-md $spacing-lg; background: #4a6a8a; color: $white; font-size: $font-size-sm; font-weight: 600; display: flex; align-items: center; gap: $spacing-sm;
}
.tree-list { padding: $spacing-sm 0; }
.tree-item {
  display: flex; align-items: center; gap: $spacing-sm; padding: 8px $spacing-lg; font-size: $font-size-sm; color: $text-secondary; cursor: pointer; transition: all $transition-fast;
  &:hover { background: $sidebar-item-hover; color: $primary; }
  &.active { background: $sidebar-item-active; color: $primary; font-weight: 600; }
  .tree-count { margin-left: auto; font-size: $font-size-xs; color: $text-muted; }
}

.dataset-list { flex: 1; }
.list-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: $spacing-md;
  .result-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
  select { padding: 4px 8px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-xs; }
}

.dataset-cards { display: flex; flex-direction: column; gap: $spacing-md; }
.dataset-card {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-lg; box-shadow: $shadow-sm; transition: all 0.25s; cursor: pointer;
  &:hover { box-shadow: $shadow-md; border-color: $primary; transform: translateY(-1px); }
  &.highlighted { border-color: $primary; box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15); animation: highlightPulse 1.5s ease 2; }
}
@keyframes highlightPulse { 0%, 100% { box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.15); } 50% { box-shadow: 0 0 0 6px rgba(0, 102, 204, 0.25); } }
.card-top { display: flex; align-items: center; gap: $spacing-sm; margin-bottom: $spacing-sm; }
.ds-type {
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 3px;
  &.db { background: #e3f2fd; color: #1565c0; }
  &.iot { background: #e8f5e9; color: #2e7d32; }
  &.gis { background: #fff3e0; color: #e65100; }
  &.csv { background: #f3e5f5; color: #7b1fa2; }
  &.api { background: #fce4ec; color: #c62828; }
}
.ds-grade {
  font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 3px;
  &.grade-1 { background: #ffebee; color: #c62828; }
  &.grade-2 { background: #fff8e1; color: #e65100; }
  &.grade-3 { background: #e8f5e9; color: #2e7d32; }
}
.ds-name { font-size: $font-size-md; font-weight: 600; margin-bottom: $spacing-xs; }
.ds-desc { font-size: $font-size-sm; color: $text-secondary; margin-bottom: $spacing-md; }
.ds-meta {
  display: flex; gap: $spacing-lg; margin-bottom: $spacing-sm;
  span { font-size: $font-size-xs; color: $text-muted; display: flex; align-items: center; gap: 4px; }
}
.ds-tags { display: flex; gap: $spacing-xs; flex-wrap: wrap; }
.ds-tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: $bg-light; color: $text-secondary; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .category-tree { width: 160px; }
  .catalog-body { flex-direction: column; }
  .category-tree { width: 100%; }
}
</style>
