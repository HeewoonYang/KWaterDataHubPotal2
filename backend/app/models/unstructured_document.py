"""비정형데이터 문서 관리 모델"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class CollectionUnstructuredDocument(AuditMixin, Base):
    """비정형데이터문서"""
    __tablename__ = "collection_unstructured_document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="비정형문서ID")
    doc_name = Column(String(300), nullable=False, comment="문서명")
    doc_type = Column(String(50), nullable=False, comment="문서유형 (MANUAL/PROCEDURE/YEARBOOK/GUIDELINE/OTHER)")
    description = Column(Text, comment="설명")
    file_name = Column(String(500), comment="원본파일명")
    stored_name = Column(String(500), comment="저장파일명")
    file_size = Column(Integer, comment="파일크기(bytes)")
    content_type = Column(String(200), comment="MIME타입")
    storage_id = Column(
        UUID(as_uuid=True),
        ForeignKey("storage_unstructured.id", ondelete="SET NULL"),
        comment="비정형저장소ID",
    )
    processing_status = Column(String(20), default="PENDING", comment="처리상태 (PENDING/PROCESSING/COMPLETED/FAILED)")
    extracted_entity_count = Column(Integer, default=0, comment="추출엔티티수")
    graph_node_count = Column(Integer, default=0, comment="그래프노드수")
    graph_integrated = Column(Boolean, default=False, comment="그래프통합여부")
    tags = Column(JSONB, comment="태그목록")
    uploaded_at = Column(DateTime, default=datetime.now, comment="업로드일시")
    review_status = Column(String(20), default="PENDING_REVIEW", comment="문서검토상태 (PENDING_REVIEW/PARTIALLY_APPROVED/ALL_APPROVED/ALL_REJECTED)")

    __table_args__ = (
        Index("ix_coll_unstruct_doc_type", "doc_type"),
        Index("ix_coll_unstruct_doc_status", "processing_status"),
        Index("ix_coll_unstruct_doc_review", "review_status"),
        Index("ix_coll_unstruct_doc_not_deleted", "is_deleted",
              postgresql_where=text("is_deleted = false")),
        {"comment": "비정형데이터문서"},
    )


class CollectionUnstructuredDocOntologyUsage(Base):
    """비정형문서온톨로지활용"""
    __tablename__ = "collection_unstructured_doc_ontology_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="활용ID")
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_unstructured_document.id", ondelete="CASCADE"),
        nullable=False,
        comment="비정형문서ID",
    )
    ontology_class = Column(String(200), nullable=False, comment="온톨로지클래스명")
    entity_count = Column(Integer, default=0, comment="엔티티수")
    relation_count = Column(Integer, default=0, comment="관계수")
    last_synced_at = Column(DateTime, comment="최근동기화일시")
    status = Column(String(20), default="ACTIVE", comment="운영동기화상태 (ACTIVE/STALE/REMOVED)")
    review_status = Column(String(20), default="PENDING_REVIEW", comment="검토상태 (PENDING_REVIEW/APPROVED/REJECTED/REVISED)")
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="검토자ID")
    reviewed_at = Column(DateTime, comment="검토일시")
    review_comment = Column(Text, comment="검토의견")

    __table_args__ = (
        Index("ix_unstruct_onto_doc", "document_id"),
        Index("ix_unstruct_onto_class", "ontology_class"),
        Index("ix_unstruct_onto_review", "review_status"),
        {"comment": "비정형문서온톨로지활용"},
    )
