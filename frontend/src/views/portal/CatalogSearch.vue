<template>
  <div class="catalog-search-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">데이터 검색</span>
    </nav>

    <div class="page-header">
      <h2>데이터 검색</h2>
      <p>키워드, 태그, 속성 기반으로 데이터를 상세 검색합니다.</p>
    </div>

    <!-- 상세 검색 폼 -->
    <div class="search-form">
      <div class="search-main">
        <SearchOutlined class="search-icon" />
        <input type="text" v-model="keyword" placeholder="키워드를 입력하세요" @keyup.enter="onSearch" />
        <button class="btn btn-primary" @click="onSearch">검색</button>
      </div>
      <div class="advanced-filters">
        <div class="filter-group"><label>데이터 유형</label><select v-model="filterType"><option value="">전체</option><option>DB</option><option>IoT</option><option>GIS</option><option>API</option><option>CSV</option></select></div>
        <div class="filter-group"><label>등급</label><select v-model="filterGrade"><option value="">전체</option><option>L1 (비공개)</option><option>L2 (내부공유)</option><option>L3 (공개)</option></select></div>
        <div class="filter-group"><label>기간</label><select v-model="filterPeriod"><option value="">전체</option><option>최근 1주</option><option>최근 1개월</option><option>최근 3개월</option><option>최근 1년</option></select></div>
        <div class="filter-group"><label>정렬</label><select v-model="sortBy"><option value="relevance">관련도순</option><option value="latest">최신순</option><option value="name">이름순</option><option value="popular">인기순</option></select></div>
      </div>
    </div>

    <!-- 검색 결과 -->
    <div class="search-results">
      <div class="result-header">
        <span class="result-count">"<strong>{{ keyword || '전체' }}</strong>" 검색 결과 <strong>{{ results.length }}</strong>건</span>
      </div>
      <div class="result-list">
        <div v-for="r in results" :key="r.id" class="result-item">
          <div class="result-top">
            <span class="r-type" :class="r.type">{{ r.typeLabel }}</span>
            <span class="r-grade" :class="'grade-' + r.grade">L{{ r.grade }}</span>
            <span class="r-score"><ThunderboltOutlined /> 관련도 {{ r.score }}%</span>
          </div>
          <h4 @click="onResultClick(r)">{{ r.name }}</h4>
          <p class="r-desc">{{ r.description }}</p>
          <div class="r-meta">
            <span><UserOutlined /> {{ r.owner }}</span>
            <span><TableOutlined /> {{ r.columns }}개 컬럼</span>
            <span><DatabaseOutlined /> {{ r.rows }}</span>
            <span><ClockCircleOutlined /> {{ r.updated }}</span>
          </div>
          <div class="r-tags">
            <span v-for="tag in r.tags" :key="tag" class="r-tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 데이터셋 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">데이터셋 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.typeLabel }}</span></div>
          <div class="modal-info-item"><span class="info-label">등급</span><span class="info-value">L{{ detailData.grade }}</span></div>
          <div class="modal-info-item"><span class="info-label">관련도</span><span class="info-value">{{ detailData.score }}%</span></div>
          <div class="modal-info-item"><span class="info-label">담당 부서</span><span class="info-value">{{ detailData.owner }}</span></div>
          <div class="modal-info-item"><span class="info-label">컬럼 수</span><span class="info-value">{{ detailData.columns }}개</span></div>
          <div class="modal-info-item"><span class="info-label">데이터 건수</span><span class="info-value">{{ detailData.rows }}</span></div>
          <div class="modal-info-item"><span class="info-label">최종 수정일</span><span class="info-value">{{ detailData.updated }}</span></div>
        </div>
      </div>
      <div class="modal-section">
        <div class="modal-section-title">설명</div>
        <p style="font-size: 13px; color: #555; line-height: 1.6;">{{ detailData.description }}</p>
      </div>
      <div class="modal-section" v-if="detailData.tags">
        <div class="modal-section-title">태그</div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
          <span v-for="tag in detailData.tags" :key="tag" class="badge badge-info">{{ tag }}</span>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false">데이터 신청</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { SearchOutlined, ThunderboltOutlined, UserOutlined, TableOutlined, DatabaseOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import AdminModal from '../../components/AdminModal.vue'
import { catalogApi } from '../../api/portal.api'

const route = useRoute()
const keyword = ref('')
const filterType = ref(''), filterGrade = ref(''), filterPeriod = ref(''), sortBy = ref('relevance')
const showDetail = ref(false)
const detailData = ref<any>({})

// Fallback mock data
const defaultResults = [
  { id: 1, name: '댐 수위 관측 데이터 (실시간)', description: '전국 다목적댐 실시간 수위 관측 데이터. 10분 간격 자동 측정, 수위(m), 유입량, 방류량, 저수율 포함', type: 'db', typeLabel: 'DB', grade: 3, score: 98, owner: '수자원부', columns: 12, rows: '1.2억건', updated: '2026-03-25', tags: ['수위', '댐', '실시간', '관측'] },
  { id: 2, name: '수질 모니터링 센서 데이터', description: 'IoT 센서 기반 수질 항목별 실시간 측정값. pH, DO, BOD, COD, SS, T-N, T-P 포함', type: 'iot', typeLabel: 'IoT', grade: 2, score: 92, owner: '환경부', columns: 18, rows: '8,500만건', updated: '2026-03-25', tags: ['수질', 'IoT', '센서', '환경'] },
  { id: 3, name: '상수도 관로 GIS 데이터', description: '전국 상수도 관로 네트워크 공간정보. 관로 위치, 구경, 매설연도, 관종 정보 포함', type: 'gis', typeLabel: 'GIS', grade: 2, score: 85, owner: '수도부', columns: 24, rows: '320만건', updated: '2026-03-24', tags: ['GIS', '관로', '상수도', '공간정보'] },
  { id: 4, name: '전력 사용량 통계 (월별)', description: 'K-water 전국 사업장별 월간 전력 사용량 집계. 사업장코드, 사용량(kWh), 요금 포함', type: 'csv', typeLabel: 'CSV', grade: 3, score: 78, owner: '경영부', columns: 8, rows: '15,600건', updated: '2026-03-23', tags: ['전력', '통계', '경영'] },
  { id: 5, name: '강수량 예측 모델 API', description: '기상청 연동 강수량 예측 REST API. 지역별 시간대별 강수 확률 및 예상 강수량 제공', type: 'api', typeLabel: 'API', grade: 3, score: 72, owner: '수자원부', columns: 6, rows: 'API', updated: '2026-03-25', tags: ['기상', 'API', '예측', '강수'] },
]

const results = ref(defaultResults)

async function onSearch() {
  try {
    const params: Record<string, any> = { page: 1, page_size: 20, sort: sortBy.value }
    if (keyword.value) params.keyword = keyword.value
    if (filterType.value) params.type = filterType.value
    if (filterGrade.value) params.grade = filterGrade.value
    if (filterPeriod.value) params.period = filterPeriod.value
    const res = await catalogApi.search(params)
    if (res.data?.items) results.value = res.data.items
  } catch (e) {
    console.error('검색 실패:', e)
  }
}

function onResultClick(result: any) {
  detailData.value = result
  showDetail.value = true
}

onMounted(() => {
  if (route.query.q) {
    keyword.value = route.query.q as string
    onSearch()
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.catalog-search-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.search-form { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-xl; box-shadow: $shadow-sm; }
.search-main { display: flex; gap: $spacing-sm; margin-bottom: $spacing-lg; position: relative;
  .search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: $text-muted; font-size: 16px; }
  input { flex: 1; padding: 12px 14px 12px 40px; border: 2px solid $border-color; border-radius: $radius-md; font-size: $font-size-md; outline: none; &:focus { border-color: $primary; } }
}
.advanced-filters { display: flex; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: $spacing-xs;
  label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; }
  select { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 130px; background: $white; }
}
.search-results { }
.result-header { margin-bottom: $spacing-md; .result-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } } }
.result-list { display: flex; flex-direction: column; gap: $spacing-md; }
.result-item { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-lg; box-shadow: $shadow-sm; &:hover { box-shadow: $shadow-md; } }
.result-top { display: flex; align-items: center; gap: $spacing-sm; margin-bottom: $spacing-sm; }
.r-type { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 3px; &.db { background: #e3f2fd; color: #1565c0; } &.iot { background: #e8f5e9; color: #2e7d32; } &.gis { background: #fff3e0; color: #e65100; } &.csv { background: #f3e5f5; color: #7b1fa2; } &.api { background: #fce4ec; color: #c62828; } }
.r-grade { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 3px; &.grade-1 { background: #ffebee; color: #c62828; } &.grade-2 { background: #fff8e1; color: #e65100; } &.grade-3 { background: #e8f5e9; color: #2e7d32; } }
.r-score { font-size: $font-size-xs; color: $primary; margin-left: auto; }
.result-item h4 { font-size: $font-size-md; font-weight: 600; margin-bottom: $spacing-xs; cursor: pointer; &:hover { color: $primary; } }
.r-desc { font-size: $font-size-sm; color: $text-secondary; margin-bottom: $spacing-md; line-height: 1.5; }
.r-meta { display: flex; gap: $spacing-lg; margin-bottom: $spacing-sm; span { font-size: $font-size-xs; color: $text-muted; display: flex; align-items: center; gap: 4px; } }
.r-tags { display: flex; gap: $spacing-xs; flex-wrap: wrap; }
.r-tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: $bg-light; color: $text-secondary; }
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) { .advanced-filters { flex-direction: column; } }
</style>
