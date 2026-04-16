"""관리자 포털 스키마"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── 시스템관리 ──
class SystemItemResponse(BaseModel):
    id: UUID
    name: str
    type: str | None = None
    host: str | None = None
    status: str | None = None
    environment: str | None = None
    cpu: float | None = None
    memory: float | None = None
    disk: float | None = None
    last_check: str | None = None
    model_config = {"from_attributes": True}

class CloudConfigResponse(BaseModel):
    id: UUID
    cloud_provider: str
    resource_type: str | None = None
    resource_name: str
    resource_id: str | None = None
    region: str | None = None
    status: str | None = None
    monthly_cost: float | None = None
    model_config = {"from_attributes": True}

class DrBackupResponse(BaseModel):
    id: UUID
    backup_name: str
    backup_type: str
    target_system: str | None = None
    schedule_cron: str | None = None
    retention_days: int | None = None
    last_backup_at: datetime | None = None
    last_backup_status: str | None = None
    model_config = {"from_attributes": True}

class PackageResponse(BaseModel):
    id: UUID
    package_name: str
    package_version: str | None = None
    vendor: str | None = None
    license_type: str | None = None
    license_expiry: str | None = None
    poc_status: str | None = None
    description: str | None = None
    model_config = {"from_attributes": True}

class InterfaceResponse(BaseModel):
    id: UUID
    interface_code: str
    interface_name: str
    interface_type: str
    source_system: str | None = None
    target_system: str | None = None
    endpoint_url: str | None = None
    schedule_type: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class IntegrationResponse(BaseModel):
    id: UUID
    integration_name: str
    source_db_type: str
    sync_direction: str | None = None
    sync_status: str | None = None
    last_sync_at: datetime | None = None
    model_config = {"from_attributes": True}

class DmzLinkResponse(BaseModel):
    id: UUID
    link_name: str
    link_type: str | None = None
    external_url: str | None = None
    transfer_direction: str | None = None
    is_active: bool = True
    model_config = {"from_attributes": True}


# ── 표준 인터페이스 / 이기종 통합 Request ──
class InterfaceCreate(BaseModel):
    interface_name: str
    interface_type: str = "REST"
    source_system: str | None = None
    target_system: str | None = None
    protocol: str | None = "HTTPS"
    endpoint_url: str | None = None
    data_format: str | None = "JSON"
    schedule_type: str | None = "REALTIME"
    schedule_cron: str | None = None
    timeout_ms: int | None = 30000
    retry_count: int | None = 3
    description: str | None = None

class InterfaceUpdate(BaseModel):
    interface_name: str | None = None
    interface_type: str | None = None
    source_system: str | None = None
    target_system: str | None = None
    protocol: str | None = None
    endpoint_url: str | None = None
    data_format: str | None = None
    schedule_type: str | None = None
    schedule_cron: str | None = None
    timeout_ms: int | None = None
    retry_count: int | None = None
    status: str | None = None
    description: str | None = None

class InterfaceDetailResponse(BaseModel):
    id: UUID
    interface_code: str
    interface_name: str
    interface_type: str
    source_system: str | None = None
    target_system: str | None = None
    protocol: str | None = None
    endpoint_url: str | None = None
    data_format: str | None = None
    schedule_type: str | None = None
    schedule_cron: str | None = None
    timeout_ms: int | None = None
    retry_count: int | None = None
    status: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

class IntegrationCreate(BaseModel):
    integration_name: str
    source_db_type: str
    connection_config: dict
    mapping_config: dict | None = None
    sync_direction: str | None = "INBOUND"

class IntegrationUpdate(BaseModel):
    integration_name: str | None = None
    source_db_type: str | None = None
    connection_config: dict | None = None
    mapping_config: dict | None = None
    sync_direction: str | None = None

class IntegrationDetailResponse(BaseModel):
    id: UUID
    integration_name: str
    source_db_type: str
    connection_config: dict | None = None
    mapping_config: dict | None = None
    sync_direction: str | None = None
    sync_status: str | None = None
    last_sync_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

class DmzLinkCreate(BaseModel):
    link_name: str
    link_type: str | None = "PROXY"
    external_url: str | None = None
    dmz_proxy_url: str | None = None
    transfer_direction: str | None = "INBOUND"
    security_level: str | None = None

class DmzLinkUpdate(BaseModel):
    link_name: str | None = None
    link_type: str | None = None
    external_url: str | None = None
    dmz_proxy_url: str | None = None
    transfer_direction: str | None = None
    security_level: str | None = None
    is_active: bool | None = None

class DmzLinkDetailResponse(BaseModel):
    id: UUID
    link_name: str
    link_type: str | None = None
    external_url: str | None = None
    dmz_proxy_url: str | None = None
    transfer_direction: str | None = None
    security_level: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}

class InterfaceLogResponse(BaseModel):
    id: UUID
    interface_id: UUID
    integration_id: UUID | None = None
    execution_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    total_records: int | None = None
    success_records: int | None = None
    error_records: int | None = None
    error_message: str | None = None
    model_config = {"from_attributes": True}


# ── 사용자관리 ──
class UserListResponse(BaseModel):
    id: UUID
    login_id: str
    name: str
    email: str | None = None
    user_type: str
    employee_no: str | None = None
    department_name: str | None = None
    position: str | None = None
    status: str
    last_login_at: datetime | None = None
    role_code: str | None = None
    model_config = {"from_attributes": True}

class UserCreate(BaseModel):
    login_id: str
    password: str | None = None  # send_initial_sms=True 이면 서버가 임시 비밀번호 생성
    name: str
    email: str | None = None
    phone: str | None = None
    user_type: str = "INTERNAL"
    employee_no: str | None = None
    department_code: str | None = None
    department_name: str | None = None
    position: str | None = None
    role_code: str = "INTERNAL"
    send_initial_sms: bool = False  # True 이면 서버에서 임시 비밀번호 생성 후 SMS 발송
    org: str | None = None  # 외부사용자 기관명 (department_name 에 매핑)

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    department_code: str | None = None
    department_name: str | None = None
    position: str | None = None
    role_code: str | None = None
    status: str | None = None
    phone: str | None = None


class RoleResponse(BaseModel):
    id: UUID
    role_code: str
    role_name: str
    role_group: str | None = None
    description: str | None = None
    is_system_role: bool = False
    can_access_admin: bool = False
    sort_order: int = 0
    user_count: int = 0
    model_config = {"from_attributes": True}

class RoleCreate(BaseModel):
    role_code: str
    role_name: str
    role_group: str | None = None
    description: str | None = None
    can_access_admin: bool = False

class RoleUpdate(BaseModel):
    role_name: str | None = None
    role_group: str | None = None
    description: str | None = None
    can_access_admin: bool | None = None


# ── 화면별 권한 ──
class ScreenPermissionResponse(BaseModel):
    id: UUID
    role_id: UUID
    screen_code: str
    screen_name: str | None = None
    screen_group: str | None = None
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    model_config = {"from_attributes": True}

class ScreenPermissionItem(BaseModel):
    screen_code: str
    screen_name: str | None = None
    screen_group: str | None = None
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False

class ScreenPermissionBulkUpdate(BaseModel):
    permissions: list[ScreenPermissionItem]

class ScreenCodeResponse(BaseModel):
    screen_code: str
    screen_name: str
    screen_group: str

class AccessPolicyResponse(BaseModel):
    id: UUID
    policy_name: str
    role_name: str | None = None
    grade_name: str | None = None
    requires_approval: bool = False
    description: str | None = None
    model_config = {"from_attributes": True}

class AccessPolicyCreate(BaseModel):
    policy_name: str
    role_id: UUID | None = None
    data_grade_id: int | None = None
    requires_approval: bool = False
    description: str | None = None

class AccessPolicyUpdate(BaseModel):
    policy_name: str | None = None
    requires_approval: bool | None = None
    description: str | None = None

class AccessRequestResponse(BaseModel):
    id: UUID
    requester_name: str | None = None
    request_type: str | None = None
    requested_role: str | None = None
    requested_grade: str | None = None
    reason: str | None = None
    status: str
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    model_config = {"from_attributes": True}


class CommonSettingsResponse(BaseModel):
    """사용자 공통 설정 응답 - 그룹별"""
    password_policy: dict[str, str]
    session_management: dict[str, str]
    security_settings: dict[str, str]
    notification_settings: dict[str, str]
    security_rules: list[dict] = []
    custom_categories: list[dict] = []

class CommonSettingsUpdate(BaseModel):
    """사용자 공통 설정 일괄 수정"""
    settings: dict[str, str]

class SecurityRuleCreate(BaseModel):
    """보안 규칙 추가"""
    rule_type: str
    rule_name: str
    value: str
    description: str | None = None

class SecurityRuleUpdate(BaseModel):
    """보안 규칙 수정"""
    rule_name: str | None = None
    value: str | None = None
    is_active: bool | None = None
    description: str | None = None

class CustomCategoryCreate(BaseModel):
    """커스텀 카테고리 생성"""
    category_name: str

class CustomSettingCreate(BaseModel):
    """커스텀 카테고리 내 설정 항목 추가"""
    category_key: str
    setting_name: str
    setting_value: str
    setting_type: str = "STRING"


# ── 데이터수집 ──
class StrategyCreate(BaseModel):
    strategy_name: str
    strategy_type: str = "BATCH"
    target_data_type: str | None = None
    priority: int = 0
    description: str | None = None

class DataSourceCreate(BaseModel):
    source_name: str
    source_type: str = "RDBMS"
    db_type: str | None = None
    connection_host: str | None = None
    connection_port: int | None = None
    connection_db: str | None = None
    connection_schema: str | None = None
    connection_user: str | None = None
    # 평문 비밀번호 (서버에서 AES-256-GCM 암호화 후 저장). 빈 문자열/None 이면 기존 값 유지
    connection_password: str | None = None
    connection_options: dict | None = None

class DatasetConfigCreate(BaseModel):
    dataset_name: str
    source_id: UUID | None = None
    source_table: str | None = None
    column_mapping: list | None = None
    classification_id: int | None = None
    grade_id: int | None = None

class ScheduleCreate(BaseModel):
    dataset_config_id: UUID | None = None
    schedule_type: str = "CRON"
    cron_expression: str | None = None
    interval_seconds: int | None = None
    is_active: bool = True

class DataSourceResponse(BaseModel):
    id: UUID
    source_name: str
    source_type: str
    db_type: str | None = None
    connection_host: str | None = None
    connection_port: int | None = None
    connection_db: str | None = None
    connection_schema: str | None = None
    connection_user: str | None = None
    has_password: bool = False  # 비밀번호 설정여부 (복호화 값 노출 금지)
    last_test_result: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class CollectionConfigResponse(BaseModel):
    id: UUID
    dataset_name: str
    source_name: str | None = None
    source_table: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class CollectionJobResponse(BaseModel):
    id: UUID
    dataset_name: str | None = None
    job_status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_rows: int | None = None
    success_rows: int | None = None
    error_rows: int | None = None
    model_config = {"from_attributes": True}

class MigrationResponse(BaseModel):
    id: UUID
    migration_name: str
    migration_type: str | None = None
    status: str | None = None
    total_tables: int | None = None
    completed_tables: int | None = None
    model_config = {"from_attributes": True}

class ExternalAgencyResponse(BaseModel):
    id: UUID
    agency_name: str
    agency_code: str | None = None
    api_endpoint: str | None = None
    protocol: str | None = None
    status: str | None = None
    endpoint_type: str | None = None
    data_type: str | None = None
    schedule_cron: str | None = None
    last_sync_at: datetime | None = None
    # 헬스체크
    health_check_enabled: bool | None = None
    last_health_check_at: datetime | None = None
    last_health_status: str | None = None
    last_health_latency_ms: int | None = None
    last_health_message: str | None = None
    consecutive_failures: int | None = None
    # 핫스왑
    failover_endpoint: str | None = None
    failover_active: bool | None = None
    # 통계
    total_tx_count: int | None = None
    total_success_count: int | None = None
    total_failure_count: int | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    # OpenMetadata
    om_service_name: str | None = None
    om_last_sync_at: datetime | None = None
    om_last_sync_status: str | None = None
    model_config = {"from_attributes": True}


class ExternalAgencyDetailResponse(ExternalAgencyResponse):
    endpoint_config: dict | None = None
    health_check_interval_sec: int | None = None
    health_timeout_sec: int | None = None
    retry_enabled: bool | None = None
    max_retries: int | None = None
    retry_interval_sec: int | None = None
    retry_backoff: str | None = None
    auth_method: str | None = None
    auth_config: dict | None = None
    security_policy: dict | None = None
    alert_enabled: bool | None = None
    alert_threshold_failures: int | None = None
    alert_channels: list | dict | None = None


class ExternalAgencyCreate(BaseModel):
    agency_name: str
    agency_code: str
    endpoint_type: str = "API"  # API/DB/MQ
    api_endpoint: str | None = None
    api_key: str | None = None  # 평문 입력 → 서버에서 암호화
    endpoint_config: dict | None = None
    data_type: str | None = None
    protocol: str | None = None
    schedule_cron: str | None = None
    status: str = "ACTIVE"
    # 점검
    health_check_enabled: bool = True
    health_check_interval_sec: int = 300
    health_timeout_sec: int = 10
    # 재시도/핫스왑
    retry_enabled: bool = True
    max_retries: int = 3
    retry_interval_sec: int = 60
    retry_backoff: str = "EXPONENTIAL"
    failover_endpoint: str | None = None
    # 인증/보안
    auth_method: str = "NONE"
    auth_config: dict | None = None
    security_policy: dict | None = None
    # 알림
    alert_enabled: bool = True
    alert_threshold_failures: int = 3
    alert_channels: list | dict | None = None
    # OpenMetadata
    om_service_name: str | None = None


class ExternalAgencyUpdate(BaseModel):
    agency_name: str | None = None
    endpoint_type: str | None = None
    api_endpoint: str | None = None
    api_key: str | None = None
    endpoint_config: dict | None = None
    data_type: str | None = None
    protocol: str | None = None
    schedule_cron: str | None = None
    status: str | None = None
    health_check_enabled: bool | None = None
    health_check_interval_sec: int | None = None
    health_timeout_sec: int | None = None
    retry_enabled: bool | None = None
    max_retries: int | None = None
    retry_interval_sec: int | None = None
    retry_backoff: str | None = None
    failover_endpoint: str | None = None
    auth_method: str | None = None
    auth_config: dict | None = None
    security_policy: dict | None = None
    alert_enabled: bool | None = None
    alert_threshold_failures: int | None = None
    alert_channels: list | dict | None = None
    om_service_name: str | None = None


class HealthCheckResponse(BaseModel):
    agency_id: UUID
    status: str  # HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN
    latency_ms: int | None = None
    http_status: int | None = None
    error_code: str | None = None
    message: str | None = None
    endpoint_type: str | None = None
    failover_used: bool = False
    checked_at: datetime


class HealthLogResponse(BaseModel):
    id: UUID
    agency_id: UUID
    checked_at: datetime
    check_type: str
    endpoint_type: str | None = None
    status: str
    latency_ms: int | None = None
    http_status: int | None = None
    error_code: str | None = None
    message: str | None = None
    failover_used: bool | None = None
    model_config = {"from_attributes": True}


class ExternalAgencyTxLogResponse(BaseModel):
    id: UUID
    agency_id: UUID
    tx_direction: str
    tx_type: str | None = None
    correlation_id: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: int | None = None
    record_count: int | None = None
    bytes_size: int | None = None
    status: str
    http_status: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_count: int | None = None
    model_config = {"from_attributes": True}


class ExternalAgencyStatsResponse(BaseModel):
    total: int
    active: int
    failed: int
    maintenance: int
    healthy: int
    unhealthy: int
    degraded: int
    by_endpoint_type: dict
    by_status: dict
    availability_7d: float | None = None
    total_tx_24h: int
    success_tx_24h: int
    fail_tx_24h: int
    avg_latency_ms: float | None = None


class FailoverToggleRequest(BaseModel):
    activate: bool
    reason: str | None = None

class StrategyResponse(BaseModel):
    id: UUID
    strategy_name: str
    strategy_type: str | None = None
    target_data_type: str | None = None
    priority: int = 0
    is_active: bool = True
    model_config = {"from_attributes": True}

class SpatialConfigBase(BaseModel):
    config_name: str
    spatial_data_type: str | None = None
    source_url: str | None = None
    coordinate_system: str | None = None
    collection_area: dict | None = None
    status: str | None = "ACTIVE"
    source_system: str | None = None
    connection_config: dict | None = None
    auth_config: dict | None = None
    target_schema: str | None = "spatial_gis"
    target_table: str | None = None
    validation_rules: dict | None = None
    schedule_id: UUID | None = None
    event_trigger_config: dict | None = None


class SpatialConfigCreate(SpatialConfigBase):
    pass


class SpatialConfigUpdate(BaseModel):
    config_name: str | None = None
    spatial_data_type: str | None = None
    source_url: str | None = None
    coordinate_system: str | None = None
    collection_area: dict | None = None
    status: str | None = None
    source_system: str | None = None
    connection_config: dict | None = None
    auth_config: dict | None = None
    target_schema: str | None = None
    target_table: str | None = None
    validation_rules: dict | None = None
    schedule_id: UUID | None = None
    event_trigger_config: dict | None = None


class SpatialConfigResponse(SpatialConfigBase):
    id: UUID
    last_collected_at: datetime | None = None
    last_status: str | None = None
    feature_count: int | None = 0
    last_error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


class SpatialLayerResponse(BaseModel):
    id: UUID
    config_id: UUID
    layer_name: str
    geometry_type: str | None = None
    srid: int | None = None
    attribute_schema: list | dict | None = None
    feature_count: int | None = 0
    last_synced_at: datetime | None = None
    is_enabled: bool = True
    model_config = {"from_attributes": True}


class SpatialHistoryResponse(BaseModel):
    id: UUID
    config_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    status: str
    feature_count: int | None = 0
    invalid_feature_count: int | None = 0
    triggered_by: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    model_config = {"from_attributes": True}


class SpatialConfigDetailResponse(SpatialConfigResponse):
    layers: list[SpatialLayerResponse] = []
    recent_history: list[SpatialHistoryResponse] = []


class SpatialConnectionTestResponse(BaseModel):
    success: bool
    message: str
    detected_version: str | None = None
    layers_preview: list[str] | None = None


class SpatialDiscoverLayersResponse(BaseModel):
    success: bool
    message: str
    layers: list[SpatialLayerResponse] = []


class SpatialRunResponse(BaseModel):
    success: bool
    message: str
    history_id: UUID | None = None


# ── 데이터정제 ──
class CleansingRuleResponse(BaseModel):
    id: UUID
    rule_name: str
    rule_type: str
    target_column_type: str | None = None
    severity: str | None = None
    is_active: bool = True
    model_config = {"from_attributes": True}

class CleansingJobResponse(BaseModel):
    id: UUID
    job_name: str
    job_status: str | None = None
    total_rows: int | None = None
    cleansed_rows: int | None = None
    error_rows: int | None = None
    started_at: datetime | None = None
    rule_ids: list[str] = []
    model_config = {"from_attributes": True}

class AnonymizationResponse(BaseModel):
    id: UUID
    config_name: str
    method: str
    is_active: bool = True
    target_columns: list | None = None
    description: str | None = None
    model_config = {"from_attributes": True}

class AnonymizationCreate(BaseModel):
    config_name: str
    dataset_id: UUID | None = None
    target_columns: list | None = None
    method: str = "MASKING"
    method_config: dict | None = None
    description: str | None = None

class AnonymizationUpdate(BaseModel):
    config_name: str | None = None
    target_columns: list | None = None
    method: str | None = None
    method_config: dict | None = None
    is_active: bool | None = None
    description: str | None = None

class TransformResponse(BaseModel):
    id: UUID
    model_name: str
    transform_type: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}


# ── 데이터저장 ──
class StorageZoneResponse(BaseModel):
    id: UUID
    zone_name: str
    zone_code: str
    zone_type: str
    storage_type: str | None = None
    max_capacity_gb: float | None = None
    used_capacity_gb: float | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class HighspeedDbResponse(BaseModel):
    id: UUID
    db_name: str
    db_type: str
    purpose: str | None = None
    max_memory_gb: float | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class UnstructuredResponse(BaseModel):
    id: UUID
    storage_name: str
    storage_type: str
    bucket_name: str | None = None
    total_capacity_gb: float | None = None
    used_capacity_gb: float | None = None
    status: str | None = None
    model_config = {"from_attributes": True}


# ── 비정형데이터관리 ──
class UnstructuredDocCreate(BaseModel):
    doc_name: str
    doc_type: str = "MANUAL"
    description: str | None = None
    storage_id: UUID | None = None
    tags: list[str] | None = None

class UnstructuredDocUpdate(BaseModel):
    doc_name: str | None = None
    doc_type: str | None = None
    description: str | None = None
    storage_id: UUID | None = None
    tags: list[str] | None = None

class UnstructuredDocResponse(BaseModel):
    id: UUID
    doc_name: str
    doc_type: str
    description: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    content_type: str | None = None
    processing_status: str = "PENDING"
    extracted_entity_count: int = 0
    graph_node_count: int = 0
    graph_integrated: bool = False
    tags: list | None = None
    uploaded_at: datetime | None = None
    created_at: datetime | None = None
    model_config = {"from_attributes": True}

class UnstructuredDocDetailResponse(UnstructuredDocResponse):
    stored_name: str | None = None
    storage_id: UUID | None = None
    updated_at: datetime | None = None
    ontology_usages: list["OntologyUsageResponse"] = []
    model_config = {"from_attributes": True}

class OntologyUsageResponse(BaseModel):
    id: UUID
    ontology_class: str
    entity_count: int = 0
    relation_count: int = 0
    last_synced_at: datetime | None = None
    status: str = "ACTIVE"
    review_status: str = "PENDING_REVIEW"
    reviewed_by: UUID | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None
    model_config = {"from_attributes": True}


# ── 데이터유통 ──
class DistConfigResponse(BaseModel):
    id: UUID
    config_name: str
    column_change_policy: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class DistFormatResponse(BaseModel):
    id: UUID
    format_code: str
    format_name: str
    mime_type: str | None = None
    file_extension: str | None = None
    is_active: bool = True
    model_config = {"from_attributes": True}

class ApiEndpointResponse(BaseModel):
    id: UUID
    api_name: str
    api_path: str
    http_method: str
    rate_limit_per_min: int | None = None
    requires_auth: bool = True
    status: str | None = None
    model_config = {"from_attributes": True}

class McpConfigResponse(BaseModel):
    id: UUID
    mcp_name: str
    server_url: str | None = None
    transport_type: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class FusionModelResponse(BaseModel):
    id: UUID
    model_name: str
    fusion_type: str | None = None
    poc_status: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}

class DistStatsResponse(BaseModel):
    id: UUID
    stat_date: str | None = None
    stat_type: str | None = None
    view_count: int = 0
    download_count: int = 0
    api_call_count: int = 0
    unique_users: int = 0
    model_config = {"from_attributes": True}


# ── 운영관리 ──
class HubStatsResponse(BaseModel):
    id: UUID
    stat_date: str | None = None
    stat_type: str | None = None
    total_datasets: int = 0
    total_users: int = 0
    active_users: int = 0
    total_downloads: int = 0
    total_api_calls: int = 0
    data_quality_score: float | None = None
    collection_success_rate: float | None = None
    model_config = {"from_attributes": True}

class AiMonitorResponse(BaseModel):
    id: UUID
    query_type: str | None = None
    model_name: str | None = None
    token_count: int | None = None
    response_time_ms: int | None = None
    satisfaction_rating: int | None = None
    queried_at: datetime | None = None
    model_config = {"from_attributes": True}

class SystemEventResponse(BaseModel):
    id: UUID
    event_type: str
    severity: str | None = None
    title: str
    description: str | None = None
    occurred_at: datetime | None = None
    resolved_at: datetime | None = None
    model_config = {"from_attributes": True}
