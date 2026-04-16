<template>
  <div class="admin-page migration-page">
    <div class="page-header">
      <h2>마이그레이션</h2>
      <p class="page-desc">
        소스 DB → 데이터허브 청크 스트리밍 ETL. 실시간 진행률/감사로그/검증을 제공합니다.
      </p>
    </div>

    <!-- KPI 카드 -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">총 작업</div>
        <div class="kpi-value">{{ kpi.total }}</div>
      </div>
      <div class="kpi-card running">
        <div class="kpi-label">실행중</div>
        <div class="kpi-value">{{ kpi.running }}</div>
      </div>
      <div class="kpi-card success">
        <div class="kpi-label">성공률</div>
        <div class="kpi-value">{{ kpi.successRate }}%</div>
      </div>
      <div class="kpi-card warn">
        <div class="kpi-label">실패</div>
        <div class="kpi-value">{{ kpi.failed }}</div>
      </div>
    </div>

    <!-- 필터 & 액션 -->
    <div class="table-section">
      <div class="table-header">
        <div class="filters">
          <input v-model="nameFilter" placeholder="작업명 검색..." class="filter-input" />
          <select v-model="statusFilter">
            <option value="">전체 상태</option>
            <option value="PENDING">대기</option>
            <option value="RUNNING">실행중</option>
            <option value="COMPLETED">완료</option>
            <option value="FAILED">실패</option>
          </select>
          <button class="btn btn-outline btn-sm" @click="loadRows"><ReloadOutlined /> 새로고침</button>
        </div>
        <div class="table-actions">
          <button class="btn btn-primary btn-sm" @click="openCreate"><PlusOutlined /> 작업 생성</button>
          <button class="btn-excel" title="엑셀 다운로드" @click="exportGridToExcel(gridCols, filteredRows, '마이그레이션')">
            <FileExcelOutlined />
          </button>
        </div>
      </div>
      <div class="ag-grid-wrapper">
        <AgGridVue class="ag-theme-alpine"
                   :rowData="filteredRows"
                   :columnDefs="gridCols"
                   :defaultColDef="defCol"
                   :pagination="true"
                   :paginationPageSize="15"
                   domLayout="autoHeight" />
      </div>
    </div>

    <!-- ═══ 생성/수정 마법사 ═══ -->
    <AdminModal :visible="showWizard" :title="wizard.id ? '마이그레이션 수정' : '마이그레이션 작업 생성'"
                size="lg" @close="closeWizard">
      <div class="wizard-steps">
        <div class="step" :class="{ active: step === 1, done: step > 1 }">
          <span class="step-num">1</span> 기본 정보
        </div>
        <div class="step-line" :class="{ done: step > 1 }"></div>
        <div class="step" :class="{ active: step === 2, done: step > 2 }">
          <span class="step-num">2</span> 테이블 선택 & 매핑
        </div>
      </div>

      <!-- Step 1: 기본 정보 -->
      <div v-show="step === 1" class="wizard-body">
        <div class="modal-form-group">
          <label class="required">작업명</label>
          <input v-model="wizard.migration_name" placeholder="예: Oracle_HR_to_Hub_2026Q2" />
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">원본 DB</label>
            <select v-model="wizard.source_id" @change="onSourceChange">
              <option value="">-- 선택 --</option>
              <option v-for="s in sources" :key="s.id" :value="s.id">
                {{ s.source_name }} ({{ s.db_type }})
              </option>
            </select>
          </div>
          <div class="modal-form-group">
            <label>대상 DB</label>
            <select v-model="wizard.target_source_id">
              <option :value="null">데이터허브 내부 PG (기본)</option>
              <option v-for="s in targetSources" :key="s.id" :value="s.id">
                {{ s.source_name }} ({{ s.db_type }})
              </option>
            </select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">대상 스키마</label>
            <input v-model="wizard.target_schema" placeholder="collection_zone" />
          </div>
          <div class="modal-form-group">
            <label>마이그레이션 유형</label>
            <select v-model="wizard.migration_type">
              <option value="FULL">FULL (전체 복제 - target TRUNCATE 후)</option>
              <option value="INCREMENTAL">INCREMENTAL (증분 - where 조건 활용)</option>
            </select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label>청크 크기 (행수)</label>
            <input type="number" v-model.number="wizard.chunk_size" min="100" max="100000" />
            <div class="hint">COPY/bulk insert 1회 처리 행수. 대용량은 1000~5000 권장</div>
          </div>
          <div class="modal-form-group"></div>
        </div>
      </div>

      <!-- Step 2: 테이블 선택 -->
      <div v-show="step === 2" class="wizard-body">
        <div class="tbl-select-toolbar">
          <div class="modal-form-group" style="flex:1">
            <label>소스 스키마</label>
            <select v-model="pickSchema" @change="loadPickTables">
              <option value="">-- 선택 --</option>
              <option v-for="s in schemas" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <button class="btn btn-outline btn-sm" @click="loadSchemas" :disabled="loadingSchemas">
            <ReloadOutlined /> 스키마 새로고침
          </button>
          <input v-model="tableFilter" placeholder="테이블 필터..." class="filter-input" />
        </div>

        <div class="tbl-select-body">
          <!-- 좌: 소스 테이블 리스트 -->
          <div class="tbl-pane">
            <div class="tbl-pane-header">
              <strong>소스 테이블</strong>
              <span class="muted" v-if="pickTables.length">({{ pickTables.length }}개)</span>
              <label class="all-check" v-if="filteredPickTables.length">
                <input type="checkbox" :checked="allPicked" @change="toggleAll" />
                전체
              </label>
            </div>
            <div class="tbl-list">
              <div v-if="loadingPickTables" class="muted pad">로드 중...</div>
              <div v-else-if="!pickTables.length" class="muted pad">스키마를 선택하세요</div>
              <label v-for="t in filteredPickTables" :key="t" class="tbl-row">
                <input type="checkbox" :checked="isPicked(t)" @change="togglePick(t)" />
                <TableOutlined /> {{ t }}
              </label>
            </div>
          </div>

          <!-- 우: 선택된 테이블 설정 -->
          <div class="tbl-pane">
            <div class="tbl-pane-header">
              <strong>선택된 테이블 매핑 ({{ wizard.tables.length }}개)</strong>
              <button v-if="wizard.tables.length" class="btn btn-ghost btn-xs" @click="wizard.tables = []">
                모두 해제
              </button>
            </div>
            <div class="tbl-mapping">
              <div v-if="!wizard.tables.length" class="muted pad">왼쪽에서 테이블을 체크하세요</div>
              <div v-for="(t, idx) in wizard.tables" :key="`${t.source_schema}.${t.source_table}`" class="mapping-row">
                <div class="mapping-head">
                  <TableOutlined /> <strong>{{ t.source_schema }}.{{ t.source_table }}</strong>
                  <button class="btn btn-ghost btn-xs text-danger" @click="wizard.tables.splice(idx, 1)">✕</button>
                </div>
                <div class="mapping-fields">
                  <div class="mf">
                    <label>타겟 테이블명</label>
                    <input v-model="t.target_table" :placeholder="t.source_table" />
                  </div>
                  <div class="mf">
                    <label>모드</label>
                    <select v-model="t.mode">
                      <option value="FULL">FULL</option>
                      <option value="INCREMENTAL">INCREMENTAL</option>
                    </select>
                  </div>
                  <div class="mf wide">
                    <label>WHERE 조건 (선택)</label>
                    <input v-model="t.where" placeholder="예: updated_at >= SYSDATE - 1" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <button v-if="step > 1" class="btn btn-outline" @click="step--">← 이전</button>
        <button v-if="step < 2" class="btn btn-primary" @click="nextStep" :disabled="!canNext">다음 →</button>
        <button v-else class="btn btn-primary" @click="saveMigration" :disabled="saving || !wizard.tables.length">
          <SaveOutlined /> {{ saving ? '저장 중...' : wizard.id ? '수정' : '생성' }}
        </button>
        <button class="btn btn-outline" @click="closeWizard">취소</button>
      </template>
    </AdminModal>

    <!-- 테이블 추가 미니 모달 -->
    <AdminModal :visible="showAddTbl" title="연계 테이블 추가" size="md" @close="showAddTbl = false">
      <div class="modal-form">
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label class="required">소스 스키마</label>
            <select v-model="addTbl.source_schema" @change="loadAddTblTables">
              <option value="">-- 선택 --</option>
              <option v-for="s in addTblSchemas" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="modal-form-group">
            <label class="required">소스 테이블</label>
            <select v-model="addTbl.source_table" @change="onAddTblTableChange">
              <option value="">-- 선택 --</option>
              <option v-for="t in addTblTables" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
        </div>
        <div class="modal-form-row">
          <div class="modal-form-group">
            <label>타겟 테이블명</label>
            <input v-model="addTbl.target_table" :placeholder="addTbl.source_table || '(원본 그대로)'" />
          </div>
          <div class="modal-form-group">
            <label>모드</label>
            <select v-model="addTbl.mode">
              <option value="FULL">FULL</option>
              <option value="INCREMENTAL">INCREMENTAL</option>
            </select>
          </div>
        </div>
        <div class="modal-form-group">
          <label>WHERE 조건 (선택)</label>
          <input v-model="addTbl.where" placeholder="예: updated_at >= SYSDATE - 1" />
        </div>
      </div>
      <template #footer>
        <button class="btn btn-primary" @click="confirmAddTable" :disabled="!addTbl.source_schema || !addTbl.source_table">
          <SaveOutlined /> 추가
        </button>
        <button class="btn btn-outline" @click="showAddTbl = false">취소</button>
      </template>
    </AdminModal>

    <!-- ═══ 상세 모달 (4 탭) ═══ -->
    <AdminModal :visible="showDetail" :title="detail?.migration_name || '마이그레이션 상세'"
                size="lg" @close="closeDetail">
      <div v-if="detail" class="detail-wrap">
        <div class="detail-tabs">
          <button v-for="t in DETAIL_TABS" :key="t.key" class="dtab"
                  :class="{ active: detailTab === t.key }" @click="switchDetailTab(t.key)">
            {{ t.label }}
          </button>
          <div class="detail-actions">
            <button class="btn btn-outline btn-sm" @click="() => reloadDetail()"><ReloadOutlined /></button>
            <span class="muted" v-if="polling">⟳ 실시간</span>
          </div>
        </div>

        <!-- 개요 -->
        <div v-show="detailTab === 'overview'" class="dpane">
          <div class="status-hero">
            <span class="status-badge" :class="statusClass(detail.status)">{{ statusLabel(detail.status) }}</span>
            <div class="progress-wrap">
              <div class="progress-bar">
                <div class="progress-fill" :class="statusClass(detail.status)" :style="{ width: progressPct + '%' }"></div>
              </div>
              <div class="progress-text">{{ progressPct }}% · {{ detail.completed_tables || 0 }}/{{ detail.total_tables || 0 }} 테이블</div>
            </div>
          </div>
          <div class="kv-grid">
            <div class="kv"><span>유형</span><b>{{ detail.migration_type }}</b></div>
            <div class="kv"><span>대상 스키마</span><b>{{ detail.target_storage_zone || '-' }}</b></div>
            <div class="kv"><span>청크 크기</span><b>{{ detail.table_list?.chunk_size || '-' }}</b></div>
            <div class="kv"><span>시작일시</span><b>{{ fmtTs(detail.started_at) }}</b></div>
            <div class="kv"><span>완료일시</span><b>{{ fmtTs(detail.completed_at) }}</b></div>
            <div class="kv"><span>현재 단계</span><b>{{ detail.progress?.current_phase || '-' }}</b></div>
            <div class="kv"><span>처리 행수</span><b>{{ (detail.progress?.processed_rows || 0).toLocaleString() }}</b></div>
            <div class="kv"><span>현재 테이블</span><b>{{ detail.progress?.current_table || '-' }}</b></div>
          </div>
          <div v-if="detail.progress?.current_table_total" class="curtbl">
            <div class="muted">현재 테이블 진행:</div>
            <div class="progress-bar small">
              <div class="progress-fill" :style="{ width: currentTablePct + '%' }"></div>
            </div>
            <div class="muted">
              {{ (detail.progress.current_table_processed || 0).toLocaleString() }}
              / {{ detail.progress.current_table_total.toLocaleString() }}
              ({{ currentTablePct }}%)
            </div>
          </div>
        </div>

        <!-- 테이블 (인라인 추가/편집/삭제 - REQ-DHUB-005-004-004) -->
        <div v-show="detailTab === 'tables'" class="dpane">
          <div class="tbl-tab-toolbar">
            <button class="btn btn-primary btn-sm" @click="openAddTable" :disabled="detail.status === 'RUNNING'">
              <PlusOutlined /> 테이블 추가
            </button>
            <span class="muted">{{ (detail.table_list?.tables || []).length }}개 매핑</span>
            <span v-if="detail.status === 'RUNNING'" class="muted err-msg">실행 중에는 수정할 수 없습니다</span>
          </div>
          <table class="tbl-data">
            <thead><tr><th>#</th><th>원본</th><th>타겟 테이블</th><th>모드</th><th>WHERE</th><th>작업</th></tr></thead>
            <tbody>
              <tr v-if="!(detail.table_list?.tables || []).length">
                <td colspan="6" class="muted pad">등록된 테이블이 없습니다. "테이블 추가" 클릭</td>
              </tr>
              <tr v-for="(t, i) in (detail.table_list?.tables || [])" :key="`${t.source_schema}.${t.source_table}`">
                <td>{{ Number(i) + 1 }}</td>
                <td><code>{{ t.source_schema }}.{{ t.source_table }}</code></td>
                <td>
                  <input v-if="editingKey === `${t.source_schema}.${t.source_table}`"
                         v-model="editingTable.target_table" class="inp-sm" />
                  <code v-else>{{ detail.table_list?.target_schema }}.{{ t.target_table || t.source_table }}</code>
                </td>
                <td>
                  <select v-if="editingKey === `${t.source_schema}.${t.source_table}`"
                          v-model="editingTable.mode" class="inp-sm">
                    <option value="FULL">FULL</option>
                    <option value="INCREMENTAL">INCREMENTAL</option>
                  </select>
                  <span v-else class="mode-tag" :class="t.mode?.toLowerCase()">{{ t.mode || 'FULL' }}</span>
                </td>
                <td class="wh">
                  <input v-if="editingKey === `${t.source_schema}.${t.source_table}`"
                         v-model="editingTable.where" class="inp-sm" placeholder="조건..." />
                  <span v-else>{{ t.where || '-' }}</span>
                </td>
                <td>
                  <template v-if="editingKey === `${t.source_schema}.${t.source_table}`">
                    <button class="grid-action-btn" @click="saveTableEdit(t)">💾 저장</button>
                    <button class="grid-action-btn edit" @click="cancelTableEdit">취소</button>
                  </template>
                  <template v-else>
                    <button class="grid-action-btn edit" @click="startTableEdit(t)"
                            :disabled="detail.status === 'RUNNING'">✎ 수정</button>
                    <button class="grid-action-btn del" @click="removeTable(t)"
                            :disabled="detail.status === 'RUNNING'">🗑</button>
                  </template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 감사로그 -->
        <div v-show="detailTab === 'audit'" class="dpane">
          <div class="audit-toolbar">
            <input v-model="auditFilter" placeholder="검색 (테이블/단계/행위)..." class="inp-sm" style="max-width:220px" />
            <select v-model="auditSeverityFilter" class="inp-sm" style="max-width:110px">
              <option value="">전체 심각도</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
            <span class="muted">{{ filteredAuditLogs.length }} / {{ auditLogs.length }}건</span>
            <button class="btn btn-outline btn-sm" @click="exportAuditLogs" :disabled="!auditLogs.length">
              <FileExcelOutlined /> 엑셀
            </button>
          </div>
          <div v-if="!filteredAuditLogs.length" class="muted pad">조회된 로그가 없습니다</div>
          <table v-else class="tbl-data">
            <thead><tr><th>시각</th><th>행위</th><th>단계</th><th>테이블</th><th>건수</th><th>소요</th><th>심각도</th></tr></thead>
            <tbody>
              <tr v-for="a in filteredAuditLogs" :key="a.id">
                <td>{{ fmtTs(a.created_at) }}</td>
                <td><span class="mode-tag">{{ a.action }}</span></td>
                <td>{{ a.phase || '-' }}</td>
                <td><code v-if="a.table_name">{{ a.table_name }}</code></td>
                <td>{{ a.row_count != null ? a.row_count.toLocaleString() : '-' }}</td>
                <td>{{ a.duration_ms ? a.duration_ms + 'ms' : '-' }}</td>
                <td><span class="sev" :class="a.severity?.toLowerCase()">{{ a.severity }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 검증 -->
        <div v-show="detailTab === 'validate'" class="dpane">
          <div class="validate-toolbar">
            <button class="btn btn-primary btn-sm" @click="runValidation" :disabled="validating">
              <CheckCircleOutlined /> {{ validating ? '검증 중...' : '검증 실행' }}
            </button>
            <span v-if="validationSummary" class="muted">
              MATCH: {{ validationSummary.match }} / MISMATCH: {{ validationSummary.mismatch }} / ERROR: {{ validationSummary.error }}
            </span>
          </div>
          <div v-if="!validationRows.length" class="muted pad">검증 결과가 없습니다. "검증 실행" 버튼을 눌러주세요.</div>
          <table v-else class="tbl-data">
            <thead><tr><th>테이블</th><th>검증유형</th><th>원본</th><th>대상</th><th>결과</th><th>차이</th></tr></thead>
            <tbody>
              <tr v-for="r in validationRows" :key="r.id">
                <td><code>{{ r.table_name }}</code></td>
                <td>{{ r.validation_type }}</td>
                <td>{{ truncate(r.source_value) }}</td>
                <td>{{ truncate(r.target_value) }}</td>
                <td><span class="sev" :class="matchClass(r.match_status)">{{ r.match_status }}</span></td>
                <td>{{ r.diff_count != null ? r.diff_count : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 에러 (상단 공통, 항상 표시) -->
        <div v-if="(detail.errors || []).length" class="errors-box">
          <div class="errors-title">⚠ 실패 항목 {{ detail.errors.length }}건</div>
          <div v-for="(e, i) in (detail.errors || []).slice(0, 5)" :key="i" class="err-item">
            <code>{{ e.table }}</code> <span class="mode-tag">{{ e.phase }}</span>
            <span class="err-msg">{{ e.error }}</span>
          </div>
        </div>
      </div>

      <template #footer>
        <button v-if="detail && ['PENDING','FAILED','COMPLETED'].includes(detail.status)" class="btn btn-primary" @click="executeRun">
          <ThunderboltOutlined /> {{ detail.status === 'PENDING' ? '실행' : '재실행' }}
        </button>
        <button v-if="detail" class="btn btn-outline" @click="editFromDetail"><EditOutlined /> 수정</button>
        <button v-if="detail" class="btn btn-danger" @click="deleteFromDetail"><DeleteOutlined /> 삭제</button>
        <button class="btn btn-outline" @click="closeDetail">닫기</button>
      </template>
    </AdminModal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { AgGridVue } from 'ag-grid-vue3'
import { AllCommunityModule, ModuleRegistry, type ColDef } from 'ag-grid-community'
import { exportGridToExcel } from '../../../utils/exportExcel'
import { defaultColDef as baseDefaultColDef, withHeaderTooltips } from '../../../utils/gridHelper'
import {
  PlusOutlined, FileExcelOutlined, EditOutlined, SaveOutlined, DeleteOutlined,
  ReloadOutlined, ThunderboltOutlined, CheckCircleOutlined, TableOutlined,
} from '@ant-design/icons-vue'
import { message } from '../../../utils/message'
import AdminModal from '../../../components/AdminModal.vue'
import { adminCollectionApi, adminDrApi } from '../../../api/admin.api'
ModuleRegistry.registerModules([AllCommunityModule])

const DETAIL_TABS = [
  { key: 'overview', label: '개요' },
  { key: 'tables', label: '테이블' },
  { key: 'audit', label: '감사로그' },
  { key: 'validate', label: '검증' },
]

// 그리드
const rows = ref<any[]>([])
const sources = ref<any[]>([])
const nameFilter = ref('')
const statusFilter = ref('')
const defCol = { ...baseDefaultColDef }

const gridCols: ColDef[] = withHeaderTooltips([
  { headerName: 'No', valueGetter: 'node.rowIndex + 1', width: 55 },
  { headerName: '작업명', field: 'migration_name', flex: 1.5, minWidth: 160,
    cellRenderer: (p: any) => `<b>${p.value || ''}</b>` },
  { headerName: '원본', field: 'sourceLabel', flex: 1, minWidth: 120 },
  { headerName: '대상', field: 'targetLabel', flex: 1, minWidth: 120 },
  { headerName: '유형', field: 'migration_type', width: 110,
    cellRenderer: (p: any) => `<span class="mode-tag ${(p.value || '').toLowerCase()}">${p.value || ''}</span>` },
  { headerName: '상태', field: 'status', width: 90,
    cellRenderer: (p: any) => `<span class="status-badge ${statusClass(p.value)}">${statusLabel(p.value)}</span>` },
  { headerName: '진행률', field: 'pct', flex: 0.9, minWidth: 130,
    cellRenderer: (p: any) => {
      const pct = p.value || 0
      const cls = statusClass(p.data.status)
      return `<div class="grid-progress"><div class="grid-progress-bar"><div class="grid-progress-fill ${cls}" style="width:${pct}%"></div></div><span>${pct}%</span></div>`
    } },
  { headerName: '테이블', field: 'tableLabel', width: 95 },
  { headerName: '행수', field: 'rowsLabel', width: 110 },
  { headerName: '최근 실행', field: 'lastRun', width: 155 },
  { headerName: '작업', width: 180, sortable: false, cellRenderer: (p: any) => {
      const wrap = document.createElement('div')
      wrap.className = 'grid-action-wrap'
      const run = document.createElement('button')
      run.className = 'grid-action-btn'
      run.innerHTML = p.data.status === 'RUNNING' ? '⟳ 실행중' : '▶ 실행'
      run.disabled = p.data.status === 'RUNNING'
      run.onclick = (ev) => { ev.stopPropagation(); runMigration(p.data._raw) }
      const view = document.createElement('button')
      view.className = 'grid-action-btn edit'
      view.innerHTML = '🔍 상세'
      view.onclick = (ev) => { ev.stopPropagation(); openDetail(p.data._raw.id) }
      const del = document.createElement('button')
      del.className = 'grid-action-btn del'
      del.innerHTML = '🗑'
      del.onclick = (ev) => { ev.stopPropagation(); deleteMigration(p.data._raw) }
      wrap.appendChild(run); wrap.appendChild(view); wrap.appendChild(del)
      return wrap
    } },
])

const filteredRows = computed(() => {
  const n = nameFilter.value.toLowerCase()
  return rows.value.filter(r => {
    if (n && !(r.migration_name || '').toLowerCase().includes(n)) return false
    if (statusFilter.value && r.status !== statusFilter.value) return false
    return true
  })
})

const kpi = computed(() => {
  const total = rows.value.length
  const running = rows.value.filter(r => r.status === 'RUNNING').length
  const completed = rows.value.filter(r => r.status === 'COMPLETED').length
  const failed = rows.value.filter(r => r.status === 'FAILED').length
  const finished = completed + failed
  return {
    total, running, failed,
    successRate: finished > 0 ? Math.round((completed / finished) * 100) : 0,
  }
})

function statusClass(s: string) {
  return {
    'COMPLETED': 'ok',
    'RUNNING': 'running',
    'PENDING': 'pending',
    'FAILED': 'fail',
  }[s] || 'pending'
}
function statusLabel(s: string) {
  return { 'COMPLETED': '완료', 'RUNNING': '실행중', 'PENDING': '대기', 'FAILED': '실패' }[s] || (s || '-')
}
function fmtTs(v?: string) {
  if (!v) return '-'
  return new Date(v).toLocaleString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
function truncate(v: any) {
  if (v == null) return '-'
  const s = String(v)
  return s.length > 40 ? s.slice(0, 37) + '...' : s
}
function matchClass(s: string) {
  return { MATCH: 'ok', MISMATCH: 'warn', ERROR: 'fail', SKIPPED: 'pending' }[s] || ''
}

async function loadRows() {
  try {
    const [migRes, srcRes] = await Promise.all([
      adminCollectionApi.migrations(),
      adminCollectionApi.dataSources(),
    ])
    const migs = migRes.data.data || []
    sources.value = srcRes.data.data || []
    const srcMap = new Map(sources.value.map((s: any) => [s.id, s]))
    // 상세를 병렬 조회해서 진행률/행수/최근실행 표시
    const details = await Promise.all(migs.map((m: any) =>
      adminCollectionApi.getMigration(m.id).then(r => r.data.data).catch(() => null)
    ))
    rows.value = migs.map((m: any, idx: number) => {
      const d = details[idx] || {}
      const cfg = d.table_list || {}
      const src = srcMap.get(d.source_id || m.source_id)
      const tgt = cfg.target_source_id ? srcMap.get(cfg.target_source_id) : null
      const totalT = d.total_tables || m.total_tables || 0
      const doneT = d.completed_tables || m.completed_tables || 0
      const pct = totalT > 0 ? Math.round((doneT / totalT) * 100) : (m.status === 'COMPLETED' ? 100 : 0)
      return {
        _raw: { ...m, ...d },
        migration_name: m.migration_name,
        sourceLabel: src ? `${src.source_name}` : '-',
        targetLabel: tgt ? tgt.source_name : `허브:${cfg.target_schema || 'collection_zone'}`,
        migration_type: m.migration_type,
        status: m.status,
        pct,
        tableLabel: `${doneT}/${totalT}`,
        rowsLabel: (d.progress?.processed_rows || 0).toLocaleString(),
        lastRun: fmtTs(d.started_at),
      }
    })
  } catch (e: any) {
    console.warn('loadRows', e)
    message.error('마이그레이션 목록 조회 실패')
  }
}

// ═════ 위자드 ═════
const showWizard = ref(false)
const step = ref(1)
const saving = ref(false)
const wizard = reactive<any>({
  id: '', migration_name: '', source_id: '', target_source_id: null,
  target_schema: 'collection_zone', migration_type: 'FULL',
  chunk_size: 1000, tables: [] as any[],
})
const schemas = ref<string[]>([])
const loadingSchemas = ref(false)
const pickSchema = ref('')
const pickTables = ref<string[]>([])
const loadingPickTables = ref(false)
const tableFilter = ref('')

const targetSources = computed(() => sources.value.filter((s: any) => s.id !== wizard.source_id))
const canNext = computed(() => wizard.migration_name && wizard.source_id && wizard.target_schema)

const filteredPickTables = computed(() => {
  if (!tableFilter.value) return pickTables.value
  const q = tableFilter.value.toLowerCase()
  return pickTables.value.filter(t => t.toLowerCase().includes(q))
})
const allPicked = computed(() => filteredPickTables.value.length > 0 &&
  filteredPickTables.value.every(t => isPicked(t)))

function isPicked(t: string) {
  return wizard.tables.some((x: any) => x.source_schema === pickSchema.value && x.source_table === t)
}
function togglePick(t: string) {
  if (isPicked(t)) {
    wizard.tables = wizard.tables.filter((x: any) => !(x.source_schema === pickSchema.value && x.source_table === t))
  } else {
    wizard.tables.push({
      source_schema: pickSchema.value, source_table: t,
      target_table: t.toLowerCase(), mode: wizard.migration_type, where: '',
    })
  }
}
function toggleAll() {
  if (allPicked.value) {
    wizard.tables = wizard.tables.filter((x: any) =>
      !(x.source_schema === pickSchema.value && filteredPickTables.value.includes(x.source_table)))
  } else {
    filteredPickTables.value.forEach(t => { if (!isPicked(t)) togglePick(t) })
  }
}

function openCreate() {
  Object.assign(wizard, {
    id: '', migration_name: '', source_id: '', target_source_id: null,
    target_schema: 'collection_zone', migration_type: 'FULL',
    chunk_size: 1000, tables: [],
  })
  schemas.value = []
  pickSchema.value = ''
  pickTables.value = []
  step.value = 1
  showWizard.value = true
}
function closeWizard() { showWizard.value = false }

function nextStep() {
  if (!canNext.value) { message.warning('필수 항목을 입력하세요'); return }
  step.value = 2
  if (!schemas.value.length) loadSchemas()
}

async function onSourceChange() {
  schemas.value = []
  pickSchema.value = ''
  pickTables.value = []
  // 소스 변경 시 기존 선택 테이블 초기화
  wizard.tables = []
}

async function loadSchemas() {
  if (!wizard.source_id) return
  loadingSchemas.value = true
  try {
    const r = await adminDrApi.listSchemas(wizard.source_id)
    schemas.value = r.data.data || []
  } catch (e: any) {
    message.error('스키마 조회 실패')
  } finally {
    loadingSchemas.value = false
  }
}
async function loadPickTables() {
  if (!pickSchema.value) { pickTables.value = []; return }
  loadingPickTables.value = true
  try {
    const r = await adminDrApi.listTables(wizard.source_id, pickSchema.value)
    pickTables.value = r.data.data || []
  } catch (e: any) {
    message.error('테이블 조회 실패')
    pickTables.value = []
  } finally {
    loadingPickTables.value = false
  }
}

async function saveMigration() {
  saving.value = true
  try {
    const payload: any = {
      migration_name: wizard.migration_name,
      source_id: wizard.source_id,
      target_source_id: wizard.target_source_id,
      target_schema: wizard.target_schema,
      migration_type: wizard.migration_type,
      chunk_size: wizard.chunk_size,
      tables: wizard.tables,
    }
    if (wizard.id) {
      const r = await adminCollectionApi.updateMigration(wizard.id, payload)
      const d = r.data.data || {}
      message.success(`수정 완료 (추가 ${d.added?.length || 0} / 삭제 ${d.removed?.length || 0} / 변경 ${d.modified?.length || 0})`)
    } else {
      await adminCollectionApi.createMigration(payload)
      message.success('작업이 생성되었습니다')
    }
    showWizard.value = false
    await loadRows()
    if (wizard.id && showDetail.value && detail.value?.id === wizard.id) {
      await reloadDetail()
    }
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '저장 실패')
  } finally {
    saving.value = false
  }
}

// ═════ 실행 · 삭제 ═════
async function runMigration(raw: any) {
  if (!raw?.id) return
  if (!confirm(`'${raw.migration_name}' 을(를) 실행하시겠습니까?`)) return
  try {
    await adminCollectionApi.executeMigration(raw.id)
    message.success('비동기 실행 요청되었습니다')
    await loadRows()
    if (showDetail.value && detail.value?.id === raw.id) reloadDetail()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '실행 실패')
  }
}

async function deleteMigration(raw: any) {
  if (!raw?.id) return
  if (!confirm(`'${raw.migration_name}' 을(를) 삭제하시겠습니까?`)) return
  try {
    await (adminCollectionApi as any).deleteMigration?.(raw.id) ||
      fetch(`/api/v1/admin/collection/migrations/${raw.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      })
    message.success('삭제되었습니다')
    await loadRows()
  } catch (e: any) {
    message.error('삭제 실패 (백엔드 API 미구현일 수 있음)')
  }
}

// ═════ 상세 ═════
const showDetail = ref(false)
const detail = ref<any>(null)
const detailTab = ref<'overview' | 'tables' | 'audit' | 'validate'>('overview')
const auditLogs = ref<any[]>([])
const auditFilter = ref('')
const auditSeverityFilter = ref('')
const filteredAuditLogs = computed(() => {
  const q = auditFilter.value.toLowerCase()
  return auditLogs.value.filter((a: any) => {
    if (auditSeverityFilter.value && a.severity !== auditSeverityFilter.value) return false
    if (q) {
      const hay = [a.action, a.phase, a.table_name].filter(Boolean).join(' ').toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})
function exportAuditLogs() {
  const cols: any[] = [
    { headerName: '시각', field: 'created_at', valueFormatter: (p: any) => fmtTs(p.value) },
    { headerName: '행위', field: 'action' },
    { headerName: '단계', field: 'phase' },
    { headerName: '테이블', field: 'table_name' },
    { headerName: '건수', field: 'row_count' },
    { headerName: '소요ms', field: 'duration_ms' },
    { headerName: '심각도', field: 'severity' },
  ]
  exportGridToExcel(cols, filteredAuditLogs.value, `감사로그_${detail.value?.migration_name || ''}`)
}
const validationRows = ref<any[]>([])
const validationSummary = ref<any>(null)
const validating = ref(false)
let pollTimer: any = null
const polling = computed(() => !!pollTimer && ['RUNNING', 'PENDING'].includes(detail.value?.status))

const progressPct = computed(() => {
  if (!detail.value) return 0
  const t = detail.value.total_tables || 0
  const d = detail.value.completed_tables || 0
  if (detail.value.status === 'COMPLETED') return 100
  return t > 0 ? Math.round((d / t) * 100) : 0
})
const currentTablePct = computed(() => {
  const p = detail.value?.progress
  if (!p?.current_table_total) return 0
  return Math.round(((p.current_table_processed || 0) / p.current_table_total) * 100)
})

async function openDetail(id: string) {
  showDetail.value = true
  detailTab.value = 'overview'
  auditLogs.value = []
  validationRows.value = []
  validationSummary.value = null
  await reloadDetail(id)
  startPolling()
}

function closeDetail() {
  showDetail.value = false
  detail.value = null
  stopPolling()
}

async function reloadDetail(id?: string) {
  const mid = id || detail.value?.id
  if (!mid) return
  try {
    const r = await adminCollectionApi.getMigration(mid)
    detail.value = r.data.data
  } catch (e: any) {
    message.error('상세 조회 실패')
  }
}

function switchDetailTab(k: any) {
  detailTab.value = k
  if (k === 'audit') loadAuditLogs()
  else if (k === 'validate') loadValidation()
}

async function loadAuditLogs() {
  if (!detail.value?.id) return
  try {
    const r = await adminDrApi.migrationAuditLogs(detail.value.id)
    auditLogs.value = r.data.data || []
  } catch (e) { /* silent */ }
}

async function loadValidation() {
  if (!detail.value?.id) return
  try {
    const r = await adminDrApi.migrationValidation(detail.value.id)
    const d = r.data.data || {}
    validationRows.value = d.results || []
    validationSummary.value = d.by_status || null
  } catch (e) { /* silent */ }
}

async function runValidation() {
  if (!detail.value?.id) return
  const cfg = detail.value.table_list || {}
  const tables = (cfg.tables || []).map((t: any) => ({
    source_schema: t.source_schema, source_table: t.source_table,
    target_schema: cfg.target_schema, target_table: t.target_table || t.source_table,
  }))
  if (!tables.length) { message.warning('검증할 테이블이 없습니다'); return }
  // target id 확정: target_source_id 있으면 그대로, 없으면 source와 동일로 (허브 내부 PG의 경우 우회)
  const targetId = cfg.target_source_id || detail.value.source_id
  validating.value = true
  try {
    const r = await adminDrApi.migrationValidate(detail.value.id, {
      source_id: detail.value.source_id,
      target_id: targetId,
      tables,
    })
    validationSummary.value = { match: r.data.data?.match, mismatch: r.data.data?.mismatch, error: r.data.data?.error }
    message.success('검증 완료')
    await loadValidation()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '검증 실패')
  } finally {
    validating.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(() => {
    if (!showDetail.value || !detail.value) return
    if (!['RUNNING', 'PENDING'].includes(detail.value.status)) return
    reloadDetail()
    if (detailTab.value === 'audit') loadAuditLogs()
  }, 2000)
}
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function executeRun() {
  if (!detail.value?.id) return
  try {
    await adminCollectionApi.executeMigration(detail.value.id)
    message.success('비동기 실행 요청되었습니다')
    setTimeout(() => reloadDetail(), 500)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '실행 실패')
  }
}

function editFromDetail() {
  if (!detail.value) return
  const d = detail.value
  const cfg = d.table_list || {}
  Object.assign(wizard, {
    id: d.id,
    migration_name: d.migration_name,
    source_id: d.source_id,
    target_source_id: cfg.target_source_id || null,
    target_schema: cfg.target_schema || 'collection_zone',
    migration_type: d.migration_type,
    chunk_size: cfg.chunk_size || 1000,
    tables: (cfg.tables || []).map((t: any) => ({ ...t })),
  })
  showDetail.value = false
  step.value = 1
  showWizard.value = true
}

async function deleteFromDetail() {
  if (!detail.value) return
  await deleteMigration(detail.value)
  if (showDetail.value) closeDetail()
}

// ═════ 인라인 테이블 편집 (REQ-DHUB-005-004-004) ═════
const editingKey = ref('')
const editingTable = reactive<any>({ target_table: '', mode: 'FULL', where: '' })
const showAddTbl = ref(false)
const addTbl = reactive<any>({ source_schema: '', source_table: '', target_table: '', mode: 'FULL', where: '' })
const addTblSchemas = ref<string[]>([])
const addTblTables = ref<string[]>([])

function startTableEdit(t: any) {
  editingKey.value = `${t.source_schema}.${t.source_table}`
  Object.assign(editingTable, {
    target_table: t.target_table || t.source_table,
    mode: t.mode || 'FULL',
    where: t.where || '',
  })
}
function cancelTableEdit() { editingKey.value = '' }

async function saveTableEdit(t: any) {
  if (!detail.value?.id) return
  const key = `${t.source_schema}.${t.source_table}`
  try {
    await adminCollectionApi.updateMigrationTable(detail.value.id, key, {
      target_table: editingTable.target_table || t.source_table,
      mode: editingTable.mode,
      where: editingTable.where || null,
    })
    message.success(`매핑 수정: ${key}`)
    editingKey.value = ''
    await reloadDetail()
    await loadAuditLogs()
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '수정 실패')
  }
}

async function removeTable(t: any) {
  if (!detail.value?.id) return
  const key = `${t.source_schema}.${t.source_table}`
  if (!confirm(`'${key}' 매핑을 제거하시겠습니까?`)) return
  try {
    await adminCollectionApi.deleteMigrationTable(detail.value.id, key)
    message.success(`매핑 삭제: ${key}`)
    await reloadDetail()
    await loadAuditLogs()
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '삭제 실패')
  }
}

async function openAddTable() {
  if (!detail.value?.source_id) return
  Object.assign(addTbl, { source_schema: '', source_table: '', target_table: '', mode: detail.value.migration_type || 'FULL', where: '' })
  addTblTables.value = []
  showAddTbl.value = true
  if (!addTblSchemas.value.length) {
    try {
      const r = await adminDrApi.listSchemas(detail.value.source_id)
      addTblSchemas.value = r.data.data || []
    } catch (e) { /* silent */ }
  }
}

async function loadAddTblTables() {
  addTbl.source_table = ''
  addTbl.target_table = ''
  addTblTables.value = []
  if (!addTbl.source_schema || !detail.value?.source_id) return
  try {
    const r = await adminDrApi.listTables(detail.value.source_id, addTbl.source_schema)
    addTblTables.value = r.data.data || []
  } catch (e: any) {
    message.error('테이블 조회 실패')
  }
}

function onAddTblTableChange() {
  if (addTbl.source_table && !addTbl.target_table) {
    addTbl.target_table = addTbl.source_table.toLowerCase()
  }
}

async function confirmAddTable() {
  if (!detail.value?.id) return
  try {
    await adminCollectionApi.addMigrationTable(detail.value.id, {
      source_schema: addTbl.source_schema,
      source_table: addTbl.source_table,
      target_table: addTbl.target_table || addTbl.source_table.toLowerCase(),
      mode: addTbl.mode,
      where: addTbl.where || null,
    })
    message.success(`테이블 추가: ${addTbl.source_schema}.${addTbl.source_table}`)
    showAddTbl.value = false
    await reloadDetail()
    await loadAuditLogs()
    await loadRows()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '추가 실패')
  }
}

watch(() => detail.value?.status, (s) => {
  if (s && !['RUNNING', 'PENDING'].includes(s)) stopPolling()
})

onMounted(() => {
  loadRows()
})
onBeforeUnmount(() => stopPolling())
</script>

<style lang="scss" scoped>
@use '../admin-common.scss';

.migration-page { display: flex; flex-direction: column; }

/* KPI */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.kpi-card {
  background: #fff; border: 1px solid #eee; border-radius: 6px; padding: 14px 16px;
  border-left: 4px solid #1677ff;
  &.running { border-left-color: #faad14; }
  &.success { border-left-color: #52c41a; }
  &.warn { border-left-color: #ff4d4f; }
}
.kpi-label { font-size: 12px; color: #888; margin-bottom: 4px; }
.kpi-value { font-size: 24px; font-weight: 700; color: #262626; }

/* 필터 */
.filters { display: flex; gap: 8px; align-items: center; }
.filter-input { padding: 5px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; min-width: 180px; }
.filters select { padding: 5px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; }

/* 상태 배지 */
:deep(.status-badge), .status-badge {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; font-weight: 600; text-align: center;
  &.ok { background: #f6ffed; color: #135200; border: 1px solid #b7eb8f; }
  &.running { background: #e6f4ff; color: #003a8c; border: 1px solid #91caff; animation: pulse 1.5s infinite; }
  &.pending { background: #f5f5f5; color: #595959; border: 1px solid #d9d9d9; }
  &.fail { background: #fff2f0; color: #820014; border: 1px solid #ffccc7; }
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

/* 유형 태그 */
:deep(.mode-tag), .mode-tag {
  display: inline-block; padding: 1px 6px; border-radius: 3px;
  font-size: 10px; font-weight: 600; background: #f0f2f5; color: #595959;
  &.full { background: #e6f4ff; color: #003a8c; }
  &.incremental { background: #fff7e6; color: #874d00; }
}

/* 그리드 진행률 */
:deep(.grid-progress) { display: flex; align-items: center; gap: 6px; height: 100%; }
:deep(.grid-progress-bar) { flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
:deep(.grid-progress-fill) { height: 100%; background: #1677ff; transition: width 0.3s; }
:deep(.grid-progress-fill.ok) { background: #52c41a; }
:deep(.grid-progress-fill.fail) { background: #ff4d4f; }
:deep(.grid-progress-fill.running) { background: #1677ff; animation: stripe 1s linear infinite;
  background-image: linear-gradient(45deg, rgba(255,255,255,0.3) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0.3) 75%, transparent 75%);
  background-size: 10px 10px;
}
@keyframes stripe { from { background-position: 0 0 } to { background-position: 10px 0 } }

/* 그리드 액션 */
:deep(.grid-action-wrap) { display: inline-flex; gap: 4px; align-items: center; height: 100%; }
:deep(.grid-action-btn) {
  background: #fff; border: 1px solid #d9d9d9; border-radius: 3px;
  padding: 2px 8px; font-size: 11px; color: #1677ff; cursor: pointer; transition: all 0.15s;
  &:hover:not(:disabled) { border-color: #1677ff; background: #e6f4ff; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &.edit { color: #595959; &:hover { border-color: #8c8c8c; background: #f5f5f5; } }
  &.del { color: #cf1322; &:hover { border-color: #cf1322; background: #fff1f0; } }
}

/* 위자드 스텝 */
.wizard-steps { display: flex; align-items: center; padding: 0 20px 16px; border-bottom: 1px solid #eee; margin-bottom: 12px; }
.step { display: flex; align-items: center; gap: 8px; color: #8c8c8c; font-size: 13px; font-weight: 600; }
.step.active { color: #1677ff; }
.step.done { color: #52c41a; }
.step-num {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: #f0f0f0; color: #8c8c8c; font-weight: 700;
}
.step.active .step-num { background: #1677ff; color: #fff; }
.step.done .step-num { background: #52c41a; color: #fff; }
.step-line { flex: 1; height: 2px; background: #f0f0f0; margin: 0 10px; }
.step-line.done { background: #52c41a; }
.wizard-body { min-height: 320px; }
.hint { font-size: 11px; color: #888; margin-top: 2px; }

/* 테이블 선택 2분할 */
.tbl-select-toolbar { display: flex; align-items: flex-end; gap: 8px; margin-bottom: 10px; }
.tbl-select-body { display: grid; grid-template-columns: 1fr 1.4fr; gap: 12px; min-height: 360px; }
.tbl-pane { border: 1px solid #eee; border-radius: 4px; padding: 8px; display: flex; flex-direction: column; background: #fafafa; }
.tbl-pane-header { display: flex; align-items: center; gap: 8px; padding: 4px 6px; border-bottom: 1px solid #eee; margin-bottom: 6px; font-size: 13px; }
.all-check { margin-left: auto; display: flex; align-items: center; gap: 4px; font-size: 11px; color: #555; cursor: pointer; }
.tbl-list { flex: 1; overflow-y: auto; max-height: 360px; }
.tbl-row { display: flex; align-items: center; gap: 6px; padding: 4px 6px; font-size: 12px; cursor: pointer; border-radius: 3px; }
.tbl-row:hover { background: #e6f4ff; }
.tbl-mapping { flex: 1; overflow-y: auto; max-height: 360px; }
.mapping-row { border: 1px solid #e8e8e8; border-radius: 4px; padding: 6px 8px; margin-bottom: 6px; background: #fff; }
.mapping-head { display: flex; align-items: center; gap: 4px; font-size: 12px; margin-bottom: 4px; }
.mapping-head > button { margin-left: auto; }
.mapping-fields { display: grid; grid-template-columns: 1fr 0.7fr; gap: 6px; }
.mapping-fields .wide { grid-column: 1 / -1; }
.mf { display: flex; flex-direction: column; gap: 2px; font-size: 11px; }
.mf label { color: #595959; font-size: 10px; }
.mf input, .mf select { padding: 3px 6px; border: 1px solid #d9d9d9; border-radius: 3px; font-size: 11px; }
.btn-xs { padding: 1px 4px; font-size: 10px; }

/* 상세 */
.detail-wrap { display: flex; flex-direction: column; gap: 10px; }
.detail-tabs { display: flex; gap: 4px; border-bottom: 1px solid #eee; padding-bottom: 6px; align-items: center; }
.dtab { padding: 4px 12px; font-size: 13px; background: none; border: none; border-bottom: 2px solid transparent; cursor: pointer; color: #595959;
  &:hover { color: #1677ff; } &.active { color: #1677ff; font-weight: 600; border-bottom-color: #1677ff; } }
.detail-actions { margin-left: auto; display: flex; align-items: center; gap: 8px; font-size: 11px; }
.dpane { min-height: 200px; padding: 6px 2px; }

/* Overview */
.status-hero { display: flex; align-items: center; gap: 12px; padding: 12px; background: #fafafa; border-radius: 4px; margin-bottom: 10px; }
.progress-wrap { flex: 1; }
.progress-bar { width: 100%; height: 12px; background: #f0f0f0; border-radius: 6px; overflow: hidden; }
.progress-bar.small { height: 8px; }
.progress-fill { height: 100%; background: #1677ff; transition: width 0.3s; }
.progress-fill.ok { background: #52c41a; }
.progress-fill.fail { background: #ff4d4f; }
.progress-fill.running { animation: stripe 1s linear infinite;
  background-image: linear-gradient(45deg, rgba(255,255,255,0.3) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0.3) 75%, transparent 75%);
  background-size: 10px 10px; background-color: #1677ff;
}
.progress-text { font-size: 12px; color: #555; margin-top: 4px; }
.kv-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.kv { display: flex; flex-direction: column; padding: 8px; background: #fff; border: 1px solid #f0f0f0; border-radius: 3px; }
.kv > span { font-size: 10px; color: #888; }
.kv > b { font-size: 13px; color: #262626; }
.curtbl { margin-top: 10px; padding: 8px; background: #fafafa; border-radius: 4px; font-size: 12px; }

/* 데이터 테이블 */
.tbl-data { width: 100%; border-collapse: collapse; font-size: 12px; }
.tbl-data th { background: #fafafa; padding: 6px 8px; text-align: left; border-bottom: 2px solid #e8e8e8; font-weight: 600; color: #595959; }
.tbl-data td { padding: 6px 8px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
.tbl-data code { background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 11px; }
.tbl-data .wh { color: #874d00; font-style: italic; }

.sev {
  display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;
  &.info { background: #e6f4ff; color: #003a8c; }
  &.warning, &.warn { background: #fff7e6; color: #874d00; }
  &.error, &.fail { background: #fff2f0; color: #820014; }
  &.ok { background: #f6ffed; color: #135200; }
  &.pending { background: #f5f5f5; color: #595959; }
}

.errors-box { margin-top: 10px; padding: 10px; background: #fff2f0; border: 1px solid #ffccc7; border-radius: 4px; }
.errors-title { font-weight: 600; color: #820014; margin-bottom: 6px; }
.err-item { font-size: 11px; margin-bottom: 3px; }
.err-msg { color: #820014; margin-left: 6px; }

.validate-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }

/* 인라인 테이블 편집 */
.tbl-tab-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.audit-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.inp-sm { padding: 2px 6px; border: 1px solid #d9d9d9; border-radius: 3px; font-size: 11px; width: 100%; max-width: 200px; }
.err-msg { color: #cf1322; font-size: 11px; }

/* Danger button */
.btn-danger { background: #ff4d4f; color: #fff; border: 1px solid #ff4d4f;
  &:hover { background: #d9363e; } &:disabled { opacity: 0.5; cursor: not-allowed; } }
</style>
