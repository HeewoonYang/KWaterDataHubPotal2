from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class DataClassification(Base):
    """분류체계"""
    __tablename__ = "data_classification"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="분류ID")
    parent_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="상위분류ID")
    level = Column(Integer, nullable=False, comment="분류레벨 (1=대분류, 2=중분류, 3=소분류)")
    name = Column(String(200), nullable=False, comment="분류명")
    code = Column(String(50), nullable=False, unique=True, comment="분류코드")
    description = Column(Text, comment="설명")
    dataset_count = Column(Integer, default=0, comment="연결데이터셋수")
    sort_order = Column(Integer, default=0, comment="정렬순서")
    status = Column(String(20), default="ACTIVE", comment="상태")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_data_class_parent", "parent_id"),
        Index("ix_data_class_code", "code"),
        Index("ix_data_classification_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "분류체계"},
    )


class DataGrade(Base):
    """데이터 등급 분류"""
    __tablename__ = "data_grade"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="등급ID")
    grade_code = Column(String(10), nullable=False, unique=True, comment="등급코드 (L1/L2/L3)")
    grade_name = Column(String(50), nullable=False, comment="등급명 (비공개/내부공유/공개)")
    description = Column(Text, comment="설명")
    access_scope = Column(String(200), comment="접근대상범위")
    dataset_count = Column(Integer, default=0, comment="데이터셋수")
    anonymize_required = Column(String(20), comment="비식별화필요여부 (필수/선택/불필요)")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")

    __table_args__ = (
        {"comment": "데이터등급"},
    )


class ClassificationSyncLog(Base):
    """분류체계 동기화 이력"""
    __tablename__ = "classification_sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="동기화로그ID")
    classification_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="분류ID")
    hub_code = Column(String(50), comment="허브코드")
    portal_code = Column(String(50), comment="포털코드")
    sync_status = Column(String(20), comment="동기화상태 (MATCH/MISMATCH/NEW/DELETED)")
    synced_at = Column(DateTime, default=datetime.now, comment="동기화일시")
    details = Column(JSONB, comment="상세정보")

    __table_args__ = (
        {"comment": "분류체계동기화이력"},
    )
