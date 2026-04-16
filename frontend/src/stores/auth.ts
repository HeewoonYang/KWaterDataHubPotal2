import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth.api'
import type { UserProfile } from '../api/auth.api'

export type UserRole = 'SUPER_ADMIN' | 'OPERATOR' | 'ENGINEER' | 'STEWARD' | 'EXECUTIVE' | 'KW_MANAGER' | 'EMPLOYEE' | 'EXTERNAL'
export type RoleGroup = 'SYS_ADMIN' | 'DATA_ADMIN' | 'GENERAL' | 'EXTERNAL'

export interface User {
  id: string
  username: string
  name: string
  email: string
  department?: string
  role: UserRole
  roleGroup: RoleGroup
  userType: string
  dataGrades: number[]
  screenPermissions: Record<string, { create: boolean; update: boolean; delete: boolean }>
  mustChangePassword?: boolean
}

const ROLE_CONFIG: Record<UserRole, { label: string; defaultRoute: string; dataGrades: number[]; group: RoleGroup }> = {
  SUPER_ADMIN: { label: '수퍼관리자', defaultRoute: '/portal', dataGrades: [1, 2, 3], group: 'SYS_ADMIN' },
  OPERATOR: { label: '운영자', defaultRoute: '/portal', dataGrades: [1, 2, 3], group: 'SYS_ADMIN' },
  ENGINEER: { label: '데이터엔지니어', defaultRoute: '/portal', dataGrades: [1, 2, 3], group: 'DATA_ADMIN' },
  STEWARD: { label: '데이터스튜어드', defaultRoute: '/portal', dataGrades: [1, 2, 3], group: 'DATA_ADMIN' },
  EXECUTIVE: { label: '수공임원', defaultRoute: '/portal', dataGrades: [2, 3], group: 'GENERAL' },
  KW_MANAGER: { label: '수공관리자', defaultRoute: '/portal', dataGrades: [2, 3], group: 'GENERAL' },
  EMPLOYEE: { label: '수공직원', defaultRoute: '/portal', dataGrades: [2, 3], group: 'GENERAL' },
  EXTERNAL: { label: '외부사용자', defaultRoute: '/portal', dataGrades: [3], group: 'EXTERNAL' },
}

function profileToUser(p: UserProfile): User {
  const roleConfig = ROLE_CONFIG[p.role_code as UserRole]
  return {
    id: p.id,
    username: p.login_id,
    name: p.name,
    email: p.email || '',
    department: p.department_name || undefined,
    role: p.role_code as UserRole,
    roleGroup: (p.role_group || roleConfig?.group || 'EXTERNAL') as RoleGroup,
    userType: p.user_type === 'INTERNAL' ? 'internal' : 'external',
    dataGrades: p.data_grades,
    screenPermissions: p.screen_permissions || {},
    mustChangePassword: !!p.must_change_password,
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role ?? null)
  const roleGroup = computed(() => user.value?.roleGroup ?? null)

  const isSysAdmin = computed(() => roleGroup.value === 'SYS_ADMIN')
  const isDataAdmin = computed(() => roleGroup.value === 'DATA_ADMIN')
  const isGeneral = computed(() => roleGroup.value === 'GENERAL')
  const isExternal = computed(() => roleGroup.value === 'EXTERNAL')

  const roleLabel = computed(() => user.value ? (ROLE_CONFIG[user.value.role]?.label || user.value.role) : '')
  const mustChangePassword = computed(() => !!user.value?.mustChangePassword)
  const defaultRoute = computed(() => {
    if (!user.value) return '/login'
    // 임시/초기 비밀번호 상태이면 강제 변경 페이지로 우선 이동
    if (user.value.mustChangePassword) return '/portal/change-password?forced=1'
    return ROLE_CONFIG[user.value.role]?.defaultRoute || '/portal'
  })

  function clearMustChangePassword() {
    if (user.value) {
      user.value = { ...user.value, mustChangePassword: false }
      saveToStorage()
    }
  }

  const isAdminOrManager = computed(() => isSysAdmin.value || isDataAdmin.value)
  const canAccessAdmin = computed(() => isSysAdmin.value || isDataAdmin.value)
  const canAccessVisualization = computed(() => !isExternal.value)
  const canAccessAISearch = computed(() => !isExternal.value)

  const adminMenuAccess = computed(() => {
    if (!user.value) return {}
    const g = user.value.roleGroup
    const isSA = g === 'SYS_ADMIN'
    const isDA = g === 'DATA_ADMIN'
    return {
      system: isSA,
      user: isSA,
      standard: isSA || isDA,
      collection: isSA || isDA,
      cleansing: isSA || isDA,
      storage: isSA || isDA,
      distribution: isSA || isDA,
      ontology: isSA || isDA,
      operation: isSA || isDA,
    }
  })

  function canCreate(screenCode: string): boolean {
    return user.value?.screenPermissions?.[screenCode]?.create ?? false
  }
  function canUpdate(screenCode: string): boolean {
    return user.value?.screenPermissions?.[screenCode]?.update ?? false
  }
  function canDelete(screenCode: string): boolean {
    return user.value?.screenPermissions?.[screenCode]?.delete ?? false
  }
  function canCUD(screenCode: string) {
    const sp = user.value?.screenPermissions?.[screenCode]
    return { create: sp?.create ?? false, update: sp?.update ?? false, delete: sp?.delete ?? false }
  }

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

  async function loginWithSsoResponse(data: any): Promise<{ success: boolean; message: string }> {
    try {
      user.value = profileToUser(data.user)
      token.value = data.access_token
      saveToStorage()
      sessionStorage.setItem('datahub_session_active', '1')
      return { success: true, message: '' }
    } catch (err: any) {
      return { success: false, message: 'SSO 인증 처리에 실패했습니다.' }
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
    roleGroup,
    isSysAdmin,
    isDataAdmin,
    isGeneral,
    isExternal,
    isAdminOrManager,
    roleLabel,
    defaultRoute,
    canAccessAdmin,
    canAccessVisualization,
    canAccessAISearch,
    adminMenuAccess,
    canCreate,
    canUpdate,
    canDelete,
    canCUD,
    login,
    loginWithSsoResponse,
    logout,
    mustChangePassword,
    clearMustChangePassword,
  }
})
