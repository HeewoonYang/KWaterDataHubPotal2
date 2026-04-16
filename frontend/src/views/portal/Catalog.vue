<template>
  <div class="catalog-page">
    <nav class="breadcrumb">
      <router-link to="/portal/catalog">데이터카탈로그</router-link>
      <span class="separator">&gt;</span>
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
      <div class="filter-bar">
        <div class="filter-tags">
          <button v-for="tag in filterTags" :key="tag" class="tag-btn" :class="{ active: selectedTag === tag }" @click="selectedTag = selectedTag === tag ? '' : tag">
            {{ tag }}
          </button>
        </div>
        <div class="advanced-filters">
          <select v-model="filterPeriod" class="adv-select">
            <option value="">전체 기간</option>
            <option value="7">최근 1주</option>
            <option value="30">최근 1개월</option>
            <option value="90">최근 3개월</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 본문: 트리 + 목록 -->
    <div class="catalog-body">
      <!-- 좌측 분류 트리 -->
      <aside class="category-tree">
        <div class="tree-header"><AppstoreOutlined /> 분류체계</div>
        <ul class="tree-list">
          <li class="tree-item" :class="{ active: selectedCategory === '' }" @click="selectedCategory = ''">
            <AppstoreOutlined /><span>전체</span><span class="tree-count">{{ categories.reduce((s, c) => s + c.count, 0) }}</span>
          </li>
          <li v-for="cat in categories" :key="cat.name" class="tree-item" :class="{ active: selectedCategory === cat.name }" @click="selectedCategory = cat.name">
            <FolderOutlined /><span>{{ cat.name }}</span><span class="tree-count">{{ cat.count }}</span>
          </li>
        </ul>
        <!-- 패싯 필터: 보안 등급 -->
        <div class="tree-header" style="margin-top:12px;"><SafetyOutlined /> 보안 등급</div>
        <ul class="tree-list">
          <li class="tree-item" :class="{ active: filterGrade === '' }" @click="filterGrade = ''"><span>전체</span></li>
          <li class="tree-item" :class="{ active: filterGrade === '3' }" @click="filterGrade = '3'"><span class="grade-dot public"></span><span>L3 공개</span></li>
          <li class="tree-item" :class="{ active: filterGrade === '2' }" @click="filterGrade = '2'"><span class="grade-dot internal"></span><span>L2 내부공유</span></li>
          <li class="tree-item" :class="{ active: filterGrade === '1' }" @click="filterGrade = '1'"><span class="grade-dot restricted"></span><span>L1 비공개</span></li>
        </ul>
        <!-- 패싯 필터: 데이터 형식 -->
        <div class="tree-header" style="margin-top:12px;"><DatabaseOutlined /> 데이터 형식</div>
        <ul class="tree-list">
          <li class="tree-item" :class="{ active: filterFormat === '' }" @click="filterFormat = ''"><span>전체</span></li>
          <li class="tree-item" :class="{ active: filterFormat === 'DB' }" @click="filterFormat = 'DB'"><span>DB</span></li>
          <li class="tree-item" :class="{ active: filterFormat === 'IoT' }" @click="filterFormat = 'IoT'"><span>IoT</span></li>
          <li class="tree-item" :class="{ active: filterFormat === 'API' }" @click="filterFormat = 'API'"><span>API</span></li>
          <li class="tree-item" :class="{ active: filterFormat === 'CSV' }" @click="filterFormat = 'CSV'"><span>CSV</span></li>
          <li class="tree-item" :class="{ active: filterFormat === 'GIS' }" @click="filterFormat = 'GIS'"><span>GIS</span></li>
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
              <span class="ds-quality good">{{ Math.round(85 + Math.random() * 12) }}%</span>
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
            <button v-if="!cartStore.isInCart(String(ds.id))" class="cart-add-btn" @click.stop="openCartModal(ds)"><ShoppingCartOutlined /> 담기</button>
            <span v-else class="cart-added"><CheckOutlined /> 담김</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 데이터셋 상세 팝업 (탭 구조) -->
    <AdminModal :visible="showDetail" :title="detailData.name" size="xl" @close="showDetail = false">
      <!-- KPI 카드 -->
      <div class="modal-stats">
        <div class="modal-stat-card primary"><div class="stat-title">유형</div><div class="stat-number">{{ detailData.typeLabel }}</div></div>
        <div class="modal-stat-card success"><div class="stat-title">등급</div><div class="stat-number">L{{ detailData.grade }}</div></div>
        <div class="modal-stat-card warning"><div class="stat-title">컬럼</div><div class="stat-number">{{ detailData.columns }}개</div></div>
        <div class="modal-stat-card info"><div class="stat-title">건수</div><div class="stat-number">{{ detailData.rows }}</div></div>
        <div class="modal-stat-card" :class="detailData.qualityScore >= 90 ? 'success' : detailData.qualityScore >= 70 ? 'warning' : 'danger'">
          <div class="stat-title">품질</div><div class="stat-number">{{ detailData.qualityScore || '-' }}%</div>
        </div>
      </div>

      <!-- 탭 -->
      <div class="detail-tabs">
        <button :class="{ active: detailTab === 'overview' }" @click="detailTab = 'overview'">개요 / 스키마</button>
        <button :class="{ active: detailTab === 'lineage' }" @click="detailTab = 'lineage'">데이터 계보</button>
        <button :class="{ active: detailTab === 'graph' }" @click="detailTab = 'graph'">지식 그래프</button>
        <button :class="{ active: detailTab === 'preview' }" @click="detailTab = 'preview'">샘플 미리보기</button>
        <button :class="{ active: detailTab === 'viz' }" @click="detailTab = 'viz'; loadRelatedCharts(String(detailData.id))"><BarChartOutlined /> 시각화</button>
      </div>

      <!-- 개요/스키마 탭 -->
      <div v-if="detailTab === 'overview'">
        <div class="modal-section">
          <div class="modal-section-title">기본 정보</div>
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">데이터셋명</span><span class="info-value">{{ detailData.name }}</span></div>
            <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ detailData.typeLabel }}</span></div>
            <div class="modal-info-item"><span class="info-label">보안 등급</span><span class="info-value">L{{ detailData.grade }} <span :class="'approval-inline ' + ((detailData.grade||3) <= 1 ? 'need' : (detailData.grade||3) <= 2 ? 'auto' : 'public')">{{ (detailData.grade||3) <= 1 ? '승인필요' : (detailData.grade||3) <= 2 ? '자동승인' : '공개' }}</span></span></div>
            <div class="modal-info-item"><span class="info-label">최종 수정일</span><span class="info-value">{{ detailData.updated }}</span></div>
            <div class="modal-info-item"><span class="info-label">컬럼 수</span><span class="info-value">{{ detailData.columns }}개</span></div>
            <div class="modal-info-item"><span class="info-label">데이터 건수</span><span class="info-value">{{ detailData.rows }}</span></div>
          </div>
        </div>
        <div class="modal-section" v-if="detailData.description">
          <div class="modal-section-title">설명</div>
          <p style="font-size:13px;color:#555;line-height:1.6;">{{ detailData.description }}</p>
        </div>
        <div class="modal-section" v-if="detailData.tags?.length">
          <div class="modal-section-title">태그</div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <span v-for="tag in detailData.tags" :key="tag" class="badge badge-info">{{ tag }}</span>
          </div>
        </div>
        <div class="modal-section">
          <div class="modal-section-title">컬럼 정보</div>
          <table class="modal-table">
            <thead><tr><th>번호</th><th>컬럼명</th><th>데이터 타입</th><th>설명</th><th>NULL 허용</th></tr></thead>
            <tbody>
              <tr v-for="(col, i) in sampleColumns" :key="i">
                <td class="text-center">{{ i + 1 }}</td><td>{{ col.name }}</td><td>{{ col.dataType }}</td><td>{{ col.desc }}</td><td class="text-center">{{ col.nullable }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 데이터 계보 탭 -->
      <div v-else-if="detailTab === 'lineage'" class="tab-content-lineage">
        <p style="font-size:12px;color:#999;margin-bottom:8px;">이 데이터셋의 수집 원천부터 활용까지의 흐름입니다.</p>
        <div class="lineage-mini">
          <div class="lineage-step"><div class="step-icon src">📡</div><div class="step-label">원천</div><div class="step-sub">{{ detailData.typeLabel || 'DB' }}</div></div>
          <div class="lineage-arrow">→</div>
          <div class="lineage-step"><div class="step-icon ing">⚙️</div><div class="step-label">수집/정제</div><div class="step-sub">ETL 파이프라인</div></div>
          <div class="lineage-arrow">→</div>
          <div class="lineage-step active"><div class="step-icon ds">📊</div><div class="step-label">{{ detailData.name?.substring(0,12) }}</div><div class="step-sub">현재 데이터셋</div></div>
          <div class="lineage-arrow">→</div>
          <div class="lineage-step"><div class="step-icon srv">📈</div><div class="step-label">활용</div><div class="step-sub">대시보드/API</div></div>
        </div>
        <div style="text-align:center;margin-top:12px;">
          <button class="btn btn-sm btn-outline" @click="goToLineageDetail()">상세 리니지 보기 →</button>
        </div>
      </div>

      <!-- 지식 그래프 탭 -->
      <div v-else-if="detailTab === 'graph'" class="tab-content-graph">
        <p style="font-size:12px;color:#999;margin-bottom:8px;">이 데이터셋과 연결된 시설, 시스템, 지표의 온톨로지 관계입니다.</p>
        <div style="text-align:center;padding:30px 0;">
          <button class="btn btn-primary" @click="goToKnowledgeGraph()"><NodeIndexOutlined /> 지식그래프에서 탐색</button>
        </div>
      </div>

      <!-- 샘플 미리보기 탭 -->
      <div v-else-if="detailTab === 'preview'" class="tab-content-preview">
        <p style="font-size:12px;color:#999;margin-bottom:8px;">최근 데이터 샘플 (최대 5건)</p>
        <table class="modal-table">
          <thead><tr><th v-for="col in sampleColumns.slice(0,6)" :key="col.name">{{ col.name }}</th></tr></thead>
          <tbody>
            <tr v-for="r in 5" :key="r"><td v-for="col in sampleColumns.slice(0,6)" :key="col.name + r" style="font-family:monospace;font-size:11px;">sample_{{ r }}_{{ col.name.substring(0,5) }}</td></tr>
          </tbody>
        </table>
      </div>

      <!-- 시각화 탭 -->
      <div v-else-if="detailTab === 'viz'" class="tab-content-viz">
        <div v-if="chartsLoading" style="text-align:center;padding:30px;color:#999;">차트를 불러오는 중...</div>
        <div v-else-if="relatedCharts.length === 0" style="text-align:center;padding:30px;">
          <p style="color:#999;margin-bottom:12px;">이 데이터셋으로 만든 시각화 차트가 없습니다.</p>
          <button class="btn btn-primary" @click="goToNewVisualization(String(detailData.id))"><PlusOutlined /> 새 시각화 만들기</button>
        </div>
        <div v-else>
          <p style="font-size:12px;color:#999;margin-bottom:12px;">이 데이터셋으로 만든 차트 {{ relatedCharts.length }}건</p>
          <div class="viz-chart-list">
            <div v-for="chart in relatedCharts" :key="chart.id" class="viz-chart-card">
              <div class="viz-chart-header">
                <component :is="chartTypeIcon[chart.chart_type] || BarChartOutlined" style="font-size:18px;color:#0066CC;" />
                <div class="viz-chart-info">
                  <span class="viz-chart-name">{{ chart.chart_name }}</span>
                  <span class="viz-chart-meta">{{ chart.owner_name || '시스템' }} · {{ chart.created_at?.substring(0, 10) }}</span>
                </div>
              </div>
              <div class="viz-chart-actions">
                <button class="btn btn-sm btn-primary" @click="reuseChartWithEdit(chart)" title="기간 재설정하여 편집"><EditOutlined /> 기간 재설정</button>
                <button class="btn btn-sm btn-outline" @click="reuseChartAsCopy(chart)" title="그대로 복사"><CopyOutlined /> 그대로 사용</button>
              </div>
            </div>
          </div>
          <div style="text-align:center;margin-top:12px;">
            <button class="btn btn-outline" @click="goToNewVisualization(String(detailData.id))"><PlusOutlined /> 새 시각화 만들기</button>
          </div>
        </div>
      </div>

      <template #footer>
        <button v-if="!cartStore.isInCart(String(detailData.id))" class="btn btn-outline" @click="openCartModal(detailData)"><ShoppingCartOutlined /> 장바구니 담기</button>
        <span v-else style="color:#28A745;font-size:12px;display:flex;align-items:center;gap:4px;"><CheckOutlined /> 장바구니에 담김</span>
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

    <!-- 장바구니 담기 모달 (기간/용량 입력) -->
    <AdminModal :visible="showCartModal" :title="'장바구니 담기 - ' + (cartTarget?.name || '')" size="md" @close="showCartModal = false">
      <div class="cart-modal-info">
        <div class="cm-row"><span class="cm-label">데이터셋</span><span class="cm-value">{{ cartTarget?.name }}</span></div>
        <div class="cm-row"><span class="cm-label">유형</span><span class="cm-value">{{ cartTarget?.typeLabel || cartTarget?.type }}</span></div>
        <div class="cm-row"><span class="cm-label">등급</span><span class="cm-value">L{{ cartTarget?.grade }}</span></div>
      </div>
      <div class="cart-modal-form">
        <div class="cm-section-title">데이터 규모 지정</div>
        <div class="cm-form-row">
          <div class="cm-form-group">
            <label>조회 기간 (시작)</label>
            <input type="date" v-model="cartOpts.dateFrom" />
          </div>
          <div class="cm-form-group">
            <label>조회 기간 (종료)</label>
            <input type="date" v-model="cartOpts.dateTo" />
          </div>
        </div>
        <div class="cm-form-row">
          <div class="cm-form-group">
            <label>최대 건수</label>
            <select v-model="cartOpts.maxRows">
              <option value="">제한 없음</option>
              <option value="1000">1,000건</option>
              <option value="10000">10,000건</option>
              <option value="100000">100,000건</option>
              <option value="1000000">1,000,000건</option>
            </select>
          </div>
          <div class="cm-form-group">
            <label>요청 포맷</label>
            <select v-model="cartOpts.format">
              <option value="CSV">CSV</option>
              <option value="JSON">JSON</option>
              <option value="API">API 접근</option>
            </select>
          </div>
        </div>
        <div class="cm-form-group">
          <label>사용 목적 (선택)</label>
          <input type="text" v-model="cartOpts.purpose" placeholder="예: 수질 분석, 보고서 작성" />
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="confirmAddToCart"><ShoppingCartOutlined /> 장바구니에 담기</button>
        <button class="btn btn-outline" @click="showCartModal = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  SearchOutlined,
  AppstoreOutlined,
  FolderOutlined,
  TableOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import AdminModal from '../../components/AdminModal.vue'
import { catalogApi, distributionApi, visualizationApi } from '../../api/portal.api'
import { useCartStore } from '../../stores/cart'
import { ShoppingCartOutlined, CheckOutlined, NodeIndexOutlined, BarChartOutlined, LineChartOutlined, PieChartOutlined, CopyOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons-vue'

import { SafetyOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const cartStore = useCartStore()
const detailTab = ref('overview')
const filterGrade = ref('')
const filterFormat = ref('')
const filterPeriod = ref('')

// 장바구니 담기 모달
const showCartModal = ref(false)
const cartTarget = ref<any>(null)
const today = new Date()
const weekAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
const cartOpts = ref({
  dateFrom: weekAgo.toISOString().substring(0, 10),
  dateTo: today.toISOString().substring(0, 10),
  maxRows: '',
  format: 'CSV',
  purpose: '',
})

function openCartModal(ds: any) {
  cartTarget.value = ds
  cartOpts.value = {
    dateFrom: weekAgo.toISOString().substring(0, 10),
    dateTo: today.toISOString().substring(0, 10),
    maxRows: '', format: 'CSV', purpose: '',
  }
  showCartModal.value = true
}

function confirmAddToCart() {
  if (!cartTarget.value) return
  const ds = cartTarget.value
  cartStore.addItem({
    id: ds.id, dataset_name: ds.name, data_format: ds.typeLabel,
    grade_code: 'L' + ds.grade, row_count: 0, tags: ds.tags,
    // 규모 옵션 저장
    dateFrom: cartOpts.value.dateFrom,
    dateTo: cartOpts.value.dateTo,
    maxRows: cartOpts.value.maxRows,
    requestFormat: cartOpts.value.format,
    purpose: cartOpts.value.purpose,
  })
  showCartModal.value = false
}

// addToCart는 openCartModal → confirmAddToCart로 대체됨

function goToLineageDetail() {
  showDetail.value = false
  router.push({ path: '/portal/catalog/lineage', query: { search: detailData.value.name } })
}
function goToKnowledgeGraph() {
  showDetail.value = false
  router.push({ path: '/portal/catalog/knowledge-graph' })
}

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
  let list = [...datasets.value]
  // 등급 필터
  if (filterGrade.value) list = list.filter(d => String(d.grade) === filterGrade.value)
  // 형식 필터
  if (filterFormat.value) list = list.filter(d => (d.typeLabel || d.type || '').toUpperCase() === filterFormat.value.toUpperCase())
  // 정렬
  if (sortBy.value === 'latest') list.sort((a, b) => b.updated.localeCompare(a.updated))
  else if (sortBy.value === 'name') list.sort((a, b) => a.name.localeCompare(b.name))
  return list
})

// Re-fetch when filters change
watch([selectedCategory, selectedTag, sortBy], () => { fetchDatasets() })

// ── 시각화 관련 ──
const relatedCharts = ref<any[]>([])
const chartsLoading = ref(false)

async function loadRelatedCharts(datasetId: string) {
  chartsLoading.value = true
  relatedCharts.value = []
  try {
    const res = await visualizationApi.listCharts({ dataset_id: datasetId, page_size: 10 })
    if (res.data?.items) relatedCharts.value = res.data.items
  } catch { /* fallback */ }
  chartsLoading.value = false
}

const chartTypeIcon: Record<string, any> = { bar: BarChartOutlined, line: LineChartOutlined, pie: PieChartOutlined }

async function reuseChartWithEdit(chart: any) {
  try {
    const res = await visualizationApi.cloneChart(String(chart.id))
    const cloned = res.data?.data
    if (cloned) {
      showDetail.value = false
      router.push({ path: '/portal/visualization', query: { edit: String(cloned.id) } })
    }
  } catch { message.error('차트 복제에 실패했습니다.') }
}

async function reuseChartAsCopy(chart: any) {
  try {
    await visualizationApi.cloneChart(String(chart.id))
    message.success('내 차트로 복사되었습니다.')
  } catch { message.error('차트 복제에 실패했습니다.') }
}

function goToNewVisualization(datasetId: string) {
  showDetail.value = false
  router.push({ path: '/portal/visualization', query: { dataset_id: datasetId } })
}

function openDetail(ds: any) {
  detailData.value = { ...ds, qualityScore: Math.round(85 + Math.random() * 12) }
  detailTab.value = 'overview'
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
  if (!requestForm.value.purpose?.trim()) return message.warning('사용 목적을 입력해주세요.')
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
    message.error('신청에 실패했습니다. 다시 시도해주세요.')
  }
}

// URL 파라미터로 최신순 정렬 + 하이라이트 처리
onMounted(async () => {
  if (route.query.sort === 'latest') sortBy.value = 'latest'

  await Promise.all([fetchCategories(), fetchDatasets()])

  // 대시보드에서 클릭 시 ?detail=id 또는 ?highlight=id 로 상세 열기
  const targetId = route.query.detail || route.query.highlight
  if (targetId) {
    const idStr = String(targetId)
    const ds = datasets.value.find(d => String(d.id) === idStr)
    if (ds) {
      highlightId.value = ds.id
      detailData.value = ds
      showDetail.value = true
      setTimeout(() => { highlightId.value = null }, 3000)
    }
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
// 품질 점수 배지
.ds-quality { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 3px; margin-left: auto;
  &.good { background: #f6ffed; color: #28A745; } &.warn { background: #fff7e6; color: #fa8c16; } &.bad { background: #fff1f0; color: #DC3545; }
}
// 패싯 필터
.grade-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px;
  &.public { background: #28A745; } &.internal { background: #0066CC; } &.restricted { background: #DC3545; }
}
// 상세 모달 탭
.detail-tabs { display: flex; gap: 2px; border-bottom: 2px solid #e8e8e8; margin-bottom: 12px;
  button { padding: 8px 16px; border: none; background: none; font-size: 13px; color: #666; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px;
    &.active { color: #0066CC; border-bottom-color: #0066CC; font-weight: 600; } &:hover { color: #0066CC; }
  }
}
// 승인 인라인 배지
.approval-inline { font-size: 10px; padding: 1px 6px; border-radius: 3px; margin-left: 4px;
  &.public { background: #f6ffed; color: #28A745; } &.auto { background: #e6f7ff; color: #0066CC; } &.need { background: #fff7e6; color: #fa8c16; }
}
// 미니 리니지
.lineage-mini { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 20px 0; }
.lineage-step { text-align: center; min-width: 80px;
  &.active .step-icon { border: 2px solid #0066CC; }
}
.step-icon { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; margin: 0 auto 4px; border: 1px solid #ddd;
  &.src { background: #e6f7ff; } &.ing { background: #f6ffed; } &.ds { background: #fff7e6; } &.srv { background: #f9f0ff; }
}
.step-label { font-size: 11px; font-weight: 600; } .step-sub { font-size: 10px; color: #999; }
.lineage-arrow { font-size: 18px; color: #ccc; }
// 장바구니 모달
.cart-modal-info { background: #f5f7fa; border-radius: 6px; padding: 12px; margin-bottom: 16px;
  .cm-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; .cm-label { color: #999; } .cm-value { font-weight: 600; } }
}
.cart-modal-form { .cm-section-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid #0066CC; }
  .cm-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 10px; }
  .cm-form-group { display: flex; flex-direction: column; gap: 4px;
    label { font-size: 12px; font-weight: 600; color: #555; }
    input, select { padding: 7px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; &:focus { outline: none; border-color: #0066CC; } }
  }
}
// 고급 필터 바
.filter-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.advanced-filters { display: flex; gap: 8px; .adv-select { padding: 4px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 12px; } }
// 장바구니 버튼
.cart-add-btn { position: absolute; bottom: 10px; right: 10px; padding: 3px 10px; border: 1px solid $primary; border-radius: 4px; background: #fff; color: $primary; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 4px; &:hover { background: #e6f7ff; } }
.cart-added { position: absolute; bottom: 10px; right: 10px; font-size: 11px; color: #28A745; display: flex; align-items: center; gap: 4px; }
.dataset-card { position: relative; }

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .category-tree { width: 160px; }
  .catalog-body { flex-direction: column; }
  .category-tree { width: 100%; }
}

// 시각화 탭 스타일
.viz-chart-list { display: flex; flex-direction: column; gap: 10px; }
.viz-chart-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border: 1px solid #e8e8e8; border-radius: 8px; background: #fafbfc;
  &:hover { border-color: #0066CC; background: #f0f7ff; }
}
.viz-chart-header { display: flex; align-items: center; gap: 12px; }
.viz-chart-info { display: flex; flex-direction: column; }
.viz-chart-name { font-size: 13px; font-weight: 600; color: #1a1a1a; }
.viz-chart-meta { font-size: 11px; color: #999; }
.viz-chart-actions { display: flex; gap: 6px; }
.btn-sm { padding: 4px 10px; font-size: 11px; }
</style>
