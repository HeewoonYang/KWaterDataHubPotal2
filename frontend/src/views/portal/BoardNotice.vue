<template>
  <div class="board-page">
    <nav class="breadcrumb">
      <span>게시판</span>
      <span class="separator">&gt;</span>
      <span class="current">공지사항</span>
    </nav>

    <div class="page-header">
      <h2>공지사항</h2>
      <p>데이터허브 포털의 공지사항을 확인하세요.</p>
    </div>
    <div class="board-tabs">
      <router-link to="/portal/board/notices" class="tab active">공지사항</router-link>
      <router-link to="/portal/board/qna" class="tab">질의응답</router-link>
      <router-link to="/portal/board/faq" class="tab">FAQ</router-link>
    </div>

    <!-- 검색 + 글쓰기 -->
    <div class="board-toolbar">
      <div class="search-wrap">
        <input v-model="searchText" placeholder="검색어를 입력하세요" @keyup.enter="fetchList" />
        <button class="btn btn-sm btn-primary" @click="fetchList"><SearchOutlined /> 검색</button>
      </div>
      <button v-if="isAdmin" class="btn btn-primary" @click="openWrite"><EditOutlined /> 글쓰기</button>
    </div>

    <!-- 목록 -->
    <div class="board-list">
      <table>
        <thead><tr><th style="width:50px">No</th><th>제목</th><th style="width:80px">작성자</th><th style="width:60px">조회</th><th style="width:100px">등록일</th></tr></thead>
        <tbody>
          <tr v-for="(post, i) in posts" :key="post.id" :class="{ pinned: post.is_pinned }" @click="openDetail(post)">
            <td class="text-center"><PushpinOutlined v-if="post.is_pinned" style="color:#e67e22" /><template v-else>{{ total - ((page - 1) * pageSize) - i }}</template></td>
            <td class="post-title">{{ post.title }}</td>
            <td class="text-center">{{ post.author_name }}</td>
            <td class="text-center">{{ post.view_count }}</td>
            <td class="text-center">{{ post.created_at }}</td>
          </tr>
          <tr v-if="posts.length === 0"><td colspan="5" class="text-center" style="padding:40px;color:#999;">등록된 공지사항이 없습니다.</td></tr>
        </tbody>
      </table>
      <div class="pagination" v-if="totalPages > 1">
        <button :disabled="page <= 1" @click="page--; fetchList()">이전</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="page++; fetchList()">다음</button>
      </div>
    </div>

    <!-- 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailPost.title" size="lg" @close="showDetail = false">
      <div class="detail-meta">
        <span>작성자: {{ detailPost.author_name }}</span>
        <span>등록일: {{ detailPost.created_at }}</span>
        <span>조회: {{ detailPost.view_count }}</span>
      </div>
      <div class="detail-content" v-html="detailPost.content?.replace(/\n/g, '<br>')"></div>
      <div v-if="detailPost.attachments?.length" class="detail-attachments">
        <h4>첨부파일</h4>
        <div v-for="att in detailPost.attachments" :key="att.id" class="attachment-item" @click="downloadFile(att)">
          <PaperClipOutlined /> {{ att.file_name }} <span class="file-size">({{ formatSize(att.file_size) }})</span>
        </div>
      </div>
      <template #footer>
        <button v-if="isAdmin" class="btn btn-danger" @click="deletePost">삭제</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 글쓰기 팝업 -->
    <AdminModal :visible="showWrite" title="공지사항 작성" size="lg" @close="showWrite = false">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div>
          <label class="form-label">제목</label>
          <input v-model="writeForm.title" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;" placeholder="제목을 입력하세요" />
        </div>
        <div>
          <label class="form-label">내용</label>
          <textarea v-model="writeForm.content" rows="10" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;resize:vertical;" placeholder="내용을 입력하세요"></textarea>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <input type="checkbox" v-model="writeForm.is_pinned" id="pinned" />
          <label for="pinned" style="font-size:13px;">상단 고정</label>
        </div>
        <div>
          <label class="form-label">첨부파일</label>
          <input type="file" multiple @change="onFileChange" style="font-size:13px;" />
        </div>
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
import { useRoute } from 'vue-router'
import { SearchOutlined, EditOutlined, PaperClipOutlined, PushpinOutlined } from '@ant-design/icons-vue'
import { message } from '../../utils/message'
import AdminModal from '../../components/AdminModal.vue'
import { boardApi } from '../../api/portal.api'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdminOrManager)

const posts = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const totalPages = computed(() => Math.ceil(total.value / pageSize))
const searchText = ref('')

const showDetail = ref(false)
const detailPost = ref<any>({})
const showWrite = ref(false)
const writeForm = ref({ title: '', content: '', is_pinned: false })
const writeFiles = ref<File[]>([])

async function fetchList() {
  try {
    const res = await boardApi.notices({ page: page.value, page_size: pageSize, search: searchText.value || undefined })
    posts.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch { /* fallback */ }
}

async function openDetail(post: any) {
  try {
    const res = await boardApi.getNotice(post.id)
    detailPost.value = res.data?.data || post
    showDetail.value = true
  } catch {
    detailPost.value = post
    showDetail.value = true
  }
}

function openWrite() {
  writeForm.value = { title: '', content: '', is_pinned: false }
  writeFiles.value = []
  showWrite.value = true
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  writeFiles.value = Array.from(input.files || [])
}

async function submitWrite() {
  if (!writeForm.value.title.trim()) return message.warning('제목을 입력하세요.')
  const fd = new FormData()
  fd.append('title', writeForm.value.title)
  fd.append('content', writeForm.value.content)
  fd.append('is_pinned', String(writeForm.value.is_pinned))
  writeFiles.value.forEach(f => fd.append('files', f))
  try {
    await boardApi.createNotice(fd)
    showWrite.value = false
    await fetchList()
  } catch { message.error('등록에 실패했습니다.') }
}

async function deletePost() {
  if (!confirm('삭제하시겠습니까?')) return
  try {
    await boardApi.deleteNotice(detailPost.value.id)
    showDetail.value = false
    await fetchList()
  } catch { message.error('삭제에 실패했습니다.') }
}

async function downloadFile(att: any) {
  try {
    const res = await boardApi.downloadAttachment(att.id)
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url; a.download = att.file_name; a.click()
    URL.revokeObjectURL(url)
  } catch { message.error('파일 다운로드에 실패했습니다.') }
}

function formatSize(bytes: number) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

onMounted(async () => {
  await fetchList()
  // 대시보드에서 공지 클릭 시 ?detail=id 로 넘어오면 자동으로 상세 열기
  const detailId = route.query.detail as string
  if (detailId) {
    const target = posts.value.find((p: any) => String(p.id) === detailId)
    if (target) openDetail(target)
  }
})
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

.board-tabs { display: flex; gap: 0; border-bottom: 2px solid $border-color; }
.tab { padding: 10px 20px; font-size: $font-size-sm; font-weight: 600; color: $text-secondary; text-decoration: none; border-bottom: 2px solid transparent; margin-bottom: -2px;
  &:hover { color: $primary; }
  &.active, &.router-link-exact-active { color: $primary; border-bottom-color: $primary; }
}

.board-toolbar { display: flex; justify-content: space-between; align-items: center; }
.search-wrap { display: flex; gap: 8px;
  input { padding: 6px 12px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-sm; width: 250px; }
}

.board-list {
  background: $white; border: 1px solid $border-color; border-radius: $radius-lg; overflow: hidden;
  table { width: 100%; border-collapse: collapse; }
  thead { background: #4a6a8a; color: #fff; th { padding: 10px 12px; font-size: $font-size-xs; font-weight: 600; } }
  tbody tr { border-bottom: 1px solid $bg-light; cursor: pointer; transition: background 0.15s;
    &:hover { background: #f0f7ff; }
    &.pinned { background: #fffde7; }
  }
  td { padding: 10px 12px; font-size: $font-size-sm; }
  .post-title { font-weight: 500; color: $text-primary; max-width: 500px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}

.pagination { display: flex; justify-content: center; align-items: center; gap: 12px; padding: 16px;
  button { padding: 4px 12px; border: 1px solid $border-color; border-radius: $radius-sm; font-size: $font-size-xs; background: $white;
    &:hover:not(:disabled) { background: $bg-light; }
    &:disabled { opacity: 0.4; cursor: not-allowed; }
  }
  span { font-size: $font-size-xs; color: $text-muted; }
}

.detail-meta { display: flex; gap: 16px; font-size: 12px; color: $text-muted; padding-bottom: 12px; border-bottom: 1px solid $bg-light; margin-bottom: 16px; }
.detail-content { font-size: 14px; line-height: 1.7; color: $text-primary; min-height: 100px; }
.detail-attachments { margin-top: 20px; padding-top: 16px; border-top: 1px solid $bg-light;
  h4 { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
}
.attachment-item { display: flex; align-items: center; gap: 6px; padding: 6px 10px; font-size: 13px; color: $primary; cursor: pointer; border-radius: $radius-sm;
  &:hover { background: #e8f0fe; }
  .file-size { color: $text-muted; font-size: 11px; }
}

.form-label { font-size: 13px; font-weight: 600; display: block; margin-bottom: 4px; }
.text-center { text-align: center; }
</style>
