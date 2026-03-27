"""SA-05. 데이터수집 (8개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
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
    connection_password_enc = Column(String(500), comment="접속비밀번호")
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

    __table_args__ = (
        Index("ix_coll_job_config", "dataset_config_id"),
        Index("ix_coll_job_status", "job_status"),
        Index("ix_coll_job_start", "started_at"),
        {"comment": "수집작업실행이력"},
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
    api_key_enc = Column(String(500), comment="API키")
    data_type = Column(String(50), comment="데이터유형")
    protocol = Column(String(50), comment="프로토콜 (REST/SOAP/FILE)")
    schedule_cron = Column(String(100), comment="수집주기CRON")
    last_sync_at = Column(DateTime, comment="최근동기화일시")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        {"comment": "외부기관연계"},
    )


class CollectionSpatialConfig(AuditMixin, Base):
    """공간정보수집설정"""
    __tablename__ = "collection_spatial_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="공간정보수집ID")
    config_name = Column(String(200), nullable=False, comment="구성명")
    spatial_data_type = Column(String(50), comment="공간데이터유형 (GIS/SATELLITE/LIDAR/DRONE)")
    source_url = Column(String(500), comment="데이터소스URL")
    coordinate_system = Column(String(50), comment="좌표계")
    collection_area = Column(JSONB, comment="수집영역")
    schedule_cron = Column(String(100), comment="스케줄CRON")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        {"comment": "공간정보수집설정"},
    )
