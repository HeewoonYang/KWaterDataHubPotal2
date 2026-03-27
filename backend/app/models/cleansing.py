"""SA-06. 데이터정제 (8개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class CleansingRule(AuditMixin, Base):
    """정제규칙"""
    __tablename__ = "cleansing_rule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="정제규칙ID")
    rule_name = Column(String(200), nullable=False, comment="규칙명")
    rule_type = Column(String(50), nullable=False, comment="규칙유형 (NULL_FILL/FORMAT/DEDUP/RANGE/REGEX/CUSTOM)")
    target_column_type = Column(String(50), comment="대상컬럼유형 (STRING/NUMBER/DATE/ALL)")
    rule_expression = Column(Text, comment="규칙표현식")
    rule_config = Column(JSONB, comment="규칙설정")
    severity = Column(String(20), default="WARNING", comment="심각도 (ERROR/WARNING/INFO)")
    is_active = Column(Boolean, default=True, comment="활성여부")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        Index("ix_cleansing_rule_type", "rule_type"),
        Index("ix_cleansing_rule_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "정제규칙"},
    )


class CleansingJob(AuditMixin, Base):
    """정제작업"""
    __tablename__ = "cleansing_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="정제작업ID")
    job_name = Column(String(200), nullable=False, comment="작업명")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="데이터셋ID")
    rule_ids = Column(JSONB, comment="적용규칙ID목록 (deprecated, use cleansing_job_rule)")
    job_status = Column(String(20), comment="작업상태 (QUEUED/RUNNING/SUCCESS/FAIL)")
    started_at = Column(DateTime, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    total_rows = Column(BigInteger, comment="총건수")
    cleansed_rows = Column(BigInteger, comment="정제건수")
    error_rows = Column(BigInteger, comment="오류건수")
    result_summary = Column(JSONB, comment="결과요약")
    celery_task_id = Column(String(200), comment="Celery작업ID")

    __table_args__ = (
        Index("ix_cleansing_job_ds", "dataset_id"),
        Index("ix_cleansing_job_status", "job_status"),
        Index("ix_cleansing_job_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "정제작업"},
    )


class CleansingResultDetail(Base):
    """정제결과상세"""
    __tablename__ = "cleansing_result_detail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="정제결과ID")
    job_id = Column(UUID(as_uuid=True), ForeignKey("cleansing_job.id", ondelete="CASCADE"), nullable=False, comment="정제작업ID")
    rule_id = Column(UUID(as_uuid=True), ForeignKey("cleansing_rule.id", ondelete="SET NULL"), comment="정제규칙ID")
    column_name = Column(String(200), comment="대상컬럼명")
    before_value = Column(Text, comment="변경전값")
    after_value = Column(Text, comment="변경후값")
    action_taken = Column(String(50), comment="수행조치 (REPLACED/REMOVED/FLAGGED)")
    row_index = Column(BigInteger, comment="행번호")
    processed_at = Column(DateTime, default=datetime.now, comment="처리일시")

    __table_args__ = (
        Index("ix_cleansing_detail_job", "job_id"),
        {"comment": "정제결과상세"},
    )


class AnonymizationConfig(AuditMixin, Base):
    """비식별화설정"""
    __tablename__ = "anonymization_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="비식별화설정ID")
    config_name = Column(String(200), nullable=False, comment="설정명")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="데이터셋ID")
    target_columns = Column(JSONB, nullable=False, comment="대상컬럼목록")
    method = Column(String(50), nullable=False, comment="비식별화방법 (MASKING/GENERALIZATION/PSEUDONYM/ENCRYPTION/SUPPRESSION)")
    method_config = Column(JSONB, comment="방법설정")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        Index("ix_anonymization_config_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "비식별화설정"},
    )


class AnonymizationLog(Base):
    """비식별화실행이력"""
    __tablename__ = "anonymization_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="비식별화이력ID")
    config_id = Column(UUID(as_uuid=True), ForeignKey("anonymization_config.id", ondelete="CASCADE"), nullable=False, comment="비식별화설정ID")
    executed_at = Column(DateTime, default=datetime.now, comment="실행일시")
    total_rows = Column(BigInteger, comment="총건수")
    processed_rows = Column(BigInteger, comment="처리건수")
    status = Column(String(20), comment="상태 (SUCCESS/FAIL)")
    error_message = Column(Text, comment="오류메시지")

    __table_args__ = (
        Index("ix_anon_log_config", "config_id"),
        {"comment": "비식별화실행이력"},
    )


class TransformModel(AuditMixin, Base):
    """변환모델"""
    __tablename__ = "transform_model"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="변환모델ID")
    model_name = Column(String(200), nullable=False, comment="모델명")
    source_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="소스데이터셋ID")
    target_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="타겟데이터셋ID")
    transform_type = Column(String(50), comment="변환유형 (MAPPING/AGGREGATION/PIVOT/JOIN/CUSTOM)")
    transform_config = Column(JSONB, comment="변환설정")
    sql_expression = Column(Text, comment="SQL변환식")
    status = Column(String(20), default="DRAFT", comment="상태 (DRAFT/ACTIVE/INACTIVE)")

    __table_args__ = (
        Index("ix_transform_model_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "변환모델"},
    )


class TransformMapping(Base):
    """변환컬럼매핑"""
    __tablename__ = "transform_mapping"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="변환매핑ID")
    transform_model_id = Column(UUID(as_uuid=True), ForeignKey("transform_model.id", ondelete="CASCADE"), nullable=False, comment="변환모델ID")
    source_column = Column(String(200), nullable=False, comment="소스컬럼명")
    target_column = Column(String(200), nullable=False, comment="타겟컬럼명")
    transform_function = Column(String(200), comment="변환함수")
    default_value = Column(String(500), comment="기본값")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        Index("ix_transform_map_model", "transform_model_id"),
        {"comment": "변환컬럼매핑"},
    )


class CleansingJobRule(Base):
    """정제작업규칙매핑"""
    __tablename__ = "cleansing_job_rule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="매핑ID")
    job_id = Column(UUID(as_uuid=True), ForeignKey("cleansing_job.id", ondelete="CASCADE"), nullable=False, comment="정제작업ID")
    rule_id = Column(UUID(as_uuid=True), ForeignKey("cleansing_rule.id", ondelete="CASCADE"), nullable=False, comment="정제규칙ID")
    sort_order = Column(Integer, default=0, comment="적용순서")

    __table_args__ = (
        Index("uq_cleansing_job_rule", "job_id", "rule_id", unique=True),
        {"comment": "정제작업규칙매핑"},
    )
