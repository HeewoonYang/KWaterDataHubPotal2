"""SSO 제공자 설정 테이블"""
from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class SsoProviderConfig(AuditMixin, Base):
    """SSO제공자설정"""
    __tablename__ = "sso_provider_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="SSO제공자ID")
    provider_type = Column(String(20), nullable=False, comment="제공자유형 (SAML/OAUTH)")
    provider_name = Column(String(100), nullable=False, unique=True, comment="제공자코드명")
    display_name = Column(String(200), nullable=False, comment="표시명")
    config_json = Column(JSONB, comment="제공자설정JSON")
    is_enabled = Column(Boolean, default=True, comment="활성여부")
    default_role_code = Column(String(50), default="EMPLOYEE", comment="자동생성시기본역할")
    default_user_type = Column(String(20), default="INTERNAL", comment="자동생성시사용자유형 (INTERNAL/EXTERNAL)")
    description = Column(Text, comment="설명")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        {"comment": "SSO제공자설정"},
    )
