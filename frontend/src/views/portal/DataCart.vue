<template>
  <div class="cart-page">
    <nav class="breadcrumb">
      <router-link to="/portal/catalog">데이터카탈로그</router-link>
      <span class="separator">&gt;</span>
      <span class="current">데이터 장바구니</span>
    </nav>

    <div class="page-header">
      <h2><ShoppingCartOutlined /> 데이터 장바구니</h2>
      <p>분석에 필요한 데이터셋을 모아 일괄 신청합니다.</p>
    </div>

    <!-- 신청 완료 -->
    <div v-if="showDone" class="done-banner">
      <CheckCircleOutlined class="done-icon" /> {{ doneMessage }}
      <div class="done-actions">
        <router-link to="/portal/distribution/download" class="done-link">신청 현황 보기</router-link>
        <router-link to="/portal/catalog" class="btn btn-sm btn-outline">카탈로그로 이동</router-link>
      </div>
    </div>

    <!-- 빈 장바구니 -->
    <div v-if="cartStore.isEmpty && !showDone" class="empty-cart">
      <ShoppingCartOutlined class="empty-icon" />
      <h3>장바구니가 비어 있습니다</h3>
      <p>데이터 카탈로그에서 필요한 데이터셋을 담아보세요.</p>
      <router-link to="/portal/catalog" class="btn btn-primary"><SearchOutlined /> 카탈로그 탐색</router-link>
    </div>

    <!-- 장바구니 목록 -->
    <template v-if="!cartStore.isEmpty">
      <div class="cart-header">
        <span class="cart-count"><strong>{{ cartStore.itemCount }}</strong>개 데이터셋</span>
        <div class="cart-actions">
          <button class="btn btn-sm btn-outline" @click="cartStore.clearCart()"><DeleteOutlined /> 전체 비우기</button>
        </div>
      </div>

      <div class="cart-list">
        <div v-for="item in cartStore.items" :key="item.id" class="cart-item">
          <div class="item-info">
            <div class="item-top">
              <span class="item-type" :class="(item.type || 'db').toLowerCase()">{{ item.typeLabel || item.type || 'DB' }}</span>
              <span class="item-grade" :class="'grade-' + (item.grade || 3)">L{{ item.grade || 3 }}</span>
              <span class="approval-badge" :class="(item.grade || 3) <= 2 ? 'need' : 'auto'">
                {{ (item.grade || 3) <= 1 ? '승인필요' : (item.grade || 3) <= 2 ? '자동승인' : '공개' }}
              </span>
            </div>
            <h4 class="item-name" @click="goToDetail(item)">{{ item.nameKr || item.name }}</h4>
            <div class="item-meta">
              <span v-if="item.rows">{{ item.rows }} 건</span>
              <span v-if="item.columns">{{ item.columns }} 컬럼</span>
              <span>추가일: {{ item.addedAt }}</span>
            </div>
            <div class="item-format-row">
              <span class="format-label">포맷:</span>
              <select v-model="item.requestFormat" class="format-select" @change="onItemFormatChange(item)">
                <option value="CSV">CSV</option>
                <option value="JSON">JSON</option>
                <option value="API">API 접근</option>
                <option v-if="isGisData(item)" value="SHP">SHP (Shapefile)</option>
                <option v-if="isGisData(item)" value="GeoJSON">GeoJSON</option>
              </select>
              <span v-if="item.requestFormat === 'API'" class="format-hint api"><ApiOutlined /> 승인 후 API 키 발급</span>
              <span v-if="item.requestFormat === 'SHP' || item.requestFormat === 'GeoJSON'" class="format-hint gis"><EnvironmentOutlined /> GIS 시각화 가능</span>
            </div>
            <div class="item-tags" v-if="item.tags?.length">
              <span v-for="tag in item.tags.slice(0, 4)" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
          <button class="remove-btn" @click="cartStore.removeItem(item.id)" title="제거"><CloseOutlined /></button>
        </div>
      </div>

      <!-- 일괄 신청 폼 -->
      <div class="request-section">
        <h3><FormOutlined /> 일괄 데이터 신청</h3>
        <div class="approval-summary">
          <div class="summary-item auto"><CheckCircleOutlined /> 공개/자동승인 <strong>{{ autoCount }}</strong>건</div>
          <div class="summary-item need" v-if="needApprovalCount > 0"><ClockCircleOutlined /> 승인필요 <strong>{{ needApprovalCount }}</strong>건</div>
        </div>
        <div class="form-row">
          <div class="form-group" :class="{ 'has-error': purposeError }">
            <label>이용 목적 *</label>
            <textarea v-model="purpose" rows="2" placeholder="데이터 이용 목적을 입력하세요" @input="purposeError = false"></textarea>
            <span v-if="purposeError" class="field-error">이용 목적을 입력해주세요.</span>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>요청 포맷 현황</label>
            <div class="format-summary">
              <span v-for="fmt in formatSummary" :key="fmt.label" class="format-chip" :class="fmt.cls">{{ fmt.label }} {{ fmt.count }}건</span>
            </div>
            <div v-if="hasApiItems" class="api-info-panel">
              <div class="api-info-header"><ApiOutlined /> API 접근 안내</div>
              <div class="api-info-body">
                <div class="api-info-row"><span class="label">엔드포인트</span><code>https://api.kwater.or.kr/data/v1/{'{dataset_id}'}</code></div>
                <div class="api-info-row"><span class="label">속도 제한</span><span>기본 60회/분</span></div>
                <div class="api-info-row"><span class="label">인증 방식</span><code>X-API-Key</code> 헤더</div>
              </div>
              <div class="api-info-notice"><InfoCircleOutlined /> 승인 완료 후 API 키가 발급됩니다. <strong>신청현황</strong>에서 확인하세요.</div>
            </div>
          </div>
        </div>
        <div class="form-footer">
          <button class="btn btn-primary btn-lg" @click="submitBatchRequest">
            <SendOutlined /> 일괄 신청 ({{ cartStore.itemCount }}건)
          </button>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ShoppingCartOutlined, SearchOutlined, DeleteOutlined, CloseOutlined, FormOutlined, SendOutlined, CheckCircleOutlined, ClockCircleOutlined, ApiOutlined, InfoCircleOutlined, EnvironmentOutlined } from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import { useCartStore } from '../../stores/cart'
import { distributionApi } from '../../api/portal.api'

const router = useRouter()
const cartStore = useCartStore()
const purpose = ref('')
const purposeError = ref(false)
const showDone = ref(false)
const doneMessage = ref('')

const autoCount = computed(() => cartStore.items.filter(i => (i.grade || 3) >= 3).length)
const needApprovalCount = computed(() => cartStore.items.filter(i => (i.grade || 3) < 3).length)
const hasApiItems = computed(() => cartStore.items.some(i => i.requestFormat === 'API'))

const formatSummary = computed(() => {
  const counts: Record<string, number> = {}
  for (const item of cartStore.items) {
    const fmt = item.requestFormat || 'CSV'
    counts[fmt] = (counts[fmt] || 0) + 1
  }
  const clsMap: Record<string, string> = { CSV: 'csv', JSON: 'json', API: 'api', SHP: 'gis', GeoJSON: 'gis' }
  return Object.entries(counts).map(([label, count]) => ({ label, count, cls: clsMap[label] || 'csv' }))
})

function isGisData(item: any) {
  const fmt = (item.type || item.typeLabel || '').toUpperCase()
  return fmt === 'GIS' || fmt === 'GEOJSON' || fmt === 'SHP'
}

function onItemFormatChange(_item: any) {
  // 포맷 변경 시 store 반영 (향후 API 연동)
}

onMounted(() => {
  cartStore.fetchCart()
})

function goToDetail(item: any) {
  router.push({ path: '/portal/catalog', query: { detail: item.dataset_id || item.id } })
}

async function submitBatchRequest() {
  if (cartStore.isEmpty) return message.warning('장바구니가 비어있습니다.')
  if (!purpose.value.trim()) {
    purposeError.value = true
    message.warning('이용 목적을 입력해주세요.')
    return
  }
  try {
    // 개별 포맷별로 요청 (같은 포맷끼리 그룹핑)
    const formatGroups: Record<string, string[]> = {}
    for (const item of cartStore.items) {
      const fmt = item.requestFormat || 'CSV'
      if (!formatGroups[fmt]) formatGroups[fmt] = []
      formatGroups[fmt].push(item.dataset_id || item.id)
    }
    for (const [fmt, ids] of Object.entries(formatGroups)) {
      await distributionApi.createRequest({
        dataset_ids: ids,
        request_type: fmt === 'API' ? 'API_ACCESS' : 'DOWNLOAD',
        requested_format: fmt,
        purpose: purpose.value,
      })
    }
    const auto = autoCount.value
    const need = needApprovalCount.value
    if (hasApiItems.value) {
      doneMessage.value = `${cartStore.itemCount}건 신청 완료 (API 접근 포함 — 승인 후 키 발급)`
    } else {
      doneMessage.value = `${cartStore.itemCount}건 신청 완료 (자동승인 ${auto}건${need > 0 ? ', 승인대기 ' + need + '건' : ''})`
    }
    showDone.value = true
    await cartStore.clearCart()
    purpose.value = ''
  } catch (e) {
    message.error('신청에 실패했습니다. 다시 시도해주세요.')
  }
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.cart-page { display: flex; flex-direction: column; gap: 16px; }
.breadcrumb { font-size: 12px; color: #999; a { color: $primary; text-decoration: none; } }
.page-header { h2 { font-size: 20px; margin: 0 0 4px; } p { margin: 0; color: #666; font-size: 13px; } }

.empty-cart { text-align: center; padding: 80px 20px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px;
  .empty-icon { font-size: 56px; color: #ddd; display: block; margin-bottom: 12px; }
  h3 { margin: 0 0 8px; color: #666; } p { color: #999; font-size: 13px; margin-bottom: 16px; }
}

.cart-header { display: flex; justify-content: space-between; align-items: center;
  .cart-count { font-size: 14px; color: #333; strong { color: $primary; font-size: 18px; } }
}

.cart-list { display: flex; flex-direction: column; gap: 8px; }
.cart-item { display: flex; align-items: flex-start; gap: 12px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px 16px; transition: border-color 0.15s;
  &:hover { border-color: $primary; }
  .item-info { flex: 1; min-width: 0; }
  .item-top { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; }
  .item-type { font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 3px;
    &.db { background: #e6f7ff; color: #0066CC; } &.iot { background: #f6ffed; color: #28A745; } &.api { background: #fff7e6; color: #fa8c16; }
    &.csv { background: #f0f0f0; color: #666; } &.gis { background: #f9f0ff; color: #722ed1; }
  }
  .item-grade { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 3px;
    &.grade-1 { background: #fff1f0; color: #DC3545; } &.grade-2 { background: #e6f7ff; color: #0066CC; } &.grade-3 { background: #f6ffed; color: #28A745; }
  }
  .approval-badge { font-size: 10px; padding: 1px 6px; border-radius: 3px;
    &.auto { background: #f6ffed; color: #28A745; } &.need { background: #fff7e6; color: #fa8c16; }
  }
  .item-name { font-size: 14px; font-weight: 600; margin: 0 0 4px; cursor: pointer; &:hover { color: $primary; } }
  .item-meta { font-size: 11px; color: #999; display: flex; gap: 12px; }
  .item-tags { display: flex; gap: 4px; margin-top: 6px; .tag { font-size: 10px; background: #f0f5ff; color: #0066CC; padding: 1px 6px; border-radius: 3px; } }
  .remove-btn { background: none; border: none; color: #ccc; cursor: pointer; font-size: 14px; padding: 4px; &:hover { color: #DC3545; } }
  .item-format-row {
    display: flex; align-items: center; gap: 8px; margin-top: 6px;
    .format-label { font-size: 11px; color: #999; font-weight: 600; }
    .format-select { padding: 2px 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 11px; background: #fff; }
    .format-hint { font-size: 10px; display: flex; align-items: center; gap: 3px; padding: 1px 6px; border-radius: 3px;
      &.api { background: #fff7e6; color: #ad6800; }
      &.gis { background: #f0f5ff; color: #0066CC; }
    }
  }
}

.request-section { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 20px;
  h3 { font-size: 15px; margin: 0 0 12px; }
  .approval-summary { display: flex; gap: 16px; margin-bottom: 16px;
    .summary-item { padding: 8px 16px; border-radius: 6px; font-size: 13px; display: flex; align-items: center; gap: 6px;
      &.auto { background: #f6ffed; color: #28A745; } &.need { background: #fff7e6; color: #fa8c16; }
      strong { font-size: 18px; }
    }
  }
  .form-row { margin-bottom: 12px; }
  .form-group { label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 4px; }
    textarea, select { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; box-sizing: border-box; transition: border-color 0.2s; }
    &.has-error {
      textarea { border-color: #DC3545; background: #fff8f8; &:focus { outline-color: #DC3545; } }
      label { color: #DC3545; }
    }
    .field-error { display: block; font-size: 12px; color: #DC3545; margin-top: 4px; }
  }
  .form-footer { display: flex; justify-content: flex-end; margin-top: 16px; }
  .btn-lg { padding: 10px 24px; font-size: 14px; }
}

.format-summary {
  display: flex; gap: 6px; flex-wrap: wrap;
  .format-chip {
    font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 12px;
    &.csv { background: #f0f0f0; color: #666; }
    &.json { background: #e6f7ff; color: #0066CC; }
    &.api { background: #fff7e6; color: #ad6800; }
    &.gis { background: #f0f5ff; color: #1890ff; }
  }
}

.api-info-panel {
  margin-top: 12px; border: 1px solid #d6e4ff; border-radius: 8px; overflow: hidden;
  .api-info-header { background: #e6f0ff; padding: 8px 14px; font-size: 13px; font-weight: 600; color: #0050b3; display: flex; align-items: center; gap: 6px; }
  .api-info-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
  .api-info-row { display: flex; align-items: center; gap: 10px; font-size: 13px;
    .label { min-width: 80px; color: #666; font-weight: 600; }
    code { background: #f0f5ff; color: #0066CC; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
  }
  .api-info-notice { background: #fffbe6; border-top: 1px solid #ffe58f; padding: 8px 14px; font-size: 12px; color: #ad6800; display: flex; align-items: center; gap: 6px; }
}

.done-banner { background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 8px; padding: 20px 24px; display: flex; align-items: center; gap: 10px; color: #28A745; font-weight: 600; font-size: 15px;
  .done-icon { font-size: 24px; }
  .done-actions { margin-left: auto; display: flex; gap: 10px; align-items: center; }
  .done-link { color: $primary; font-size: 13px; }
}
</style>
