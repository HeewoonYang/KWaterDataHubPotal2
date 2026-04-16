<template>
  <div class="admin-page">
    <div class="page-header"><h2>SSO 인증 설정</h2><p class="page-desc">SAML 2.0(오아시스) 및 OAuth 2.0 SSO 제공자를 관리합니다.</p></div>

    <!-- SAML 설정 -->
    <div class="card">
      <div class="card-title"><SafetyOutlined /> SAML 2.0 (오아시스 SSO)</div>
      <div class="info-grid">
        <div class="info-row"><span class="info-label">SP Entity ID</span><span class="info-value">{{ samlConfig.sp_entity_id }}</span></div>
        <div class="info-row"><span class="info-label">ACS URL</span><span class="info-value">{{ samlConfig.acs_url }}</span></div>
        <div class="info-row"><span class="info-label">IdP Entity ID</span><span class="info-value">{{ samlConfig.idp_entity_id }}</span></div>
        <div class="info-row"><span class="info-label">IdP SSO URL</span><span class="info-value">{{ samlConfig.idp_sso_url }}</span></div>
        <div class="info-row"><span class="info-label">상태</span><span class="info-value" :style="{color: samlConfig.idp_sso_url ? '#28A745' : '#DC3545'}">{{ samlConfig.idp_sso_url ? '설정됨' : '미설정' }}</span></div>
      </div>
      <div class="card-actions">
        <button class="btn-sm btn-default" @click="openMetadata">
          <FileTextOutlined /> SP 메타데이터 보기
        </button>
      </div>
    </div>

    <!-- OAuth 제공자 목록 -->
    <div class="card" style="margin-top:16px">
      <div class="card-title-row">
        <span class="card-title"><ApiOutlined /> OAuth 2.0 제공자</span>
        <button class="btn-sm btn-primary" @click="showAddModal = true"><PlusOutlined /> 제공자 추가</button>
      </div>
      <table class="data-table">
        <thead><tr><th>제공자명</th><th>유형</th><th>표시명</th><th>기본역할</th><th>사용자유형</th><th>상태</th><th>관리</th></tr></thead>
        <tbody>
          <tr v-for="p in providers" :key="p.id">
            <td class="name-cell">{{ p.provider_name }}</td>
            <td>{{ p.provider_type }}</td>
            <td>{{ p.display_name }}</td>
            <td>{{ p.default_role_code }}</td>
            <td>{{ p.default_user_type }}</td>
            <td><span :class="['status-badge', p.is_enabled ? 'active' : 'inactive']">{{ p.is_enabled ? '활성' : '비활성' }}</span></td>
            <td>
              <button class="btn-sm btn-default" @click="editProvider(p)"><EditOutlined /></button>
              <button class="btn-sm btn-danger" @click="deleteProvider(p)" style="margin-left:4px"><DeleteOutlined /></button>
            </td>
          </tr>
          <tr v-if="providers.length === 0"><td colspan="7" style="text-align:center;color:#999;padding:20px">등록된 OAuth 제공자가 없습니다.</td></tr>
        </tbody>
      </table>
    </div>

    <!-- 추가/수정 모달 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-box">
        <h3>{{ editId ? 'OAuth 제공자 수정' : 'OAuth 제공자 추가' }}</h3>
        <div class="form-grid">
          <div class="form-group"><label>제공자 코드명</label><input v-model="form.provider_name" placeholder="예: azure_ad" /></div>
          <div class="form-group"><label>표시명</label><input v-model="form.display_name" placeholder="예: Azure AD" /></div>
          <div class="form-group"><label>Client ID</label><input v-model="form.client_id" /></div>
          <div class="form-group"><label>Client Secret</label><input v-model="form.client_secret" type="password" /></div>
          <div class="form-group"><label>Authorize URL</label><input v-model="form.authorize_url" /></div>
          <div class="form-group"><label>Token URL</label><input v-model="form.token_url" /></div>
          <div class="form-group"><label>UserInfo URL</label><input v-model="form.userinfo_url" /></div>
          <div class="form-group"><label>기본 역할</label>
            <select v-model="form.default_role_code"><option value="EXTERNAL">외부사용자</option><option value="EMPLOYEE">직원</option></select>
          </div>
          <div class="form-group"><label>활성</label>
            <select v-model="form.is_enabled"><option :value="true">활성</option><option :value="false">비활성</option></select>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-sm btn-primary" @click="saveProvider">저장</button>
          <button class="btn-sm btn-default" @click="showAddModal = false">취소</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { SafetyOutlined, ApiOutlined, FileTextOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import apiClient from '../../../api/client'

const samlConfig = ref({ sp_entity_id: '', acs_url: '', idp_entity_id: '', idp_sso_url: '' })
const providers = ref<any[]>([])
const showAddModal = ref(false)
const editId = ref('')
const form = ref<any>({ provider_name: '', display_name: '', client_id: '', client_secret: '', authorize_url: '', token_url: '', userinfo_url: '', default_role_code: 'EXTERNAL', is_enabled: true })

async function loadProviders() {
  try {
    const r = await apiClient.get('/admin/system/sso-providers')
    providers.value = r.data?.data || []
  } catch {}
}

async function loadSamlConfig() {
  try {
    const r = await apiClient.get('/sso/providers')
    const saml = (r.data?.data || []).find((p: any) => p.provider_type === 'SAML')
    if (saml) {
      samlConfig.value.idp_sso_url = 'https://oasis.kwater.or.kr/idp/sso'
      samlConfig.value.idp_entity_id = 'https://oasis.kwater.or.kr/idp'
    }
    samlConfig.value.sp_entity_id = window.location.origin
    samlConfig.value.acs_url = window.location.origin + '/api/v1/sso/saml/acs'
  } catch {}
}

function editProvider(p: any) {
  editId.value = p.id
  const cfg = p.config_json || {}
  form.value = { provider_name: p.provider_name, display_name: p.display_name, client_id: cfg.client_id || '', client_secret: '', authorize_url: cfg.authorize_url || '', token_url: cfg.token_url || '', userinfo_url: cfg.userinfo_url || '', default_role_code: p.default_role_code || 'EXTERNAL', is_enabled: p.is_enabled }
  showAddModal.value = true
}

async function saveProvider() {
  const data = {
    provider_type: 'OAUTH', provider_name: form.value.provider_name, display_name: form.value.display_name,
    default_role_code: form.value.default_role_code, default_user_type: form.value.default_role_code === 'EMPLOYEE' ? 'INTERNAL' : 'EXTERNAL', is_enabled: form.value.is_enabled,
    config_json: { client_id: form.value.client_id, client_secret: form.value.client_secret, authorize_url: form.value.authorize_url, token_url: form.value.token_url, userinfo_url: form.value.userinfo_url, scopes: ['openid', 'profile', 'email'] },
  }
  try {
    if (editId.value) { await apiClient.put(`/admin/system/sso-providers/${editId.value}`, data) }
    else { await apiClient.post('/admin/system/sso-providers', data) }
    showAddModal.value = false
    editId.value = ''
    await loadProviders()
  } catch (e: any) { alert(e.response?.data?.detail || '저장 실패') }
}

async function deleteProvider(p: any) {
  if (!confirm(`${p.display_name} 제공자를 삭제하시겠습니까?`)) return
  try { await apiClient.delete(`/admin/system/sso-providers/${p.id}`); await loadProviders() } catch {}
}

function openMetadata() { window.open('/api/v1/sso/saml/metadata', '_blank') }

onMounted(() => { loadSamlConfig(); loadProviders() })
</script>

<style lang="scss" scoped>
@use '../../../styles/variables' as *; @use '../admin-common.scss';
.card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; .card-title { font-weight: 700; font-size: 14px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; } }
.card-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; .card-title { font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 6px; } }
.card-actions { margin-top: 12px; }
.info-grid { display: grid; gap: 8px; }
.info-row { display: flex; gap: 12px; font-size: 13px; .info-label { color: #999; min-width: 120px; } .info-value { font-weight: 600; color: #333; word-break: break-all; } }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } .name-cell { font-weight: 600; } }
.status-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; &.active { background: #e8f5e9; color: #2e7d32; } &.inactive { background: #fce4ec; color: #c62828; } }
.btn-sm { padding: 4px 10px; font-size: 11px; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer; background: #fff; display: inline-flex; align-items: center; gap: 4px; &:hover { border-color: #1890ff; color: #1890ff; } }
.btn-primary { background: #1890ff; color: #fff; border-color: #1890ff; &:hover { background: #40a9ff; color: #fff; } }
.btn-danger { color: #DC3545; border-color: #DC3545; &:hover { background: #DC3545; color: #fff; } }
.btn-default { &:hover { border-color: #1890ff; color: #1890ff; } }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: #fff; border-radius: 8px; padding: 24px; width: 520px; max-height: 80vh; overflow-y: auto; h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; } }
.form-grid { display: grid; gap: 10px; }
.form-group { label { font-size: 12px; font-weight: 600; color: #666; display: block; margin-bottom: 4px; } input, select { width: 100%; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; &:focus { outline: none; border-color: #1890ff; } } }
.modal-actions { margin-top: 16px; display: flex; gap: 8px; justify-content: flex-end; }
</style>
