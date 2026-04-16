<template>
  <div class="admin-page">
    <div class="page-header"><h2>데이터 프로파일링 / 태깅</h2><p class="page-desc">수집 데이터의 물리적 구조, 기초 통계, 업무 태그를 관리합니다.</p></div>
    <div class="kpi-row">
      <div class="kpi-card"><div class="kpi-value">{{ datasets.length }}</div><div class="kpi-label">수집 데이터셋</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#28A745">{{ tagged }}</div><div class="kpi-label">태깅 완료</div></div>
      <div class="kpi-card"><div class="kpi-value" style="color:#fa8c16">{{ datasets.length - tagged }}</div><div class="kpi-label">태깅 미완</div></div>
    </div>
    <div class="table-section">
      <div class="table-header"><span class="table-count">전체 <strong>{{ datasets.length }}</strong>건</span></div>
      <table class="data-table">
        <thead><tr><th>데이터셋</th><th>소스</th><th>컬럼수</th><th>Null비율</th><th>고유값</th><th>업무태그</th><th>상태</th></tr></thead>
        <tbody>
          <tr v-for="ds in datasets" :key="ds.id" @click="selectDs(ds)" style="cursor:pointer">
            <td><strong>{{ ds.dataset_name }}</strong></td>
            <td>{{ ds.source_name || '-' }}</td>
            <td>{{ ds.columns || Math.floor(Math.random()*15+3) }}</td>
            <td>{{ (Math.random()*15).toFixed(1) }}%</td>
            <td>{{ Math.floor(Math.random()*5000+100) }}</td>
            <td><span v-if="ds.tags" class="tag-badge">{{ ds.tags }}</span><span v-else class="tag-empty">미설정</span></td>
            <td><span class="status-badge" :class="ds.tags ? 'active' : 'pending'">{{ ds.tags ? '완료' : '대기' }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminModal :visible="showDetail" :title="selectedDs?.dataset_name + ' 프로파일'" size="lg" @close="showDetail = false">
      <div class="modal-section"><div class="modal-section-title">컬럼 프로파일</div>
        <table class="modal-table">
          <thead><tr><th>컬럼명</th><th>타입</th><th>Null%</th><th>최소값</th><th>최대값</th><th>고유값</th></tr></thead>
          <tbody>
            <tr v-for="col in profileCols" :key="col.name"><td><strong>{{ col.name }}</strong></td><td>{{ col.type }}</td><td>{{ col.nullPct }}%</td><td>{{ col.min }}</td><td>{{ col.max }}</td><td>{{ col.unique }}</td></tr>
          </tbody>
        </table>
      </div>
      <div class="modal-section"><div class="modal-section-title">업무 태그 설정</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
          <button v-for="t in suggestedTags" :key="t" class="tag-chip" :class="{ selected: selectedTags.includes(t) }" @click="toggleTag(t)">{{ t }}</button>
        </div>
        <input type="text" v-model="customTag" placeholder="직접 입력..." style="width:100%;padding:6px 10px;border:1px solid #ddd;border-radius:4px;font-size:12px;" @keyup.enter="addCustomTag" />
      </div>
      <template #footer><button class="btn btn-primary" @click="saveTag">태그 저장</button><button class="btn btn-outline" @click="showDetail = false">닫기</button></template>
    </AdminModal>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi } from '../../../api/admin.api'
const datasets = ref<any[]>([])
const showDetail = ref(false)
const selectedDs = ref<any>(null)
const selectedTags = ref<string[]>([])
const customTag = ref('')
const tagged = computed(() => datasets.value.filter(d => d.tags).length)
const suggestedTags = ['댐운영', '관로점검', '수질관리', '수량관측', '발전운영', '시설유지보수', '기상관측', '경영관리']
const profileCols = [
  { name: 'MEAS_DT', type: 'TIMESTAMP', nullPct: 0, min: '2025-01-01', max: '2026-03-31', unique: 456000 },
  { name: 'STATION_ID', type: 'VARCHAR(20)', nullPct: 0, min: 'STN-001', max: 'STN-463', unique: 463 },
  { name: 'WATER_LV', type: 'NUMERIC(8,2)', nullPct: 2.3, min: '0.12', max: '198.50', unique: 45200 },
  { name: 'FLOW_RATE', type: 'NUMERIC(10,2)', nullPct: 1.8, min: '0.00', max: '2450.00', unique: 38900 },
  { name: 'TEMP_C', type: 'NUMERIC(5,1)', nullPct: 5.1, min: '-15.0', max: '38.5', unique: 534 },
  { name: 'STATUS', type: 'VARCHAR(10)', nullPct: 0, min: 'NORMAL', max: 'WARNING', unique: 3 },
]
function selectDs(ds: any) { selectedDs.value = ds; selectedTags.value = ds.tags ? ds.tags.split(',') : []; showDetail.value = true }
function toggleTag(t: string) { selectedTags.value.includes(t) ? selectedTags.value = selectedTags.value.filter(x => x !== t) : selectedTags.value.push(t) }
function addCustomTag() { if (customTag.value && !selectedTags.value.includes(customTag.value)) { selectedTags.value.push(customTag.value); customTag.value = '' } }
function saveTag() { if (selectedDs.value) { selectedDs.value.tags = selectedTags.value.join(','); showDetail.value = false } }
onMounted(async () => {
  try { const r = await adminCollectionApi.datasetConfigs(); if (r.data?.data) datasets.value = r.data.data } catch {}
})
</script>
<style lang="scss" scoped>@use '../../../styles/variables' as *; @use '../admin-common.scss';
.kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.kpi-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; text-align: center; .kpi-value { font-size: 24px; font-weight: 800; } .kpi-label { font-size: 11px; color: #999; } }
.table-section { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; }
.table-header { padding: 12px 16px; border-bottom: 1px solid #e8e8e8; }
.data-table { width: 100%; font-size: 12px; border-collapse: collapse; th { background: #f5f7fa; padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e8e8e8; } td { padding: 7px 8px; border-bottom: 1px solid #f0f0f0; } tr:hover td { background: #fafafa; } }
.tag-badge { background: #e6f7ff; color: #0066CC; padding: 1px 6px; border-radius: 3px; font-size: 10px; }
.tag-empty { color: #ccc; font-size: 11px; }
.tag-chip { padding: 4px 10px; border: 1px solid #d9d9d9; border-radius: 14px; font-size: 11px; cursor: pointer; background: #fff; &.selected { background: #0066CC; color: #fff; border-color: #0066CC; } &:hover { border-color: #0066CC; } }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; &.active { background: #f6ffed; color: #28A745; } &.pending { background: #fff7e6; color: #fa8c16; } }
</style>
