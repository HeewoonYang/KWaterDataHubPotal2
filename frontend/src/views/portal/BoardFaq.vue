<template>
  <div class="board-page">
    <nav class="breadcrumb">
      <span>게시판</span>
      <span class="separator">&gt;</span>
      <span class="current">FAQ</span>
    </nav>

    <div class="page-header"><h2>FAQ</h2><p>자주 묻는 질문을 확인하세요.</p></div>
    <div class="board-tabs">
      <router-link to="/portal/board/notices" class="tab">공지사항</router-link>
      <router-link to="/portal/board/qna" class="tab">질의응답</router-link>
      <router-link to="/portal/board/faq" class="tab active">FAQ</router-link>
    </div>

    <div class="board-toolbar">
      <div class="faq-categories">
        <button v-for="cat in faqCategories" :key="cat" class="cat-btn" :class="{ active: selectedCategory === cat }" @click="selectedCategory = cat; fetchFaq()">{{ cat }}</button>
      </div>
      <button v-if="isAdmin" class="btn btn-primary btn-sm" @click="openWrite"><EditOutlined /> FAQ 등록</button>
    </div>

    <div class="faq-list">
      <div v-for="faq in faqs" :key="faq.id" class="faq-item" :class="{ open: openId === faq.id }">
        <div class="faq-question" @click="openId = openId === faq.id ? null : faq.id">
          <span class="faq-badge">Q</span>
          <span class="faq-title">{{ faq.title }}</span>
          <span class="faq-category-tag">{{ faq.faq_category }}</span>
          <span class="faq-arrow">{{ openId === faq.id ? '▲' : '▼' }}</span>
        </div>
        <div v-if="openId === faq.id" class="faq-answer">
          <span class="faq-badge answer">A</span>
          <div class="faq-answer-text" v-html="faq.content?.replace(/\n/g, '<br>')"></div>
        </div>
      </div>
      <div v-if="faqs.length === 0" class="faq-empty">등록된 FAQ가 없습니다.</div>
    </div>

    <!-- FAQ 등록 -->
    <AdminModal :visible="showWrite" title="FAQ 등록" size="md" @close="showWrite = false">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div><label class="form-label">카테고리</label>
          <select v-model="writeForm.category" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;">
            <option v-for="cat in faqCategories.filter(c => c !== '전체')" :key="cat" :value="cat">{{ cat }}</option>
          </select>
        </div>
        <div><label class="form-label">질문</label><input v-model="writeForm.title" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;" placeholder="질문을 입력하세요" /></div>
        <div><label class="form-label">답변</label><textarea v-model="writeForm.content" rows="6" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;resize:vertical;" placeholder="답변을 입력하세요"></textarea></div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="submitWrite">등록</button>
        <button class="btn btn-outline" @click="showWrite = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { EditOutlined } from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import AdminModal from '../../components/AdminModal.vue'
import { boardApi } from '../../api/portal.api'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdminOrManager)

const faqCategories = ['전체', '데이터 이용', '계정/권한', '시스템', '유통/다운로드', '기타']
const selectedCategory = ref('전체')
const faqs = ref<any[]>([])
const openId = ref<string | null>(null)
const showWrite = ref(false)
const writeForm = ref({ title: '', content: '', category: '데이터 이용' })

async function fetchFaq() {
  try {
    const params: Record<string, any> = {}
    if (selectedCategory.value !== '전체') params.category = selectedCategory.value
    const res = await boardApi.faqList(params)
    faqs.value = res.data?.data || []
  } catch { /* fallback */ }
}

function openWrite() { writeForm.value = { title: '', content: '', category: '데이터 이용' }; showWrite.value = true }

async function submitWrite() {
  if (!writeForm.value.title.trim()) return message.warning('질문을 입력하세요.')
  const fd = new FormData()
  fd.append('title', writeForm.value.title)
  fd.append('content', writeForm.value.content)
  fd.append('category', writeForm.value.category)
  try { await boardApi.createFaq(fd); showWrite.value = false; await fetchFaq() } catch { message.error('등록에 실패했습니다.') }
}

onMounted(fetchFaq)
</script>

<style lang="scss" scoped>
@use '../../styles/variables' as *;
.board-page { display: flex; flex-direction: column; gap: $spacing-lg; }
.breadcrumb {
  font-size: 12px; color: #999; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
  a { color: #999; text-decoration: none; &:hover { color: #0066CC; } }
  .separator { color: #ddd; }
  .current { color: #333; font-weight: 600; }
}
.page-header { h2 { font-size: $font-size-xl; font-weight: 700; margin-bottom: 4px; } p { font-size: $font-size-sm; color: $text-muted; } }
.board-tabs { display: flex; border-bottom: 2px solid $border-color; }
.tab { padding: 10px 20px; font-size: $font-size-sm; font-weight: 600; color: $text-secondary; text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -2px; &:hover { color: $primary; } &.active, &.router-link-exact-active { color: $primary; border-bottom-color: $primary; } }
.board-toolbar { display: flex; justify-content: space-between; align-items: center; }
.faq-categories { display: flex; gap: 6px; }
.cat-btn { padding: 5px 14px; border: 1px solid $border-color; border-radius: 16px; font-size: $font-size-xs; background: $white; cursor: pointer; &:hover { border-color: $primary; color: $primary; } &.active { background: $primary; color: $white; border-color: $primary; } }

.faq-list { display: flex; flex-direction: column; gap: 8px; }
.faq-item { background: $white; border: 1px solid $border-color; border-radius: $radius-lg; overflow: hidden; &.open { border-color: $primary; } }
.faq-question { display: flex; align-items: center; gap: 12px; padding: 14px 16px; cursor: pointer; &:hover { background: #f0f7ff; } }
.faq-badge { width: 28px; height: 28px; border-radius: 50%; background: $primary; color: $white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; flex-shrink: 0; &.answer { background: #28A745; } }
.faq-title { flex: 1; font-size: $font-size-sm; font-weight: 500; }
.faq-category-tag { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: $bg-light; color: $text-muted; }
.faq-arrow { font-size: 12px; color: $text-muted; }
.faq-answer { display: flex; gap: 12px; padding: 14px 16px; background: #f8fdf8; border-top: 1px solid #e8f5e9; }
.faq-answer-text { flex: 1; font-size: $font-size-sm; line-height: 1.7; color: $text-secondary; }
.faq-empty { text-align: center; padding: 60px; color: $text-muted; font-size: $font-size-sm; }
.form-label { font-size: 13px; font-weight: 600; display: block; margin-bottom: 4px; }
</style>
