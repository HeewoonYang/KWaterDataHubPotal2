"""SA-04. 데이터자산/카탈로그 (6개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class CatalogDataset(AuditMixin, Base):
    """데이터셋카탈로그"""
    __tablename__ = "catalog_dataset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="데이터셋ID")
    dataset_name = Column(String(300), nullable=False, comment="데이터셋명")
    dataset_name_kr = Column(String(300), comment="데이터셋한글명")
    classification_id = Column(Integer, ForeignKey("data_classification.id", ondelete="SET NULL"), comment="분류ID")
    grade_id = Column(Integer, ForeignKey("data_grade.id", ondelete="SET NULL"), comment="등급ID")
    source_system = Column(String(200), comment="원천시스템")
    owner_department = Column(String(200), comment="관리부서")
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="소유자ID")
    description = Column(Text, comment="설명")
    tags = Column(JSONB, comment="태그목록")
    openmetadata_fqn = Column(String(500), unique=True, comment="OpenMetadataFQN")
    openmetadata_id = Column(String(200), comment="OpenMetadataID")
    schema_info = Column(JSONB, comment="스키마정보")
    row_count = Column(BigInteger, comment="총건수")
    size_bytes = Column(BigInteger, comment="데이터크기")
    data_format = Column(String(50), comment="데이터형식 (TABLE/VIEW/FILE/API)")
    refresh_frequency = Column(String(50), comment="갱신주기 (REALTIME/HOURLY/DAILY/WEEKLY/MANUAL)")
    last_updated_data_at = Column(DateTime, comment="데이터최종갱신일시")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_catalog_ds_name", "dataset_name"),
        Index("ix_catalog_ds_class", "classification_id"),
        Index("ix_catalog_ds_grade", "grade_id"),
        Index("ix_catalog_ds_fqn", "openmetadata_fqn"),
        Index("ix_catalog_dataset_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "데이터셋카탈로그"},
    )


class CatalogColumn(Base):
    """컬럼메타데이터"""
    __tablename__ = "catalog_column"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="컬럼메타ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    column_name = Column(String(200), nullable=False, comment="컬럼물리명")
    column_name_kr = Column(String(200), comment="컬럼한글명")
    data_type = Column(String(50), comment="데이터타입")
    length = Column(Integer, comment="길이")
    is_pk = Column(Boolean, default=False, comment="PK여부")
    is_nullable = Column(Boolean, default=True, comment="NULL허용여부")
    description = Column(Text, comment="설명")
    term_id = Column(Integer, ForeignKey("std_term.id", ondelete="SET NULL"), comment="표준용어ID")
    domain_id = Column(Integer, ForeignKey("std_domain.id", ondelete="SET NULL"), comment="표준도메인ID")
    sample_values = Column(JSONB, comment="샘플값")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        Index("ix_catalog_col_ds", "dataset_id"),
        {"comment": "컬럼메타데이터"},
    )


class CatalogTag(AuditMixin, Base):
    """태그관리"""
    __tablename__ = "catalog_tag"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="태그ID")
    tag_name = Column(String(100), nullable=False, unique=True, comment="태그명")
    tag_category = Column(String(50), comment="태그카테고리")
    usage_count = Column(Integer, default=0, comment="사용횟수")

    __table_args__ = (
        Index("ix_catalog_tag_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "태그관리"},
    )


class CatalogDatasetTag(Base):
    """데이터셋태그매핑"""
    __tablename__ = "catalog_dataset_tag"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="매핑ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    tag_id = Column(UUID(as_uuid=True), ForeignKey("catalog_tag.id", ondelete="CASCADE"), nullable=False, comment="태그ID")

    __table_args__ = (
        Index("uq_ds_tag", "dataset_id", "tag_id", unique=True),
        {"comment": "데이터셋태그매핑"},
    )


class CatalogLineage(AuditMixin, Base):
    """데이터리니지"""
    __tablename__ = "catalog_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="리니지ID")
    upstream_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), comment="상위데이터셋ID")
    downstream_dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), comment="하위데이터셋ID")
    lineage_type = Column(String(50), comment="리니지유형 (ETL/VIEW/TRANSFORM/COPY)")
    pipeline_name = Column(String(200), comment="파이프라인명")
    description = Column(Text, comment="설명")

    __table_args__ = (
        Index("ix_lineage_upstream", "upstream_dataset_id"),
        Index("ix_lineage_downstream", "downstream_dataset_id"),
        Index("ix_catalog_lineage_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "데이터리니지"},
    )


class CatalogSearchIndex(Base):
    """검색인덱스"""
    __tablename__ = "catalog_search_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="검색인덱스ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    search_text = Column(Text, nullable=False, comment="검색용텍스트")
    # search_vector TSVECTOR는 마이그레이션에서 직접 추가
    indexed_at = Column(DateTime, default=datetime.now, comment="색인일시")

    __table_args__ = (
        Index("ix_search_ds", "dataset_id"),
        {"comment": "검색인덱스"},
    )
