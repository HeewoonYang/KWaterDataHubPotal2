<template>
  <div class="download-page">
    <nav class="breadcrumb">
      <router-link to="/portal/distribution">데이터유통</router-link>
      <span class="separator">&gt;</span>
      <span class="current">데이터 다운로드</span>
    </nav>

    <div class="page-header"><h2>데이터 다운로드</h2><p>신청한 데이터의 승인 현황을 확인하고 다운로드합니다.</p></div>

    <!-- 필터 -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group"><label>상태</label>
          <select v-model="filterStatus"><option value="">전체</option><option value="APPROVED">승인완료</option><option value="PENDING">대기중</option><option value="REJECTED">반려</option></select>
        </div>
        <div class="filter-group search-group"><label>검색</label><input v-model="filterSearch" placeholder="데이터셋명 검색" @keyup.enter="loadRequests" /></div>
        <div class="filter-actions"><button class="btn btn-primary" @click="loadRequests"><SearchOutlined /> 조회</button></div>
      </div>
    </div>

    <!-- 신청 목록 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ requests.length }}</strong>건</span>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue :tooltipShowDelay="0" class="ag-theme-alpine" :rowData="requests" :columnDefs="cols" :defaultColDef="defaultColDef"
          :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="openDetail" />
      </div>
    </div>

    <!-- 상세 모달 -->
    <AdminModal :visible="showDetail" :title="detailData.datasetName || '신청 상세'" size="lg" @close="showDetail = false">
      <!-- 승인 현황 -->
      <div class="detail-section">
        <div class="section-title">승인 현황</div>
        <div class="approval-flow">
          <div class="approval-step" :class="{ done: true }">
            <div class="step-icon done"><CheckCircleOutlined /></div>
            <div class="step-info">
              <div class="step-label">신청</div>
              <div class="step-date">{{ detailData.createdAt }}</div>
            </div>
          </div>
          <div class="approval-line" :class="{ active: detailData.status !== 'PENDING' }"></div>
          <div class="approval-step" :class="{ done: detailData.status === 'APPROVED', rejected: detailData.status === 'REJECTED', pending: detailData.status === 'PENDING' }">
            <div class="step-icon" :class="detailData.status === 'APPROVED' ? 'done' : detailData.status === 'REJECTED' ? 'rejected' : 'pending'">
              <CheckCircleOutlined v-if="detailData.status === 'APPROVED'" />
              <CloseCircleOutlined v-else-if="detailData.status === 'REJECTED'" />
              <ClockCircleOutlined v-else />
            </div>
            <div class="step-info">
              <div class="step-label">{{ detailData.status === 'APPROVED' ? '승인 완료' : detailData.status === 'REJECTED' ? '반려' : '검토 대기' }}</div>
              <div class="step-date">{{ detailData.approvedAt || '검토자: 데이터관리팀' }}</div>
            </div>
          </div>
          <div class="approval-line" :class="{ active: detailData.status === 'APPROVED' }"></div>
          <div class="approval-step" :class="{ done: detailData.downloaded }">
            <div class="step-icon" :class="detailData.downloaded ? 'done' : ''">
              <DownloadOutlined />
            </div>
            <div class="step-info">
              <div class="step-label">다운로드</div>
              <div class="step-date">{{ detailData.downloaded ? detailData.downloadCount + '회 다운로드' : '대기' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 신청 정보 -->
      <div class="detail-section">
        <div class="section-title">신청 정보</div>
        <div class="info-grid">
          <div class="info-item"><span class="info-label">데이터셋</span><span class="info-value">{{ detailData.datasetName }}</span></div>
          <div class="info-item"><span class="info-label">요청 포맷</span><span class="info-value">{{ detailData.format }}</span></div>
          <div class="info-item"><span class="info-label">신청 목적</span><span class="info-value">{{ detailData.purpose || '-' }}</span></div>
          <div class="info-item"><span class="info-label">신청일</span><span class="info-value">{{ detailData.createdAt }}</span></div>
          <div class="info-item"><span class="info-label">승인일</span><span class="info-value">{{ detailData.approvedAt || '-' }}</span></div>
          <div class="info-item"><span class="info-label">다운로드 횟수</span><span class="info-value">{{ detailData.downloadCount }}회</span></div>
        </div>
      </div>

      <template #footer>
        <template v-if="detailData.format === 'API' && detailData.status === 'APPROVED'">
          <button class="btn btn-primary" @click="openApiKeyModal(detailData)">
            <KeyOutlined /> API 키 보기
          </button>
        </template>
        <template v-else>
          <button class="btn btn-primary" :disabled="detailData.status !== 'APPROVED'" @click="handleDownload">
            <DownloadOutlined /> {{ detailData.status === 'APPROVED' ? '다운로드' : (detailData.status === 'PENDING' ? '승인 대기중' : '반려됨') }}
          </button>
          <button v-if="isGisFormat(detailData.format)" class="btn btn-outline" :disabled="detailData.status !== 'APPROVED'" @click="goToGisVisualization">
            <EnvironmentOutlined /> GIS 시각화
          </button>
          <button v-else class="btn btn-outline" :disabled="detailData.status !== 'APPROVED'" @click="goToVisualization">
            <BarChartOutlined /> 시각화
          </button>
          <button class="btn btn-gallery" :disabled="detailData.status !== 'APPROVED'" @click="goToGalleryPublish">
            <UploadOutlined /> 갤러리에 올리기
          </button>
        </template>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- API 키 모달 -->
    <AdminModal :visible="showApiKeyModal" title="API 키 관리" size="md" @close="showApiKeyModal = false">
      <template v-if="apiKeyData">
        <div class="api-key-section">
          <div class="section-label">API 키</div>
          <div class="key-display">
            <code class="key-value">{{ keyVisible ? apiKeyData.apiKey : apiKeyData.apiKeyPrefix + '••••••••••••••••••••••••••••' }}</code>
            <button class="btn-icon" @click="keyVisible = !keyVisible" :title="keyVisible ? '숨기기' : '보기'">
              <EyeInvisibleOutlined v-if="keyVisible" /><EyeOutlined v-else />
            </button>
            <button class="btn-icon" @click="copyApiKey" title="복사"><CopyOutlined /></button>
          </div>
        </div>
        <div class="api-info-grid">
          <div class="info-item"><span class="label">엔드포인트</span><code>{{ apiKeyData.endpoint }}</code></div>
          <div class="info-item"><span class="label">속도 제한</span><span>{{ apiKeyData.rateLimitPerMin }}회/분</span></div>
          <div class="info-item"><span class="label">발급일</span><span>{{ apiKeyData.issuedAt }}</span></div>
          <div class="info-item"><span class="label">만료일</span><span>{{ apiKeyData.expiresAt }}</span></div>
        </div>
        <div class="api-usage-stats">
          <div class="usage-stat"><div class="stat-value">{{ apiKeyData.totalCalls?.toLocaleString() }}</div><div class="stat-label">총 호출</div></div>
          <div class="usage-stat"><div class="stat-value">{{ apiKeyData.todayCalls || 0 }}</div><div class="stat-label">오늘 호출</div></div>
          <div class="usage-stat"><div class="stat-value">{{ apiKeyData.lastUsedAt || '-' }}</div><div class="stat-label">마지막 사용</div></div>
        </div>
        <div class="code-example">
          <div class="example-label">사용 예시 (curl)</div>
          <pre>curl -H "X-API-Key: {{ apiKeyData.apiKeyPrefix }}..." \
     {{ apiKeyData.endpoint }}</pre>
        </div>
      </template>
      <template #footer>
        <button class="btn btn-outline" style="color:#fa8c16;border-color:#fa8c16;" @click="handleRegenerateKey"><ReloadOutlined /> 키 재발급</button>
        <button class="btn btn-outline" style="color:#DC3545;border-color:#DC3545;" @click="handleRevokeKey"><DeleteOutlined /> 키 폐기</button>
        <button class="btn btn-outline" @click="showApiKeyModal = false">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../utils/gridHelper'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { SearchOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, DownloadOutlined, BarChartOutlined, KeyOutlined, CopyOutlined, EyeOutlined, EyeInvisibleOutlined, ReloadOutlined, DeleteOutlined, EnvironmentOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import AdminModal from '../../components/AdminModal.vue'
import { distributionApi } from '../../api/portal.api'
import { useRouter } from 'vue-router'
ModuleRegistry.registerModules([AllCommunityModule])
const router = useRouter()

const filterStatus = ref('')
const filterSearch = ref('')
const showDetail = ref(false)
const detailData = ref<any>({})
const requests = ref<any[]>([])
const showApiKeyModal = ref(false)
const apiKeyData = ref<any>(null)
const keyVisible = ref(false)

const defaultColDef = { ...baseDefaultColDef }
const cols = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 45 },
  { headerName: '데이터셋', field: 'datasetName', flex: 2, minWidth: 200 },
  { headerName: '포맷', field: 'format', flex: 0.5, minWidth: 65 },
  { headerName: '목적', field: 'purpose', flex: 1, minWidth: 100 },
  { headerName: '상태', field: 'statusLabel', flex: 0.7, minWidth: 80,
    cellStyle: (params: any) => {
      if (params.value === '승인완료') return { color: '#28A745', fontWeight: '600' }
      if (params.value === '반려') return { color: '#DC3545', fontWeight: '600' }
      return { color: '#fa8c16', fontWeight: '600' }
    }
  },
  { headerName: '신청일', field: 'createdAt', flex: 0.8, minWidth: 100 },
  { headerName: '다운로드', field: 'downloadCount', flex: 0.6, minWidth: 75 },
])

const defaultRequests = [
  { id: '1', datasetName: '댐 수위 관측 데이터 (2026-Q1)', format: 'CSV', purpose: '수자원 분석', status: 'APPROVED', statusLabel: '승인완료', createdAt: '2026-03-20', approvedAt: '2026-03-21', downloadCount: 3, downloaded: true, datasetIds: [] },
  { id: '2', datasetName: '수질 모니터링 센서 데이터', format: 'JSON', purpose: '수질 연구', status: 'APPROVED', statusLabel: '승인완료', createdAt: '2026-03-18', approvedAt: '2026-03-19', downloadCount: 1, downloaded: true, datasetIds: [] },
  { id: '3', datasetName: '전력 사용량 통계 (월별)', format: 'Excel', purpose: '경영 보고', status: 'PENDING', statusLabel: '대기중', createdAt: '2026-03-25', approvedAt: '', downloadCount: 0, downloaded: false, datasetIds: [] },
  { id: '4', datasetName: '하천 유량 관측 데이터', format: 'CSV', purpose: '홍수 예측', status: 'REJECTED', statusLabel: '반려', createdAt: '2026-03-15', approvedAt: '', downloadCount: 0, downloaded: false, datasetIds: [] },
  { id: '5', datasetName: '스마트미터링 실시간 데이터', format: 'CSV', purpose: '계측 분석', status: 'APPROVED', statusLabel: '승인완료', createdAt: '2026-03-28', approvedAt: '2026-03-29', downloadCount: 0, downloaded: false, datasetIds: [] },
  { id: 'api-1', datasetName: '기관간 수자원 공유 API', format: 'API', purpose: 'API 연동', status: 'APPROVED', statusLabel: '승인완료', createdAt: '2026-03-28', approvedAt: '2026-03-28', downloadCount: 0, downloaded: false, datasetIds: [],
    apiKeyInfo: { id: 'ak-1', apiKey: 'kw_live_a3f8c9d1e2b4f6a8d0c3e5b7a9f1d3e5c7b9a1f3', apiKeyPrefix: 'kw_live_a3f8c9', endpoint: 'https://api.kwater.or.kr/data/v1/water-share', rateLimitPerMin: 60, expiresAt: '2027-03-28', issuedAt: '2026-03-28', lastUsedAt: '2026-04-01 14:23', totalCalls: 1247, todayCalls: 23, isActive: true } },
  { id: 'api-2', datasetName: '수도계량기 실시간 수위', format: 'API', purpose: '실시간 연동', status: 'PENDING', statusLabel: '대기중', createdAt: '2026-04-01', approvedAt: '', downloadCount: 0, downloaded: false, datasetIds: [], apiKeyInfo: null },
]

async function loadRequests() {
  try {
    const res = await distributionApi.requests({ page: 1, page_size: 50 })
    if (res.data?.items?.length) {
      requests.value = res.data.items.map((r: any) => {
        const nameKr = r.dataset_name_kr || ''
        const nameEn = r.dataset_name || ''
        const dsId = r.dataset_ids?.[0] || ''
        // 한글명이 있으면 "한글명 (영문명)" 형식, 없으면 영문명, 그것도 없으면 ID
        let displayName = '-'
        if (nameKr && nameEn) {
          displayName = `${nameKr} (${nameEn})`
        } else if (nameKr) {
          displayName = nameKr
        } else if (nameEn) {
          displayName = nameEn
        } else if (dsId) {
          displayName = dsId
        }
        return {
          id: r.id,
          datasetName: displayName,
          datasetNameKr: nameKr,
          datasetNameEn: nameEn,
          format: r.requested_format || 'CSV',
          purpose: r.purpose || '-',
          status: r.status,
          statusLabel: r.status === 'APPROVED' ? '승인완료' : r.status === 'REJECTED' ? '반려' : '대기중',
          createdAt: r.created_at ? String(r.created_at).substring(0, 10) : '',
          approvedAt: r.approved_at ? String(r.approved_at).substring(0, 10) : '',
          downloadCount: 0,
          downloaded: false,
          datasetIds: r.dataset_ids || [],
        }
      })
    } else {
      requests.value = defaultRequests
    }
  } catch {
    requests.value = defaultRequests
  }
}

function openDetail(event: any) {
  detailData.value = { ...event.data }
  showDetail.value = true
}

function isGisFormat(format: string) {
  const f = (format || '').toUpperCase()
  return f === 'SHP' || f === 'GEOJSON' || f === 'GIS'
}

function goToVisualization() {
  const dsId = detailData.value.datasetIds?.[0] || detailData.value.id
  showDetail.value = false
  router.push({ path: '/portal/visualization', query: { dataset_id: String(dsId) } })
}

function goToGalleryPublish() {
  const dsId = detailData.value.datasetIds?.[0] || detailData.value.id
  if (isGisFormat(detailData.value.format)) {
    // GIS 포맷 → GIS 지도로 이동 (갤러리에 올리기는 GIS 페이지에서)
    const dsNameKr = detailData.value.datasetNameKr || ''
    const dsNameEn = detailData.value.datasetNameEn || detailData.value.datasetName || ''
    showDetail.value = false
    router.push({ path: '/portal/monitoring/gis', query: { dataset_id: String(dsId), name: dsNameEn, name_kr: dsNameKr, publish: '1' } })
  } else {
    // 일반 포맷 → 시각화 페이지로 이동 (차트 생성 후 갤러리 저장)
    showDetail.value = false
    router.push({ path: '/portal/visualization', query: { dataset_id: String(dsId), publish: '1' } })
  }
}

function goToGisVisualization() {
  const dsId = detailData.value.datasetIds?.[0] || detailData.value.id
  const dsNameKr = detailData.value.datasetNameKr || ''
  const dsNameEn = detailData.value.datasetNameEn || detailData.value.datasetName || ''
  showDetail.value = false
  router.push({ path: '/portal/monitoring/gis', query: { dataset_id: String(dsId), name: dsNameEn, name_kr: dsNameKr } })
}

async function handleDownload() {
  if (detailData.value.status !== 'APPROVED') return
  const dsId = detailData.value.datasetIds?.[0] || detailData.value.id
  try {
    const res = await distributionApi.downloadFile(dsId, detailData.value.format || 'CSV')
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${detailData.value.datasetName || 'data'}.${(detailData.value.format || 'csv').toLowerCase()}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    // 카운트 증가
    detailData.value.downloadCount = (detailData.value.downloadCount || 0) + 1
    detailData.value.downloaded = true
    // 목록에도 반영
    const row = requests.value.find((r: any) => r.id === detailData.value.id)
    if (row) {
      row.downloadCount = detailData.value.downloadCount
      row.downloaded = true
    }
  } catch (e) {
    message.error('다운로드에 실패했습니다.')
    console.error(e)
  }
}

function openApiKeyModal(row: any) {
  apiKeyData.value = row.apiKeyInfo ? { ...row.apiKeyInfo } : null
  keyVisible.value = false
  showApiKeyModal.value = true
}

function copyApiKey() {
  if (apiKeyData.value?.apiKey) {
    navigator.clipboard.writeText(apiKeyData.value.apiKey).then(() => {
      message.success('API 키가 클립보드에 복사되었습니다.')
    }).catch(() => {
      window.prompt('API 키를 복사하세요:', apiKeyData.value.apiKey)
    })
  }
}

function handleRegenerateKey() {
  const newKey = 'kw_live_' + Array.from({ length: 32 }, () => Math.random().toString(16).charAt(2)).join('')
  apiKeyData.value = { ...apiKeyData.value, apiKey: newKey, apiKeyPrefix: newKey.slice(0, 14), issuedAt: new Date().toISOString().split('T')[0] }
  message.success('API 키가 재발급되었습니다. 새 키를 복사해주세요.')
  keyVisible.value = true
}

function handleRevokeKey() {
  if (apiKeyData.value) {
    apiKeyData.value.isActive = false
    message.warning('API 키가 폐기되었습니다.')
    showApiKeyModal.value = false
  }
}

onMounted(() => { loadRequests() })
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.download-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb { font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px; a { color: #999; text-decoration: none; &:hover { color: #0066CC; } } .separator { color: #ddd; } .current { color: #333; font-weight: 600; } }
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; } p { font-size: $font-size-sm; color: $text-muted; } }
.search-filter { background: #f5f7fa; border: 1px solid $border-color; border-radius: $radius-md; padding: $spacing-lg; }
.filter-row { display: flex; align-items: flex-end; gap: $spacing-lg; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: $spacing-xs; label { font-size: $font-size-xs; color: $text-secondary; font-weight: 600; } select, input { padding: 6px 10px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; min-width: 130px; background: $white; } &.search-group { flex: 1; input { width: 100%; } } }
.filter-actions { display: flex; gap: $spacing-sm; }
.table-section { background: $white; border: 1px solid $border-color; border-radius: $radius-md; box-shadow: $shadow-sm; overflow: hidden; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: $spacing-md $spacing-lg; border-bottom: 1px solid $border-color; }
.table-count { font-size: $font-size-sm; color: $text-secondary; strong { color: $primary; } }
.ag-grid-wrapper { :deep(.ag-theme-alpine) { --ag-header-background-color: #ffffff; --ag-header-foreground-color: #333; --ag-header-height: 38px; --ag-row-height: 40px; --ag-font-size: 13px; --ag-borders: none; font-family: $font-family; } :deep(.ag-header-cell-label) { font-weight: 600; font-size: 12px; } :deep(.ag-header-row) { border-bottom: 2px solid #4a6a8a; } :deep(.ag-row) { cursor: pointer; } }

// 상세 모달
.detail-section { margin-bottom: 20px; }
.section-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid $primary; }

// 승인 플로우
.approval-flow { display: flex; align-items: center; padding: 16px 0; }
.approval-step { display: flex; align-items: center; gap: 8px; }
.step-icon {
  width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px;
  border: 2px solid #d9d9d9; color: #d9d9d9; background: #fafafa;
  &.done { border-color: #28A745; color: #28A745; background: #f6ffed; }
  &.rejected { border-color: #DC3545; color: #DC3545; background: #fff1f0; }
  &.pending { border-color: #fa8c16; color: #fa8c16; background: #fff7e6; }
}
.step-info { .step-label { font-size: 12px; font-weight: 600; color: #333; } .step-date { font-size: 11px; color: #999; } }
.approval-line { flex: 1; height: 2px; background: #e8e8e8; margin: 0 8px; &.active { background: #28A745; } }

// 정보 그리드
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.info-item { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #fafafa;
  .info-label { color: #999; } .info-value { color: #333; font-weight: 500; }
}

// 버튼
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-gallery { background: #f0f7ff; color: #0066CC; border: 1px solid #0066CC; &:hover:not(:disabled) { background: #0066CC; color: #fff; } }

// API 키 모달
.api-key-section {
  margin-bottom: 16px;
  .section-label { font-size: 12px; color: #666; font-weight: 600; margin-bottom: 6px; }
  .key-display { display: flex; align-items: center; gap: 8px; background: #f8f9fa; padding: 10px 14px; border-radius: 6px; border: 1px solid #e0e0e0; }
  .key-value { flex: 1; font-size: 13px; font-family: 'JetBrains Mono', 'D2Coding', monospace; word-break: break-all; color: #333; background: none; padding: 0; }
  .btn-icon { background: none; border: 1px solid #ddd; border-radius: 4px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; color: #666; cursor: pointer; &:hover { border-color: $primary; color: $primary; } }
}

.api-info-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;
  .info-item { display: flex; flex-direction: column; gap: 2px; padding: 8px 12px; background: #f8f9fa; border-radius: 6px;
    .label { font-size: 11px; color: #999; }
    code { font-size: 12px; color: $primary; word-break: break-all; }
    span:not(.label) { font-size: 13px; font-weight: 600; }
  }
}

.api-usage-stats {
  display: flex; gap: 12px; margin-bottom: 16px;
  .usage-stat { flex: 1; text-align: center; padding: 12px; background: #f0f7ff; border-radius: 8px;
    .stat-value { font-size: 20px; font-weight: 700; color: $primary; }
    .stat-label { font-size: 11px; color: #999; margin-top: 2px; }
  }
}

.code-example {
  .example-label { font-size: 12px; color: #666; font-weight: 600; margin-bottom: 6px; }
  pre { background: #1e1e2e; color: #cdd6f4; padding: 14px; border-radius: 8px; font-size: 12px; font-family: 'JetBrains Mono', 'D2Coding', monospace; overflow-x: auto; white-space: pre-wrap; line-height: 1.6; }
}
</style>
