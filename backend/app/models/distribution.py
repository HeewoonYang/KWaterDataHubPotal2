"""SA-08. 데이터유통 (15개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class DistributionConfig(AuditMixin, Base):
    """유통구성"""
    __tablename__ = "distribution_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="유통구성ID")
    config_name = Column(String(200), nullable=False, comment="구성명")
    source_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="원본데이터셋ID")
    target_db_config = Column(JSONB, comment="유통DB연결설정")
    migration_schedule = Column(String(100), comment="마이그레이션스케줄")
    column_change_policy = Column(String(50), comment="컬럼변경정책 (AUTO_APPROVE/REQUIRE_APPROVAL)")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_distribution_config_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "유통구성"},
    )


class DistributionDataset(AuditMixin, Base):
    """유통데이터셋"""
    __tablename__ = "distribution_dataset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="유통데이터셋ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="카탈로그데이터셋ID")
    distribution_name = Column(String(300), nullable=False, comment="유통명")
    classification_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="분류ID")
    grade_id = Column(Integer, ForeignKey("data_grade.id", ondelete="SET NULL"), comment="등급ID")
    is_downloadable = Column(Boolean, default=True, comment="다운로드가능여부")
    allowed_formats = Column(JSONB, comment="허용포맷목록")
    max_download_rows = Column(Integer, comment="최대다운로드건수")
    requires_approval = Column(Boolean, default=False, comment="승인필요여부")
    description = Column(Text, comment="설명")
    view_count = Column(Integer, default=0, comment="조회수")
    download_count = Column(Integer, default=0, comment="다운로드수")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_dist_ds_dataset", "dataset_id"),
        Index("ix_dist_ds_class", "classification_id"),
        Index("ix_dist_ds_grade", "grade_id"),
        Index("ix_distribution_dataset_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "유통데이터셋"},
    )


class DistributionFormat(Base):
    """유통포맷"""
    __tablename__ = "distribution_format"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="유통포맷ID")
    format_code = Column(String(20), nullable=False, unique=True, comment="포맷코드 (CSV/JSON/XML/PARQUET/XLSX)")
    format_name = Column(String(100), nullable=False, comment="포맷명")
    mime_type = Column(String(100), comment="MIME타입")
    file_extension = Column(String(10), comment="파일확장자")
    description = Column(Text, comment="설명")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "유통포맷"},
    )


class DistributionRequest(AuditMixin, Base):
    """유통신청"""
    __tablename__ = "distribution_request"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="유통신청ID")
    requester_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="신청자ID")
    dataset_ids = Column(JSONB, nullable=False, comment="신청데이터셋ID목록 (deprecated, use distribution_request_dataset)")
    request_type = Column(String(20), comment="신청유형 (DOWNLOAD/SHARE/API_ACCESS)")
    requested_format = Column(String(20), comment="요청포맷")
    purpose = Column(Text, comment="사용목적")
    status = Column(String(20), default="PENDING", comment="신청상태 (PENDING/APPROVED/REJECTED/COMPLETED)")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="승인자ID")
    approved_at = Column(DateTime, comment="승인일시")
    valid_until = Column(DateTime, comment="유효기한")

    __table_args__ = (
        Index("ix_dist_req_requester", "requester_id"),
        Index("ix_dist_req_status", "status"),
        Index("ix_distribution_request_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "유통신청"},
    )


class DistributionDownloadLog(Base):
    """다운로드이력"""
    __tablename__ = "distribution_download_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="다운로드이력ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), nullable=False, comment="사용자ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("distribution_dataset.id", ondelete="SET NULL"), nullable=False, comment="유통데이터셋ID")
    request_id = Column(UUID(as_uuid=True), ForeignKey("distribution_request.id", ondelete="SET NULL"), comment="신청ID")
    download_format = Column(String(20), comment="다운로드포맷")
    row_count = Column(BigInteger, comment="건수")
    file_size_bytes = Column(BigInteger, comment="파일크기")
    client_ip = Column(String(45), comment="클라이언트IP")
    downloaded_at = Column(DateTime, default=datetime.now, comment="다운로드일시")

    __table_args__ = (
        Index("ix_dl_log_user", "user_id"),
        Index("ix_dl_log_date", "downloaded_at"),
        {"comment": "다운로드이력"},
    )


class DistributionApiEndpoint(AuditMixin, Base):
    """표준API관리"""
    __tablename__ = "distribution_api_endpoint"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="API엔드포인트ID")
    api_name = Column(String(200), nullable=False, comment="API명")
    api_path = Column(String(500), nullable=False, unique=True, comment="API경로")
    http_method = Column(String(10), nullable=False, comment="HTTP메서드 (GET/POST)")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("distribution_dataset.id", ondelete="SET NULL"), comment="유통데이터셋ID")
    description = Column(Text, comment="설명")
    request_schema = Column(JSONB, comment="요청스키마")
    response_schema = Column(JSONB, comment="응답스키마")
    rate_limit_per_min = Column(Integer, default=60, comment="분당제한횟수")
    requires_auth = Column(Boolean, default=True, comment="인증필요여부")
    version = Column(String(10), default="v1", comment="API버전")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_dist_api_path", "api_path"),
        Index("ix_distribution_api_endpoint_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "표준API관리"},
    )


class DistributionApiKey(AuditMixin, Base):
    """API키관리"""
    __tablename__ = "distribution_api_key"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="API키ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="소유자ID")
    api_key_hash = Column(String(255), nullable=False, unique=True, comment="API키해시")
    api_key_prefix = Column(String(10), comment="API키접두사")
    name = Column(String(200), comment="키명")
    allowed_endpoints = Column(JSONB, comment="허용API목록 (deprecated, use distribution_api_key_endpoint)")
    rate_limit_per_min = Column(Integer, default=60, comment="분당제한횟수")
    expires_at = Column(DateTime, comment="만료일시")
    last_used_at = Column(DateTime, comment="최근사용일시")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        Index("ix_api_key_user", "user_id"),
        Index("ix_distribution_api_key_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "API키관리"},
    )


class DistributionApiUsageLog(Base):
    """API사용로그"""
    __tablename__ = "distribution_api_usage_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="API사용로그ID")
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("distribution_api_key.id", ondelete="SET NULL"), comment="API키ID")
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("distribution_api_endpoint.id", ondelete="SET NULL"), comment="엔드포인트ID")
    client_ip = Column(String(45), comment="클라이언트IP")
    request_params = Column(JSONB, comment="요청파라미터")
    response_status = Column(Integer, comment="응답상태코드")
    response_time_ms = Column(Integer, comment="응답시간MS")
    called_at = Column(DateTime, default=datetime.now, comment="호출일시")

    __table_args__ = (
        Index("ix_api_usage_key", "api_key_id"),
        Index("ix_api_usage_date", "called_at"),
        {"comment": "API사용로그"},
    )


class DistributionMcpConfig(AuditMixin, Base):
    """MCP연동설정"""
    __tablename__ = "distribution_mcp_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="MCP설정ID")
    mcp_name = Column(String(200), nullable=False, comment="MCP서버명")
    server_url = Column(String(500), comment="서버URL")
    transport_type = Column(String(50), comment="전송유형 (STDIO/SSE/HTTP)")
    auth_config = Column(JSONB, comment="인증설정")
    tool_definitions = Column(JSONB, comment="Tool정의목록")
    resource_definitions = Column(JSONB, comment="Resource정의목록")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_distribution_mcp_config_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "MCP연동설정"},
    )


class DistributionFusionModel(AuditMixin, Base):
    """융합모델"""
    __tablename__ = "distribution_fusion_model"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="융합모델ID")
    model_name = Column(String(200), nullable=False, comment="모델명")
    source_datasets = Column(JSONB, nullable=False, comment="원본데이터셋ID목록 (deprecated, use distribution_fusion_source)")
    fusion_type = Column(String(50), comment="융합유형 (JOIN/MERGE/AGGREGATE)")
    fusion_config = Column(JSONB, comment="융합설정")
    output_schema = Column(JSONB, comment="출력스키마")
    poc_status = Column(String(20), comment="PoC상태 (NOT_STARTED/IN_PROGRESS/COMPLETED)")
    status = Column(String(20), default="DRAFT", comment="상태")

    __table_args__ = (
        Index("ix_distribution_fusion_model_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "융합모델"},
    )


class DistributionStats(Base):
    """유통통계"""
    __tablename__ = "distribution_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="유통통계ID")
    stat_date = Column(Date, nullable=False, comment="통계일자")
    stat_type = Column(String(50), nullable=False, comment="통계유형 (DAILY/WEEKLY/MONTHLY)")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("distribution_dataset.id", ondelete="SET NULL"), comment="유통데이터셋ID")
    view_count = Column(Integer, default=0, comment="조회수")
    download_count = Column(Integer, default=0, comment="다운로드수")
    api_call_count = Column(Integer, default=0, comment="API호출수")
    unique_users = Column(Integer, default=0, comment="순사용자수")
    total_bytes_served = Column(BigInteger, default=0, comment="총전송바이트")

    __table_args__ = (
        Index("uq_dist_stats", "stat_date", "stat_type", "dataset_id", unique=True),
        {"comment": "유통통계"},
    )


class DistributionRequestDataset(Base):
    """유통신청데이터셋매핑"""
    __tablename__ = "distribution_request_dataset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="매핑ID")
    request_id = Column(UUID(as_uuid=True), ForeignKey("distribution_request.id", ondelete="CASCADE"), nullable=False, comment="신청ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("distribution_dataset.id", ondelete="CASCADE"), nullable=False, comment="유통데이터셋ID")

    __table_args__ = (
        Index("uq_dist_req_ds", "request_id", "dataset_id", unique=True),
        {"comment": "유통신청데이터셋매핑"},
    )


class DistributionFusionSource(Base):
    """융합모델원본데이터셋매핑"""
    __tablename__ = "distribution_fusion_source"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="매핑ID")
    fusion_model_id = Column(UUID(as_uuid=True), ForeignKey("distribution_fusion_model.id", ondelete="CASCADE"), nullable=False, comment="융합모델ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    sort_order = Column(Integer, default=0, comment="순서")

    __table_args__ = (
        Index("uq_fusion_source", "fusion_model_id", "dataset_id", unique=True),
        {"comment": "융합모델원본데이터셋매핑"},
    )


class DistributionApiKeyEndpoint(Base):
    """API키엔드포인트매핑"""
    __tablename__ = "distribution_api_key_endpoint"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="매핑ID")
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("distribution_api_key.id", ondelete="CASCADE"), nullable=False, comment="API키ID")
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("distribution_api_endpoint.id", ondelete="CASCADE"), nullable=False, comment="엔드포인트ID")

    __table_args__ = (
        Index("uq_apikey_endpoint", "api_key_id", "endpoint_id", unique=True),
        {"comment": "API키엔드포인트매핑"},
    )
