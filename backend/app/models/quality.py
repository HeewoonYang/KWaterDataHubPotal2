from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class QualityRule(Base):
    """품질검증규칙"""
    __tablename__ = "quality_rule"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="규칙ID")
    rule_name = Column(String(200), nullable=False, comment="규칙명")
    rule_type = Column(String(50), nullable=False, comment="규칙유형 (COMPLETENESS/VALIDITY/ACCURACY/CONSISTENCY)")
    target_type = Column(String(50), comment="대상유형 (DATASET/TABLE/COLUMN)")
    rule_expression = Column(Text, comment="규칙표현식")
    severity = Column(String(20), default="WARNING", comment="심각도 (ERROR/WARNING/INFO)")
    is_active = Column(Boolean, default=True, comment="활성여부")
    schedule_cron = Column(String(100), comment="배치스케줄")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    __table_args__ = (
        {"comment": "품질검증규칙"},
    )


class QualityCheckResult(Base):
    """품질검증결과"""
    __tablename__ = "quality_check_result"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="검증결과ID")
    rule_id = Column(Integer, ForeignKey("quality_rule.id", ondelete="SET NULL"), comment="규칙ID")
    dataset_name = Column(String(300), comment="데이터셋명")
    check_type = Column(String(50), comment="검증유형")
    total_count = Column(Integer, comment="총건수")
    error_count = Column(Integer, comment="오류건수")
    score = Column(Numeric(5, 2), comment="점수")
    executed_at = Column(DateTime, default=datetime.now, comment="실행일시")
    execution_time_ms = Column(Integer, comment="실행시간MS")
    details = Column(JSONB, comment="상세정보")
    # 추적성 FK (신규) - dataset_name 은 하위호환 유지
    catalog_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), nullable=True, comment="카탈로그데이터셋ID")
    distribution_dataset_id = Column(UUID(as_uuid=True), ForeignKey("distribution_dataset.id", ondelete="SET NULL"), nullable=True, comment="유통데이터셋ID")
    collection_job_id = Column(UUID(as_uuid=True), ForeignKey("collection_job.id", ondelete="SET NULL"), nullable=True, comment="수집잡ID")
    # AI 학습 피드백 플래그
    ai_feedback_used = Column(Boolean, default=False, comment="AI학습반영여부")
    ai_feedback_at = Column(DateTime, comment="AI학습반영일시")
    ai_training_score = Column(Numeric(5, 2), comment="AI학습기여가중치(0~100)")

    __table_args__ = (
        Index("ix_qcr_catalog", "catalog_dataset_id"),
        Index("ix_qcr_distribution", "distribution_dataset_id"),
        Index("ix_qcr_collection_job", "collection_job_id"),
        Index("ix_qcr_ai_feedback", "ai_feedback_used"),
        {"comment": "품질검증결과"},
    )


class QualityAiFeedback(AuditMixin, Base):
    """품질AI학습피드백"""
    __tablename__ = "quality_ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="품질AI학습피드백ID")
    source_result_id = Column(Integer, ForeignKey("quality_check_result.id", ondelete="CASCADE"), nullable=False, comment="원본품질결과ID")
    target_system = Column(String(30), nullable=False, comment="대상AI시스템 (LLM/RAG/T2SQL)")
    feedback_type = Column(String(30), nullable=False, comment="피드백유형 (FAILURE_PATTERN/LOW_SCORE/STANDARD_VIOLATION/MISSING_METADATA)")
    payload = Column(JSONB, nullable=False, comment="학습페이로드JSON")
    dispatch_status = Column(String(20), default="PENDING", comment="전송상태 (PENDING/SENT/FAILED/SKIPPED)")
    dispatched_at = Column(DateTime, comment="전송일시")
    dispatch_error = Column(Text, comment="전송오류메시지")

    __table_args__ = (
        Index("ix_qaf_source", "source_result_id"),
        Index("ix_qaf_status", "dispatch_status"),
        Index("ix_qaf_target", "target_system"),
        Index("ix_qaf_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "품질AI학습피드백"},
    )


class StdComplianceResult(Base):
    """표준준수결과"""
    __tablename__ = "std_compliance_result"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="준수결과ID")
    standard_name = Column(String(200), nullable=False, comment="표준명")
    category = Column(String(50), nullable=False, comment="카테고리 (단어/용어/도메인/코드)")
    total_items = Column(Integer, comment="총항목수")
    passed_items = Column(Integer, comment="통과항목수")
    failed_items = Column(Integer, comment="실패항목수")
    compliance_rate = Column(Numeric(5, 2), comment="준수율")
    checked_at = Column(DateTime, default=datetime.now, comment="검사일시")
    details = Column(JSONB, comment="상세정보")

    __table_args__ = (
        {"comment": "표준준수결과"},
    )


class QualitySchedule(Base):
    """품질검증스케줄"""
    __tablename__ = "quality_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="품질스케줄ID")
    rule_id = Column(Integer, ForeignKey("quality_rule.id", ondelete="SET NULL"), comment="규칙ID")
    schedule_name = Column(String(200), nullable=False, comment="스케줄명")
    schedule_cron = Column(String(100), nullable=False, comment="스케줄CRON")
    target_dataset = Column(String(300), comment="대상데이터셋")
    is_active = Column(Boolean, default=True, comment="활성여부")
    last_run_at = Column(DateTime, comment="최근실행일시")
    next_run_at = Column(DateTime, comment="다음실행일시")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_quality_schedule_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "품질검증스케줄"},
    )
