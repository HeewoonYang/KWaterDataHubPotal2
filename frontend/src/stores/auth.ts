import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth.api'
import type { UserProfile } from '../api/auth.api'

export type UserRole = 'ADMIN' | 'MANAGER' | 'INTERNAL' | 'EXTERNAL'

export interface User {
  id: string
  username: string
  name: string
  email: string
  department?: string
  role: UserRole
  userType: string
  dataGrades: number[]
}

const ROLE_CONFIG: Record<UserRole, { label: string; defaultRoute: string; dataGrades: number[] }> = {
  ADMIN: { label: '시스템 관리자', defaultRoute: '/portal', dataGrades: [1, 2, 3] },
  MANAGER: { label: '데이터 관리자', defaultRoute: '/portal', dataGrades: [1, 2, 3] },
  INTERNAL: { label: '내부 사용자', defaultRoute: '/portal', dataGrades: [2, 3] },
  EXTERNAL: { label: '외부 사용자', defaultRoute: '/portal', dataGrades: [3] },
}

function profileToUser(p: UserProfile): User {
  return {
    id: p.id,
    username: p.login_id,
    name: p.name,
    email: p.email || '',
    department: p.department_name || undefined,
    role: p.role_code as UserRole,
    userType: p.user_type === 'INTERNAL' ? 'internal' : 'external',
    dataGrades: p.data_grades,
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role ?? null)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isManager = computed(() => user.value?.role === 'MANAGER')
  const isAdminOrManager = computed(() => isAdmin.value || isManager.value)
  const roleLabel = computed(() => user.value ? ROLE_CONFIG[user.value.role].label : '')
  const defaultRoute = computed(() => user.value ? ROLE_CONFIG[user.value.role].defaultRoute : '/login')

  const canAccessAdmin = computed(() => isAdminOrManager.value)
  const canAccessVisualization = computed(() => user.value?.role !== 'EXTERNAL')
  const canAccessAISearch = computed(() => user.value?.role !== 'EXTERNAL')

  const adminMenuAccess = computed(() => {
    if (!user.value) return {}
    const role = user.value.role
    return {
      system: role === 'ADMIN',
      user: role === 'ADMIN',
      standard: role === 'ADMIN' || role === 'MANAGER',
      collection: role === 'ADMIN' || role === 'MANAGER',
      cleansing: role === 'ADMIN' || role === 'MANAGER',
      storage: role === 'ADMIN',
      distribution: role === 'ADMIN' || role === 'MANAGER',
      operation: role === 'ADMIN',
    }
  })

  function restoreFromStorage() {
    try {
      const storedToken = localStorage.getItem('access_token')
      const storedAuth = localStorage.getItem('datahub_auth')
      if (storedToken && storedAuth) {
        const data = JSON.parse(storedAuth)
        user.value = data.user
        token.value = storedToken
      }
    } catch { /* ignore */ }
  }

  function saveToStorage() {
    if (user.value && token.value) {
      localStorage.setItem('access_token', token.value)
      localStorage.setItem('datahub_auth', JSON.stringify({ user: user.value, token: token.value }))
    } else {
      localStorage.removeItem('access_token')
      localStorage.removeItem('datahub_auth')
    }
  }

  async function login(username: string, password: string): Promise<{ success: boolean; message: string }> {
    try {
      const res = await authApi.login({ login_id: username, password })
      const data = res.data
      user.value = profileToUser(data.user)
      token.value = data.access_token
      saveToStorage()
      sessionStorage.setItem('datahub_session_active', '1')
      return { success: true, message: '' }
    } catch (err: any) {
      const msg = err.response?.data?.detail || '로그인에 실패했습니다.'
      return { success: false, message: msg }
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch { /* ignore */ }
    user.value = null
    token.value = null
    saveToStorage()
    sessionStorage.removeItem('datahub_session_active')
  }

  restoreFromStorage()

  return {
    user,
    token,
    isAuthenticated,
    userRole,
    isAdmin,
    isManager,
    isAdminOrManager,
    roleLabel,
    defaultRoute,
    canAccessAdmin,
    canAccessVisualization,
    canAccessAISearch,
    adminMenuAccess,
    login,
    logout,
  }
})
