"""공통 Mixin 정의"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID


class AuditMixin:
    """모든 신규 테이블에 적용되는 공통 감사 컬럼"""
    created_by = Column(UUID(as_uuid=True), comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(UUID(as_uuid=True), comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")


def new_uuid():
    return uuid.uuid4()
