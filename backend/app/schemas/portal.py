"""포털 전용 스키마 (대시보드, 카탈로그, 유통, 시각화, 사용자, AI)"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


# ── 대시보드 ──
class DashboardSummary(BaseModel):
    total_datasets: int = 0
    today_collection: int = 0
    today_load: int = 0
    active_users: int = 0
    storage_used_gb: float = 0
    storage_total_gb: float = 5000
    quality_score: float = 0


class CollectionTrendItem(BaseModel):
    day: str
    collect: int = 0
    load: int = 0


class CategoryStatItem(BaseModel):
    name: str
    count: int
    color: str = "#0066CC"


class RecentDataItem(BaseModel):
    id: UUID
    name: str
    data_format: str | None = None
    date: str

    model_config = {"from_attributes": True}


class NoticeItem(BaseModel):
    id: UUID
    title: str
    date: str


# ── 카탈로그 ──
class CatalogDatasetListItem(BaseModel):
    id: UUID
    dataset_name: str
    dataset_name_kr: str | None = None
    classification_name: str | None = None
    grade_code: str | None = None
    source_system: str | None = None
    owner_department: str | None = None
    data_format: str | None = None
    refresh_frequency: str | None = None
    row_count: int | None = None
    size_bytes: int | None = None
    tags: list | None = None
    description: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CatalogColumnResponse(BaseModel):
    column_name: str
    column_name_kr: str | None = None
    data_type: str | None = None
    length: int | None = None
    is_pk: bool = False
    is_nullable: bool = True
    description: str | None = None

    model_config = {"from_attributes": True}


class CatalogDatasetDetail(CatalogDatasetListItem):
    columns: list[CatalogColumnResponse] = []


class CategoryTreeItem(BaseModel):
    id: int
    name: str
    code: str
    count: int = 0
    children: list["CategoryTreeItem"] = []


# ── 유통 ──
class DistDatasetListItem(BaseModel):
    id: UUID
    distribution_name: str
    dataset_name: str | None = None
    classification_name: str | None = None
    grade_code: str | None = None
    owner_department: str | None = None
    is_downloadable: bool = True
    allowed_formats: list | None = None
    requires_approval: bool = False
    view_count: int | None = 0
    download_count: int | None = 0

    model_config = {"from_attributes": True}


class DistRequestCreate(BaseModel):
    dataset_ids: list[UUID]
    request_type: str = "DOWNLOAD"
    requested_format: str = "CSV"
    purpose: str = ""


class DistRequestResponse(BaseModel):
    id: UUID
    request_type: str | None = None
    requested_format: str | None = None
    purpose: str | None = None
    status: str
    dataset_ids: list[str] = []
    dataset_name: str | None = None
    dataset_name_kr: str | None = None
    created_at: datetime | None = None
    approved_at: datetime | None = None

    model_config = {"from_attributes": True}


class DistDownloadItem(BaseModel):
    id: UUID
    dataset_name: str | None = None
    download_format: str | None = None
    row_count: int | None = None
    file_size_bytes: int | None = None
    downloaded_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── API 키 ──
class ApiKeyResponse(BaseModel):
    id: UUID
    api_key: str | None = None
    api_key_prefix: str = ""
    name: str = ""
    endpoint: str = ""
    rate_limit_per_min: int = 60
    expires_at: datetime | None = None
    issued_at: datetime | None = None
    last_used_at: datetime | None = None
    total_calls: int = 0
    is_active: bool = True

    model_config = {"from_attributes": True}


# ── 시각화 ──
class DataSourceItem(BaseModel):
    id: UUID
    dataset_name: str
    data_format: str | None = None

    model_config = {"from_attributes": True}


class DatasetColumnItem(BaseModel):
    column_name: str
    column_name_kr: str | None = None
    data_type: str | None = None

    model_config = {"from_attributes": True}


class ChartCreate(BaseModel):
    chart_name: str
    chart_type: str
    dataset_id: UUID | None = None
    chart_config: dict = {}
    is_public: bool = False


class ChartResponse(BaseModel):
    id: UUID
    chart_name: str
    chart_type: str
    dataset_id: UUID | None = None
    chart_config: dict = {}
    is_public: bool = False
    view_count: int = 0
    owner_name: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 사용자 ──
class BookmarkCreate(BaseModel):
    resource_type: str
    resource_id: UUID
    resource_name: str | None = None


class BookmarkResponse(BaseModel):
    id: UUID
    resource_type: str
    resource_id: UUID
    resource_name: str | None = None
    bookmarked_at: datetime | None = None

    model_config = {"from_attributes": True}


class RecentViewResponse(BaseModel):
    id: UUID
    resource_type: str | None = None
    resource_id: UUID | None = None
    resource_name: str | None = None
    viewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str | None = None
    link_url: str | None = None
    is_read: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationSettingItem(BaseModel):
    notification_type: str
    is_enabled: bool = True
    channel: str = "WEB"


class NotificationSettingsUpdate(BaseModel):
    settings: list[NotificationSettingItem]


# ── 리니지 ──
class LineageNodeResponse(BaseModel):
    id: UUID
    dataset_name: str | None = None
    dataset_name_kr: str | None = None
    node_type: str = "DATASET"  # DATASET, EXTERNAL, TRANSFORM
    source_system: str | None = None
    owner_department: str | None = None
    data_format: str | None = None
    row_count: int | None = None
    quality_score: float | None = None
    status: str | None = None
    model_config = {"from_attributes": True}


class LineageEdgeResponse(BaseModel):
    id: UUID
    upstream_id: str | None = None
    downstream_id: str | None = None
    upstream_name: str | None = None
    downstream_name: str | None = None
    lineage_type: str | None = None
    pipeline_name: str | None = None
    description: str | None = None
    model_config = {"from_attributes": True}


class LineageGraphResponse(BaseModel):
    nodes: list[LineageNodeResponse] = []
    edges: list[LineageEdgeResponse] = []


# ── AI 검색 ──
class AiSearchRequest(BaseModel):
    query: str


class AiDatasetResult(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    data_format: str | None = None
    relevance: str = "관련"


class AiChartResult(BaseModel):
    id: UUID
    chart_name: str
    chart_type: str
    dataset_id: UUID | None = None
    dataset_name: str | None = None
    created_at: datetime | None = None


class AiSearchResponse(BaseModel):
    answer: str
    datasets: list[AiDatasetResult] = []
    charts: list[AiChartResult] = []
