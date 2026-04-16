<template>
  <AdminModal :visible="visible" title="아이디 찾기" size="sm" @close="handleClose">
    <!-- Step 1: 이름 + 휴대폰 입력 -->
    <div v-if="step === 'request'" class="recovery-form">
      <p class="recovery-desc">가입 시 입력한 이름과 휴대폰번호로 본인 확인 후 아이디를 찾아드립니다.</p>
      <div class="form-group">
        <label class="required">이름</label>
        <input v-model="name" placeholder="이름을 입력하세요" autocomplete="name" />
      </div>
      <div class="form-group">
        <label class="required">휴대폰번호</label>
        <input v-model="phone" placeholder="010-0000-0000" autocomplete="tel" inputmode="tel" />
      </div>
      <div v-if="errorMsg" class="error-msg"><ExclamationCircleOutlined /> {{ errorMsg }}</div>
      <div v-if="infoMsg" class="info-msg"><InfoCircleOutlined /> {{ infoMsg }}</div>
    </div>

    <!-- Step 2: OTP 입력 -->
    <div v-else-if="step === 'verify'" class="recovery-form">
      <p class="recovery-desc">
        <strong>{{ maskedPhone }}</strong> 로 전송된 6자리 인증번호를 5분 이내 입력하세요.
      </p>
      <div class="form-group">
        <label class="required">인증번호</label>
        <input v-model="code" placeholder="6자리 숫자" maxlength="6" inputmode="numeric" />
      </div>
      <div v-if="errorMsg" class="error-msg"><ExclamationCircleOutlined /> {{ errorMsg }}</div>
    </div>

    <!-- Step 3: 결과 -->
    <div v-else-if="step === 'result'" class="recovery-form">
      <p class="recovery-desc">확인된 아이디는 아래와 같습니다.</p>
      <div class="result-box">
        <span class="result-label">아이디</span>
        <span class="result-value">{{ maskedId }}</span>
      </div>
      <p class="info-msg">보안을 위해 아이디의 일부를 마스킹(*)처리하여 표시했습니다.</p>
    </div>

    <template #footer>
      <template v-if="step === 'request'">
        <button class="btn btn-primary" :disabled="loading || !name || !phone" @click="submitRequest">
          <SendOutlined /> 인증번호 요청
        </button>
        <button class="btn btn-outline" @click="handleClose">취소</button>
      </template>
      <template v-else-if="step === 'verify'">
        <button class="btn btn-primary" :disabled="loading || code.length !== 6" @click="submitVerify">
          <CheckOutlined /> 확인
        </button>
        <button class="btn btn-outline" @click="step = 'request'">이전</button>
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
  SendOutlined, CheckOutlined,
  ExclamationCircleOutlined, InfoCircleOutlined,
} from '@ant-design/icons-vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

type Step = 'request' | 'verify' | 'result'
const step = ref<Step>('request')
const name = ref('')
const phone = ref('')
const code = ref('')
const requestId = ref('')
const maskedPhone = ref('')
const maskedId = ref('')
const errorMsg = ref('')
const infoMsg = ref('')
const loading = ref(false)

watch(() => props.visible, (v) => {
  if (v) reset()
})

function reset() {
  step.value = 'request'
  name.value = ''
  phone.value = ''
  code.value = ''
  requestId.value = ''
  maskedPhone.value = ''
  maskedId.value = ''
  errorMsg.value = ''
  infoMsg.value = ''
  loading.value = false
}

function handleClose() {
  emit('close')
}

async function submitRequest() {
  errorMsg.value = ''
  infoMsg.value = ''
  if (!name.value.trim() || !phone.value.trim()) {
    errorMsg.value = '이름과 휴대폰번호를 입력하세요.'
    return
  }
  loading.value = true
  try {
    const res = await authApi.findIdRequest({ name: name.value.trim(), phone: phone.value.trim() })
    const data = res.data?.data
    if (data) {
      requestId.value = data.request_id
      maskedPhone.value = data.masked_phone
      step.value = 'verify'
    } else {
      errorMsg.value = '요청 처리 중 오류가 발생했습니다.'
    }
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '요청 처리 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

async function submitVerify() {
  errorMsg.value = ''
  loading.value = true
  try {
    const res = await authApi.findIdVerify({ request_id: requestId.value, code: code.value.trim() })
    const data = res.data?.data
    if (data) {
      maskedId.value = data.login_id_masked
      step.value = 'result'
    } else {
      errorMsg.value = '인증번호가 일치하지 않습니다.'
    }
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || '인증번호가 일치하지 않거나 만료되었습니다.'
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

.info-msg {
  font-size: $font-size-xs;
  color: $text-muted;
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md;
  background: $bg-light;
  border: 1px solid $border-color;
  border-radius: $radius-md;

  .result-label {
    font-size: $font-size-sm;
    color: $text-secondary;
  }

  .result-value {
    font-family: 'JetBrains Mono', 'D2Coding', monospace;
    font-weight: 700;
    font-size: $font-size-lg;
    color: $primary;
  }
}
</style>
