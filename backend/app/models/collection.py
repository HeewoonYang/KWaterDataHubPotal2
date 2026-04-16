"""SA-05. 데이터수집 (8개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class CollectionStrategy(AuditMixin, Base):
    """수집전략"""
    __tablename__ = "collection_strategy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="수집전략ID")
    strategy_name = Column(String(200), nullable=False, comment="전략명")
    strategy_type = Column(String(50), comment="전략유형 (BATCH/REALTIME/CDC/FILE_UPLOAD)")
    description = Column(Text, comment="설명")
    target_data_type = Column(String(50), comment="대상데이터유형 (STRUCTURED/SEMI_STRUCTURED/UNSTRUCTURED)")
    priority = Column(Integer, default=0, comment="우선순위")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "수집전략"},
    )


class CollectionDataSource(AuditMixin, Base):
    """수집원천데이터소스"""
    __tablename__ = "collection_data_source"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="데이터소스ID")
    source_name = Column(String(200), nullable=False, comment="소스명")
    source_type = Column(String(50), nullable=False, comment="소스유형 (RDBMS/FILE/API/KAFKA/IoT)")
    db_type = Column(String(50), comment="DB유형 (ORACLE/SAP_HANA/TIBERO/POSTGRESQL)")
    connection_host = Column(String(500), comment="접속호스트")
    connection_port = Column(Integer, comment="접속포트")
    connection_db = Column(String(200), comment="접속DB명")
    connection_schema = Column(String(200), comment="접속스키마명")
    connection_user = Column(String(200), comment="접속계정")
    connection_password_enc = Column(String(1000), comment="접속비밀번호 (AES-256-GCM 암호화, prefix enc:v1:)")
    connection_options = Column(JSONB, comment="접속옵션")
    last_test_at = Column(DateTime, comment="최근연결테스트일시")
    last_test_result = Column(String(20), comment="최근연결테스트결과 (SUCCESS/FAIL)")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_coll_src_type", "source_type"),
        Index("ix_coll_src_status", "status"),
        {"comment": "수집원천데이터소스"},
    )


class CollectionDatasetConfig(AuditMixin, Base):
    """수집데이터셋구성"""
    __tablename__ = "collection_dataset_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="수집데이터셋구성ID")
    source_id = Column(UUID(as_uuid=True), ForeignKey("collection_data_source.id", ondelete="CASCADE"), nullable=False, comment="데이터소스ID")
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("collection_strategy.id", ondelete="SET NULL"), comment="수집전략ID")
    dataset_name = Column(String(300), nullable=False, comment="데이터셋명")
    source_table = Column(String(200), comment="원본테이블명")
    source_query = Column(Text, comment="수집쿼리")
    column_mapping = Column(JSONB, comment="컬럼매핑")
    incremental_column = Column(String(200), comment="증분기준컬럼")
    filter_condition = Column(Text, comment="필터조건")
    target_classification_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="대상분류ID")
    target_grade_id = Column(Integer, ForeignKey("data_grade.id", ondelete="SET NULL"), comment="대상등급ID")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_coll_ds_source", "source_id"),
        {"comment": "수집데이터셋구성"},
    )


class CollectionSchedule(AuditMixin, Base):
    """수집스케줄"""
    __tablename__ = "collection_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="수집스케줄ID")
    dataset_config_id = Column(UUID(as_uuid=True), ForeignKey("collection_dataset_config.id", ondelete="CASCADE"), nullable=False, comment="수집데이터셋구성ID")
    schedule_type = Column(String(20), nullable=False, comment="스케줄유형 (CRON/INTERVAL/ONCE)")
    schedule_cron = Column(String(100), comment="스케줄CRON")
    interval_seconds = Column(Integer, comment="간격초")
    start_time = Column(DateTime, comment="시작시간")
    end_time = Column(DateTime, comment="종료시간")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "수집스케줄"},
    )


class CollectionJob(Base):
    """수집작업실행이력"""
    __tablename__ = "collection_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="수집작업ID")
    dataset_config_id = Column(UUID(as_uuid=True), ForeignKey("collection_dataset_config.id", ondelete="CASCADE"), nullable=False, comment="수집데이터셋구성ID")
    job_status = Column(String(20), nullable=False, comment="작업상태 (QUEUED/RUNNING/SUCCESS/FAIL/CANCELLED)")
    started_at = Column(DateTime, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    total_rows = Column(BigInteger, comment="총처리건수")
    success_rows = Column(BigInteger, comment="성공건수")
    error_rows = Column(BigInteger, comment="오류건수")
    error_message = Column(Text, comment="오류메시지")
    execution_log = Column(JSONB, comment="실행로그")
    celery_task_id = Column(String(200), comment="Celery작업ID")
    catalog_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="등록된카탈로그데이터셋ID")
    # 실패 사유 자동 분류 (REQ-DHUB-005-002-003 피드백 체계)
    failure_category = Column(String(50), comment="실패카테고리 (CONNECTION_ERROR/SCHEMA_MISMATCH/DATA_TYPE_ERROR/PERMISSION_DENIED/TIMEOUT/QUOTA_EXCEEDED/QUALITY_FAIL/UNKNOWN)")
    failure_detail = Column(JSONB, comment="실패상세 (분류 근거/추천조치)")
    # 품질 검증 자동 연계 (REQ-DHUB-004-004 + 005-002)
    quality_score = Column(Numeric(5, 2), comment="수집후품질점수")
    quality_check_at = Column(DateTime, comment="품질검증일시")

    __table_args__ = (
        Index("ix_coll_job_config", "dataset_config_id"),
        Index("ix_coll_job_status", "job_status"),
        Index("ix_coll_job_start", "started_at"),
        Index("ix_coll_job_failure_cat", "failure_category"),
        {"comment": "수집작업실행이력"},
    )


class CollectionAlertConfig(AuditMixin, Base):
    """수집장애 알람 설정 (REQ-DHUB-005-002-003)"""
    __tablename__ = "collection_alert_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="알람설정ID")
    config_name = Column(String(200), nullable=False, comment="알람명")
    channel_type = Column(String(30), nullable=False, comment="채널유형 (WEBHOOK/SLACK/TEAMS/EMAIL)")
    webhook_url = Column(String(1000), comment="웹훅URL")
    email_to = Column(String(500), comment="이메일수신자(콤마구분)")
    trigger_type = Column(String(50), nullable=False, comment="트리거유형 (CONSECUTIVE_FAIL/FAILURE_RATE/QUALITY_FAIL/CATEGORY_MATCH)")
    threshold = Column(Integer, default=1, comment="임계값 (연속실패횟수 또는 실패율%)")
    period_minutes = Column(Integer, default=60, comment="평가주기(분)")
    failure_categories = Column(JSONB, comment="감시대상 실패카테고리 배열 (CATEGORY_MATCH 트리거용)")
    target_source_id = Column(UUID(as_uuid=True), ForeignKey("collection_data_source.id", ondelete="CASCADE"), comment="대상소스ID(NULL=전체)")
    severity = Column(String(20), default="WARNING", comment="심각도 (INFO/WARNING/ERROR/CRITICAL)")
    enabled = Column(Boolean, default=True, comment="활성여부")
    last_triggered_at = Column(DateTime, comment="최근발송일시")
    last_triggered_status = Column(String(30), comment="최근발송상태 (SENT/FAILED)")
    last_triggered_error = Column(Text, comment="최근발송오류")
    trigger_count = Column(Integer, default=0, comment="누적발송횟수")

    __table_args__ = (
        Index("ix_coll_alert_enabled", "enabled"),
        Index("ix_coll_alert_trigger", "trigger_type"),
        Index("ix_coll_alert_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "수집장애 알람 설정"},
    )


class CollectionMigration(AuditMixin, Base):
    """DB복제마이그레이션"""
    __tablename__ = "collection_migration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="마이그레이션ID")
    migration_name = Column(String(200), nullable=False, comment="마이그레이션명")
    source_id = Column(UUID(as_uuid=True), ForeignKey("collection_data_source.id", ondelete="CASCADE"), nullable=False, comment="원본소스ID")
    target_storage_zone = Column(String(200), comment="대상저장영역")
    table_list = Column(JSONB, comment="대상테이블목록")
    migration_type = Column(String(50), comment="마이그레이션유형 (FULL/INCREMENTAL/CDC)")
    status = Column(String(20), default="PENDING", comment="상태 (PENDING/RUNNING/COMPLETED/FAILED)")
    started_at = Column(DateTime, comment="시작일시")
    completed_at = Column(DateTime, comment="완료일시")
    total_tables = Column(Integer, comment="총테이블수")
    completed_tables = Column(Integer, comment="완료테이블수")
    error_log = Column(JSONB, comment="오류로그")

    __table_args__ = (
        {"comment": "DB복제마이그레이션"},
    )


class CollectionExternalAgency(AuditMixin, Base):
    """외부기관연계"""
    __tablename__ = "collection_external_agency"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="외부기관ID")
    agency_name = Column(String(200), nullable=False, comment="기관명")
    agency_code = Column(String(50), unique=True, comment="기관코드")
    api_endpoint = Column(String(500), comment="API엔드포인트")
    api_key_enc = Column(String(1000), comment="API키 (AES-256-GCM 암호화, prefix enc:v1:)")
    data_type = Column(String(50), comment="데이터유형")
    protocol = Column(String(50), comment="프로토콜 (REST/SOAP/FILE)")
    schedule_cron = Column(String(100), comment="수집주기CRON")
    last_sync_at = Column(DateTime, comment="최근동기화일시")
    status = Column(String(20), default="ACTIVE", comment="상태 (ACTIVE/INACTIVE/MAINTENANCE/FAILED)")

    # ── REQ-DHUB-005-005-001: 연계 포인트 점검 ─────────────────────────
    endpoint_type = Column(String(20), default="API", comment="연계포인트 유형 (API/DB/MQ)")
    endpoint_config = Column(JSONB, comment="점검 파라미터 (DB: host/port/user/pwd_enc, MQ: brokers/topic, API: path/method)")
    health_check_enabled = Column(Boolean, default=True, comment="자동점검 활성화")
    health_check_interval_sec = Column(Integer, default=300, comment="자동점검주기(초)")
    health_timeout_sec = Column(Integer, default=10, comment="점검 타임아웃(초)")
    last_health_check_at = Column(DateTime, comment="최근 점검 일시")
    last_health_status = Column(String(20), comment="최근 점검 결과 (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)")
    last_health_latency_ms = Column(Integer, comment="최근 응답시간(ms)")
    last_health_message = Column(Text, comment="최근 점검 메시지/오류")
    consecutive_failures = Column(Integer, default=0, comment="연속 실패 횟수")

    # ── 재시도/핫스왑/보안 ────────────────────────────────────────────
    retry_enabled = Column(Boolean, default=True, comment="자동 재시도 활성화")
    max_retries = Column(Integer, default=3, comment="최대 재시도 횟수")
    retry_interval_sec = Column(Integer, default=60, comment="재시도 간격(초)")
    retry_backoff = Column(String(20), default="EXPONENTIAL", comment="재시도 백오프 전략 (FIXED/EXPONENTIAL)")
    failover_endpoint = Column(String(500), comment="핫스왑 대체 엔드포인트")
    failover_active = Column(Boolean, default=False, comment="핫스왑 활성화 상태")
    failover_activated_at = Column(DateTime, comment="핫스왑 전환 일시")
    auth_method = Column(String(30), default="NONE", comment="인증 방식 (NONE/API_KEY/BASIC/OAUTH2/MTLS)")
    auth_config = Column(JSONB, comment="인증 상세 (OAuth token URL, Basic user 등)")
    security_policy = Column(JSONB, comment="보안 정책 (TLS 필수, IP allowlist, RateLimit)")

    # ── 알림 설정 ────────────────────────────────────────────────────
    alert_enabled = Column(Boolean, default=True, comment="장애 알림 활성화")
    alert_threshold_failures = Column(Integer, default=3, comment="연속실패 N회 이상 시 알림")
    alert_channels = Column(JSONB, comment="알림 채널 목록 (EMAIL/SMS/WEBHOOK)")
    alert_last_sent_at = Column(DateTime, comment="최근 알림 발송 일시")

    # ── OpenMetadata 연계 ────────────────────────────────────────────
    om_service_name = Column(String(200), comment="OpenMetadata 서비스명")
    om_last_sync_at = Column(DateTime, comment="OpenMetadata 최근 동기화 일시")
    om_last_sync_status = Column(String(20), comment="OpenMetadata 동기화 상태")

    # ── 집계 통계 ────────────────────────────────────────────────────
    total_tx_count = Column(BigInteger, default=0, comment="총 송수신 건수")
    total_success_count = Column(BigInteger, default=0, comment="총 성공 건수")
    total_failure_count = Column(BigInteger, default=0, comment="총 실패 건수")
    last_success_at = Column(DateTime, comment="최근 성공 일시")
    last_failure_at = Column(DateTime, comment="최근 실패 일시")

    __table_args__ = (
        Index("ix_collection_external_agency_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        Index("ix_collection_external_agency_status", "status"),
        Index("ix_collection_external_agency_endpoint_type", "endpoint_type"),
        {"comment": "외부기관연계"},
    )


class CollectionExternalAgencyHealthLog(Base):
    """외부기관 연계포인트 점검 이력 (REQ-DHUB-005-005-001)"""
    __tablename__ = "collection_external_agency_health_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="점검이력ID")
    agency_id = Column(UUID(as_uuid=True), ForeignKey("collection_external_agency.id", ondelete="CASCADE"),
                       nullable=False, comment="기관ID")
    checked_at = Column(DateTime, default=datetime.now, nullable=False, comment="점검일시")
    check_type = Column(String(20), nullable=False, comment="점검유형 (SCHEDULED/MANUAL)")
    endpoint_type = Column(String(20), comment="연계포인트 유형 (API/DB/MQ)")
    status = Column(String(20), nullable=False, comment="점검결과 (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN)")
    latency_ms = Column(Integer, comment="응답시간(ms)")
    http_status = Column(Integer, comment="HTTP 응답코드 (API)")
    error_code = Column(String(50), comment="에러코드")
    message = Column(Text, comment="상세 메시지")
    detail = Column(JSONB, comment="점검 세부(JSON)")
    failover_used = Column(Boolean, default=False, comment="핫스왑 엔드포인트 사용 여부")

    __table_args__ = (
        Index("ix_ext_agency_health_log_agency", "agency_id", "checked_at"),
        Index("ix_ext_agency_health_log_status", "status"),
        {"comment": "외부기관 연계포인트 점검 이력"},
    )


class CollectionExternalAgencyTxLog(Base):
    """외부기관 연계 송·수신 이력 로그 (REQ-DHUB-005-005-001)"""
    __tablename__ = "collection_external_agency_tx_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="송수신이력ID")
    agency_id = Column(UUID(as_uuid=True), ForeignKey("collection_external_agency.id", ondelete="CASCADE"),
                       nullable=False, comment="기관ID")
    tx_direction = Column(String(10), nullable=False, comment="방향 (SEND/RECV)")
    tx_type = Column(String(30), comment="유형 (DATA/ACK/HEARTBEAT/METADATA)")
    correlation_id = Column(String(100), comment="상관ID / 외부 tx_id")
    started_at = Column(DateTime, default=datetime.now, nullable=False, comment="시작일시")
    ended_at = Column(DateTime, comment="종료일시")
    duration_ms = Column(Integer, comment="소요시간(ms)")
    record_count = Column(BigInteger, default=0, comment="레코드수")
    bytes_size = Column(BigInteger, comment="바이트")
    status = Column(String(20), nullable=False, comment="상태 (SUCCESS/FAIL/PARTIAL/TIMEOUT)")
    http_status = Column(Integer, comment="HTTP 응답코드")
    error_code = Column(String(50), comment="에러코드")
    error_message = Column(Text, comment="오류메시지")
    retry_count = Column(Integer, default=0, comment="재시도 횟수")
    payload_preview = Column(Text, comment="페이로드 요약(최대 1KB)")
    metadata_ref = Column(JSONB, comment="라이프사이클/메타데이터 참조(OpenMetadata entity 등)")

    __table_args__ = (
        Index("ix_ext_agency_tx_log_agency_time", "agency_id", "started_at"),
        Index("ix_ext_agency_tx_log_status", "status"),
        Index("ix_ext_agency_tx_log_direction", "tx_direction"),
        {"comment": "외부기관 연계 송수신 이력"},
    )


class CollectionExternalAgencyRetryQueue(Base):
    """외부기관 연계 재시도 큐 (REQ-DHUB-005-005-001)"""
    __tablename__ = "collection_external_agency_retry_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="재시도ID")
    agency_id = Column(UUID(as_uuid=True), ForeignKey("collection_external_agency.id", ondelete="CASCADE"),
                       nullable=False, comment="기관ID")
    tx_log_id = Column(UUID(as_uuid=True), ForeignKey("collection_external_agency_tx_log.id", ondelete="SET NULL"),
                       comment="원본 송수신 이력ID")
    attempt = Column(Integer, default=0, comment="시도 횟수")
    max_attempts = Column(Integer, default=3, comment="최대 시도 횟수")
    next_run_at = Column(DateTime, default=datetime.now, nullable=False, comment="다음 실행 일시")
    status = Column(String(20), default="PENDING", comment="상태 (PENDING/RUNNING/DONE/DEAD)")
    last_error = Column(Text, comment="최근 오류 메시지")
    payload = Column(JSONB, comment="재시도용 원본 요청 페이로드")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")

    __table_args__ = (
        Index("ix_ext_agency_retry_queue_due", "next_run_at", "status"),
        Index("ix_ext_agency_retry_queue_agency", "agency_id"),
        {"comment": "외부기관 연계 재시도 큐"},
    )


class CollectionSpatialConfig(AuditMixin, Base):
    """공간정보수집설정"""
    __tablename__ = "collection_spatial_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="공간정보수집ID")
    config_name = Column(String(200), nullable=False, comment="구성명")
    spatial_data_type = Column(String(50), comment="공간데이터유형 (GIS/SATELLITE/LIDAR/DRONE)")
    source_url = Column(String(500), comment="데이터소스URL")
    coordinate_system = Column(String(50), comment="좌표계 (EPSG:5186/5179/4326 등)")
    collection_area = Column(JSONB, comment="수집영역 (BBOX 또는 polygon GeoJSON)")
    schedule_cron = Column(String(100), comment="스케줄CRON (deprecated, use schedule_id)")
    status = Column(String(20), default="ACTIVE", comment="상태 (ACTIVE/INACTIVE)")

    source_system = Column(String(50), comment="소스시스템 (ARCGIS_REST/GEOSERVER_WFS/GEOSERVER_WMS/GEOJSON_URL/ORACLE_SPATIAL/SHAPEFILE)")
    connection_config = Column(JSONB, comment="연결구성 {base_url, service_path, layer_query_params}")
    auth_config = Column(JSONB, comment="인증구성 {auth_type: NONE/BASIC/TOKEN, token_enc, username, password_enc}")
    target_schema = Column(String(100), default="spatial_gis", comment="대상PostGIS스키마")
    target_table = Column(String(200), comment="대상PostGIS테이블명")
    validation_rules = Column(JSONB, comment="검증규칙 {required_srid, geometry_types[], check_topology, max_feature_count}")
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("collection_schedule.id", ondelete="SET NULL"), nullable=True, comment="스케줄ID")
    event_trigger_config = Column(JSONB, comment="이벤트트리거구성 {enabled, trigger_type: FILE_UPLOAD/KAFKA/API, topic_or_path}")
    last_collected_at = Column(DateTime, comment="최근수집시각")
    last_status = Column(String(20), comment="최근상태 (SUCCESS/FAILED/RUNNING)")
    feature_count = Column(BigInteger, default=0, comment="최근수집피처수")
    last_error_message = Column(Text, comment="최근에러메시지")

    __table_args__ = (
        Index("ix_collection_spatial_config_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        Index("ix_collection_spatial_config_schedule", "schedule_id"),
        {"comment": "공간정보수집설정"},
    )


class CollectionSpatialLayer(AuditMixin, Base):
    """공간정보수집레이어 (설정↔레이어 중간)"""
    __tablename__ = "collection_spatial_layer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="레이어ID")
    config_id = Column(UUID(as_uuid=True), ForeignKey("collection_spatial_config.id", ondelete="CASCADE"), nullable=False, comment="공간정보수집ID")
    layer_name = Column(String(200), nullable=False, comment="레이어명")
    geometry_type = Column(String(50), comment="지오메트리유형 (POINT/LINESTRING/POLYGON/MULTIPOLYGON/GEOMETRY)")
    srid = Column(Integer, comment="SRID (EPSG 코드)")
    attribute_schema = Column(JSONB, comment="속성스키마 [{name, type, nullable}]")
    feature_count = Column(BigInteger, default=0, comment="피처수")
    last_synced_at = Column(DateTime, comment="최근동기화시각")
    is_enabled = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        Index("uq_collection_spatial_layer", "config_id", "layer_name", unique=True),
        Index("ix_collection_spatial_layer_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "공간정보수집레이어"},
    )


class CollectionSpatialHistory(Base):
    """공간정보수집이력"""
    __tablename__ = "collection_spatial_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="이력ID")
    config_id = Column(UUID(as_uuid=True), ForeignKey("collection_spatial_config.id", ondelete="CASCADE"), nullable=False, comment="공간정보수집ID")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="시작시각")
    ended_at = Column(DateTime, comment="종료시각")
    status = Column(String(20), nullable=False, comment="상태 (RUNNING/SUCCESS/FAILED/CANCELLED)")
    feature_count = Column(BigInteger, default=0, comment="수집피처수")
    invalid_feature_count = Column(BigInteger, default=0, comment="무효피처수")
    triggered_by = Column(String(20), comment="트리거유형 (SCHEDULE/EVENT/MANUAL)")
    error_message = Column(Text, comment="에러메시지")
    duration_ms = Column(Integer, comment="소요시간(ms)")

    __table_args__ = (
        Index("ix_collection_spatial_history_config", "config_id", "started_at"),
        {"comment": "공간정보수집이력"},
    )
