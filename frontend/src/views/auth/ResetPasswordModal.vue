<template>
  <AdminModal :visible="visible" title="비밀번호 찾기 / 초기화" size="sm" @close="handleClose">
    <div v-if="step === 'form'" class="recovery-form">
      <p class="recovery-desc">
        가입 시 입력한 정보가 모두 일치하면 등록된 휴대폰번호로 임시 비밀번호를 발송해 드립니다.
        로그인 후 반드시 비밀번호를 변경해주세요.
      </p>
      <div class="form-group">
        <label class="required">아이디</label>
        <input v-model="loginId" placeholder="아이디를 입력하세요" autocomplete="username" />
      </div>
      <div class="form-group">
        <label class="required">이름</label>
        <input v-model="name" placeholder="이름을 입력하세요" autocomplete="name" />
      </div>
      <div class="form-group">
        <label class="required">휴대폰번호</label>
        <input v-model="phone" placeholder="010-0000-0000" autocomplete="tel" inputmode="tel" />
      </div>
      <div v-if="errorMsg" class="error-msg"><ExclamationCircleOutlined /> {{ errorMsg }}</div>
    </div>

    <div v-else-if="step === 'done'" class="recovery-form">
      <div class="done-box">
        <CheckCircleOutlined class="done-icon" />
        <p class="done-title">요청이 접수되었습니다</p>
        <p class="done-desc">
          입력하신 정보와 일치하는 계정이 있다면 등록된 휴대폰번호로 임시 비밀번호가 발송됩니다.
          로그인 후 반드시 비밀번호를 변경해주세요.
        </p>
      </div>
    </div>

    <template #footer>
      <template v-if="step === 'form'">
        <button class="btn btn-primary" :disabled="loading || !loginId || !name || !phone" @click="submit">
          <SendOutlined /> 임시 비밀번호 발송
        </button>
        <button class="btn btn-outline" @click="handleClose">취소</button>
      </template>
      <template v-else>
        <button class="btn btn-primary" @click="handleClose">로그인 화면으로</button>
      </template>
    </template>
  </AdminModal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import AdminModal from '../../components/AdminModal.vue'
import { authApi } from '../../api/auth.api'
import {
  SendOutlined, CheckCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons-vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

type Step = 'form' | 'done'
const step = ref<Step>('form')
const loginId = ref('')
const name = ref('')
const phone = ref('')
const errorMsg = ref('')
const loading = ref(false)

watch(() => props.visible, (v) => {
  if (v) reset()
})

function reset() {
  step.value = 'form'
  loginId.value = ''
  name.value = ''
  phone.value = ''
  errorMsg.value = ''
  loading.value = false
}

function handleClose() {
  emit('close')
}

async function submit() {
  errorMsg.value = ''
  if (!loginId.value.trim() || !name.value.trim() || !phone.value.trim()) {
    errorMsg.value = '모든 항목을 입력하세요.'
    return
  }
  loading.value = true
  try {
    await authApi.resetPassword({
      login_id: loginId.value.trim(),
      name: name.value.trim(),
      phone: phone.value.trim(),
    })
    // 보안 정책: 일치/불일치 여부와 무관하게 동일 메시지 노출 (열거 방지)
    step.value = 'done'
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '요청 처리 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.recovery-form {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.recovery-desc {
  font-size: $font-size-sm;
  color: $text-secondary;
  line-height: 1.5;
  margin-bottom: $spacing-sm;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: $spacing-xs;

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

.error-msg {
  font-size: $font-size-xs;
  color: $error;
  display: flex;
  align-items: center;
  gap: 4px;
}

.done-box {
  text-align: center;
  padding: $spacing-lg 0;

  .done-icon {
    font-size: 48px;
    color: $success;
  }

  .done-title {
    font-size: $font-size-lg;
    font-weight: 700;
    color: $text-primary;
    margin-top: $spacing-md;
  }

  .done-desc {
    font-size: $font-size-sm;
    color: $text-secondary;
    line-height: 1.6;
    margin-top: $spacing-sm;
  }
}
</style>
