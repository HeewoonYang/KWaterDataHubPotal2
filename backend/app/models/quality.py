from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


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

    __table_args__ = (
        {"comment": "품질검증결과"},
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
