"""ERP 조직/사용자 동기화 이력 테이블"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import new_uuid


class OrgSyncLog(Base):
    """조직동기화이력"""
    __tablename__ = "org_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="동기화이력ID")
    sync_type = Column(String(20), nullable=False, comment="동기화유형 (MANUAL/SCHEDULED)")
    trigger_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="실행자ID")
    scope = Column(String(100), comment="동기화범위 (ORG/USER/POSITION/ALL)")
    conflict_policy = Column(String(20), default="ERP_FIRST", comment="충돌정책 (ERP_FIRST/HUB_FIRST/MANUAL)")
    is_dry_run = Column(Boolean, default=False, comment="사전점검여부")
    started_at = Column(DateTime, default=datetime.now, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    duration_ms = Column(Integer, comment="소요시간MS")
    total_records = Column(Integer, default=0, comment="전체건수")
    added = Column(Integer, default=0, comment="신규건수")
    updated = Column(Integer, default=0, comment="변경건수")
    deactivated = Column(Integer, default=0, comment="비활성건수")
    errors = Column(Integer, default=0, comment="오류건수")
    skipped = Column(Integer, default=0, comment="건너뛴건수")
    status = Column(String(20), default="RUNNING", comment="상태 (RUNNING/SUCCESS/PARTIAL/FAILED)")
    error_message = Column(Text, comment="오류메시지")

    __table_args__ = (
        Index("ix_org_sync_log_date", "started_at"),
        Index("ix_org_sync_log_status", "status"),
        {"comment": "조직동기화이력"},
    )


class OrgSyncDetail(Base):
    """조직동기화상세"""
    __tablename__ = "org_sync_detail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="동기화상세ID")
    sync_log_id = Column(UUID(as_uuid=True), ForeignKey("org_sync_log.id", ondelete="CASCADE"), nullable=False, comment="동기화이력ID")
    action = Column(String(20), nullable=False, comment="작업구분 (ADD/UPDATE/DEACTIVATE/ERROR)")
    employee_no = Column(String(20), comment="사번")
    user_name = Column(String(100), comment="사용자명")
    field_name = Column(String(100), comment="변경항목")
    old_value = Column(String(500), comment="변경전값")
    new_value = Column(String(500), comment="변경후값")
    error_message = Column(String(500), comment="오류메시지")

    __table_args__ = (
        Index("ix_org_sync_detail_log", "sync_log_id"),
        {"comment": "조직동기화상세"},
    )
