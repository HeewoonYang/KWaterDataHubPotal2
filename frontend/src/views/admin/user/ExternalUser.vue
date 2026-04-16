<template>
  <div class="admin-page">
    <div class="page-header"><h2>외부 사용자</h2><p class="page-desc">외부 기관 사용자 계정을 관리합니다.</p></div>
    <div class="search-filter"><div class="filter-row">
      <div class="filter-group"><label>기관</label><select><option value="">전체</option><option>환경부</option><option>기상청</option><option>국토부</option></select></div>
      <div class="filter-group"><label>상태</label><select><option value="">전체</option><option>활성</option><option>대기</option><option>만료</option></select></div>
      <div class="filter-group search-group"><label>검색</label><input placeholder="이름/기관 검색" /></div>
      <div class="filter-actions"><button class="btn btn-primary btn-sm">조회</button></div>
    </div></div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">외부 사용자 <strong>{{ rows.length }}</strong>건</span><div class="table-actions"><button class="btn btn-primary btn-sm" @click="showRegister = true"><PlusOutlined /> 등록</button><button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(cols, rows, '외부_사용자')"><FileExcelOutlined /></button></div></div>
      <div class="ag-grid-wrapper"><AgGridVue class="ag-theme-alpine" :rowData="rows" :columnDefs="cols" :defaultColDef="defCol" :tooltipShowDelay="0" :pagination="true" :paginationPageSize="10" domLayout="autoHeight" @row-clicked="onRowClick" /></div>
    </div>

    <!-- 외부 사용자 상세 팝업 -->
    <AdminModal :visible="showDetail" :title="detailData.name + ' 사용자 상세'" size="lg" @close="showDetail = false">
      <div class="modal-section">
        <div class="modal-section-title">기본 정보</div>
        <div class="modal-info-grid">
          <div class="modal-info-item"><span class="info-label">이름</span><span class="info-value">{{ detailData.name }}</span></div>
          <div class="modal-info-item"><span class="info-label">기관</span><span class="info-value">{{ detailData.org }}</span></div>
          <div class="modal-info-item"><span class="info-label">이메일</span><span class="info-value">{{ detailData.email }}</span></div>
          <div class="modal-info-item"><span class="info-label">권한</span><span class="info-value">{{ detailData.role }}</span></div>
          <div class="modal-info-item"><span class="info-label">가입일</span><span class="info-value">{{ detailData.joinDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">만료일</span><span class="info-value">{{ detailData.expireDate }}</span></div>
          <div class="modal-info-item"><span class="info-label">상태</span><span class="info-value"><span class="badge" :class="detailData.status === '활성' ? 'badge-success' : detailData.status === '대기' ? 'badge-warning' : 'badge-muted'">{{ detailData.status }}</span></span></div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="showDetail = false"><EditOutlined /> 수정</button>
        <button class="btn btn-outline" @click="showDetail = false">닫기</button>
      </template>
    </AdminModal>

    <!-- 외부 사용자 등록 팝업 -->
    <AdminModal :visible="showRegister" title="외부 사용자 등록" size="md" @close="showRegister = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">아이디</label><input v-model="regForm.login_id" placeholder="로그인 아이디" /></div>
          <div class="modal-form-group"><label class="required">이름</label><input v-model="regForm.name" placeholder="이름 입력" /></div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">기관</label>
            <select v-model="regForm.org">
              <option value="">선택</option>
              <option>환경부</option><option>기상청</option><option>국토부</option><option>한국환경공단</option><option>기타</option>
            </select>
          </div>
          <div class="modal-form-group"><label class="required">휴대폰번호</label><input v-model="regForm.phone" placeholder="010-0000-0000" /></div>
        </div>
        <div class="modal-form-group"><label class="required">이메일</label><input v-model="regForm.email" placeholder="email@example.go.kr" /></div>
        <div class="modal-form-row">
          <div class="modal-form-group"><label class="required">권한</label>
            <select v-model="regForm.role_code">
              <option value="EXTERNAL">외부사용자</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label style="display:flex;align-items:center;gap:6px;">
              <input type="checkbox" v-model="regForm.send_initial_sms" />
              초기 비밀번호 SMS 자동 발송
            </label>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="handleRegister"><SaveOutlined /> 등록</button>
        <button class="btn btn-outline" @click="showRegister = false">취소</button>
      </template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'

import { ref, onMounted } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminUserApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const showDetail = ref(false), showRegister = ref(false)
const detailData = ref<any>({})
const regForm = ref({
  login_id: '',
  name: '',
  org: '',
  phone: '',
  email: '',
  role_code: 'EXTERNAL',
  send_initial_sms: true,
})

function resetRegForm() {
  regForm.value = { login_id: '', name: '', org: '', phone: '', email: '', role_code: 'EXTERNAL', send_initial_sms: true }
}

const defCol = { ...baseDefaultColDef }
const cols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', flex: 0.4, minWidth: 50 },
  { headerName: '이름', field: 'name', flex: 0.8, minWidth: 100 },
  { headerName: '기관', field: 'org', flex: 1 },
  { headerName: '이메일', field: 'email', flex: 1 },
  { headerName: '권한', field: 'role', flex: 0.8, minWidth: 100 },
  { headerName: '가입일', field: 'joinDate', flex: 0.8, minWidth: 110 },
  { headerName: '만료일', field: 'expireDate', flex: 0.8, minWidth: 110 },
  { headerName: '상태', field: 'status', flex: 0.5, minWidth: 70 },
  {
    headerName: '초기PW',
    field: '_actions',
    flex: 0.8,
    minWidth: 120,
    cellRenderer: (params: any) => {
      const btn = document.createElement('button')
      btn.innerText = '초기PW 재발송'
      btn.className = 'btn btn-outline btn-xs'
      btn.addEventListener('click', (ev) => {
        ev.stopPropagation()
        handleResendInitialPw(params.data)
      })
      return btn
    },
  },
])
const rows = ref([
  { name: '이외부', org: '환경부', email: 'lee@me.go.kr', role: '외부사용자', joinDate: '2026-01-15', expireDate: '2026-07-15', status: '활성' },
  { name: '박기상', org: '기상청', email: 'park@kma.go.kr', role: '외부사용자', joinDate: '2026-02-10', expireDate: '2026-08-10', status: '활성' },
  { name: '최국토', org: '국토부', email: 'choi@molit.go.kr', role: '외부사용자', joinDate: '2026-03-01', expireDate: '2026-09-01', status: '대기' },
])


onMounted(async () => {
  try {
    const res = await adminUserApi.users({ user_type: 'EXTERNAL' })
    const items = res.data.items
    if (items && items.length > 0) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        id: r.id,
        name: r.name || '',
        org: r.department_name || r.org || '',
        email: r.email || '',
        role: r.role_code || r.role || '외부사용자',
        joinDate: r.joinDate || '-',
        expireDate: r.expireDate || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'PENDING' ? '대기' : r.status === 'EXPIRED' ? '만료' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('ExternalUser: API call failed, using mock data', e)
  }
})

function onRowClick(event: any) {
  detailData.value = event.data
  showDetail.value = true
}

async function reloadList() {
  try {
    const res = await adminUserApi.users({ user_type: 'EXTERNAL' })
    const items = res.data.items
    if (items) {
      rows.value = items.map((r: any) => ({
        _raw: r,
        id: r.id,
        name: r.name || '',
        org: r.department_name || r.org || '',
        email: r.email || '',
        role: r.role_code || r.role || '외부사용자',
        joinDate: r.joinDate || '-',
        expireDate: r.expireDate || '-',
        status: r.status === 'ACTIVE' ? '활성' : r.status === 'PENDING' ? '대기' : r.status === 'EXPIRED' ? '만료' : (r.status || '-'),
      }))
    }
  } catch (e) {
    console.warn('ExternalUser: reload failed', e)
  }
}

async function handleRegister() {
  const f = regForm.value
  if (!f.login_id || !f.name || !f.org) {
    message.warning('아이디, 이름, 기관은 필수입니다.')
    return
  }
  if (f.send_initial_sms && !f.phone) {
    message.warning('초기 비밀번호 SMS 발송을 위해 휴대폰번호를 입력하세요.')
    return
  }
  try {
    const payload: any = {
      login_id: f.login_id,
      name: f.name,
      email: f.email || null,
      phone: f.phone || null,
      user_type: 'EXTERNAL',
      department_name: f.org,
      org: f.org,
      role_code: f.role_code || 'EXTERNAL',
      send_initial_sms: f.send_initial_sms,
    }
    if (!f.send_initial_sms) {
      payload.password = 'ChangeMe!123'  // 관리자가 별도 전달. 정책: 첫 로그인 후 변경 권고.
    }
    const res = await adminUserApi.createUser(payload)
    message.success(res.data?.message || '등록되었습니다.')
    showRegister.value = false
    resetRegForm()
    await reloadList()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '등록에 실패했습니다.')
  }
}

async function handleResendInitialPw(row: any) {
  const userId = row?._raw?.id || row?.id
  if (!userId) {
    message.warning('사용자 ID를 확인할 수 없습니다.')
    return
  }
  if (!confirm(`${row.name || '대상 사용자'} 에게 초기 비밀번호를 재발송 하시겠습니까?\n기존 세션은 즉시 해제되며, 다음 로그인 시 비밀번호 변경이 강제됩니다.`)) return
  try {
    const res = await adminUserApi.sendInitialPassword(userId)
    message.success(res.data?.message || '초기 비밀번호 SMS를 발송했습니다.')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || 'SMS 발송에 실패했습니다.')
  }
}
</script>
<style lang="scss" scoped>
@use '../admin-common.scss';
:deep(.ag-row) { cursor: pointer; }
:deep(.btn-xs) {
  font-size: 11px;
  padding: 2px 8px;
  line-height: 1.3;
}
</style>
