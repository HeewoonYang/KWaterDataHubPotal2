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
    password: str
    name: str
    email: str | None = None
    user_type: str = "INTERNAL"
    employee_no: str | None = None
    department_code: str | None = None
    department_name: str | None = None
    position: str | None = None
    role_code: str = "INTERNAL"

class RoleResponse(BaseModel):
    id: UUID
    role_code: str
    role_name: str
    description: str | None = None
    is_system_role: bool = False
    can_access_admin: bool = False
    sort_order: int = 0
    user_count: int = 0
    model_config = {"from_attributes": True}

class AccessPolicyResponse(BaseModel):
    id: UUID
    policy_name: str
    role_name: str | None = None
    grade_name: str | None = None
    requires_approval: bool = False
    description: str | None = None
    model_config = {"from_attributes": True}


# ── 데이터수집 ──
class DataSourceResponse(BaseModel):
    id: UUID
    source_name: str
    source_type: str
    db_type: str | None = None
    connection_host: str | None = None
    connection_port: int | None = None
    connection_db: str | None = None
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
    model_config = {"from_attributes": True}

class StrategyResponse(BaseModel):
    id: UUID
    strategy_name: str
    strategy_type: str | None = None
    target_data_type: str | None = None
    priority: int = 0
    is_active: bool = True
    model_config = {"from_attributes": True}

class SpatialConfigResponse(BaseModel):
    id: UUID
    config_name: str
    spatial_data_type: str | None = None
    source_url: str | None = None
    coordinate_system: str | None = None
    status: str | None = None
    model_config = {"from_attributes": True}


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
    model_config = {"from_attributes": True}

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
