from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text

from app.database import Base


class MetaModel(Base):
    """논리/물리 모델 컨테이너"""
    __tablename__ = "meta_model"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="메타모델ID")
    model_type = Column(String(20), nullable=False, comment="모델유형 (LOGICAL/PHYSICAL)")
    model_name = Column(String(300), nullable=False, comment="모델명")
    system_name = Column(String(200), comment="정보시스템")
    sub_system = Column(String(200), comment="서브시스템")
    db_account = Column(String(100), comment="DB계정")
    description = Column(Text, comment="설명")
    version = Column(String(20), comment="버전")
    classification_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="분류ID")
    status = Column(String(20), default="ACTIVE", comment="상태")

    created_by = Column(Integer, comment="생성자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_by = Column(Integer, comment="수정자ID")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    is_deleted = Column(Boolean, default=False, comment="삭제여부")

    __table_args__ = (
        Index("ix_meta_model_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "메타모델"},
    )


class MetaModelEntity(Base):
    """엔터티/테이블"""
    __tablename__ = "meta_model_entity"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="엔터티ID")
    model_id = Column(Integer, ForeignKey("meta_model.id", ondelete="CASCADE"), nullable=False, comment="메타모델ID")
    entity_name = Column(String(200), nullable=False, comment="엔터티명")
    entity_name_kr = Column(String(200), comment="엔터티한글명")
    entity_type = Column(String(50), comment="엔터티유형 (TABLE/VIEW/ENTITY)")
    owner = Column(String(100), comment="테이블소유자")
    description = Column(Text, comment="설명")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")

    __table_args__ = (
        {"comment": "메타모델엔터티"},
    )


class MetaModelAttribute(Base):
    """컬럼/속성"""
    __tablename__ = "meta_model_attribute"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="속성ID")
    entity_id = Column(Integer, ForeignKey("meta_model_entity.id", ondelete="CASCADE"), nullable=False, comment="엔터티ID")
    attr_name = Column(String(200), nullable=False, comment="속성명")
    attr_name_kr = Column(String(200), comment="속성한글명")
    term_id = Column(Integer, ForeignKey("std_term.id", ondelete="SET NULL"), comment="표준용어ID")
    domain_id = Column(Integer, ForeignKey("std_domain.id", ondelete="SET NULL"), comment="표준도메인ID")
    data_type = Column(String(50), comment="데이터타입")
    length = Column(Integer, comment="길이")
    decimal_places = Column(Integer, default=0, comment="소수점자릿수")
    is_pk = Column(Boolean, default=False, comment="PK여부")
    is_nullable = Column(Boolean, default=True, comment="NULL허용여부")
    default_value = Column(String(200), comment="기본값")
    description = Column(Text, comment="설명")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        {"comment": "메타모델속성"},
    )
