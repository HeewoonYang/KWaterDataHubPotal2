// ── 단어사전 ──
export interface StdWord {
  id: number
  word_name: string
  english_name: string
  english_meaning?: string
  attr_classifier?: string
  synonyms?: string
  description?: string
  status: string
  created_at?: string
  updated_at?: string
}

// ── 도메인사전 ──
export interface StdDomain {
  id: number
  domain_group: string
  domain_name: string
  domain_code: string
  data_type: string
  length?: number
  decimal_places?: number
  data_format?: string
  valid_values?: string
  characteristics?: string
  description?: string
  status: string
  created_at?: string
  updated_at?: string
}

// ── 용어사전 ──
export interface StdTerm {
  id: number
  term_name: string
  english_name: string
  english_meaning?: string
  domain_code?: string
  term_classifier?: string
  domain_group?: string
  data_type?: string
  length?: number
  decimal_places?: number
  data_format?: string
  valid_values?: string
  characteristics?: string
  description?: string
  status: string
  created_at?: string
  updated_at?: string
}

// ── 코드사전 ──
export interface StdCode {
  id: number
  code_group: string
  system_name?: string
  table_name?: string
  code_group_name: string
  code_type?: string
  seq_no?: number
  code_id: string
  code_value?: string
  code_value_name?: string
  sort_order?: number
  parent_code_name?: string
  parent_code_value?: string
  description?: string
  effective_date?: string
  expiration_date?: string
  status: string
  created_at?: string
  updated_at?: string
}

// ── 표준 신청 ──
export interface StdRequest {
  id: number
  request_type: string
  action_type: string
  request_data: Record<string, any>
  validation_result?: string
  validation_message?: string
  status: string
  requested_by?: number
  requested_at?: string
  reviewed_by?: number
  reviewed_at?: string
  review_comment?: string
}

// ── 분류체계 ──
export interface Classification {
  id: number
  parent_id?: number | null
  level: number
  name: string
  code: string
  description?: string
  dataset_count: number
  sort_order: number
  status: string
  std_word_id?: number | null
  std_term_id?: number | null
  std_domain_id?: number | null
  std_code_id?: number | null
  std_word_name?: string | null
  std_term_name?: string | null
  std_domain_name?: string | null
  std_code_name?: string | null
  created_at?: string
  updated_at?: string
  children?: Classification[]
}

// ── 데이터 등급 ──
export interface DataGrade {
  id: number
  grade_code: string
  grade_name: string
  description?: string
  access_scope?: string
  dataset_count: number
  anonymize_required?: string
  sort_order: number
}

// ── 품질 ──
export interface QualityRule {
  id: number
  rule_name: string
  rule_type: string
  target_type?: string
  rule_expression?: string
  severity: string
  is_active: boolean
  schedule_cron?: string
  created_at?: string
}

export interface QualityCheckResult {
  id: number
  rule_id?: number
  dataset_name?: string
  check_type?: string
  total_count?: number
  error_count?: number
  score?: number
  executed_at?: string
  execution_time_ms?: number
  details?: Record<string, any>
}

export interface ComplianceResult {
  id: number
  standard_name: string
  category: string
  total_items?: number
  passed_items?: number
  failed_items?: number
  compliance_rate?: number
  checked_at?: string
  details?: Record<string, any>
}

// ── 메타모델 ──
export interface MetaModelAttribute {
  id: number
  attr_name: string
  attr_name_kr?: string
  term_id?: number
  domain_id?: number
  data_type?: string
  length?: number
  decimal_places?: number
  is_pk: boolean
  is_nullable: boolean
  default_value?: string
  description?: string
}

export interface MetaModelEntity {
  id: number
  entity_name: string
  entity_name_kr?: string
  entity_type?: string
  owner?: string
  description?: string
  attributes: MetaModelAttribute[]
}

export interface MetaModel {
  id: number
  model_type: string
  model_name: string
  system_name?: string
  sub_system?: string
  db_account?: string
  description?: string
  version?: string
  classification_id?: number
  status: string
  entities: MetaModelEntity[]
}
