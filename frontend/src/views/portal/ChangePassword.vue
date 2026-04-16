<template>
  <div class="change-password-page">
    <div class="change-password-card">
      <div class="header">
        <LockOutlined class="header-icon" />
        <h2>{{ forced ? '비밀번호를 변경해주세요' : '비밀번호 변경' }}</h2>
        <p v-if="forced" class="forced-desc">
          초기 또는 임시 비밀번호로 로그인하셨습니다. 보안을 위해 지금 새 비밀번호로 변경해주세요.
        </p>
        <p v-else class="desc">보안을 위해 주기적으로 비밀번호를 변경하세요.</p>
      </div>

      <form class="form" @submit.prevent="submit">
        <div class="form-group">
          <label class="required">현재 비밀번호</label>
          <input v-model="oldPassword" type="password" autocomplete="current-password" placeholder="현재 비밀번호" />
        </div>
        <div class="form-group">
          <label class="required">새 비밀번호</label>
          <input v-model="newPassword" type="password" autocomplete="new-password" placeholder="9자 이상, 대/소문자·숫자·특수문자 중 3종 이상" />
        </div>
        <div class="form-group">
          <label class="required">새 비밀번호 확인</label>
          <input v-model="confirmPassword" type="password" autocomplete="new-password" placeholder="새 비밀번호 재입력" />
        </div>

        <ul class="policy">
          <li>9자 이상</li>
          <li>대문자 / 소문자 / 숫자 / 특수문자 중 <strong>3종 이상</strong> 포함</li>
          <li>변경 후에는 재로그인해주세요 (기존 세션은 자동 해제)</li>
        </ul>

        <div v-if="errorMsg" class="error-msg"><ExclamationCircleOutlined /> {{ errorMsg }}</div>
        <div v-if="successMsg" class="success-msg"><CheckCircleOutlined /> {{ successMsg }}</div>

        <div class="actions">
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <SaveOutlined /> 비밀번호 변경
          </button>
          <button v-if="!forced" type="button" class="btn btn-outline" @click="$router.back()">취소</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { authApi } from '../../api/auth.api'
import {
  LockOutlined, SaveOutlined,
  ExclamationCircleOutlined, CheckCircleOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const forced = computed(() => route.query.forced === '1' || authStore.mustChangePassword)

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const successMsg = ref('')
const loading = ref(false)

async function submit() {
  errorMsg.value = ''
  successMsg.value = ''

  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    errorMsg.value = '모든 항목을 입력하세요.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = '새 비밀번호와 확인 값이 일치하지 않습니다.'
    return
  }
  if (newPassword.value === oldPassword.value) {
    errorMsg.value = '현재 비밀번호와 다른 값을 입력하세요.'
    return
  }

  loading.value = true
  try {
    const res = await authApi.changePassword(oldPassword.value, newPassword.value)
    successMsg.value = res.data?.message || '비밀번호가 변경되었습니다. 다시 로그인해주세요.'
    authStore.clearMustChangePassword()
    // 기존 세션은 서버에서 무효화됨 → 재로그인 유도
    setTimeout(async () => {
      await authStore.logout()
      router.push('/login')
    }, 1500)
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '비밀번호 변경에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.change-password-page {
  min-height: calc(100vh - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
  background: $bg-light;
}

.change-password-card {
  width: 100%;
  max-width: 480px;
  background: $white;
  border-radius: $radius-lg;
  box-shadow: $shadow-md;
  padding: $spacing-xxl;
}

.header {
  text-align: center;
  margin-bottom: $spacing-xl;

  .header-icon {
    font-size: 36px;
    color: $primary;
    margin-bottom: $spacing-sm;
  }

  h2 {
    font-size: $font-size-xl;
    font-weight: 700;
    margin-bottom: $spacing-xs;
  }

  .forced-desc {
    font-size: $font-size-sm;
    color: $warning;
    line-height: 1.5;
  }

  .desc {
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: $font-size-xs;
    font-weight: 600;
    color: $text-secondary;

    &.required::after {
      content: ' *';
      color: $error;
    }
  }

  input {
    padding: 9px 12px;
    border: 1px solid $border-color;
    border-radius: $radius-md;
    font-size: $font-size-md;
    outline: none;

    &:focus { border-color: $primary; }
  }
}

.policy {
  margin: 0;
  padding: $spacing-sm $spacing-md;
  background: $bg-light;
  border-radius: $radius-md;
  font-size: $font-size-xs;
  color: $text-secondary;
  list-style: disc;
  padding-left: 28px;

  li { line-height: 1.7; }
}

.error-msg {
  font-size: $font-size-xs;
  color: $error;
  display: flex;
  align-items: center;
  gap: 4px;
}

.success-msg {
  font-size: $font-size-sm;
  color: $success;
  display: flex;
  align-items: center;
  gap: 4px;
}

.actions {
  display: flex;
  gap: $spacing-sm;
  margin-top: $spacing-md;

  .btn { flex: 1; }
}
</style>
