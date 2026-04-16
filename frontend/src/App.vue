<template>
  <!-- Global Progress Bar -->
  <div class="global-progress" :class="{ active: isLoading, done: isDone }">
    <div class="progress-bar"></div>
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useLoadingStore } from './stores/loading'

const loadingStore = useLoadingStore()
const isLoading = ref(false)
const isDone = ref(false)
let doneTimer: ReturnType<typeof setTimeout> | null = null

watch(() => loadingStore.isLoading, (loading) => {
  if (doneTimer) {
    clearTimeout(doneTimer)
    doneTimer = null
  }
  if (loading) {
    isDone.value = false
    isLoading.value = true
  } else {
    // 로딩 완료: 바를 100%로 채운 뒤 fade out
    isDone.value = true
    isLoading.value = false
    doneTimer = setTimeout(() => {
      isDone.value = false
    }, 400)
  }
})
</script>

<style>
/* Global Progress Bar - NProgress 스타일 */
.global-progress {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  z-index: 99999;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s;
}

.global-progress.active {
  opacity: 1;
}

.global-progress.active .progress-bar {
  width: 85%;
  transition: width 8s cubic-bezier(0.1, 0.05, 0.1, 0.05);
}

.global-progress.done {
  opacity: 1;
}

.global-progress.done .progress-bar {
  width: 100%;
  transition: width 0.15s ease-out, opacity 0.3s 0.15s ease;
}

/* done 상태에서 fade out */
.global-progress.done {
  animation: progressFadeOut 0.4s 0.15s forwards;
}

@keyframes progressFadeOut {
  to {
    opacity: 0;
  }
}

.progress-bar {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #0066CC, #4a8fd9, #0066CC);
  background-size: 200% 100%;
  animation: progressShimmer 1.5s linear infinite;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px rgba(0, 102, 204, 0.4);
}

@keyframes progressShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
