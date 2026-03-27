from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class StdAuditLog(Base):
    """표준 데이터 변경 이력"""
    __tablename__ = "std_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="감사로그ID")
    table_name = Column(String(100), nullable=False, comment="변경테이블명")
    record_id = Column(Integer, nullable=False, comment="변경레코드PK")
    action = Column(String(20), nullable=False, comment="수행작업 (INSERT/UPDATE/DELETE)")
    old_data = Column(JSONB, comment="변경전데이터")
    new_data = Column(JSONB, comment="변경후데이터")
    changed_by = Column(Integer, comment="변경자ID")
    changed_at = Column(DateTime, default=datetime.now, comment="변경일시")
    change_reason = Column(Text, comment="변경사유")

    __table_args__ = (
        Index("ix_std_audit_table", "table_name", "record_id"),
        Index("ix_std_audit_date", "changed_at"),
        {"comment": "표준감사로그"},
    )
