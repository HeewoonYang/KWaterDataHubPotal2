"""SA-07. 데이터저장 (4개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class StorageZone(AuditMixin, Base):
    """저장소영역"""
    __tablename__ = "storage_zone"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="저장소영역ID")
    zone_name = Column(String(200), nullable=False, comment="영역명")
    zone_code = Column(String(50), nullable=False, unique=True, comment="영역코드")
    zone_type = Column(String(50), nullable=False, comment="영역유형 (RAW/STAGING/ODS/EDW/MART/ARCHIVE)")
    storage_type = Column(String(50), comment="저장소유형 (RDBMS/OBJECT/FILE_SYSTEM/DATA_LAKE)")
    connection_config = Column(JSONB, comment="연결설정")
    max_capacity_gb = Column(Numeric(12, 2), comment="최대용량GB")
    used_capacity_gb = Column(Numeric(12, 2), comment="사용용량GB")
    retention_policy_days = Column(Integer, comment="보관정책일수")
    description = Column(Text, comment="설명")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        Index("ix_storage_zone_code", "zone_code"),
        Index("ix_storage_zone_type", "zone_type"),
        {"comment": "저장소영역"},
    )


class StorageHighspeedDb(AuditMixin, Base):
    """고속처리DB"""
    __tablename__ = "storage_highspeed_db"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="고속DB설정ID")
    db_name = Column(String(200), nullable=False, comment="DB명")
    db_type = Column(String(50), nullable=False, comment="DB유형 (REDIS/IGNITE/HAZELCAST/MEMCACHED)")
    connection_config = Column(JSONB, nullable=False, comment="연결설정")
    purpose = Column(String(200), comment="용도")
    max_memory_gb = Column(Numeric(8, 2), comment="최대메모리GB")
    eviction_policy = Column(String(50), comment="퇴거정책 (LRU/LFU/TTL)")
    ttl_seconds = Column(Integer, comment="기본TTL초")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        {"comment": "고속처리DB"},
    )


class StorageUnstructured(AuditMixin, Base):
    """비정형저장소"""
    __tablename__ = "storage_unstructured"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="비정형저장소ID")
    storage_name = Column(String(200), nullable=False, comment="저장소명")
    storage_type = Column(String(50), nullable=False, comment="저장소유형 (OBJECT_STORAGE/NAS/HDFS/S3)")
    bucket_name = Column(String(200), comment="버킷명")
    base_path = Column(String(500), comment="기본경로")
    access_config = Column(JSONB, comment="접근설정")
    supported_formats = Column(JSONB, comment="지원포맷목록")
    max_file_size_mb = Column(Integer, comment="최대파일크기MB")
    total_capacity_gb = Column(Numeric(12, 2), comment="총용량GB")
    used_capacity_gb = Column(Numeric(12, 2), comment="사용용량GB")
    status = Column(String(20), default="ACTIVE", comment="상태")

    __table_args__ = (
        {"comment": "비정형저장소"},
    )


class StorageDatasetLocation(Base):
    """데이터셋저장위치"""
    __tablename__ = "storage_dataset_location"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="저장위치ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    zone_id = Column(UUID(as_uuid=True), ForeignKey("storage_zone.id", ondelete="CASCADE"), nullable=False, comment="저장소영역ID")
    physical_location = Column(String(500), comment="물리위치")
    partition_key = Column(String(200), comment="파티션키")
    size_bytes = Column(BigInteger, comment="크기")
    row_count = Column(BigInteger, comment="건수")
    last_refreshed_at = Column(DateTime, comment="최근갱신일시")

    __table_args__ = (
        Index("ix_storage_loc_ds", "dataset_id"),
        Index("ix_storage_loc_zone", "zone_id"),
        {"comment": "데이터셋저장위치"},
    )
