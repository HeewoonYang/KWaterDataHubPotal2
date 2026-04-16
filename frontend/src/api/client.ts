import axios from 'axios'
import { useLoadingStore } from '../stores/loading'

// 런타임 ENV 우선 → 빌드타임 ENV → 기본값
// K8s 에서는 ConfigMap 의 API_BASE_URL 이 docker-entrypoint.sh 를 통해 window.__ENV__ 로 주입됨
declare global {
  interface Window {
    __ENV__?: { API_BASE_URL?: string; APP_ENV?: string }
  }
}
const API_BASE_URL =
  (typeof window !== 'undefined' && window.__ENV__?.API_BASE_URL) ||
  import.meta.env.VITE_API_BASE_URL ||
  '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Pinia 스토어는 앱 초기화 후 접근해야 하므로 lazy 초기화
let loadingStore: ReturnType<typeof useLoadingStore> | null = null
function getLoadingStore() {
  if (!loadingStore) {
    try {
      loadingStore = useLoadingStore()
    } catch {
      // Pinia가 아직 초기화되지 않은 경우 무시
    }
  }
  return loadingStore
}

// 요청 인터셉터: JWT 토큰 추가 + 로딩 시작
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    getLoadingStore()?.startLoading()
    return config
  },
  (error) => {
    getLoadingStore()?.finishLoading()
    return Promise.reject(error)
  }
)

// 응답 인터셉터: 에러 처리 + 로딩 종료
apiClient.interceptors.response.use(
  (response) => {
    getLoadingStore()?.finishLoading()
    return response
  },
  (error) => {
    getLoadingStore()?.finishLoading()
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
