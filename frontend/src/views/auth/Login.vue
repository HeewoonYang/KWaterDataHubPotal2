<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 좌측 브랜딩 영역 -->
      <div class="login-brand">
        <div class="brand-content">
          <CloudOutlined class="brand-logo" />
          <h1>K-water 데이터허브</h1>
          <p>클라우드 데이터 에코시스템</p>
          <div class="brand-features">
            <div class="feature-item">
              <DatabaseOutlined />
              <span>통합 데이터 카탈로그</span>
            </div>
            <div class="feature-item">
              <BarChartOutlined />
              <span>데이터 시각화 & 분석</span>
            </div>
            <div class="feature-item">
              <ApiOutlined />
              <span>표준 API 유통</span>
            </div>
            <div class="feature-item">
              <SafetyOutlined />
              <span>데이터 품질 관리</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측 로그인 폼 -->
      <div class="login-form-area">
        <div class="login-form-inner">
          <h2>로그인</h2>
          <p class="login-desc">데이터허브 포털에 로그인하세요.</p>

          <!-- 탭: 내부/외부 -->
          <div class="login-tabs">
            <button
              class="tab-btn"
              :class="{ active: loginType === 'internal' }"
              @click="loginType = 'internal'"
            >
              <TeamOutlined /> 내부 사용자
            </button>
            <button
              class="tab-btn"
              :class="{ active: loginType === 'external' }"
              @click="loginType = 'external'"
            >
              <UserOutlined /> 외부 사용자
            </button>
          </div>

          <!-- SSO 안내 (내부) -->
          <div v-if="loginType === 'internal'" class="sso-section">
            <button class="btn-sso" @click="showIdPwForm = !showIdPwForm">
              <LoginOutlined />
              오아시스 SSO 로그인
            </button>
            <p class="sso-hint">K-water 임직원은 SSO를 통해 로그인합니다.</p>
            <div class="divider">
              <span>또는 테스트 계정</span>
            </div>
          </div>

          <!-- ID/PW 폼 -->
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label>
                <UserOutlined /> 아이디
              </label>
              <input
                type="text"
                v-model="username"
                placeholder="아이디를 입력하세요"
                autocomplete="username"
              />
            </div>
            <div class="form-group">
              <label>
                <LockOutlined /> 비밀번호
              </label>
              <input
                type="password"
                v-model="password"
                placeholder="비밀번호를 입력하세요"
                autocomplete="current-password"
              />
            </div>

            <div v-if="errorMsg" class="error-msg">
              <ExclamationCircleOutlined /> {{ errorMsg }}
            </div>

            <button type="submit" class="btn-login">로그인</button>
          </form>

          <!-- 테스트 계정 안내 -->
          <div class="test-accounts">
            <p class="test-title"><InfoCircleOutlined /> 테스트 계정</p>
            <div class="account-list">
              <div
                v-for="acc in testAccounts"
                :key="acc.id"
                class="account-item"
                @click="fillTestAccount(acc.id, acc.pw)"
              >
                <span class="acc-role" :class="acc.roleClass">{{ acc.roleLabel }}</span>
                <span class="acc-info">{{ acc.id }} / {{ acc.pw }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import {
  CloudOutlined,
  DatabaseOutlined,
  BarChartOutlined,
  ApiOutlined,
  SafetyOutlined,
  TeamOutlined,
  UserOutlined,
  LoginOutlined,
  LockOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const loginType = ref<'internal' | 'external'>('internal')
const showIdPwForm = ref(false)
const username = ref('')
const password = ref('')
const errorMsg = ref('')

const testAccounts = [
  { id: 'admin', pw: 'admin', roleLabel: 'ADMIN', roleClass: 'admin' },
  { id: 'manager', pw: 'manager', roleLabel: 'MANAGER', roleClass: 'manager' },
  { id: 'user', pw: 'user', roleLabel: 'INTERNAL', roleClass: 'internal' },
  { id: 'guest', pw: 'guest', roleLabel: 'EXTERNAL', roleClass: 'external' },
]

function fillTestAccount(id: string, pw: string) {
  username.value = id
  password.value = pw
  errorMsg.value = ''
  handleLogin()
}

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '아이디와 비밀번호를 입력하세요.'
    return
  }
  const result = await authStore.login(username.value, password.value)
  if (result.success) {
    router.push(authStore.defaultRoute)
  } else {
    errorMsg.value = result.message
  }
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-light;
}

.login-container {
  display: flex;
  width: 900px;
  min-height: 560px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: $shadow-lg;
}

// ===== Brand =====
.login-brand {
  width: 380px;
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  color: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-xxl;
}

.brand-content {
  text-align: center;

  .brand-logo {
    font-size: 48px;
    margin-bottom: $spacing-lg;
    opacity: 0.9;
  }

  h1 {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: $spacing-sm;
  }

  p {
    font-size: $font-size-md;
    opacity: 0.8;
    margin-bottom: $spacing-xxl;
  }
}

.brand-features {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: $font-size-sm;
  opacity: 0.85;

  :deep(.anticon) {
    font-size: 16px;
  }
}

// ===== Form Area =====
.login-form-area {
  flex: 1;
  background: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-xxl;
}

.login-form-inner {
  width: 100%;
  max-width: 340px;

  h2 {
    font-size: $font-size-xxl;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: $spacing-xs;
  }

  .login-desc {
    font-size: $font-size-sm;
    color: $text-muted;
    margin-bottom: $spacing-xl;
  }
}

// ===== Tabs =====
.login-tabs {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-xl;
}

.tab-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid $border-color;
  border-radius: $radius-md;
  background: $white;
  color: $text-secondary;
  font-size: $font-size-sm;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all $transition-fast;

  &:hover {
    border-color: $primary;
    color: $primary;
  }

  &.active {
    background: $primary;
    border-color: $primary;
    color: $white;
  }
}

// ===== SSO =====
.sso-section {
  margin-bottom: $spacing-lg;
}

.btn-sso {
  width: 100%;
  padding: 10px;
  background: $secondary;
  color: $white;
  border-radius: $radius-md;
  font-size: $font-size-md;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-sm;

  &:hover { opacity: 0.9; }
}

.sso-hint {
  text-align: center;
  font-size: $font-size-xs;
  color: $text-muted;
  margin-top: $spacing-sm;
}

.divider {
  display: flex;
  align-items: center;
  margin: $spacing-lg 0;

  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: $border-color;
  }

  span {
    padding: 0 $spacing-md;
    font-size: $font-size-xs;
    color: $text-muted;
  }
}

// ===== Form =====
.login-form {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.form-group {
  label {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }

  input {
    width: 100%;
    padding: 9px 12px;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    font-size: $font-size-md;
    outline: none;
    transition: border $transition-fast;

    &:focus { border-color: $primary; }
    &::placeholder { color: #ccc; }
  }
}

.error-msg {
  font-size: $font-size-xs;
  color: $error;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-login {
  width: 100%;
  padding: 10px;
  background: $primary;
  color: $white;
  border-radius: $radius-md;
  font-size: $font-size-md;
  font-weight: 600;
  margin-top: $spacing-sm;
  transition: background $transition-fast;

  &:hover { background: darken($primary, 8%); }
}

// ===== Test Accounts =====
.test-accounts {
  margin-top: $spacing-xl;
  padding-top: $spacing-lg;
  border-top: 1px solid $border-color;

  .test-title {
    font-size: $font-size-xs;
    color: $text-muted;
    margin-bottom: $spacing-sm;
    display: flex;
    align-items: center;
    gap: 5px;
  }
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;
}

.account-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: 5px 8px;
  border-radius: $radius-sm;
  cursor: pointer;
  transition: background $transition-fast;

  &:hover { background: $bg-light; }
}

.acc-role {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 3px;
  min-width: 65px;
  text-align: center;

  &.admin { background: #fce4ec; color: #c62828; }
  &.manager { background: #fff3e0; color: #e65100; }
  &.internal { background: #e3f2fd; color: #1565c0; }
  &.external { background: #e8f5e9; color: #2e7d32; }
}

.acc-info {
  font-size: $font-size-xs;
  color: $text-secondary;
  font-family: 'JetBrains Mono', 'D2Coding', monospace;
}

// ===== 반응형: 태블릿 =====
@media (max-width: #{$bp-desktop - 1px}) and (min-width: $bp-tablet) {
  .login-container {
    width: 95%;
    max-width: 800px;
  }

  .login-brand {
    width: 300px;
    padding: $spacing-xl;

    .brand-logo { font-size: 36px; }
    h1 { font-size: 20px; }
  }
}
</style>
