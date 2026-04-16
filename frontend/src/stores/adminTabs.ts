import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface AdminTab {
  path: string
  label: string
  closable: boolean
}

const STORAGE_KEY = 'admin_tabs'

export const useAdminTabsStore = defineStore('adminTabs', () => {
  const tabs = ref<AdminTab[]>([])
  const activeTabPath = ref('')

  // sessionStorage에서 복원
  function loadFromStorage() {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed.tabs) && parsed.tabs.length > 0) {
          tabs.value = parsed.tabs
          activeTabPath.value = parsed.activeTabPath || parsed.tabs[0].path
          return true
        }
      }
    } catch {}
    return false
  }

  // sessionStorage에 저장
  function saveToStorage() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        tabs: tabs.value,
        activeTabPath: activeTabPath.value,
      }))
    } catch {}
  }

  // 탭 추가 (이미 있으면 활성화만)
  function addTab(path: string, label: string) {
    const existing = tabs.value.find(t => t.path === path)
    if (existing) {
      // 라벨 업데이트 (breadcrumb 변경 가능)
      existing.label = label
      activeTabPath.value = path
    } else {
      tabs.value.push({
        path,
        label,
        closable: tabs.value.length > 0, // 첫 번째 탭은 닫기 불가
      })
      activeTabPath.value = path
    }
    saveToStorage()
  }

  // 탭 닫기
  function removeTab(path: string): string | null {
    const idx = tabs.value.findIndex(t => t.path === path)
    if (idx === -1) return null

    const tab = tabs.value[idx]
    if (!tab.closable) return null

    tabs.value.splice(idx, 1)

    // 닫은 탭이 현재 활성 탭이면 인접 탭으로 이동
    let nextPath: string | null = null
    if (activeTabPath.value === path) {
      if (tabs.value.length > 0) {
        // 같은 인덱스 또는 이전 탭으로
        const nextIdx = Math.min(idx, tabs.value.length - 1)
        nextPath = tabs.value[nextIdx].path
        activeTabPath.value = nextPath
      }
    }

    saveToStorage()
    return nextPath
  }

  // 모든 탭 닫기 (첫 번째 고정 탭 제외)
  function removeAllClosable() {
    const fixed = tabs.value.filter(t => !t.closable)
    tabs.value = fixed
    if (fixed.length > 0) {
      activeTabPath.value = fixed[0].path
    }
    saveToStorage()
    return activeTabPath.value
  }

  // 현재 탭 외 모두 닫기
  function removeOthers(path: string) {
    tabs.value = tabs.value.filter(t => !t.closable || t.path === path)
    // 고정 탭도 유지
    const fixedTabs = tabs.value.filter(t => !t.closable)
    if (!tabs.value.find(t => t.path === path) && fixedTabs.length > 0) {
      activeTabPath.value = fixedTabs[0].path
    } else {
      activeTabPath.value = path
    }
    saveToStorage()
    return activeTabPath.value
  }

  // 초기화
  function init() {
    loadFromStorage()
  }

  return {
    tabs,
    activeTabPath,
    addTab,
    removeTab,
    removeAllClosable,
    removeOthers,
    init,
  }
})
