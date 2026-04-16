<template>
  <div class="dashboard">
    <!-- 공유 대시보드 배너 -->
    <div v-if="isSharedView" class="shared-banner">
      <ShareAltOutlined /> 공유된 대시보드를 보고 있습니다
      <button class="btn btn-sm btn-primary" @click="saveSharedAsOwn">내 대시보드로 저장</button>
      <router-link to="/portal" class="btn btn-sm btn-outline">내 대시보드로 돌아가기</router-link>
    </div>
    <!-- 인사말 & 검색 영역 (항상 표시, 그리드 밖) -->
    <section class="welcome-section">
      <div class="welcome-text">
        <h1>{{ welcomeTitle }}</h1>
        <p>{{ welcomeDescription }}</p>
      </div>
      <div class="search-box">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="데이터 카탈로그 검색 (데이터셋명, 키워드, 분류)"
          @keyup.enter="onSearch"
        />
        <button class="search-btn" @click="onSearch">검색</button>
      </div>
    </section>

    <!-- 빠른 실행 링크 -->
    <section v-if="quickActions.length > 0" class="quick-actions">
      <div
        v-for="action in quickActions"
        :key="action.route"
        class="quick-action-card"
        @click="router.push(action.route)"
      >
        <component :is="action.icon" class="quick-action-icon" />
        <span class="quick-action-label">{{ action.label }}</span>
        <RightOutlined class="quick-action-arrow" />
      </div>
    </section>

    <!-- 편집 모드 토글 바 -->
    <div class="edit-toolbar">
      <template v-if="!isEditMode">
        <button class="share-btn" @click="shareDashboard">
          <ShareAltOutlined /> 공유
        </button>
        <button class="edit-btn" @click="enterEditMode">
          <EditOutlined /> 편집
        </button>
      </template>
      <template v-else>
        <button class="save-btn" @click="saveLayout">
          <SaveOutlined /> 저장
        </button>
        <button class="cancel-btn" @click="cancelEdit">
          <CloseOutlined /> 취소
        </button>
      </template>
    </div>

    <!-- 위젯/갤러리 혼합 그리드 -->
    <section class="layout-grid" :class="{ 'edit-mode': isEditMode }">
      <div
        v-for="(item, idx) in layoutItems"
        :key="item.id"
        class="grid-item"
        :class="{ dragging: dragIndex === idx, 'drag-over': dropTargetIndex === idx, 'kpi-item': item.type === 'widget' && getWidgetType(item.code!) === 'KPI' }"
        :style="{
          gridColumn: `span ${item.colSpan}`,
          gridRow: `span ${item.rowSpan}`,
        }"
        :draggable="isEditMode"
        @dragstart="onDragStart($event, idx)"
        @dragover.prevent="onDragOver(idx)"
        @dragleave="onDragLeave(idx)"
        @drop="onDrop($event, idx)"
        @dragend="onDragEnd"
      >
        <!-- 편집 오버레이 -->
        <div v-if="isEditMode" class="edit-overlay">
          <div class="edit-overlay-left">
            <DragOutlined class="drag-handle" />
          </div>
          <div class="edit-overlay-right">
            <select
              class="span-select"
              :value="item.colSpan"
              @change="updateColSpan(idx, Number(($event.target as HTMLSelectElement).value))"
              title="가로 크기"
              @mousedown.stop
              @click.stop
            >
              <option :value="1">1칸</option>
              <option :value="2">2칸</option>
              <option :value="3">3칸</option>
              <option :value="4">4칸</option>
            </select>
            <select
              class="span-select"
              :value="item.rowSpan"
              @change="updateRowSpan(idx, Number(($event.target as HTMLSelectElement).value))"
              title="세로 크기"
              @mousedown.stop
              @click.stop
            >
              <option :value="1">1행</option>
              <option :value="2">2행</option>
            </select>
            <button class="remove-btn" @click.stop="removeItem(idx)" title="제거">
              <CloseOutlined />
            </button>
          </div>
        </div>

        <!-- 위젯 렌더링 -->
        <template v-if="item.type === 'widget'">
          <div class="widget-render-card">
            <div class="widget-render-header">
              <span class="widget-render-title">{{ getWidgetName(item.code!) }}</span>
              <button
                v-if="!isEditMode && isChartWidget(item.code!)"
                class="publish-gallery-btn"
                @click.stop="publishWidgetToGallery(item)"
                title="시각화 갤러리에 올리기"
              >
                <UploadOutlined />
              </button>
            </div>
            <div class="widget-render-body">
              <!-- KPI 위젯 -->
              <template v-if="getWidgetType(item.code!) === 'KPI'">
                <div class="widget-kpi">
                  <div class="widget-kpi-icon" :style="{ background: getWidgetDef(item.code!)?.iconColor }">
                    <component :is="getWidgetDef(item.code!)?.icon" />
                  </div>
                  <div class="widget-kpi-detail">
                    <span class="widget-kpi-value">{{ kpiValues[item.code!] || '-' }}</span>
                    <span class="widget-kpi-label">{{ getWidgetDef(item.code!)?.label }}</span>
                  </div>
                </div>
              </template>

              <!-- 수집/적재 현황 바 차트 -->
              <template v-else-if="item.code === 'COLLECTION_CHART'">
                <div class="widget-bar-chart">
                  <div class="chart-bar-group">
                    <div v-for="(bar, i) in barData" :key="i" class="chart-bar-item">
                      <div class="bar-wrapper">
                        <div class="bar bar-collect" :style="{ height: bar.collect + '%' }"></div>
                        <div class="bar bar-load" :style="{ height: bar.load + '%' }"></div>
                      </div>
                      <span class="bar-label">{{ bar.day }}</span>
                    </div>
                  </div>
                  <div class="chart-legend">
                    <span class="legend-item"><i class="dot" style="background:#4a8fd9"></i> 수집</span>
                    <span class="legend-item"><i class="dot" style="background:#28A745"></i> 적재</span>
                  </div>
                </div>
              </template>

              <!-- 카테고리별 도넛 차트 -->
              <template v-else-if="item.code === 'CATEGORY_CHART'">
                <div class="widget-donut-chart">
                  <div class="donut-chart">
                    <svg viewBox="0 0 120 120">
                      <circle cx="60" cy="60" r="50" fill="none" stroke="#e0e0e0" stroke-width="18" />
                      <circle
                        v-for="(seg, si) in donutSegments"
                        :key="si"
                        cx="60" cy="60" r="50" fill="none"
                        :stroke="seg.color"
                        stroke-width="18"
                        :stroke-dasharray="seg.dash"
                        :stroke-dashoffset="seg.offset"
                      />
                    </svg>
                    <div class="donut-center">
                      <span class="donut-total">{{ totalDatasets }}</span>
                      <span class="donut-label">전체</span>
                    </div>
                  </div>
                  <div class="donut-legend">
                    <div v-for="cat in categories" :key="cat.name" class="legend-row">
                      <i class="dot" :style="{ background: cat.color }"></i>
                      <span class="cat-name">{{ cat.name }}</span>
                      <span class="cat-count">{{ cat.count }}</span>
                    </div>
                  </div>
                </div>
              </template>

              <!-- 다운로드 순위 가로 바 차트 -->
              <template v-else-if="item.code === 'DOWNLOAD_RANK'">
                <div class="widget-hbar-chart">
                  <div v-for="(rank, ri) in downloadRankData" :key="ri" class="hbar-row">
                    <span class="hbar-rank">{{ ri + 1 }}</span>
                    <span class="hbar-name">{{ rank.name }}</span>
                    <div class="hbar-track">
                      <div class="hbar-fill" :style="{ width: rank.pct + '%', background: rank.color }"></div>
                    </div>
                    <span class="hbar-value">{{ rank.count }}</span>
                  </div>
                </div>
              </template>

              <!-- 최근 등록 데이터 -->
              <template v-else-if="item.code === 'RECENT_DATA'">
                <div class="widget-table">
                  <div
                    v-for="row in recentData.slice(0, 5)"
                    :key="row.id"
                    class="widget-table-row clickable"
                    @click="goToDataDetail(row)"
                  >
                    <span class="data-badge" :class="row.type">{{ row.typeLabel }}</span>
                    <span class="row-text">{{ row.name }}</span>
                    <span class="row-sub">{{ row.date }}</span>
                  </div>
                </div>
                <div class="widget-table-footer">
                  <router-link to="/portal/catalog?sort=latest" class="more-link">더보기 <RightOutlined /></router-link>
                </div>
              </template>

              <!-- 공지사항 -->
              <template v-else-if="item.code === 'NOTICES'">
                <div class="widget-table">
                  <div
                    v-for="row in notices.slice(0, 5)"
                    :key="row.id"
                    class="widget-table-row clickable"
                    @click="goToNoticeDetail(row)"
                  >
                    <span class="row-text">{{ row.title }}</span>
                    <span class="row-sub">{{ row.date }}</span>
                  </div>
                </div>
                <div class="widget-table-footer">
                  <router-link to="/portal/board/notices" class="more-link">더보기 <RightOutlined /></router-link>
                </div>
              </template>

              <!-- AI 검색 위젯 -->
              <template v-else-if="item.code === 'AI_SEARCH'">
                <div class="widget-search">
                  <SearchOutlined class="widget-search-icon" />
                  <input
                    placeholder="AI 자연어 검색으로 데이터를 찾아보세요..."
                    readonly
                    @click="router.push('/portal/ai-search')"
                  />
                </div>
              </template>
            </div>
          </div>
        </template>

        <!-- 갤러리 차트 렌더링 -->
        <template v-else-if="item.type === 'gallery'">
          <div class="widget-render-card gallery-card">
            <div class="widget-render-header">
              <span class="widget-render-title">{{ getGalleryChartName(item.chartId!) }}</span>
              <div class="gallery-header-actions">
                <button
                  v-if="!isEditMode"
                  class="publish-gallery-btn"
                  @click.stop="publishGalleryToGallery(item)"
                  title="시각화 갤러리에 올리기"
                >
                  <UploadOutlined />
                </button>
                <span class="gallery-chart-type">{{ getGalleryChartType(item.chartId!) }}</span>
              </div>
            </div>
            <div class="widget-render-body gallery-body" :class="{ 'gallery-map-body': isMapChart(item.chartId!) }">
              <!-- MAP 타입: GIS 미니맵 -->
              <template v-if="isMapChart(item.chartId!)">
                <GisMiniMap
                  :config="getGalleryMapConfig(item.chartId!)"
                  :label="getGalleryChartName(item.chartId!)"
                  :showOverlayLabel="true"
                  :interactive="true"
                />
              </template>
              <!-- 일반 차트 타입 -->
              <template v-else>
                <div class="gallery-chart-area" v-html="getGalleryChartSvg(item.chartId!)"></div>
                <div class="gallery-chart-info">
                  <div v-for="(s, si) in getGalleryChartSeries(item.chartId!)" :key="si" class="gallery-series-item">
                    <span class="series-dot" :style="{ background: seriesColors[si % seriesColors.length] }"></span>
                    <span class="series-name">{{ s.name }}</span>
                    <span class="series-value">{{ s.lastValue }}</span>
                  </div>
                  <div v-if="getGalleryChartLabels(item.chartId!).length" class="gallery-x-info">
                    {{ getGalleryChartLabels(item.chartId!)[0] }} ~ {{ getGalleryChartLabels(item.chartId!).at(-1) }}
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
      </div>
    </section>

    <!-- 레이아웃이 비어있을 때 안내 -->
    <section v-if="layoutItems.length === 0 && !isEditMode" class="empty-widgets-hint">
      <div class="hint-card" @click="enterEditMode">
        <AppstoreOutlined class="hint-icon" />
        <p>편집 버튼을 눌러 위젯과 갤러리 차트로 나만의 대시보드를 구성하세요.</p>
        <span class="hint-link">대시보드 편집하기</span>
      </div>
    </section>

    <!-- 갤러리 게시 모달 -->
    <div v-if="showPublishModal" class="publish-modal-overlay" @click.self="showPublishModal = false">
      <div class="publish-modal">
        <div class="publish-modal-header">
          <UploadOutlined /> 시각화 갤러리에 올리기
          <button class="publish-modal-close" @click="showPublishModal = false"><CloseOutlined /></button>
        </div>
        <div class="publish-modal-body">
          <div class="publish-field">
            <label>차트 이름</label>
            <input v-model="publishForm.name" placeholder="갤러리에 표시될 이름" />
          </div>
          <div class="publish-field">
            <label>설명</label>
            <textarea v-model="publishForm.description" rows="3" placeholder="차트에 대한 설명 (선택)"></textarea>
          </div>
        </div>
        <div class="publish-modal-footer">
          <button class="btn btn-primary" @click="confirmPublish"><UploadOutlined /> 갤러리에 올리기</button>
          <button class="btn btn-outline" @click="showPublishModal = false">취소</button>
        </div>
      </div>
    </div>

    <!-- 편집 모드: 아이템 추가 패널 -->
    <div class="add-panel" v-if="isEditMode">
      <div class="add-section">
        <h4><AppstoreOutlined /> 위젯 추가</h4>
        <div class="add-grid">
          <div
            v-for="w in availableWidgets"
            :key="w.code"
            class="add-card"
            @click="addWidget(w.code)"
          >
            <component v-if="w.icon" :is="w.icon" class="add-card-icon" />
            <span class="add-card-name">{{ w.name }}</span>
            <span class="add-card-type">{{ w.type }}</span>
          </div>
          <div v-if="availableWidgets.length === 0" class="add-empty">
            모든 위젯이 배치되어 있습니다.
          </div>
        </div>
      </div>
      <div class="add-section">
        <h4><BarChartOutlined /> 갤러리 차트 추가</h4>
        <div class="add-grid">
          <div
            v-for="chart in availableGalleryCharts"
            :key="chart.id"
            class="add-card"
            @click="addGalleryChart(chart)"
          >
            <BarChartOutlined class="add-card-icon" />
            <span class="add-card-name">{{ chart.name }}</span>
            <span class="add-card-type">{{ chart.chart_type || 'chart' }}</span>
          </div>
          <div v-if="availableGalleryCharts.length === 0" class="add-empty">
            추가 가능한 갤러리 차트가 없습니다.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DatabaseOutlined,
  SyncOutlined,
  DownloadOutlined,
  TeamOutlined,
  HddOutlined,
  SafetyCertificateOutlined,
  BarChartOutlined,
  AppstoreOutlined,
  SearchOutlined,
  RightOutlined,
  EditOutlined,
  SaveOutlined,
  CloseOutlined,
  DragOutlined,
  ShareAltOutlined,
  UploadOutlined,
  SettingOutlined,
  DashboardOutlined,
  CloudDownloadOutlined,
  FilterOutlined,
  CheckCircleOutlined,
  SwapOutlined,
  FileSearchOutlined,
  FolderOpenOutlined,
  GlobalOutlined,
} from '@ant-design/icons-vue'
import { dashboardApi, boardApi, widgetApi, visualizationApi } from '../../api/portal.api'
import { useAuthStore } from '../../stores/auth'
import GisMiniMap from '../../components/GisMiniMap.vue'

const route = useRoute()

const router = useRouter()
const authStore = useAuthStore()
const searchQuery = ref('')

// ── Layout Item 인터페이스 ──
interface LayoutItem {
  id: string
  type: 'widget' | 'gallery'
  code?: string
  chartId?: string
  colSpan: number
  rowSpan: number
}

// ── 위젯 정의 ──
interface WidgetDef {
  name: string
  type: 'KPI' | 'CHART' | 'TABLE' | 'SEARCH'
  defaultColSpan: number
  defaultRowSpan: number
  label?: string
  icon?: Component
  iconColor?: string
}

const widgetDefs: Record<string, WidgetDef> = {
  TOTAL_DATASETS:   { name: '총 데이터셋',     type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '전체 데이터셋',  icon: DatabaseOutlined,          iconColor: '#0066CC' },
  TODAY_COLLECTION: { name: '금일 수집건수',    type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '금일 수집',      icon: SyncOutlined,              iconColor: '#28A745' },
  TODAY_LOAD:       { name: '금일 적재건수',    type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '금일 적재',      icon: DownloadOutlined,          iconColor: '#4a8fd9' },
  ACTIVE_USERS:     { name: '활성 사용자',      type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '접속 중',        icon: TeamOutlined,              iconColor: '#9b59b6' },
  STORAGE_USAGE:    { name: '저장 용량',        type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '사용률',         icon: HddOutlined,               iconColor: '#e67e22' },
  QUALITY_SCORE:    { name: '품질 점수',        type: 'KPI',    defaultColSpan: 1, defaultRowSpan: 1, label: '전체 품질',      icon: SafetyCertificateOutlined,  iconColor: '#28A745' },
  COLLECTION_CHART: { name: '수집/적재 현황',   type: 'CHART',  defaultColSpan: 2, defaultRowSpan: 2 },
  CATEGORY_CHART:   { name: '분류별 현황',      type: 'CHART',  defaultColSpan: 2, defaultRowSpan: 2 },
  RECENT_DATA:      { name: '최근 등록 데이터', type: 'TABLE',  defaultColSpan: 2, defaultRowSpan: 2 },
  NOTICES:          { name: '공지사항',          type: 'TABLE',  defaultColSpan: 2, defaultRowSpan: 2 },
  AI_SEARCH:        { name: 'AI 검색',          type: 'SEARCH', defaultColSpan: 4, defaultRowSpan: 1 },
  DOWNLOAD_RANK:    { name: '다운로드 순위',     type: 'CHART',  defaultColSpan: 2, defaultRowSpan: 2 },
}

// ── 역할별 대시보드 설정 ──
interface QuickAction {
  label: string
  icon: Component
  route: string
}

interface RoleDashboardConfig {
  welcomeTitle: string
  welcomeDescription: string
  defaultWidgets: LayoutItem[]
  hiddenWidgets: string[]
  quickActions: QuickAction[]
}

const roleConfigs: Record<string, RoleDashboardConfig> = {
  SYS_ADMIN: {
    welcomeTitle: '시스템 관리자님, 데이터허브 현황입니다',
    welcomeDescription: '시스템 운영 현황과 데이터 관리 상태를 확인하세요.',
    defaultWidgets: [
      { id: 'w-1', type: 'widget', code: 'TOTAL_DATASETS',   colSpan: 1, rowSpan: 1 },
      { id: 'w-2', type: 'widget', code: 'TODAY_COLLECTION', colSpan: 1, rowSpan: 1 },
      { id: 'w-3', type: 'widget', code: 'TODAY_LOAD',       colSpan: 1, rowSpan: 1 },
      { id: 'w-4', type: 'widget', code: 'ACTIVE_USERS',     colSpan: 1, rowSpan: 1 },
      { id: 'w-5', type: 'widget', code: 'STORAGE_USAGE',    colSpan: 1, rowSpan: 1 },
      { id: 'w-6', type: 'widget', code: 'QUALITY_SCORE',    colSpan: 1, rowSpan: 1 },
      { id: 'w-7', type: 'widget', code: 'COLLECTION_CHART', colSpan: 2, rowSpan: 2 },
      { id: 'w-8', type: 'widget', code: 'CATEGORY_CHART',   colSpan: 2, rowSpan: 2 },
      { id: 'w-9', type: 'widget', code: 'RECENT_DATA',      colSpan: 2, rowSpan: 2 },
      { id: 'w-10', type: 'widget', code: 'NOTICES',         colSpan: 2, rowSpan: 2 },
    ],
    hiddenWidgets: [],
    quickActions: [
      { label: '시스템 관리', icon: SettingOutlined, route: '/admin/system' },
      { label: '사용자 관리', icon: TeamOutlined, route: '/admin/user' },
      { label: '운영 모니터링', icon: DashboardOutlined, route: '/admin/operation' },
    ],
  },
  DATA_ADMIN: {
    welcomeTitle: '데이터 관리자님, 데이터 현황을 확인하세요',
    welcomeDescription: '데이터 수집/정제/품질 현황을 모니터링하고 관리하세요.',
    defaultWidgets: [
      { id: 'w-1', type: 'widget', code: 'TOTAL_DATASETS',   colSpan: 1, rowSpan: 1 },
      { id: 'w-2', type: 'widget', code: 'TODAY_COLLECTION', colSpan: 1, rowSpan: 1 },
      { id: 'w-3', type: 'widget', code: 'TODAY_LOAD',       colSpan: 1, rowSpan: 1 },
      { id: 'w-4', type: 'widget', code: 'QUALITY_SCORE',    colSpan: 1, rowSpan: 1 },
      { id: 'w-5', type: 'widget', code: 'COLLECTION_CHART', colSpan: 2, rowSpan: 2 },
      { id: 'w-6', type: 'widget', code: 'CATEGORY_CHART',   colSpan: 2, rowSpan: 2 },
      { id: 'w-7', type: 'widget', code: 'RECENT_DATA',      colSpan: 2, rowSpan: 2 },
      { id: 'w-8', type: 'widget', code: 'DOWNLOAD_RANK',    colSpan: 2, rowSpan: 2 },
    ],
    hiddenWidgets: [],
    quickActions: [
      { label: '데이터 수집', icon: CloudDownloadOutlined, route: '/admin/collection' },
      { label: '데이터 정제', icon: FilterOutlined, route: '/admin/cleansing' },
      { label: '품질 관리', icon: CheckCircleOutlined, route: '/admin/standard/quality-check' },
      { label: '데이터 유통', icon: SwapOutlined, route: '/admin/distribution' },
    ],
  },
  GENERAL: {
    welcomeTitle: 'K-water 데이터허브에 오신 것을 환영합니다',
    welcomeDescription: '통합 데이터를 검색하고 활용하세요.',
    defaultWidgets: [
      { id: 'w-1', type: 'widget', code: 'TOTAL_DATASETS', colSpan: 1, rowSpan: 1 },
      { id: 'w-2', type: 'widget', code: 'ACTIVE_USERS',   colSpan: 1, rowSpan: 1 },
      { id: 'w-3', type: 'widget', code: 'CATEGORY_CHART', colSpan: 2, rowSpan: 2 },
      { id: 'w-4', type: 'widget', code: 'RECENT_DATA',    colSpan: 2, rowSpan: 2 },
      { id: 'w-5', type: 'widget', code: 'NOTICES',        colSpan: 2, rowSpan: 2 },
      { id: 'w-6', type: 'widget', code: 'AI_SEARCH',      colSpan: 4, rowSpan: 1 },
    ],
    hiddenWidgets: ['STORAGE_USAGE', 'QUALITY_SCORE'],
    quickActions: [
      { label: '데이터 검색', icon: FileSearchOutlined, route: '/portal/catalog/search' },
      { label: '데이터 유통 신청', icon: SwapOutlined, route: '/portal/distribution/request' },
      { label: '마이데이터', icon: FolderOpenOutlined, route: '/portal/mypage/data' },
    ],
  },
  EXTERNAL: {
    welcomeTitle: '공개 데이터를 검색하고 활용하세요',
    welcomeDescription: '공개된 데이터셋을 탐색하고 다운로드할 수 있습니다.',
    defaultWidgets: [
      { id: 'w-1', type: 'widget', code: 'TOTAL_DATASETS',  colSpan: 1, rowSpan: 1 },
      { id: 'w-2', type: 'widget', code: 'CATEGORY_CHART',  colSpan: 2, rowSpan: 2 },
      { id: 'w-3', type: 'widget', code: 'RECENT_DATA',     colSpan: 2, rowSpan: 2 },
      { id: 'w-4', type: 'widget', code: 'NOTICES',         colSpan: 2, rowSpan: 2 },
      { id: 'w-5', type: 'widget', code: 'DOWNLOAD_RANK',   colSpan: 2, rowSpan: 2 },
    ],
    hiddenWidgets: ['AI_SEARCH', 'ACTIVE_USERS', 'TODAY_COLLECTION', 'TODAY_LOAD', 'STORAGE_USAGE', 'QUALITY_SCORE'],
    quickActions: [
      { label: '데이터 검색', icon: FileSearchOutlined, route: '/portal/catalog/search' },
      { label: '공개 데이터 다운로드', icon: GlobalOutlined, route: '/portal/distribution/download' },
    ],
  },
}

// ── 역할별 computed ──
const currentRoleConfig = computed(() => {
  const group = authStore.roleGroup || 'GENERAL'
  return roleConfigs[group] || roleConfigs['GENERAL']
})

const welcomeTitle = computed(() => currentRoleConfig.value.welcomeTitle)
const welcomeDescription = computed(() => currentRoleConfig.value.welcomeDescription)
const quickActions = computed(() => currentRoleConfig.value.quickActions)

const roleBasedDefaultLayout = computed<LayoutItem[]>(() => {
  return currentRoleConfig.value.defaultWidgets
})


// ── 반응형 상태 ──
const layoutItems = ref<LayoutItem[]>([])
const originalLayout = ref<LayoutItem[]>([])
const isEditMode = ref(false)

// 대시보드 데이터
const barData = ref([
  { day: '월', collect: 70, load: 60 },
  { day: '화', collect: 85, load: 78 },
  { day: '수', collect: 60, load: 55 },
  { day: '목', collect: 90, load: 82 },
  { day: '금', collect: 75, load: 68 },
  { day: '토', collect: 40, load: 35 },
  { day: '일', collect: 30, load: 25 },
])

const categories = ref([
  { name: '수자원', count: 423, color: '#0066CC' },
  { name: '수도',   count: 287, color: '#4a8fd9' },
  { name: '환경',   count: 215, color: '#28A745' },
  { name: '경영',   count: 178, color: '#FFC107' },
  { name: '기타',   count: 144, color: '#9b59b6' },
])

const recentData = ref([
  { id: 1, name: '댐 수위 관측 데이터 (2026)',   typeLabel: 'DB',  type: 'db',  date: '2026-03-25' },
  { id: 2, name: '수질 모니터링 센서 데이터',     typeLabel: 'IoT', type: 'iot', date: '2026-03-24' },
  { id: 3, name: '상수도 관로 GIS 데이터',        typeLabel: 'GIS', type: 'gis', date: '2026-03-24' },
  { id: 4, name: '전력 사용량 통계 (월별)',        typeLabel: 'CSV', type: 'csv', date: '2026-03-23' },
  { id: 5, name: '강수량 예측 모델 결과',          typeLabel: 'API', type: 'api', date: '2026-03-23' },
])

const notices = ref([
  { id: 1, title: '데이터허브 포털 오픈 안내',                date: '2026-03-25' },
  { id: 2, title: '3월 정기 품질 진단 결과 공유',              date: '2026-03-22' },
  { id: 3, title: '신규 데이터셋 등록 절차 안내',              date: '2026-03-20' },
  { id: 4, title: '시스템 점검 안내 (03/28 02:00~06:00)',     date: '2026-03-18' },
])

const downloadRankData = ref([
  { name: '댐 수위 관측 데이터',     count: 1284, pct: 100, color: '#0066CC' },
  { name: '수질 모니터링 센서',       count: 967,  pct: 75,  color: '#4a8fd9' },
  { name: '상수도 관로 GIS',         count: 723,  pct: 56,  color: '#28A745' },
  { name: '전력 사용량 통계',         count: 512,  pct: 40,  color: '#FFC107' },
  { name: '강수량 예측 모델',         count: 389,  pct: 30,  color: '#9b59b6' },
])

const diskUsage = ref({ total_gb: 500, used_gb: 310, free_gb: 190, usage_pct: 62 })
const summaryState = ref<Record<string, any>>({})

// 갤러리 차트 데이터
const allGalleryCharts = ref<any[]>([])
const galleryChartMap = ref<Record<string, any>>({})

// ── KPI 값 ──
const kpiValues = computed<Record<string, string>>(() => {
  const s = summaryState.value
  return {
    TOTAL_DATASETS:   s.total_datasets ? String(s.total_datasets) : '1,247',
    TODAY_COLLECTION: s.today_collection ? String(s.today_collection) : '328',
    TODAY_LOAD:       s.today_load ? String(s.today_load) : '312',
    ACTIVE_USERS:     s.active_users ? String(s.active_users) : '156',
    STORAGE_USAGE:    diskUsage.value.usage_pct + '%',
    QUALITY_SCORE:    (s.quality_score ?? '92.4') + '점',
  }
})

// ── 도넛 차트 세그먼트 ──
const circumference = 2 * Math.PI * 50

const totalDatasets = computed(() => {
  const total = categories.value.reduce((sum, c) => sum + c.count, 0)
  return total.toLocaleString()
})

const donutSegments = computed(() => {
  const total = categories.value.reduce((sum, c) => sum + c.count, 0)
  if (total === 0) return []
  let accumulated = 0
  return categories.value.map(cat => {
    const ratio = cat.count / total
    const length = ratio * circumference
    const seg = {
      color: cat.color,
      dash: `${length} ${circumference - length}`,
      offset: -accumulated,
    }
    accumulated += length
    return seg
  })
})

// ── 위젯 헬퍼 ──
function getWidgetDef(code: string): WidgetDef | undefined {
  return widgetDefs[code]
}

function getWidgetName(code: string): string {
  return widgetDefs[code]?.name || code
}

function getWidgetType(code: string): string {
  return widgetDefs[code]?.type || ''
}

// ── 갤러리 차트 헬퍼 ──
function getGalleryChartName(chartId: string): string {
  const c = galleryChartMap.value[chartId]
  return c?.chart_name || c?.name || '갤러리 차트'
}

const seriesColors = ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8']

const chartTypeLabels: Record<string, string> = {
  bar: '막대', line: '선', area: '영역', pie: '원형', scatter: '산점도', heatmap: '히트맵', MAP: 'GIS 지도', map: 'GIS 지도',
}

function getGalleryChartType(chartId: string): string {
  const c = galleryChartMap.value[chartId]
  const t = c?.chart_type || c?.chartType || 'bar'
  return chartTypeLabels[t] || t
}

function isMapChart(chartId: string): boolean {
  const c = galleryChartMap.value[chartId]
  const t = (c?.chart_type || c?.chartType || '').toUpperCase()
  return t === 'MAP'
}

function getGalleryMapConfig(chartId: string): any {
  const c = galleryChartMap.value[chartId]
  return c?.chart_config || {}
}

function getGalleryChartSeries(chartId: string): { name: string; lastValue: string }[] {
  const c = galleryChartMap.value[chartId]
  const cfg = c?.chart_config || {}
  const series = cfg.series || []
  const yAxesKr = cfg.y_axes_kr || []
  return series.map((s: any, i: number) => {
    const data = s.data || []
    const last = data.length > 0 ? data[data.length - 1] : '-'
    return { name: s.name || yAxesKr[i] || `시리즈${i + 1}`, lastValue: typeof last === 'number' ? last.toLocaleString() : String(last) }
  })
}

function getGalleryChartLabels(chartId: string): string[] {
  const c = galleryChartMap.value[chartId]
  return c?.chart_config?.labels || []
}

function getGalleryChartSvg(chartId: string): string {
  const chart = galleryChartMap.value[chartId]
  if (!chart) return '<div style="color:#999;text-align:center;padding:20px;">차트 로딩 중...</div>'
  return buildPreviewSvg(chart)
}

// ── SVG 차트 미리보기 빌드 ──
function linePoints(data: number[], w: number, h: number): string {
  if (!data || data.length === 0) return ''
  const max = Math.max(...data, 1)
  const stepX = w / Math.max(data.length - 1, 1)
  return data.map((v, i) => `${i * stepX},${h - (v / max) * h}`).join(' ')
}

function buildPreviewSvg(chart: any): string {
  const config = chart.chart_config || chart.chartConfig || {}
  const series = config.series || []
  const chartType = chart.chart_type || chart.chartType || 'bar'
  const w = 280
  const h = 80
  const colors = ['#0066CC', '#28A745', '#FFC107', '#DC3545', '#9b59b6', '#17a2b8']

  if (chartType === 'pie') {
    const data = series[0]?.data || [30, 25, 20, 15, 10]
    const total = data.reduce((a: number, b: number) => a + b, 0)
    if (total === 0) return `<svg viewBox="0 0 ${w} ${h}"><text x="${w / 2}" y="${h / 2}" text-anchor="middle" fill="#999" font-size="12">데이터 없음</text></svg>`
    let accumulated = 0
    const r = 35
    const cx = w / 2
    const cy = h / 2
    let paths = ''
    data.forEach((val: number, i: number) => {
      const ratio = val / total
      const startAngle = accumulated * 2 * Math.PI - Math.PI / 2
      accumulated += ratio
      const endAngle = accumulated * 2 * Math.PI - Math.PI / 2
      const largeArc = ratio > 0.5 ? 1 : 0
      const x1 = cx + r * Math.cos(startAngle)
      const y1 = cy + r * Math.sin(startAngle)
      const x2 = cx + r * Math.cos(endAngle)
      const y2 = cy + r * Math.sin(endAngle)
      paths += `<path d="M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${largeArc},1 ${x2},${y2} Z" fill="${colors[i % colors.length]}" opacity="0.85"/>`
    })
    return `<svg viewBox="0 0 ${w} ${h}">${paths}</svg>`
  }

  if (chartType === 'line' || chartType === 'area') {
    const allSvg = series.map((s: any, si: number) => {
      const data = s.data || []
      const pts = linePoints(data, w, h)
      if (!pts) return ''
      const color = colors[si % colors.length]
      if (chartType === 'area') {
        const firstX = 0
        const lastX = (data.length - 1) * (w / Math.max(data.length - 1, 1))
        return `<polygon points="${pts} ${lastX},${h} ${firstX},${h}" fill="${color}" opacity="0.2"/>
                <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2"/>`
      }
      return `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2"/>`
    }).join('')
    return `<svg viewBox="0 0 ${w} ${h}">${allSvg}</svg>`
  }

  if (chartType === 'scatter') {
    const dots = series.map((s: any, si: number) => {
      const data = s.data || []
      const color = colors[si % colors.length]
      return data.map((pt: any) => {
        const x = Array.isArray(pt) ? pt[0] : (pt.x ?? 0)
        const y = Array.isArray(pt) ? pt[1] : (pt.y ?? 0)
        return `<circle cx="${(x / 100) * w}" cy="${h - (y / 100) * h}" r="3" fill="${color}" opacity="0.7"/>`
      }).join('')
    }).join('')
    return `<svg viewBox="0 0 ${w} ${h}">${dots}</svg>`
  }

  // Default: bar chart
  const data = series[0]?.data || [40, 60, 35, 80, 55]
  const max = Math.max(...data, 1)
  const barW = Math.max(w / data.length - 4, 4)
  const bars = data.map((v: number, i: number) => {
    const bh = (v / max) * h
    const x = i * (w / data.length) + 2
    return `<rect x="${x}" y="${h - bh}" width="${barW}" height="${bh}" fill="${colors[i % colors.length]}" rx="2" opacity="0.85"/>`
  }).join('')
  return `<svg viewBox="0 0 ${w} ${h}">${bars}</svg>`
}

// ── 드래그 앤 드롭 ──
const dragIndex = ref<number | null>(null)
const dropTargetIndex = ref<number | null>(null)

function onDragStart(event: DragEvent, idx: number) {
  dragIndex.value = idx
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(idx))
  }
}

function onDragOver(idx: number) {
  if (dragIndex.value !== null && dragIndex.value !== idx) {
    dropTargetIndex.value = idx
  }
}

function onDragLeave(idx: number) {
  if (dropTargetIndex.value === idx) {
    dropTargetIndex.value = null
  }
}

function onDrop(event: DragEvent, idx: number) {
  event.preventDefault()
  dropTargetIndex.value = null
  if (dragIndex.value === null || dragIndex.value === idx) return

  const items = [...layoutItems.value]
  const draggedItem = items[dragIndex.value]
  items.splice(dragIndex.value, 1)
  items.splice(idx, 0, draggedItem)
  layoutItems.value = items
  dragIndex.value = null
}

function onDragEnd() {
  dragIndex.value = null
  dropTargetIndex.value = null
}

// ── 편집 모드 ──
function enterEditMode() {
  originalLayout.value = JSON.parse(JSON.stringify(layoutItems.value))
  isEditMode.value = true
}

function cancelEdit() {
  layoutItems.value = JSON.parse(JSON.stringify(originalLayout.value))
  isEditMode.value = false
}

async function saveLayout() {
  try {
    await widgetApi.saveUserDashboard({ widget_layout: { items: layoutItems.value } })
    isEditMode.value = false

    // 대시보드에 남아있는 갤러리 chartId만 localStorage 캔버스에 남기기 (동기화)
    const remainingGalleryIds = new Set(
      layoutItems.value.filter(it => it.type === 'gallery' && it.chartId).map(it => it.chartId)
    )
    try {
      const saved = localStorage.getItem('datahub_gallery_canvas')
      if (saved) {
        const canvas = JSON.parse(saved) as any[]
        const synced = canvas.filter((c: any) => remainingGalleryIds.has(String(c.id)))
        localStorage.setItem('datahub_gallery_canvas', JSON.stringify(synced))
      }
    } catch { /* ignore */ }

    showNotification('대시보드 레이아웃이 저장되었습니다.', 'success')
  } catch (e) {
    console.error('레이아웃 저장 실패:', e)
    showNotification('레이아웃 저장에 실패했습니다.', 'error')
  }
}

// ── 아이템 크기 조절 ──
function updateColSpan(idx: number, val: number) {
  layoutItems.value[idx].colSpan = val
}

function updateRowSpan(idx: number, val: number) {
  layoutItems.value[idx].rowSpan = val
}

// ── 아이템 제거 ──
function removeItem(idx: number) {
  const removed = layoutItems.value[idx]
  layoutItems.value.splice(idx, 1)

  // 갤러리 아이템이 삭제되면 localStorage 캔버스에서도 동기화 제거
  if (removed?.type === 'gallery' && removed.chartId) {
    try {
      const saved = localStorage.getItem('datahub_gallery_canvas')
      if (saved) {
        const canvas = JSON.parse(saved) as any[]
        const updated = canvas.filter((c: any) => String(c.id) !== String(removed.chartId))
        localStorage.setItem('datahub_gallery_canvas', JSON.stringify(updated))
      }
    } catch { /* ignore */ }
  }
}

// ── 사용 가능한 위젯 (아직 배치되지 않은 + 역할에 허용된 위젯) ──
const availableWidgets = computed(() => {
  const usedCodes = new Set(
    layoutItems.value.filter(i => i.type === 'widget').map(i => i.code)
  )
  const hidden = new Set(currentRoleConfig.value.hiddenWidgets)
  return Object.entries(widgetDefs)
    .filter(([code]) => !usedCodes.has(code) && !hidden.has(code))
    .map(([code, def]) => ({ code, ...def }))
})

// ── 사용 가능한 갤러리 차트 (아직 배치되지 않은 차트) ──
const availableGalleryCharts = computed(() => {
  const usedIds = new Set(
    layoutItems.value.filter(i => i.type === 'gallery').map(i => i.chartId)
  )
  return allGalleryCharts.value.filter(c => !usedIds.has(c.id))
})

// ── 위젯 추가 ──
function addWidget(code: string) {
  const def = widgetDefs[code]
  if (!def) return
  const id = 'w-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6)
  layoutItems.value.push({
    id,
    type: 'widget',
    code,
    colSpan: def.defaultColSpan,
    rowSpan: def.defaultRowSpan,
  })
}

// ── 갤러리 차트 추가 ──
function addGalleryChart(chart: any) {
  const id = 'g-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6)
  layoutItems.value.push({
    id,
    type: 'gallery',
    chartId: chart.id,
    colSpan: 2,
    rowSpan: 2,
  })
}

// ── 알림 표시 ──
const isSharedView = ref(false)

function shareDashboard() {
  try {
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(layoutItems.value))))
    const url = window.location.origin + '/portal?shared=' + encoded
    navigator.clipboard.writeText(url).then(() => {
      showNotification('공유 링크가 클립보드에 복사되었습니다', 'success')
    }).catch(() => {
      window.prompt('공유 링크를 복사하세요:', url)
    })
  } catch {
    showNotification('공유 링크 생성에 실패했습니다', 'error')
  }
}

function loadSharedLayout() {
  const shared = route.query.shared as string
  if (shared) {
    try {
      const decoded = JSON.parse(decodeURIComponent(escape(atob(shared))))
      if (Array.isArray(decoded) && decoded.length > 0) {
        layoutItems.value = decoded
        isSharedView.value = true
      }
    } catch { /* invalid shared data */ }
  }
}

function saveSharedAsOwn() {
  widgetApi.saveUserDashboard({ widget_layout: { items: layoutItems.value } }).then(() => {
    isSharedView.value = false
    showNotification('공유 대시보드가 내 대시보드로 저장되었습니다', 'success')
    router.replace('/portal')
  })
}

function showNotification(message: string, type: 'success' | 'error') {
  const el = document.createElement('div')
  el.className = `dashboard-notification dashboard-notification--${type}`
  el.textContent = message
  document.body.appendChild(el)
  requestAnimationFrame(() => el.classList.add('show'))
  setTimeout(() => {
    el.classList.remove('show')
    setTimeout(() => el.remove(), 300)
  }, 2500)
}

// ── 네비게이션 ──
function onSearch() {
  router.push({ path: '/portal/catalog/search', query: { q: searchQuery.value } })
}

function goToDataDetail(item: any) {
  router.push({ path: '/portal/catalog', query: { sort: 'latest', highlight: item.id, detail: item.id } })
}

function goToNoticeDetail(item: any) {
  router.push({ path: '/portal/board/notices', query: { detail: item.id } })
}

// ── 갤러리에 올리기 ──
function isChartWidget(code: string): boolean {
  return ['COLLECTION_CHART', 'CATEGORY_CHART', 'DOWNLOAD_RANK'].includes(code)
}

// 위젯 → 갤러리 차트 데이터 변환 맵
function getWidgetChartConfig(code: string): { chart_name: string; chart_type: string; chart_config: any } | null {
  switch (code) {
    case 'COLLECTION_CHART':
      return {
        chart_name: '수집/적재 현황',
        chart_type: 'bar',
        chart_config: {
          dataset_name: '대시보드 위젯',
          series: [
            { name: '수집', data: barData.value.map(b => b.collect) },
            { name: '적재', data: barData.value.map(b => b.load) },
          ],
          labels: barData.value.map(b => b.day),
          y_axes_kr: ['수집', '적재'],
        },
      }
    case 'CATEGORY_CHART':
      return {
        chart_name: '분류별 데이터 현황',
        chart_type: 'pie',
        chart_config: {
          dataset_name: '대시보드 위젯',
          series: [{ name: '건수', data: categories.value.map(c => c.count) }],
          labels: categories.value.map(c => c.name),
        },
      }
    case 'DOWNLOAD_RANK':
      return {
        chart_name: '다운로드 순위',
        chart_type: 'bar',
        chart_config: {
          dataset_name: '대시보드 위젯',
          series: [{ name: '다운로드', data: downloadRankData.value.map(r => r.count) }],
          labels: downloadRankData.value.map(r => r.name),
          y_axes_kr: ['다운로드 건수'],
        },
      }
    default:
      return null
  }
}

const showPublishModal = ref(false)
const publishForm = ref({ name: '', description: '' })
let publishCallback: (() => Promise<void>) | null = null

function publishWidgetToGallery(item: LayoutItem) {
  const config = getWidgetChartConfig(item.code!)
  if (!config) return
  publishForm.value = { name: config.chart_name, description: `대시보드 '${config.chart_name}' 위젯에서 갤러리로 게시` }
  publishCallback = async () => {
    try {
      await visualizationApi.createChart({
        chart_name: publishForm.value.name || config.chart_name,
        chart_type: config.chart_type,
        chart_config: config.chart_config,
        description: publishForm.value.description,
        visibility: 'PUBLIC',
      })
      showNotification('시각화 갤러리에 등록되었습니다.', 'success')
      showPublishModal.value = false
    } catch (e) {
      console.error('갤러리 등록 실패:', e)
      showNotification('갤러리 등록에 실패했습니다.', 'error')
    }
  }
  showPublishModal.value = true
}

function publishGalleryToGallery(item: LayoutItem) {
  const chart = galleryChartMap.value[item.chartId!]
  if (!chart) return
  const chartName = chart.chart_name || chart.name || '갤러리 차트'
  publishForm.value = { name: chartName + ' (복사)', description: `대시보드 갤러리 차트에서 복사하여 게시` }
  publishCallback = async () => {
    try {
      // 기존 차트가 DB에 있으면 clone, 없으면 새로 생성
      if (chart.id && !String(chart.id).startsWith('default-')) {
        await visualizationApi.cloneChart(chart.id)
      } else {
        await visualizationApi.createChart({
          chart_name: publishForm.value.name,
          chart_type: chart.chart_type || chart.chartType || 'bar',
          chart_config: chart.chart_config || chart.chartConfig || {},
          description: publishForm.value.description,
          visibility: 'PUBLIC',
        })
      }
      showNotification('시각화 갤러리에 등록되었습니다.', 'success')
      showPublishModal.value = false
    } catch (e) {
      console.error('갤러리 등록 실패:', e)
      showNotification('갤러리 등록에 실패했습니다.', 'error')
    }
  }
  showPublishModal.value = true
}

async function confirmPublish() {
  if (publishCallback) await publishCallback()
}

// ── 마운트 시 데이터 로드 ──
onMounted(async () => {
  // 0. 공유 레이아웃 체크
  loadSharedLayout()

  // 1. 대시보드 통계 데이터 로드
  try {
    const [summaryRes, trendRes, categoryRes, recentRes, noticesRes] = await Promise.all([
      dashboardApi.summary(),
      dashboardApi.collectionTrend(),
      dashboardApi.categoryStats(),
      dashboardApi.recentData(),
      dashboardApi.notices(),
    ])

    if (summaryRes.data?.data) {
      const s = summaryRes.data.data
      summaryState.value = {
        total_datasets: s.totalDatasets ?? s.total_datasets,
        today_collection: s.todayCollected ?? s.today_collection,
        today_load: s.todayLoaded ?? s.today_load,
        active_users: s.activeUsers ?? s.active_users,
        quality_score: s.qualityScore ?? s.quality_score ?? 92.4,
      }
    }
    if (trendRes.data?.data) barData.value = trendRes.data.data
    if (categoryRes.data?.data) categories.value = categoryRes.data.data
    if (recentRes.data?.data) recentData.value = recentRes.data.data
    if (noticesRes.data?.data) notices.value = noticesRes.data.data
  } catch (e) {
    console.error('Dashboard API 호출 실패:', e)
  }

  // 2. 디스크 사용량
  try {
    const diskRes = await boardApi.diskUsage()
    if (diskRes.data?.data) diskUsage.value = diskRes.data.data
  } catch {
    diskUsage.value = { total_gb: 500, used_gb: 310, free_gb: 190, usage_pct: 62 }
  }

  // 3. 사용자 대시보드 레이아웃 로드 (역할별 기본 레이아웃 적용)
  const roleDefault = JSON.parse(JSON.stringify(roleBasedDefaultLayout.value))
  const hidden = new Set(currentRoleConfig.value.hiddenWidgets)
  try {
    const layoutRes = await widgetApi.getUserDashboard()
    if (layoutRes.data?.data?.widget_layout?.items) {
      const saved = layoutRes.data.data.widget_layout.items as LayoutItem[]
      if (saved.length > 0) {
        // 저장된 레이아웃에서 현재 역할에 숨겨진 위젯 제거
        layoutItems.value = hidden.size > 0
          ? saved.filter(item => !(item.type === 'widget' && item.code && hidden.has(item.code)))
          : saved
      } else {
        layoutItems.value = roleDefault
      }
    } else {
      layoutItems.value = roleDefault
    }
  } catch {
    layoutItems.value = roleDefault
  }

  // 4. 갤러리 차트 목록 로드
  try {
    const chartRes = await widgetApi.galleryCharts()
    const charts = chartRes.data?.items || chartRes.data?.data || []
    allGalleryCharts.value = charts
    const map: Record<string, any> = {}
    for (const c of charts) {
      map[c.id] = c
    }
    galleryChartMap.value = map

    // 레이아웃에 갤러리 차트가 있는데 상세 정보가 없으면 개별 로드 or fallback
    for (const item of layoutItems.value) {
      if (item.type === 'gallery' && item.chartId && !map[item.chartId]) {
        try {
          const detailRes = await visualizationApi.getChart(item.chartId)
          if (detailRes.data?.data) {
            const detail = detailRes.data.data
            galleryChartMap.value[item.chartId] = detail
            allGalleryCharts.value.push(detail)
          }
        } catch {
          // 차트 로드 실패 시 → 가장 가까운 기존 차트로 대체
          if (charts.length > 0) {
            const fallback = charts[0]
            galleryChartMap.value[item.chartId] = { ...fallback, chart_name: fallback.chart_name + ' (복원)' }
          }
        }
      }
    }
  } catch {
    allGalleryCharts.value = []
  }

  // ── colSpan/rowSpan 보정: 저장된 값이 없을 때만 기본값 적용 ──
  layoutItems.value.forEach(item => {
    if (item.type === 'widget' && item.code) {
      const def = widgetDefs[item.code]
      if (def) {
        // 저장된 값이 없거나 0이면 기본값 적용, 있으면 사용자 설정 유지
        if (!item.colSpan || item.colSpan <= 0) item.colSpan = def.defaultColSpan
        if (!item.rowSpan || item.rowSpan <= 0) item.rowSpan = def.defaultRowSpan
      }
    } else if (item.type === 'gallery') {
      if (!item.colSpan || item.colSpan <= 0) item.colSpan = 2
      if (!item.rowSpan || item.rowSpan <= 0) item.rowSpan = 2
    }
  })

  // 5. localStorage 갤러리 캔버스 fallback
  if (allGalleryCharts.value.length === 0) {
    try {
      const saved = localStorage.getItem('datahub_gallery_canvas')
      if (saved) {
        const parsed = JSON.parse(saved) as any[]
        allGalleryCharts.value = parsed
        for (const c of parsed) {
          galleryChartMap.value[c.id] = c
        }
      }
    } catch { /* ignore */ }
  }

  // 6. 갤러리 차트가 전혀 없으면 레이아웃의 gallery 아이템에 기본 차트 데이터 삽입
  const galleryItemsInLayout = layoutItems.value.filter(it => it.type === 'gallery')
  if (galleryItemsInLayout.length > 0 && Object.keys(galleryChartMap.value).length === 0) {
    const defaultCharts = [
      { id: 'default-1', chart_name: '월별 수집 추이', chart_type: 'bar', chart_config: { series: [{ name: '수집', data: [328, 412, 385, 398, 445, 512, 489] }], labels: ['1월','2월','3월','4월','5월','6월','7월'] } },
      { id: 'default-2', chart_name: '데이터 유형 분포', chart_type: 'pie', chart_config: { series: [{ name: '건수', data: [423, 287, 215, 178, 89] }], labels: ['수자원','수도','환경','경영','공간정보'] } },
      { id: 'default-3', chart_name: '수질 항목 변화', chart_type: 'line', chart_config: { series: [{ name: 'pH', data: [7.2, 7.4, 7.1, 7.3, 7.5, 7.2, 7.4] }], labels: ['월','화','수','목','금','토','일'] } },
    ]
    galleryItemsInLayout.forEach((item, i) => {
      const dc = defaultCharts[i % defaultCharts.length]
      item.chartId = dc.id
      galleryChartMap.value[dc.id] = dc
      allGalleryCharts.value.push(dc)
    })
  }
})
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.dashboard {
  display: flex;
  flex-direction: column;
  gap: $spacing-xl;
}

// ===== Welcome =====
.welcome-section {
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  border-radius: $radius-lg;
  padding: $spacing-xxl $spacing-xl;
  color: $white;

  h1 {
    font-size: $font-size-xxl;
    font-weight: 700;
    margin-bottom: $spacing-sm;
  }
  p {
    font-size: $font-size-md;
    opacity: 0.85;
    margin-bottom: $spacing-lg;
  }
}

.search-box {
  display: flex;
  max-width: 600px;

  input {
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: $radius-md 0 0 $radius-md;
    font-size: $font-size-md;
    outline: none;
  }

  .search-btn {
    padding: 10px 24px;
    background: $dark;
    color: $white;
    border-radius: 0 $radius-md $radius-md 0;
    font-size: $font-size-md;
    font-weight: 600;
    border: none;
    cursor: pointer;

    &:hover { background: lighten($dark, 10%); }
  }
}

// ===== Quick Actions =====
.quick-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.quick-action-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all $transition-fast;
  font-size: $font-size-sm;
  color: $text-primary;

  &:hover {
    border-color: $primary;
    color: $primary;
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);

    .quick-action-icon { color: $primary; }
    .quick-action-arrow { opacity: 1; }
  }
}

.quick-action-icon {
  font-size: 16px;
  color: $primary;
}

.quick-action-label {
  font-weight: 500;
}

.quick-action-arrow {
  font-size: 10px;
  color: $text-muted;
  opacity: 0;
  transition: opacity $transition-fast;
}

// ===== Edit Toolbar =====
.edit-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-sm;
}

.shared-banner {
  background: #e6f7ff; border: 1px solid #91d5ff; border-radius: 8px; padding: 10px 16px;
  display: flex; align-items: center; gap: 10px; font-size: 13px; color: #0066CC; font-weight: 600; margin-bottom: 12px;
  .btn { margin-left: auto; }
  .btn + .btn { margin-left: 6px; }
}

.share-btn {
  padding: 6px 14px; border-radius: $radius-md; font-size: $font-size-sm; font-weight: 500; cursor: pointer;
  border: 1px solid #13c2c2; color: #13c2c2; background: #fff;
  display: flex; align-items: center; gap: $spacing-xs;
  &:hover { background: #e6fffb; }
}

.edit-btn,
.save-btn,
.cancel-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  font-size: $font-size-sm;
  font-weight: 600;
  cursor: pointer;
  transition: all $transition-fast;
}

.edit-btn {
  background: $white;
  color: $text-secondary;

  &:hover {
    border-color: $primary;
    color: $primary;
  }
}

.save-btn {
  background: $primary;
  color: $white;
  border-color: $primary;

  &:hover { background: darken($primary, 8%); }
}

.cancel-btn {
  background: $white;
  color: $text-secondary;

  &:hover {
    border-color: $error;
    color: $error;
  }
}

// ===== Layout Grid =====
.layout-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: minmax(90px, auto);
  gap: $spacing-md;
}

.grid-item {
  position: relative;
  min-height: 0;
  transition: opacity 0.2s, box-shadow 0.2s;

  // KPI 카드(1칸 1행)는 컴팩트하게
  &.kpi-item {
    .widget-render-card {
      height: 100%;
      min-height: 90px;
    }
  }

  &.dragging {
    opacity: 0.4;
  }

  &.drag-over {
    &::before {
      content: '';
      position: absolute;
      inset: -2px;
      border: 2px solid $primary;
      border-radius: $radius-lg;
      pointer-events: none;
      z-index: 10;
    }
  }

  .edit-mode & {
    cursor: grab;

    .widget-render-card {
      border: 2px dashed $primary-light;
    }
  }
}

// ===== Edit Overlay =====
.edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid $border-color;
  border-radius: $radius-lg $radius-lg 0 0;
}

.edit-overlay-left {
  display: flex;
  align-items: center;
}

.drag-handle {
  font-size: 16px;
  color: $text-muted;
  cursor: grab;

  &:active { cursor: grabbing; }
}

.edit-overlay-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.span-select {
  padding: 2px 4px;
  font-size: 11px;
  border: 1px solid $border-color;
  border-radius: $radius-sm;
  background: $white;
  cursor: pointer;
  outline: none;

  &:focus { border-color: $primary; }
}

.remove-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: $text-muted;
  font-size: 12px;
  cursor: pointer;
  border-radius: $radius-sm;
  transition: all $transition-fast;

  &:hover {
    color: $error;
    background: rgba($error, 0.08);
  }
}

// ===== Widget Render Card =====
.widget-render-card {
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  overflow: hidden;
  box-shadow: $shadow-sm;
  transition: box-shadow $transition-fast;
  height: 100%;
  display: flex;
  flex-direction: column;

  &:hover {
    box-shadow: $shadow-md;
  }
}

.widget-render-header {
  padding: 10px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid $bg-light;
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .widget-render-title {
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-secondary;
  }
}

.publish-gallery-btn {
  background: none;
  border: 1px solid transparent;
  color: #bbb;
  cursor: pointer;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  opacity: 0;

  .widget-render-card:hover & { opacity: 1; }

  &:hover { color: $primary; border-color: $primary; background: #f0f7ff; }
}

.gallery-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.widget-render-body {
  padding: 16px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}

// ===== Gallery Card =====
.gallery-map-body {
  padding: 0 !important;
  min-height: 200px;
}

.gallery-card {
  .widget-render-header {
    display: flex; justify-content: space-between; align-items: center;
    .gallery-chart-type {
      font-size: 10px; padding: 1px 8px; border-radius: 3px;
      background: #e6f7ff; color: #1677ff; font-weight: 600;
    }
  }
  .gallery-body {
    display: flex; flex-direction: column; gap: 8px; min-height: 100px;
  }
  .gallery-chart-area {
    flex: 1; display: flex; align-items: center; justify-content: center; min-height: 80px;
    :deep(svg) { width: 100%; max-height: 140px; }
  }
  .gallery-chart-info {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding-top: 6px; border-top: 1px solid #f0f0f0;
  }
  .gallery-series-item {
    display: flex; align-items: center; gap: 4px; font-size: 11px;
    .series-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .series-name { color: $text-secondary; }
    .series-value { font-weight: 700; color: $text-primary; }
  }
  .gallery-x-info { font-size: 10px; color: $text-muted; margin-left: auto; }
}

// ===== KPI Widget (compact half-height) =====
.kpi-item {
  .widget-render-card { min-height: 0; }
  .widget-render-header { padding: 6px 12px; }
  .widget-render-body { padding: 8px 12px; }
}

.widget-kpi {
  display: flex;
  align-items: center;
  gap: 10px;
}

.widget-kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  color: $white;
}

.widget-kpi-detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.widget-kpi-value {
  font-size: 20px;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.1;
}

.widget-kpi-label {
  font-size: 11px;
  color: $text-muted;
  margin-top: 1px;
}

// ===== Bar Chart Widget =====
.widget-bar-chart {
  .chart-bar-group {
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    height: 160px;
    padding: 0 $spacing-sm;
  }
}

.chart-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  flex: 1;
}

.bar-wrapper {
  display: flex;
  gap: 3px;
  align-items: flex-end;
  height: 140px;
}

.bar {
  width: 16px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s ease;
}

.bar-collect { background: $primary-light; }
.bar-load { background: $success; }

.bar-label {
  font-size: $font-size-xs;
  color: $text-muted;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: $spacing-lg;
  margin-top: $spacing-md;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: $font-size-xs;
  color: $text-secondary;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

// ===== Donut Chart Widget =====
.widget-donut-chart {
  display: flex;
  align-items: center;
  gap: $spacing-xl;
  padding: $spacing-sm 0;
}

.donut-chart {
  position: relative;
  width: 140px;
  height: 140px;
  flex-shrink: 0;

  svg {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
  }
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;

  .donut-total {
    display: block;
    font-size: $font-size-xl;
    font-weight: 700;
    color: $text-primary;
  }
  .donut-label {
    font-size: $font-size-xs;
    color: $text-muted;
  }
}

.donut-legend {
  flex: 1;
  min-width: 0;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 5px 0;
  border-bottom: 1px solid $bg-light;

  &:last-child { border-bottom: none; }

  .cat-name {
    flex: 1;
    font-size: $font-size-sm;
    color: $text-secondary;
  }
  .cat-count {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $text-primary;
  }
}

// ===== Horizontal Bar (Download Rank) Widget =====
.widget-hbar-chart {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.hbar-row {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.hbar-rank {
  width: 20px;
  font-size: $font-size-xs;
  font-weight: 700;
  color: $primary;
  text-align: center;
  flex-shrink: 0;
}

.hbar-name {
  width: 120px;
  font-size: $font-size-xs;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.hbar-track {
  flex: 1;
  height: 14px;
  background: $bg-light;
  border-radius: 7px;
  overflow: hidden;
}

.hbar-fill {
  height: 100%;
  border-radius: 7px;
  transition: width 0.4s ease;
}

.hbar-value {
  width: 40px;
  font-size: $font-size-xs;
  font-weight: 600;
  color: $text-primary;
  text-align: right;
  flex-shrink: 0;
}

// ===== Table Widget =====
.widget-table {
  display: flex;
  flex-direction: column;
}

.widget-table-row {
  display: flex;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid $bg-light;
  gap: $spacing-sm;

  &:last-child { border-bottom: none; }

  &.clickable {
    cursor: pointer;
    border-radius: $radius-sm;
    padding: 7px $spacing-xs;
    margin: 0 (-$spacing-xs);
    transition: background 0.2s;
    &:hover { background: #e8f0fe; }
  }

  .row-text {
    flex: 1;
    font-size: $font-size-sm;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .row-sub {
    font-size: 11px;
    color: $text-muted;
    flex-shrink: 0;
  }
}

.data-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
  flex-shrink: 0;

  &.db  { background: #e3f2fd; color: #1565c0; }
  &.iot { background: #e8f5e9; color: #2e7d32; }
  &.gis { background: #fff3e0; color: #e65100; }
  &.csv { background: #f3e5f5; color: #7b1fa2; }
  &.api { background: #fce4ec; color: #c62828; }
}

.widget-table-footer {
  text-align: right;
  padding-top: $spacing-sm;
  border-top: 1px solid $bg-light;
  margin-top: $spacing-xs;

  .more-link {
    font-size: $font-size-xs;
    color: $primary;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    &:hover { text-decoration: underline; }
  }
}

// ===== Search Widget =====
.widget-search {
  position: relative;

  .widget-search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
    color: $text-muted;
    pointer-events: none;
  }

  input {
    width: 100%;
    padding: 10px 12px 10px 36px;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    font-size: $font-size-sm;
    cursor: pointer;
    background: $bg-light;
    transition: border-color $transition-fast;

    &:hover { border-color: $primary; }
  }
}

// ===== Hint Cards =====
.empty-widgets-hint {
  margin-top: 0;
}

.hint-card {
  background: $bg-light;
  border: 2px dashed $border-color;
  border-radius: $radius-lg;
  padding: $spacing-xl;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: $primary;
    background: #f0f7ff;
  }

  .hint-icon {
    font-size: 32px;
    color: $text-muted;
    margin-bottom: $spacing-sm;
    display: block;
  }

  p {
    font-size: $font-size-sm;
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }

  .hint-link {
    font-size: $font-size-xs;
    color: $primary;
  }
}

// ===== Add Panel =====
.add-panel {
  background: $bg-light;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: $spacing-lg;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

.add-section {
  h4 {
    font-size: $font-size-md;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $spacing-md;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.add-grid {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-sm;
}

.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
  background: $white;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  cursor: pointer;
  transition: all $transition-fast;
  min-width: 90px;

  &:hover {
    border-color: $primary;
    box-shadow: $shadow-sm;
    background: #f0f7ff;
  }

  .add-card-icon {
    font-size: 18px;
    color: $primary;
  }

  .add-card-name {
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-primary;
    text-align: center;
    white-space: nowrap;
  }

  .add-card-type {
    font-size: 10px;
    color: $text-muted;
    text-transform: uppercase;
  }
}

.add-empty {
  font-size: $font-size-sm;
  color: $text-muted;
  padding: $spacing-md;
}

// ===== Publish Modal =====
.publish-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-modal {
  background: $white;
  border-radius: $radius-lg;
  width: 440px;
  max-width: 90vw;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.publish-modal-header {
  padding: 14px 20px;
  background: #f5f7fa;
  border-bottom: 1px solid $border-color;
  font-size: 14px;
  font-weight: 700;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.publish-modal-close {
  margin-left: auto;
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
  border-radius: 4px;

  &:hover { color: $error; background: #fff1f0; }
}

.publish-modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.publish-field {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 12px;
    font-weight: 600;
    color: #666;
  }

  input, textarea {
    padding: 8px 12px;
    border: 1px solid $border-color;
    border-radius: $radius-sm;
    font-size: 13px;
    font-family: $font-family;
    transition: border-color 0.15s;

    &:focus { border-color: $primary; outline: none; }
  }

  textarea { resize: vertical; }
}

.publish-modal-footer {
  padding: 12px 20px;
  border-top: 1px solid $border-color;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  background: #fafbfc;

  .btn {
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 600;
    border-radius: $radius-sm;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: all 0.15s;
  }

  .btn-primary {
    background: $primary;
    color: $white;
    border: 1px solid $primary;

    &:hover { background: darken($primary, 8%); }
  }

  .btn-outline {
    background: $white;
    color: $text-secondary;
    border: 1px solid $border-color;

    &:hover { border-color: #999; }
  }
}

// ===== Notification Toast (global) =====
:global(.dashboard-notification) {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  pointer-events: none;
}

:global(.dashboard-notification.show) {
  opacity: 1;
  transform: translateY(0);
}

:global(.dashboard-notification--success) {
  background: #28A745;
}

:global(.dashboard-notification--error) {
  background: #DC3545;
}

// ===== 반응형: 태블릿 =====
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .welcome-section h1 {
    font-size: $font-size-xl;
  }

  .layout-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid-item {
    // 태블릿에서 4칸짜리는 2칸으로
    &[style*="span 4"] {
      grid-column: span 2 !important;
    }
    // 3칸짜리도 2칸으로
    &[style*="span 3"] {
      grid-column: span 2 !important;
    }
  }
}
</style>
