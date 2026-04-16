<template>
  <div class="mypage">
    <nav class="breadcrumb">
      <router-link to="/portal/mypage">마이페이지</router-link>
      <span class="separator">&gt;</span>
      <span class="current">내 프로필</span>
    </nav>

    <div class="page-header">
      <h2>내 프로필</h2>
      <p>사용자 정보와 활동 내역을 확인하세요.</p>
    </div>

    <div class="mypage-body">
      <!-- 프로필 카드 -->
      <div class="profile-card">
        <div class="profile-avatar">
          <UserOutlined />
        </div>
        <div class="profile-info">
          <h3>{{ authStore.user?.name }}</h3>
          <span class="profile-role">{{ authStore.roleLabel }}</span>
          <div class="profile-details">
            <div class="detail-row"><MailOutlined /> {{ authStore.user?.email }}</div>
            <div class="detail-row" v-if="authStore.user?.department"><BankOutlined /> {{ authStore.user?.department }}</div>
            <div class="detail-row"><SafetyOutlined /> 접근 등급: {{ authStore.user?.dataGrades.map(g => 'L' + g).join(', ') }}</div>
          </div>
        </div>
        <button class="btn btn-outline"><EditOutlined /> 정보 수정</button>
      </div>

      <!-- 활동 요약 -->
      <div class="activity-section">
        <div class="activity-cards">
          <div v-for="act in activities" :key="act.label" class="activity-card">
            <component :is="act.icon" class="act-icon" :style="{ color: act.color }" />
            <span class="act-value">{{ act.value }}</span>
            <span class="act-label">{{ act.label }}</span>
          </div>
        </div>
      </div>

      <!-- 탭 영역 -->
      <div class="tab-section">
        <div class="tab-nav">
          <button v-for="tab in tabs" :key="tab.key" class="tab-btn" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
            <component :is="tab.icon" /> {{ tab.label }}
          </button>
        </div>

        <!-- 즐겨찾기 -->
        <div v-if="activeTab === 'favorites'" class="tab-content">
          <div v-for="item in favorites" :key="item.name" class="list-item clickable" @click="goToDetail(item)">
            <StarFilled class="star-icon" />
            <span class="item-name">{{ item.name }}</span>
            <span class="item-type">{{ item.type }}</span>
            <span class="item-date">{{ item.date }}</span>
          </div>
        </div>

        <!-- 최근 조회 -->
        <div v-if="activeTab === 'recent'" class="tab-content">
          <div v-for="item in recentViews" :key="item.name" class="list-item clickable" @click="goToDetail(item)">
            <EyeOutlined class="view-icon" />
            <span class="item-name">{{ item.name }}</span>
            <span class="item-type">{{ item.type }}</span>
            <span class="item-date">{{ item.date }}</span>
          </div>
        </div>

        <!-- 다운로드 이력 -->
        <div v-if="activeTab === 'downloads'" class="tab-content">
          <div v-for="item in downloads" :key="item.name" class="list-item clickable" @click="goToDownload()">
            <DownloadOutlined class="dl-icon" />
            <span class="item-name">{{ item.name }}</span>
            <span class="item-format">{{ item.format }}</span>
            <span class="item-date">{{ item.date }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type Component } from 'vue'
import { useRouter } from 'vue-router'
import {
  UserOutlined,
  MailOutlined,
  BankOutlined,
  SafetyOutlined,
  EditOutlined,
  StarOutlined,
  StarFilled,
  EyeOutlined,
  DownloadOutlined,
  HeartOutlined,
  ClockCircleOutlined,
  CloudDownloadOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { userApi } from '../../api/portal.api'

const router = useRouter()
const authStore = useAuthStore()
const activeTab = ref('favorites')

const activities = ref<{ icon: Component; label: string; value: string; color: string }[]>([
  { icon: HeartOutlined, label: '즐겨찾기', value: '12', color: '#DC3545' },
  { icon: ClockCircleOutlined, label: '최근 조회', value: '48', color: '#0066CC' },
  { icon: CloudDownloadOutlined, label: '다운로드', value: '23', color: '#28A745' },
  { icon: StarOutlined, label: '내 차트', value: '5', color: '#FFC107' },
])

const tabs = [
  { key: 'favorites', label: '즐겨찾기', icon: StarFilled },
  { key: 'recent', label: '최근 조회', icon: EyeOutlined },
  { key: 'downloads', label: '다운로드 이력', icon: DownloadOutlined },
]

// Fallback mock data
const defaultFavorites = [
  { name: '댐 수위 관측 데이터', type: 'DB', date: '2026-03-25' },
  { name: '수질 모니터링 센서 데이터', type: 'IoT', date: '2026-03-24' },
  { name: '강수량 예측 API', type: 'API', date: '2026-03-23' },
]

const defaultRecentViews = [
  { name: '상수도 관로 GIS 데이터', type: 'GIS', date: '2026-03-25 14:30' },
  { name: '전력 사용량 통계', type: 'CSV', date: '2026-03-25 11:20' },
  { name: '댐 수위 관측 데이터', type: 'DB', date: '2026-03-24 16:45' },
  { name: '하천 유량 관측 데이터', type: 'DB', date: '2026-03-24 10:15' },
]

const defaultDownloads = [
  { name: '전력 사용량 통계 (월별)', format: 'CSV', date: '2026-03-25' },
  { name: '상수도 수질검사 결과', format: 'JSON', date: '2026-03-23' },
  { name: '댐 수위 관측 (2026-Q1)', format: 'CSV', date: '2026-03-20' },
]

const favorites = ref(defaultFavorites)
const recentViews = ref(defaultRecentViews)
const downloads = ref(defaultDownloads)

onMounted(async () => {
  try {
    const [favRes, recentRes, dlRes] = await Promise.all([
      userApi.favorites({ page: 1, page_size: 10 }),
      userApi.recentViews({ page: 1, page_size: 10 }),
      userApi.downloadHistory({ page: 1, page_size: 10 }),
    ])
    if (favRes.data?.items?.length) favorites.value = favRes.data.items.map((i: any) => ({
      _resourceId: i.resource_id, name: i.resource_name ?? i.name, type: i.resource_type ?? i.type, date: (i.bookmarked_at ?? i.date ?? '').slice(0, 10),
    }))
    if (recentRes.data?.items?.length) recentViews.value = recentRes.data.items.map((i: any) => ({
      _resourceId: i.resource_id, name: i.resource_name ?? i.name, type: i.resource_type ?? i.type, date: (i.viewed_at ?? i.date ?? '').slice(0, 16).replace('T', ' '),
    }))
    if (dlRes.data?.items?.length) downloads.value = dlRes.data.items.map((i: any) => ({
      name: i.dataset_name ?? i.name, format: i.download_format ?? i.format, date: (i.downloaded_at ?? i.date ?? '').slice(0, 10),
    }))

    // Update activity counts
    activities.value = [
      { icon: HeartOutlined, label: '즐겨찾기', value: String(favRes.data?.total ?? favorites.value.length), color: '#DC3545' },
      { icon: ClockCircleOutlined, label: '최근 조회', value: String(recentRes.data?.total ?? recentViews.value.length), color: '#0066CC' },
      { icon: CloudDownloadOutlined, label: '다운로드', value: String(dlRes.data?.total ?? downloads.value.length), color: '#28A745' },
      { icon: StarOutlined, label: '내 차트', value: '5', color: '#FFC107' },
    ]
  } catch (e) {
    console.error('마이페이지 데이터 조회 실패:', e)
  }
})

function goToDetail(item: any) {
  if (item._resourceId) {
    router.push({ path: '/portal/catalog', query: { detail: item._resourceId } })
  }
}

function goToDownload() {
  router.push('/portal/distribution/download')
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.mypage { display: flex; flex-direction: column; gap: $spacing-lg; }
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
.mypage-body { display: flex; flex-direction: column; gap: $spacing-lg; }

.profile-card {
  display: flex; align-items: center; gap: $spacing-xl; background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-xl; box-shadow: $shadow-sm;
}
.profile-avatar {
  width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, $primary, $primary-dark); color: $white; display: flex; align-items: center; justify-content: center; font-size: 32px; flex-shrink: 0;
}
.profile-info { flex: 1; h3 { font-size: $font-size-lg; font-weight: 700; margin-bottom: 2px; } }
.profile-role { font-size: $font-size-xs; color: $primary; background: rgba($primary, 0.1); padding: 2px 10px; border-radius: 10px; font-weight: 600; }
.profile-details { margin-top: $spacing-md; display: flex; flex-direction: column; gap: $spacing-xs; }
.detail-row { font-size: $font-size-sm; color: $text-secondary; display: flex; align-items: center; gap: $spacing-sm; }

.activity-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: $spacing-md; }
.activity-card {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg; padding: $spacing-lg; display: flex; flex-direction: column; align-items: center; gap: $spacing-xs; box-shadow: $shadow-sm;
  .act-icon { font-size: 24px; }
  .act-value { font-size: $font-size-xl; font-weight: 700; }
  .act-label { font-size: $font-size-xs; color: $text-muted; }
}

.tab-section { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden; }
.tab-nav { display: flex; border-bottom: 1px solid $border-color; }
.tab-btn {
  padding: $spacing-md $spacing-lg; font-size: $font-size-sm; color: $text-secondary; background: none; border-bottom: 2px solid transparent; display: flex; align-items: center; gap: 6px;
  &:hover { color: $primary; }
  &.active { color: $primary; border-bottom-color: $primary; font-weight: 600; }
}
.tab-content { padding: $spacing-md; }
.list-item {
  display: flex; align-items: center; gap: $spacing-md; padding: $spacing-md; border-bottom: 1px solid $bg-light;
  transition: background 0.15s;
  &.clickable { cursor: pointer; &:hover { background: #f0f7ff; } }
  &:last-child { border-bottom: none; }
  .star-icon { color: #FFC107; }
  .view-icon { color: $primary; }
  .dl-icon { color: $success; }
  .item-name { flex: 1; font-size: $font-size-sm; font-weight: 500; }
  .item-type, .item-format { font-size: $font-size-xs; color: $text-muted; background: $bg-light; padding: 2px 8px; border-radius: 3px; }
  .item-date { font-size: $font-size-xs; color: $text-muted; }
}

@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .activity-cards { grid-template-columns: repeat(2, 1fr); }
  .profile-card { flex-direction: column; text-align: center; }
}
</style>
