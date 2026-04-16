<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>비정형데이터관리</h2>
      <p class="page-desc">매뉴얼, 절차서, 연보, 지침 등 비정형 문서를 등록하고 온톨로지 활용 현황을 조회합니다.</p>
    </div>

    <!-- KPI 카드 -->
    <div class="stat-cards">
      <div class="stat-card" v-for="s in statCards" :key="s.label">
        <div class="stat-icon" :style="{ background: s.color }"><component :is="s.icon" /></div>
        <div class="stat-info"><span class="stat-value">{{ s.value }}</span><span class="stat-label">{{ s.label }}</span></div>
      </div>
    </div>

    <!-- 검색/필터 -->
    <div class="search-filter">
      <div class="filter-row">
        <div class="filter-group">
          <label>문서유형</label>
          <select v-model="filterType">
            <option value="">전체</option>
            <option value="MANUAL">매뉴얼</option>
            <option value="PROCEDURE">절차서</option>
            <option value="YEARBOOK">연보</option>
            <option value="GUIDELINE">지침</option>
            <option value="OTHER">기타</option>
          </select>
        </div>
        <div class="filter-group">
          <label>처리상태</label>
          <select v-model="filterStatus">
            <option value="">전체</option>
            <option value="PENDING">대기</option>
            <option value="PROCESSING">처리중</option>
            <option value="COMPLETED">완료</option>
            <option value="FAILED">실패</option>
          </select>
        </div>
        <div class="filter-group search-group">
          <label>검색</label>
          <input v-model="searchKeyword" placeholder="문서명 검색" @keyup.enter="fetchList" />
        </div>
        <div class="filter-actions">
          <button class="btn btn-primary" @click="fetchList"><SearchOutlined /> 조회</button>
        </div>
      </div>
    </div>

    <!-- 테이블 -->
    <div class="table-section">
      <div class="table-header">
        <span class="table-count">전체 <strong>{{ totalCount }}</strong>건</span>
        <div class="table-actions">
          <button class="btn btn-success" @click="openRegModal"><PlusOutlined /> 문서 등록</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="handleExportExcel"><FileExcelOutlined /></button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue
          class="ag-theme-alpine"
          :rowData="rows"
          :columnDefs="cols"
          :defaultColDef="defaultColDef"
          :pagination="true"
          :paginationPageSize="20"
          domLayout="autoHeight"
          :tooltipShowDelay="0"
          @row-clicked="onRowClick"
        />
      </div>
    </div>

    <!-- 등록 모달 -->
    <AdminModal :visible="regVisible" title="비정형 문서 등록" size="md" @close="regVisible = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">문서명</label>
          <input v-model="regForm.doc_name" placeholder="문서명 입력" />
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">문서유형</label>
            <select v-model="regForm.doc_type">
              <option value="MANUAL">매뉴얼</option>
              <option value="PROCEDURE">절차서</option>
              <option value="YEARBOOK">연보</option>
              <option value="GUIDELINE">지침</option>
              <option value="OTHER">기타</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>태그</label>
            <input v-model="regForm.tags" placeholder="콤마 구분 (예: 수도,관로)" />
          </div>
        </div>
        <div class="modal-form-group">
          <label>파일</label>
          <input type="file" @change="onFileChange" />
        </div>
        <div class="modal-form-group">
          <label>설명</label>
          <textarea v-model="regForm.description" rows="3" placeholder="문서 설명"></textarea>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="regVisible = false">취소</button>
      </template>
    </AdminModal>

    <!-- 상세 모달 -->
    <AdminModal :visible="detailVisible" :title="detailDoc?.doc_name || '문서 상세'" size="lg" @close="detailVisible = false">
      <template v-if="detailDoc">
        <div class="modal-section">
          <div class="modal-section-title">문서 정보</div>
          <div class="modal-info-grid">
            <div class="modal-info-item"><span class="info-label">문서명</span><span class="info-value">{{ detailDoc.doc_name }}</span></div>
            <div class="modal-info-item"><span class="info-label">유형</span><span class="info-value">{{ typeLabel(detailDoc.doc_type) }}</span></div>
            <div class="modal-info-item"><span class="info-label">파일명</span><span class="info-value">{{ detailDoc.file_name || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">파일크기</span><span class="info-value">{{ formatSize(detailDoc.file_size) }}</span></div>
            <div class="modal-info-item">
              <span class="info-label">처리상태</span>
              <span class="info-value"><span class="badge" :class="statusBadge(detailDoc.processing_status)">{{ statusLabel(detailDoc.processing_status) }}</span></span>
            </div>
            <div class="modal-info-item"><span class="info-label">업로드일시</span><span class="info-value">{{ detailDoc.uploaded_at?.replace('T', ' ').substring(0, 19) || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">업로드자</span><span class="info-value">{{ detailDoc.created_by_name || '-' }}</span></div>
            <div class="modal-info-item"><span class="info-label">추출엔티티</span><span class="info-value">{{ detailDoc.extracted_entity_count }}개</span></div>
            <div class="modal-info-item"><span class="info-label">그래프노드</span><span class="info-value">{{ detailDoc.graph_node_count }}개</span></div>
            <div class="modal-info-item">
              <span class="info-label">그래프통합</span>
              <span class="info-value"><span class="badge" :class="detailDoc.graph_integrated ? 'badge-success' : 'badge-secondary'">{{ detailDoc.graph_integrated ? '통합완료' : '미통합' }}</span></span>
            </div>
            <div class="modal-info-item"><span class="info-label">태그</span><span class="info-value">{{ (detailDoc.tags || []).join(', ') || '-' }}</span></div>
          </div>
        </div>
        <div class="modal-section" v-if="detailDoc.description">
          <div class="modal-section-title">설명</div>
          <p style="font-size:13px;color:#555;margin:0">{{ detailDoc.description }}</p>
        </div>

        <!-- 파일 미리보기 -->
        <div class="modal-section" v-if="detailDoc.file_name">
          <div class="modal-section-title">
            파일 미리보기
            <button v-if="!previewUrl && canPreview(detailDoc)" class="btn btn-sm btn-outline" style="margin-left:8px;font-size:11px;padding:2px 10px" @click="loadPreview"><EyeOutlined /> 미리보기</button>
            <button v-if="previewUrl" class="btn btn-sm btn-outline" style="margin-left:8px;font-size:11px;padding:2px 10px" @click="closePreview"><CloseCircleOutlined /> 닫기</button>
          </div>
          <div v-if="previewLoading" style="text-align:center;padding:30px;color:#999"><SyncOutlined spin /> 파일 로드 중...</div>
          <div v-else-if="previewUrl" class="preview-area">
            <!-- PDF -->
            <iframe v-if="isPdf(detailDoc)" :src="previewUrl" class="preview-pdf" />
            <!-- 이미지 -->
            <img v-else-if="isImage(detailDoc)" :src="previewUrl" class="preview-img" />
            <!-- 텍스트 -->
            <pre v-else-if="isText(detailDoc)" class="preview-text">{{ previewText }}</pre>
          </div>
          <p v-else-if="!canPreview(detailDoc)" style="color:#999;font-size:12px;padding:8px 0">
            <FileTextOutlined /> {{ detailDoc.content_type || detailDoc.file_name }} — 미리보기를 지원하지 않는 형식입니다. 다운로드 후 확인하세요.
          </p>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">온톨로지 활용현황 ({{ (detailDoc.ontology_usages || []).length }}건)</div>
          <table class="modal-table" v-if="(detailDoc.ontology_usages || []).length">
            <thead><tr><th>온톨로지 클래스</th><th>엔티티수</th><th>관계수</th><th>동기화일시</th><th>검토상태</th><th>검토자</th></tr></thead>
            <tbody>
              <tr v-for="u in detailDoc.ontology_usages" :key="u.id" class="clickable-row" @click="openOntologyDetail(u)">
                <td>{{ u.ontology_class }}</td>
                <td class="text-center">{{ u.entity_count }}</td>
                <td class="text-center">{{ u.relation_count }}</td>
                <td class="text-center">{{ u.last_synced_at?.substring(0, 10) || '-' }}</td>
                <td class="text-center"><span class="badge" :class="reviewBadge(u.review_status)">{{ reviewLabel(u.review_status) }}</span></td>
                <td class="text-center">{{ u.reviewed_by_name || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else style="color:#999;font-size:13px;text-align:center;padding:16px 0">온톨로지 활용 데이터 없음</p>
        </div>
      </template>
      <template #footer>
        <button class="btn btn-outline" @click="handleDownload" :disabled="!detailDoc?.file_name"><DownloadOutlined /> 다운로드</button>
        <button class="btn btn-primary" @click="openEditModal"><EditOutlined /> 수정</button>
        <button class="btn btn-danger" @click="handleDelete"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="detailVisible = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 온톨로지 활용 상세 모달 -->
    <AdminModal :visible="ontoDetailVisible" :title="'온톨로지 클래스: ' + (ontoDetail?.ontology_class || '')" size="lg" @close="ontoDetailVisible = false">
      <template v-if="ontoDetail">
        <div class="modal-section">
          <div class="modal-section-title">추출 엔티티 ({{ ontoDetail.entities?.length || 0 }}건)</div>
          <table class="modal-table">
            <thead><tr><th>엔티티명</th><th>유형</th><th>문서 내 위치</th><th>신뢰도</th></tr></thead>
            <tbody>
              <tr v-for="(e, i) in ontoDetail.entities" :key="i">
                <td><strong>{{ e.name }}</strong></td>
                <td class="text-center"><span class="badge badge-info">{{ e.type }}</span></td>
                <td style="color:#666;font-size:12px">{{ e.source }}</td>
                <td class="text-center">{{ e.confidence }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="modal-section">
          <div class="modal-section-title">도출된 관계 ({{ ontoDetail.relations?.length || 0 }}건)</div>
          <table class="modal-table">
            <thead><tr><th>소스 엔티티</th><th>관계 유형</th><th>대상 엔티티</th><th>근거</th></tr></thead>
            <tbody>
              <tr v-for="(r, i) in ontoDetail.relations" :key="i">
                <td><strong>{{ r.source }}</strong></td>
                <td class="text-center"><span class="badge badge-relation">{{ r.relation }}</span></td>
                <td><strong>{{ r.target }}</strong></td>
                <td style="color:#666;font-size:12px">{{ r.evidence }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- 검토 영역 -->
        <div class="modal-section review-section">
          <div class="modal-section-title">검토</div>
          <div v-if="ontoDetail.review_status === 'APPROVED'" class="review-result">
            <span class="badge badge-success">승인완료</span>
            <span v-if="ontoDetail.reviewed_by_name" style="margin-left:8px;color:#666;font-size:12px">{{ ontoDetail.reviewed_by_name }} ({{ ontoDetail.reviewed_at?.substring(0,10) }})</span>
            <p v-if="ontoDetail.review_comment" style="margin:8px 0 0;color:#555;font-size:13px">{{ ontoDetail.review_comment }}</p>
          </div>
          <div v-else-if="ontoDetail.review_status === 'REJECTED'" class="review-result">
            <span class="badge badge-danger">반려됨</span>
            <span v-if="ontoDetail.reviewed_by_name" style="margin-left:8px;color:#666;font-size:12px">{{ ontoDetail.reviewed_by_name }} ({{ ontoDetail.reviewed_at?.substring(0,10) }})</span>
            <p v-if="ontoDetail.review_comment" style="margin:8px 0 0;color:#555;font-size:13px">사유: {{ ontoDetail.review_comment }}</p>
          </div>
          <div v-else>
            <div class="modal-form-group" style="margin-bottom:0">
              <label>검토의견</label>
              <textarea v-model="reviewComment" rows="2" placeholder="승인 또는 반려 사유를 입력하세요 (선택)"></textarea>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <template v-if="ontoDetail && ontoDetail.review_status !== 'APPROVED' && ontoDetail.review_status !== 'REJECTED'">
          <button class="btn btn-success" @click="handleApproveUsage"><CheckCircleOutlined /> 승인 (운영 반영)</button>
          <button class="btn btn-danger" @click="handleRejectUsage"><CloseCircleOutlined /> 반려</button>
        </template>
        <button class="btn btn-outline" @click="ontoDetailVisible = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 수정 모달 -->
    <AdminModal :visible="editVisible" title="비정형 문서 수정" size="md" @close="editVisible = false">
      <div class="modal-form">
        <div class="modal-form-group">
          <label class="required">문서명</label>
          <input v-model="editForm.doc_name" />
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label>문서유형</label>
            <select v-model="editForm.doc_type">
              <option value="MANUAL">매뉴얼</option>
              <option value="PROCEDURE">절차서</option>
              <option value="YEARBOOK">연보</option>
              <option value="GUIDELINE">지침</option>
              <option value="OTHER">기타</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>태그</label>
            <input v-model="editForm.tags" placeholder="콤마 구분" />
          </div>
        </div>
        <div class="modal-form-group">
          <label>파일 교체</label>
          <input type="file" ref="editFileRef" />
        </div>
        <div class="modal-form-group">
          <label>설명</label>
          <textarea v-model="editForm.description" rows="3"></textarea>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleUpdate"><SaveOutlined /> 저장</button>
        <button class="btn btn-outline" @click="editVisible = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import { ref, reactive, onMounted, type Component } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import {
  FileTextOutlined, CheckCircleOutlined, SyncOutlined, ClockCircleOutlined,
  PlusOutlined, FileExcelOutlined, SaveOutlined, EditOutlined, DeleteOutlined,
  DownloadOutlined, SearchOutlined, EyeOutlined, CloseCircleOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

// --- state ---
const summary = reactive({ total: 0, completed: 0, processing: 0, pending: 0, failed: 0 })
const rows = ref<any[]>([])
const totalCount = ref(0)
const filterType = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')

const regVisible = ref(false)
const regForm = reactive({ doc_name: '', doc_type: 'MANUAL', description: '', tags: '' })
let selectedFile: File | null = null

const detailVisible = ref(false)
const detailDoc = ref<any>(null)

const editVisible = ref(false)
const editForm = reactive({ doc_name: '', doc_type: '', description: '', tags: '' })
const editFileRef = ref<HTMLInputElement | null>(null)

// --- KPI ---
const statCards = ref<{ icon: Component; label: string; value: number; color: string }[]>([
  { icon: FileTextOutlined, label: '총 문서', value: 0, color: '#0066CC' },
  { icon: CheckCircleOutlined, label: '처리완료', value: 0, color: '#28A745' },
  { icon: SyncOutlined, label: '처리중', value: 0, color: '#FFC107' },
  { icon: ClockCircleOutlined, label: '대기/실패', value: 0, color: '#DC3545' },
])

// --- columns ---
const defaultColDef = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.3, minWidth: 50 },
  { headerName: '문서명', field: 'doc_name', flex: 2, minWidth: 200 },
  { headerName: '유형', field: 'doc_type', flex: 0.6, minWidth: 80, valueFormatter: (p: any) => typeLabel(p.value) },
  { headerName: '파일크기', field: 'file_size', flex: 0.6, minWidth: 80, valueFormatter: (p: any) => formatSize(p.value) },
  { headerName: '업로드일', field: 'uploaded_at', flex: 0.8, minWidth: 100, valueFormatter: (p: any) => p.value?.substring(0, 10) || '-' },
  { headerName: '처리상태', field: 'processing_status', flex: 0.6, minWidth: 80, cellRenderer: (p: any) => {
    const cls: Record<string, string> = { COMPLETED: 'badge-success', PROCESSING: 'badge-warning', PENDING: 'badge-secondary', FAILED: 'badge-danger' }
    return `<span class="badge ${cls[p.value] || ''}">${statusLabel(p.value)}</span>`
  }},
  { headerName: '추출엔티티', field: 'extracted_entity_count', flex: 0.5, minWidth: 80, type: 'numericColumn' },
  { headerName: '그래프통합', field: 'graph_integrated', flex: 0.5, minWidth: 80, cellRenderer: (p: any) =>
    p.value ? '<span class="badge badge-success">통합</span>' : '<span class="badge badge-secondary">미통합</span>'
  },
  { headerName: '검토', field: 'review_status', flex: 0.6, minWidth: 80, cellRenderer: (p: any) => {
    const cls: Record<string, string> = { ALL_APPROVED: 'badge-success', PARTIALLY_APPROVED: 'badge-info', PENDING_REVIEW: 'badge-warning', ALL_REJECTED: 'badge-danger' }
    const lbl: Record<string, string> = { ALL_APPROVED: '전체승인', PARTIALLY_APPROVED: '부분승인', PENDING_REVIEW: '검토대기', ALL_REJECTED: '전체반려' }
    const v = p.value || 'PENDING_REVIEW'
    return `<span class="badge ${cls[v] || 'badge-warning'}">${lbl[v] || v}</span>`
  }},
])

// --- helpers ---
function typeLabel(t: string) {
  return ({ MANUAL: '매뉴얼', PROCEDURE: '절차서', YEARBOOK: '연보', GUIDELINE: '지침', OTHER: '기타' } as any)[t] || t
}
function statusLabel(s: string) {
  return ({ PENDING: '대기', PROCESSING: '처리중', COMPLETED: '완료', FAILED: '실패' } as any)[s] || s
}
function statusBadge(s: string) {
  return ({ COMPLETED: 'badge-success', PROCESSING: 'badge-warning', PENDING: 'badge-secondary', FAILED: 'badge-danger' } as any)[s] || ''
}
function reviewLabel(s: string) {
  return ({ PENDING_REVIEW: '검토대기', APPROVED: '승인', REJECTED: '반려', REVISED: '수정요청' } as any)[s] || s || '검토대기'
}
function reviewBadge(s: string) {
  return ({ PENDING_REVIEW: 'badge-warning', APPROVED: 'badge-success', REJECTED: 'badge-danger', REVISED: 'badge-info' } as any)[s] || 'badge-warning'
}
function formatSize(bytes: number | null) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// --- fetch ---
async function fetchSummary() {
  try {
    const res = await adminCollectionApi.unstructuredDocSummary()
    const d = res.data?.data || res.data
    summary.total = d.total || 0
    summary.completed = d.completed || 0
    summary.processing = d.processing || 0
    summary.pending = d.pending || 0
    summary.failed = d.failed || 0
    statCards.value = [
      { icon: FileTextOutlined, label: '총 문서', value: summary.total, color: '#0066CC' },
      { icon: CheckCircleOutlined, label: '처리완료', value: summary.completed, color: '#28A745' },
      { icon: SyncOutlined, label: '처리중', value: summary.processing, color: '#FFC107' },
      { icon: ClockCircleOutlined, label: '대기/실패', value: summary.pending + summary.failed, color: '#DC3545' },
    ]
  } catch { /* ignore */ }
}

async function fetchList() {
  try {
    const params: any = { page: 1, page_size: 100 }
    if (filterType.value) params.doc_type = filterType.value
    if (filterStatus.value) params.processing_status = filterStatus.value
    if (searchKeyword.value) params.search = searchKeyword.value
    const res = await adminCollectionApi.unstructuredDocs(params)
    const data = res.data
    rows.value = data?.items || []
    totalCount.value = data?.total || 0
  } catch {
    rows.value = []
    totalCount.value = 0
  }
}

// --- register ---
function openRegModal() {
  regForm.doc_name = ''; regForm.doc_type = 'MANUAL'; regForm.description = ''; regForm.tags = ''
  selectedFile = null
  regVisible.value = true
}
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile = input.files?.[0] || null
}
async function handleRegister() {
  if (!regForm.doc_name) { message.warning('문서명을 입력하세요.'); return }
  try {
    const fd = new FormData()
    fd.append('doc_name', regForm.doc_name)
    fd.append('doc_type', regForm.doc_type)
    fd.append('description', regForm.description)
    if (regForm.tags) fd.append('tags', regForm.tags)
    if (selectedFile) fd.append('file', selectedFile)
    await adminCollectionApi.createUnstructuredDoc(fd)
    message.success('문서가 등록되었습니다.')
    regVisible.value = false
    fetchSummary(); fetchList()
  } catch { message.error('등록 실패') }
}

// --- ontology detail (Mock) ---
const ontoDetailVisible = ref(false)
const ontoDetail = ref<any>(null)
const reviewComment = ref('')

const mockEntityMap: Record<string, { entities: any[]; relations: any[] }> = {
  WaterFacility: {
    entities: [
      { name: '소양강댐', type: 'Dam', source: '3장 2절 "소양강댐 현황" (p.42)', confidence: 96 },
      { name: '충주댐', type: 'Dam', source: '3장 2절 "충주댐 운영현황" (p.58)', confidence: 94 },
      { name: '화북정수장', type: 'WaterPlant', source: '4장 1절 "정수시설 목록" (p.81)', confidence: 92 },
      { name: '가압펌프 P-201', type: 'Equipment', source: '5장 "주요 설비 사양" (p.105)', confidence: 88 },
      { name: '송수관로 L-12', type: 'Pipeline', source: '6장 "관로 현황표" (p.132)', confidence: 91 },
    ],
    relations: [
      { source: '소양강댐', relation: 'hasEquipment', target: '수문설비 G-01', evidence: '3장 "댐 수문설비 배치도" (p.45)' },
      { source: '화북정수장', relation: 'connectedTo', target: '송수관로 L-12', evidence: '6장 "관로 연결도" (p.134)' },
      { source: '가압펌프 P-201', relation: 'locatedIn', target: '화북정수장', evidence: '5장 "설비 배치" (p.108)' },
      { source: '충주댐', relation: 'supplies', target: '화북정수장', evidence: '4장 "원수 공급 계통도" (p.83)' },
    ]
  },
  PipelineNetwork: {
    entities: [
      { name: '송수관로 L-12', type: 'Pipeline', source: '6장 "관로 현황표" (p.132)', confidence: 95 },
      { name: '배수관로 D-45', type: 'Pipeline', source: '6장 "배수관 목록" (p.145)', confidence: 93 },
      { name: '밸브 V-078', type: 'Valve', source: '7장 "밸브 설치 현황" (p.162)', confidence: 89 },
      { name: '수압계 M-23', type: 'Sensor', source: '7장 "계측기 배치" (p.170)', confidence: 87 },
    ],
    relations: [
      { source: '송수관로 L-12', relation: 'hasValve', target: '밸브 V-078', evidence: '7장 "관로-밸브 연결도" (p.165)' },
      { source: '배수관로 D-45', relation: 'monitoredBy', target: '수압계 M-23', evidence: '7장 "계측 배치도" (p.172)' },
      { source: '송수관로 L-12', relation: 'feeds', target: '배수관로 D-45', evidence: '6장 "관로 계통도" (p.138)' },
    ]
  },
  OperationProcess: {
    entities: [
      { name: '일상점검 프로세스', type: 'Process', source: '8장 1절 "점검 절차" (p.201)', confidence: 94 },
      { name: '비상대응 절차', type: 'Process', source: '9장 "비상 운영" (p.245)', confidence: 92 },
      { name: '수질검사 주기', type: 'Schedule', source: '4장 3절 "검사 일정" (p.92)', confidence: 90 },
    ],
    relations: [
      { source: '일상점검 프로세스', relation: 'appliesTo', target: '화북정수장', evidence: '8장 "점검 대상 시설" (p.203)' },
      { source: '비상대응 절차', relation: 'triggers', target: '수질이상 이벤트', evidence: '9장 "비상 발령 기준" (p.248)' },
    ]
  },
  WaterQuality: {
    entities: [
      { name: '탁도 기준값', type: 'Standard', source: '2장 "수질 기준표" (p.15)', confidence: 97 },
      { name: 'pH 측정점 Q-05', type: 'SensorPoint', source: '3장 "측정 위치도" (p.38)', confidence: 91 },
      { name: '잔류염소 기준', type: 'Standard', source: '2장 "음용수 기준" (p.18)', confidence: 95 },
    ],
    relations: [
      { source: 'pH 측정점 Q-05', relation: 'measures', target: '탁도 기준값', evidence: '3장 "측정항목 매핑" (p.40)' },
      { source: '잔류염소 기준', relation: 'regulatedBy', target: '먹는물수질기준', evidence: '2장 "법적 근거" (p.12)' },
    ]
  },
  TestProcedure: {
    entities: [
      { name: '수질시료 채취 절차', type: 'Procedure', source: '1장 "시료 채취법" (p.5)', confidence: 96 },
      { name: '미생물 검사 프로토콜', type: 'Protocol', source: '4장 "미생물 시험" (p.55)', confidence: 93 },
    ],
    relations: [
      { source: '수질시료 채취 절차', relation: 'precedes', target: '미생물 검사 프로토콜', evidence: '1장 "검사 흐름도" (p.8)' },
    ]
  },
  HydroObservation: {
    entities: [
      { name: '소양강 수위관측소', type: 'Station', source: '2장 "관측소 현황" (p.22)', confidence: 95 },
      { name: '낙동강 유량관측소', type: 'Station', source: '2장 "관측소 현황" (p.28)', confidence: 94 },
      { name: '강수량 센서 R-12', type: 'Sensor', source: '3장 "기상 관측" (p.45)', confidence: 90 },
      { name: '연평균 강수량 1,274mm', type: 'Statistic', source: '5장 "기후 통계" (p.88)', confidence: 98 },
    ],
    relations: [
      { source: '소양강 수위관측소', relation: 'locatedAt', target: '소양강댐', evidence: '2장 "관측소 위치도" (p.25)' },
      { source: '강수량 센서 R-12', relation: 'installedAt', target: '소양강 수위관측소', evidence: '3장 "센서 배치" (p.48)' },
      { source: '낙동강 유량관측소', relation: 'monitors', target: '낙동강 본류', evidence: '2장 "관측 대상" (p.30)' },
    ]
  },
  HydroPower: {
    entities: [
      { name: '소양강 수력발전소', type: 'PowerPlant', source: '1장 "발전소 현황" (p.8)', confidence: 97 },
      { name: '터빈 T-01', type: 'Turbine', source: '3장 "발전설비" (p.42)', confidence: 94 },
      { name: '발전량 125MW', type: 'Capacity', source: '1장 "설비 용량" (p.10)', confidence: 96 },
    ],
    relations: [
      { source: '소양강 수력발전소', relation: 'hasTurbine', target: '터빈 T-01', evidence: '3장 "터빈 배치도" (p.44)' },
      { source: '터빈 T-01', relation: 'generates', target: '발전량 125MW', evidence: '3장 "발전 성능" (p.46)' },
    ]
  },
  CustomerBilling: {
    entities: [
      { name: '가정용 요금체계', type: 'TariffPlan', source: '8장 "요금 구조" (p.156)', confidence: 93 },
      { name: '산업용 요금체계', type: 'TariffPlan', source: '8장 "산업용 단가" (p.162)', confidence: 91 },
    ],
    relations: [
      { source: '가정용 요금체계', relation: 'appliesTo', target: '일반 가정 수용가', evidence: '8장 "적용 대상" (p.158)' },
    ]
  },
  Statistics: {
    entities: [
      { name: '2025년 총급수량', type: 'Statistic', source: '1장 "연간 실적" (p.3)', confidence: 98 },
      { name: '누수율 8.2%', type: 'KPI', source: '7장 "손실 분석" (p.142)', confidence: 96 },
    ],
    relations: [
      { source: '2025년 총급수량', relation: 'measuredFor', target: '전국 광역상수도', evidence: '1장 "급수 범위" (p.5)' },
    ]
  },
  DataQuality: {
    entities: [
      { name: '완전성 검증 규칙', type: 'QualityRule', source: '2장 "품질 규칙" (p.15)', confidence: 95 },
      { name: '유효성 검증 규칙', type: 'QualityRule', source: '2장 "유효값 범위" (p.22)', confidence: 93 },
      { name: '정합성 체크', type: 'QualityRule', source: '3장 "교차 검증" (p.35)', confidence: 91 },
    ],
    relations: [
      { source: '완전성 검증 규칙', relation: 'validates', target: '수집 데이터셋', evidence: '2장 "적용 대상" (p.18)' },
      { source: '유효성 검증 규칙', relation: 'detects', target: '이상치 데이터', evidence: '2장 "이상치 판별" (p.25)' },
    ]
  },
  EmergencyResponse: {
    entities: [
      { name: '비상급수차 배치', type: 'Resource', source: '1장 "비상 자원" (p.5)', confidence: 94 },
      { name: '대체 수원 확보', type: 'Action', source: '2장 "대응 절차" (p.18)', confidence: 92 },
    ],
    relations: [
      { source: '비상급수차 배치', relation: 'activatedBy', target: '단수 발생 이벤트', evidence: '1장 "발동 조건" (p.8)' },
      { source: '대체 수원 확보', relation: 'follows', target: '비상급수차 배치', evidence: '2장 "단계별 대응" (p.20)' },
    ]
  },
}

// --- approve / reject ---
async function handleApproveUsage() {
  if (!detailDoc.value?.id || !ontoDetail.value?.usage_id) return
  try {
    await adminCollectionApi.approveOntologyUsage(detailDoc.value.id, ontoDetail.value.usage_id, reviewComment.value || undefined)
    message.success('승인되었습니다. 운영 그래프에 반영됩니다.')
    ontoDetail.value.review_status = 'APPROVED'
    // 상세 새로고침
    const res = await adminCollectionApi.getUnstructuredDoc(detailDoc.value.id)
    detailDoc.value = res.data?.data || res.data
    fetchSummary(); fetchList()
  } catch { message.error('승인 처리 실패') }
}
async function handleRejectUsage() {
  if (!detailDoc.value?.id || !ontoDetail.value?.usage_id) return
  if (!reviewComment.value) { message.warning('반려 사유를 입력하세요.'); return }
  try {
    await adminCollectionApi.rejectOntologyUsage(detailDoc.value.id, ontoDetail.value.usage_id, reviewComment.value)
    message.success('반려되었습니다.')
    ontoDetail.value.review_status = 'REJECTED'
    const res = await adminCollectionApi.getUnstructuredDoc(detailDoc.value.id)
    detailDoc.value = res.data?.data || res.data
    fetchSummary(); fetchList()
  } catch { message.error('반려 처리 실패') }
}

function openOntologyDetail(usage: any) {
  reviewComment.value = ''
  const cls = usage.ontology_class
  const mock = mockEntityMap[cls]
  if (mock) {
    ontoDetail.value = { ontology_class: cls, usage_id: usage.id, review_status: usage.review_status, reviewed_by_name: usage.reviewed_by_name, reviewed_at: usage.reviewed_at, review_comment: usage.review_comment, ...mock }
  } else {
    ontoDetail.value = {
      ontology_class: cls, usage_id: usage.id, review_status: usage.review_status, reviewed_by_name: usage.reviewed_by_name, reviewed_at: usage.reviewed_at, review_comment: usage.review_comment,
      entities: Array.from({ length: usage.entity_count > 5 ? 5 : usage.entity_count }, (_, i) => ({
        name: `${cls}_Entity_${i + 1}`, type: 'Concept', source: `문서 내 추출 (섹션 ${i + 1})`, confidence: 85 + Math.floor(Math.random() * 10),
      })),
      relations: Array.from({ length: usage.relation_count > 4 ? 4 : usage.relation_count }, (_, i) => ({
        source: `${cls}_Entity_${i + 1}`, relation: 'relatedTo', target: `${cls}_Entity_${i + 2}`, evidence: `자동 추출 관계 (p.${10 + i * 5})`,
      })),
    }
  }
  ontoDetailVisible.value = true
}

// --- preview ---
const previewUrl = ref<string | null>(null)
const previewText = ref('')
const previewLoading = ref(false)

function canPreview(doc: any): boolean {
  return isPdf(doc) || isImage(doc) || isText(doc)
}
function isPdf(doc: any): boolean {
  return doc?.content_type === 'application/pdf' || doc?.file_name?.toLowerCase().endsWith('.pdf')
}
function isImage(doc: any): boolean {
  const ct = doc?.content_type || ''
  const fn = doc?.file_name?.toLowerCase() || ''
  return ct.startsWith('image/') || /\.(jpg|jpeg|png|gif|bmp|webp|svg)$/.test(fn)
}
function isText(doc: any): boolean {
  const ct = doc?.content_type || ''
  const fn = doc?.file_name?.toLowerCase() || ''
  return ct.startsWith('text/') || /\.(txt|csv|log|md|json|xml|yml|yaml)$/.test(fn)
}
async function loadPreview() {
  if (!detailDoc.value?.id) return
  previewLoading.value = true
  previewUrl.value = null
  previewText.value = ''
  try {
    const res = await adminCollectionApi.downloadUnstructuredDoc(detailDoc.value.id)
    const blob = new Blob([res.data], { type: detailDoc.value.content_type || 'application/octet-stream' })
    if (isText(detailDoc.value)) {
      previewText.value = await blob.text()
      previewUrl.value = 'text'
    } else {
      previewUrl.value = window.URL.createObjectURL(blob)
    }
  } catch { message.error('미리보기 로드 실패') }
  finally { previewLoading.value = false }
}
function closePreview() {
  if (previewUrl.value && previewUrl.value !== 'text') window.URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = null
  previewText.value = ''
}

// --- detail ---
async function onRowClick(event: any) {
  const row = event.data
  if (!row?.id) return
  closePreview()
  try {
    const res = await adminCollectionApi.getUnstructuredDoc(String(row.id))
    detailDoc.value = res.data?.data || res.data
    detailVisible.value = true
  } catch (err) {
    console.error('상세 조회 실패', err)
    // fallback: API 호출 실패시 row 데이터로 상세 표시
    detailDoc.value = { ...row, ontology_usages: [] }
    detailVisible.value = true
  }
}

// --- download ---
async function handleDownload() {
  if (!detailDoc.value?.id) return
  try {
    const res = await adminCollectionApi.downloadUnstructuredDoc(detailDoc.value.id)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url; a.download = detailDoc.value.file_name || 'download'; a.click()
    window.URL.revokeObjectURL(url)
  } catch { message.error('다운로드 실패') }
}

// --- edit ---
function openEditModal() {
  if (!detailDoc.value) return
  editForm.doc_name = detailDoc.value.doc_name
  editForm.doc_type = detailDoc.value.doc_type
  editForm.description = detailDoc.value.description || ''
  editForm.tags = (detailDoc.value.tags || []).join(', ')
  editVisible.value = true
}
async function handleUpdate() {
  if (!detailDoc.value?.id) return
  try {
    const fd = new FormData()
    fd.append('doc_name', editForm.doc_name)
    fd.append('doc_type', editForm.doc_type)
    fd.append('description', editForm.description)
    if (editForm.tags) fd.append('tags', editForm.tags)
    const fileEl = editFileRef.value
    if (fileEl?.files?.[0]) fd.append('file', fileEl.files[0])
    await adminCollectionApi.updateUnstructuredDoc(detailDoc.value.id, fd)
    message.success('수정되었습니다.')
    editVisible.value = false; detailVisible.value = false
    fetchSummary(); fetchList()
  } catch { message.error('수정 실패') }
}

// --- delete ---
async function handleDelete() {
  if (!detailDoc.value?.id) return
  if (!confirm('이 문서를 삭제하시겠습니까?')) return
  try {
    await adminCollectionApi.deleteUnstructuredDoc(detailDoc.value.id)
    message.success('삭제되었습니다.')
    detailVisible.value = false
    fetchSummary(); fetchList()
  } catch { message.error('삭제 실패') }
}

// --- excel ---
function handleExportExcel() {
  exportGridToExcel(cols, rows.value, '비정형데이터목록')
}

onMounted(() => { fetchSummary(); fetchList() })
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *;
@use '../admin-common.scss';

.modal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  th, td { padding: 8px 12px; border: 1px solid #e5e7eb; }
  th { background: #f8f9fa; font-weight: 600; color: #555; text-align: center; }
  .text-center { text-align: center; }
}
.clickable-row { cursor: pointer; transition: background .15s; &:hover { background: #f0f7ff; } }
.review-section { background: #fafbfc; border-radius: 8px; padding: 12px 16px; }
.review-result { display: flex; align-items: center; flex-wrap: wrap; }
.badge-info { background: #e8f4fd; color: #0066CC; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
.badge-relation { background: #fff3e0; color: #e65100; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.preview-area { border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; margin-top: 8px; background: #fafafa; }
.preview-pdf { width: 100%; height: 500px; border: none; }
.preview-img { max-width: 100%; max-height: 500px; display: block; margin: 0 auto; padding: 12px; }
.preview-text { max-height: 400px; overflow: auto; padding: 16px; margin: 0; font-size: 12px; line-height: 1.6; background: #f8f9fa; white-space: pre-wrap; word-break: break-all; }
</style>
