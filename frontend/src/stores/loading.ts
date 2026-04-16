import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useLoadingStore = defineStore('loading', () => {
  const activeRequests = ref(0)

  const isLoading = computed(() => activeRequests.value > 0)

  function startLoading() {
    activeRequests.value++
  }

  function finishLoading() {
    if (activeRequests.value > 0) {
      activeRequests.value--
    }
  }

  return { isLoading, activeRequests, startLoading, finishLoading }
})
