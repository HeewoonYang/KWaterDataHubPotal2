<template>
  <div class="sso-callback">
    <div class="callback-card">
      <div v-if="loading" class="loading-state">
        <LoadingOutlined class="spin-icon" />
        <p>SSO 인증 처리 중...</p>
      </div>
      <div v-else-if="error" class="error-state">
        <ExclamationCircleOutlined class="error-icon" />
        <p>{{ error }}</p>
        <button class="btn-retry" @click="goLogin">로그인 페이지로 이동</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import apiClient from '../../api/client'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const code = route.query.code as string
  if (!code) {
    error.value = 'SSO 인증 코드가 없습니다.'
    loading.value = false
    return
  }
  try {
    const res = await apiClient.post('/sso/exchange', { code })
    const data = res.data
    if (data?.access_token && data?.user) {
      const result = await authStore.loginWithSsoResponse(data)
      if (result.success) {
        router.replace(authStore.defaultRoute)
        return
      }
      error.value = result.message
    } else {
      error.value = 'SSO 응답 형식이 올바르지 않습니다.'
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'SSO 인증에 실패했습니다.'
  }
  loading.value = false
})

function goLogin() {
  router.replace('/portal/login')
}
</script>

<style scoped>
.sso-callback { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f5f7fa; }
.callback-card { background: #fff; border-radius: 12px; padding: 48px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.1); min-width: 320px; }
.loading-state p, .error-state p { margin-top: 16px; font-size: 14px; color: #666; }
.spin-icon { font-size: 36px; color: #1890ff; animation: spin 1s linear infinite; }
.error-icon { font-size: 36px; color: #DC3545; }
.btn-retry { margin-top: 20px; padding: 8px 24px; background: #1890ff; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-retry:hover { background: #40a9ff; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
