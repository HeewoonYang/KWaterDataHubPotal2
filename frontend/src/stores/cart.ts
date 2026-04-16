import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cartApi } from '../api/portal.api'

export interface CartItem {
  id: string          // portal_cart_item.id (DB PK)
  dataset_id: string  // catalog_dataset.id
  name: string
  nameKr?: string
  type?: string
  typeLabel?: string
  grade?: number
  gradeCode?: string
  columns?: number
  rows?: string
  tags?: string[]
  addedAt: string
  // 데이터 규모 옵션
  dateFrom?: string
  dateTo?: string
  maxRows?: string
  requestFormat?: string
  purpose?: string
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const loading = ref(false)

  const itemCount = computed(() => items.value.length)
  const isEmpty = computed(() => items.value.length === 0)
  const datasetIds = computed(() => new Set(items.value.map(i => i.dataset_id)))

  function isInCart(datasetId: string): boolean {
    return datasetIds.value.has(String(datasetId))
  }

  // DB에서 장바구니 목록 조회
  async function fetchCart() {
    loading.value = true
    try {
      const res = await cartApi.list()
      const data = res.data?.data || []
      items.value = data.map((item: any) => ({
        id: item.id,
        dataset_id: item.dataset_id,
        name: item.dataset_name || '',
        nameKr: item.dataset_name_kr || item.dataset_name || '',
        type: item.data_format || '',
        typeLabel: item.data_format || '',
        grade: item.grade || 3,
        gradeCode: `L${item.grade || 3}`,
        columns: item.columns || 0,
        rows: item.rows || '-',
        tags: item.tags || [],
        addedAt: item.added_at || '',
        dateFrom: item.date_from || '',
        dateTo: item.date_to || '',
        maxRows: item.max_rows || '',
        requestFormat: item.request_format || 'CSV',
        purpose: '',
      }))
    } catch {
      // API 실패 시 localStorage fallback
      try {
        const saved = localStorage.getItem('datahub_cart')
        if (saved) items.value = JSON.parse(saved)
      } catch { /* ignore */ }
    } finally {
      loading.value = false
    }
  }

  // DB에 장바구니 항목 추가
  async function addItem(dataset: any) {
    const dsId = String(dataset.id)
    if (isInCart(dsId)) return

    try {
      await cartApi.add({
        dataset_id: dsId,
        dataset_name: dataset.dataset_name_kr || dataset.dataset_name || dataset.nameKr || dataset.name || '',
        data_format: dataset.data_format || dataset.type || '',
        grade: dataset.grade || parseInt(dataset.grade_code?.replace('L', '') || '3'),
        date_from: dataset.dateFrom || '',
        date_to: dataset.dateTo || '',
        max_rows: dataset.maxRows || '',
        request_format: dataset.requestFormat || 'CSV',
      })

      // 성공하면 전체 목록 재조회
      await fetchCart()
    } catch {
      // fallback: 로컬에 추가
      items.value.push({
        id: dsId,
        dataset_id: dsId,
        name: dataset.dataset_name || dataset.name || '',
        nameKr: dataset.dataset_name_kr || dataset.nameKr || '',
        type: dataset.data_format || dataset.type || '',
        typeLabel: dataset.typeLabel || dataset.data_format || '',
        grade: dataset.grade || parseInt(dataset.grade_code?.replace('L', '') || '3'),
        gradeCode: dataset.grade_code || 'L3',
        columns: dataset.columns || 0,
        rows: dataset.rows || dataset.row_count?.toLocaleString() || '-',
        tags: dataset.tags || [],
        addedAt: new Date().toISOString().substring(0, 10),
        dateFrom: dataset.dateFrom || '',
        dateTo: dataset.dateTo || '',
        maxRows: dataset.maxRows || '',
        requestFormat: dataset.requestFormat || 'CSV',
        purpose: dataset.purpose || '',
      })
    }
  }

  // DB에서 장바구니 항목 삭제
  async function removeItem(id: string) {
    try {
      await cartApi.remove(id)
      items.value = items.value.filter(i => i.id !== id)
    } catch {
      items.value = items.value.filter(i => i.id !== id)
    }
  }

  // DB 장바구니 전체 비우기
  async function clearCart() {
    try {
      await cartApi.clear()
    } catch { /* ignore */ }
    items.value = []
  }

  return { items, itemCount, isEmpty, datasetIds, loading, isInCart, addItem, removeItem, clearCart, fetchCart }
})
