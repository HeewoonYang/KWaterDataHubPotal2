<template>
  <div class="ai-search-page">
    <nav class="breadcrumb">
      <router-link to="/portal">대시보드</router-link>
      <span class="separator">/</span>
      <span class="current">AI검색</span>
    </nav>

    <div class="page-header">
      <h2>AI 검색</h2>
      <p>생성형 AI 기반 자연어로 데이터를 검색하고 질의하세요.</p>
    </div>

    <!-- 대화 영역 -->
    <div class="chat-area">
      <div class="chat-messages" ref="chatContainer">
        <!-- 환영 메시지 -->
        <div class="message system">
          <div class="msg-avatar"><RobotOutlined /></div>
          <div class="msg-content">
            <p>안녕하세요! K-water 데이터허브 AI 검색입니다.</p>
            <p>자연어로 데이터를 검색하거나 질문해 보세요.</p>
            <div class="quick-questions">
              <button v-for="q in quickQuestions" :key="q" class="quick-btn" @click="askQuestion(q)">{{ q }}</button>
            </div>
          </div>
        </div>

        <!-- 대화 메시지 -->
        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="msg-avatar">
            <UserOutlined v-if="msg.role === 'user'" />
            <RobotOutlined v-else />
          </div>
          <div class="msg-content">
            <p v-html="msg.text"></p>
            <div v-if="msg.datasets" class="result-cards">
              <div v-for="ds in msg.datasets" :key="ds.name" class="result-card">
                <DatabaseOutlined />
                <div class="result-info">
                  <span class="result-name">{{ ds.name }}</span>
                  <span class="result-meta">{{ ds.meta }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 입력 -->
      <div class="chat-input">
        <input type="text" v-model="inputText" placeholder="데이터에 대해 질문해 보세요..." @keyup.enter="sendMessage" />
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim()">
          <SendOutlined />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import {
  RobotOutlined,
  UserOutlined,
  DatabaseOutlined,
  SendOutlined,
} from '@ant-design/icons-vue'
import { aiApi } from '../../api/portal.api'

const inputText = ref('')
const chatContainer = ref<HTMLElement>()
let msgId = 0

interface ChatMessage {
  id: number
  role: 'user' | 'ai'
  text: string
  datasets?: { name: string; meta: string }[]
}

const messages = ref<ChatMessage[]>([])

const defaultQuickQuestions = [
  '최근 등록된 수자원 데이터는?',
  '댐 수위 데이터의 컬럼 정보 알려줘',
  '수질 관련 공개 데이터 목록',
  '전력 사용량 데이터 다운로드 방법',
]

const quickQuestions = ref(defaultQuickQuestions)

onMounted(async () => {
  try {
    const res = await aiApi.suggestions()
    if (res.data?.data) quickQuestions.value = res.data.data
  } catch (e) {
    console.error('AI 추천 질문 조회 실패:', e)
  }
})

function askQuestion(q: string) {
  inputText.value = q
  sendMessage()
}

async function sendMessage() {
  if (!inputText.value.trim()) return
  const userMsg = inputText.value.trim()
  messages.value.push({ id: ++msgId, role: 'user', text: userMsg })
  inputText.value = ''

  try {
    const res = await aiApi.search(userMsg)
    const data = res.data?.data
    const aiResponse: ChatMessage = {
      id: ++msgId,
      role: 'ai',
      text: data?.text || data?.answer || `"${userMsg}"에 대한 검색 결과입니다.`,
      datasets: data?.datasets || undefined,
    }
    messages.value.push(aiResponse)
  } catch (e) {
    console.error('AI 검색 실패:', e)
    // Fallback to simulated response
    messages.value.push(generateFallbackResponse(userMsg))
  }

  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  })
}

function generateFallbackResponse(query: string): ChatMessage {
  if (query.includes('수자원') || query.includes('최근')) {
    return {
      id: ++msgId, role: 'ai',
      text: '최근 등록된 <strong>수자원</strong> 관련 데이터셋 3건을 찾았습니다.',
      datasets: [
        { name: '댐 수위 관측 데이터 (2026)', meta: 'DB | L3 | 1.2억건 | 2026-03-25' },
        { name: '하천 유량 관측 데이터', meta: 'DB | L2 | 5,200만건 | 2026-03-24' },
        { name: '강수량 예측 모델 API', meta: 'API | L3 | 실시간 | 2026-03-25' },
      ],
    }
  }
  if (query.includes('수질')) {
    return {
      id: ++msgId, role: 'ai',
      text: '공개(L3) 등급의 <strong>수질</strong> 관련 데이터셋 2건을 찾았습니다.',
      datasets: [
        { name: '수질 모니터링 센서 데이터', meta: 'IoT | L2 | 8,500만건' },
        { name: '상수도 수질검사 결과', meta: 'CSV | L3 | 52만건' },
      ],
    }
  }
  return {
    id: ++msgId, role: 'ai',
    text: `"${query}"에 대해 검색 중입니다. 데이터허브에서 관련 데이터셋을 조회하고 있습니다. 보다 구체적인 키워드(예: 데이터 종류, 기간, 분류)를 포함하면 더 정확한 결과를 얻을 수 있습니다.`,
  }
}
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;

.ai-search-page { display: flex; flex-direction: column; height: calc(100vh - 160px); }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header {
  margin-bottom: $spacing-lg;
  h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: $spacing-xs; }
  p { font-size: $font-size-sm; color: $text-muted; }
}

.chat-area {
  flex: 1; display: flex; flex-direction: column; background: $white; border: 1px solid $border-color; border-radius: $radius-lg; box-shadow: $shadow-sm; overflow: hidden;
}
.chat-messages { flex: 1; overflow-y: auto; padding: $spacing-xl; display: flex; flex-direction: column; gap: $spacing-lg; }

.message {
  display: flex; gap: $spacing-md; max-width: 80%;
  &.user { align-self: flex-end; flex-direction: row-reverse; }
  &.system { max-width: 100%; }
}
.msg-avatar {
  width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;
  .user & { background: $primary; color: $white; }
  .ai &, .system & { background: #e8f5e9; color: #2e7d32; }
}
.msg-content {
  padding: $spacing-md $spacing-lg; border-radius: $radius-lg; font-size: $font-size-sm; line-height: 1.6;
  .user & { background: $primary; color: $white; border-bottom-right-radius: 4px; }
  .ai & { background: $bg-light; color: $text-primary; border-bottom-left-radius: 4px; }
  .system & { background: transparent; }
}

.quick-questions { display: flex; flex-wrap: wrap; gap: $spacing-sm; margin-top: $spacing-md; }
.quick-btn {
  padding: 6px 14px; border: 1px solid $primary; border-radius: 20px; background: $white; color: $primary; font-size: $font-size-xs; cursor: pointer;
  &:hover { background: $primary; color: $white; }
}

.result-cards { display: flex; flex-direction: column; gap: $spacing-sm; margin-top: $spacing-md; }
.result-card {
  display: flex; align-items: center; gap: $spacing-sm; padding: $spacing-sm $spacing-md; background: $white; border: 1px solid $border-color; border-radius: $radius-md; cursor: pointer;
  &:hover { border-color: $primary; }
  :deep(.anticon) { font-size: 20px; color: $primary; }
}
.result-info { display: flex; flex-direction: column; }
.result-name { font-size: $font-size-sm; font-weight: 500; }
.result-meta { font-size: $font-size-xs; color: $text-muted; }

.chat-input {
  display: flex; gap: $spacing-sm; padding: $spacing-md $spacing-lg; border-top: 1px solid $border-color; background: $bg-light;
  input { flex: 1; padding: 10px 14px; border: 1px solid $border-color; border-radius: 24px; font-size: $font-size-md; outline: none; background: $white; &:focus { border-color: $primary; } }
  .send-btn {
    width: 42px; height: 42px; border-radius: 50%; background: $primary; color: $white; font-size: 18px; display: flex; align-items: center; justify-content: center;
    &:disabled { opacity: 0.4; cursor: not-allowed; }
    &:hover:not(:disabled) { background: darken($primary, 8%); }
  }
}
</style>
