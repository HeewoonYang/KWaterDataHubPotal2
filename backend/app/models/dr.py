"""재해복구(DR) / 이관 감사 / OpenMetadata 동기화 모델 (REQ-DHUB-005-003)."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class DrPitRecovery(AuditMixin, Base):
    """PIT(Point-In-Time) 복구 정의"""
    __tablename__ = "dr_pit_recovery"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="PIT복구ID")
    recovery_name = Column(String(200), nullable=False, comment="복구명")
    target_source_id = Column(UUID(as_uuid=True), ForeignKey("collection_data_source.id", ondelete="SET NULL"), comment="대상소스ID")
    target_backup_id = Column(UUID(as_uuid=True), ForeignKey("sys_dr_backup.id", ondelete="SET NULL"), comment="참조백업ID")
    target_timestamp = Column(DateTime, nullable=False, comment="복구목표시각")
    simulation_only = Column(Boolean, default=True, comment="시뮬레이션만 (실제복구금지)")
    approval_status = Column(String(30), default="PENDING", comment="승인상태 (PENDING/APPROVED/REJECTED/EXECUTED)")
    approved_by = Column(UUID(as_uuid=True), comment="승인자ID")
    approved_at = Column(DateTime, comment="승인일시")
    reject_reason = Column(Text, comment="반려사유")
    simulation_result = Column(JSONB, comment="시뮬레이션결과 (예상건수/용량/소요시간/경고)")
    execution_result = Column(JSONB, comment="실행결과")
    executed_at = Column(DateTime, comment="실행일시")
    status = Column(String(30), default="DRAFT", comment="진행상태 (DRAFT/SIMULATED/READY/EXECUTING/COMPLETED/FAILED)")
    error_message = Column(Text, comment="오류메시지")

    __table_args__ = (
        Index("ix_dr_pit_status", "status"),
        Index("ix_dr_pit_target_source", "target_source_id"),
        Index("ix_dr_pit_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "PIT 복구 정의(시뮬레이션+승인+실행)"},
    )


class DrRestoreLog(Base):
    """복구 실행 이력 로그"""
    __tablename__ = "dr_restore_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="복구로그ID")
    pit_recovery_id = Column(UUID(as_uuid=True), ForeignKey("dr_pit_recovery.id", ondelete="SET NULL"), comment="PIT복구ID")
    backup_id = Column(UUID(as_uuid=True), ForeignKey("sys_dr_backup.id", ondelete="SET NULL"), comment="백업ID")
    restore_type = Column(String(30), nullable=False, comment="복구유형 (FULL_RESTORE/PIT_RESTORE/SIMULATION)")
    source_system = Column(String(200), comment="원본시스템")
    target_system = Column(String(200), comment="복구대상")
    started_at = Column(DateTime, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    duration_sec = Column(Integer, comment="소요초")
    restored_rows = Column(BigInteger, comment="복구건수")
    restored_tables = Column(Integer, comment="복구테이블수")
    restored_size_mb = Column(Numeric(14, 2), comment="복구용량MB")
    status = Column(String(30), comment="상태 (SUCCESS/FAIL/PARTIAL)")
    error_message = Column(Text, comment="오류메시지")
    details = Column(JSONB, comment="상세정보")
    executed_by = Column(UUID(as_uuid=True), comment="실행자ID")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    __table_args__ = (
        Index("ix_dr_restore_pit", "pit_recovery_id"),
        Index("ix_dr_restore_status", "status"),
        Index("ix_dr_restore_started", "started_at"),
        {"comment": "복구 실행 이력 로그"},
    )


class DrDbAccountHistory(Base):
    """DB 계정 변경 이력"""
    __tablename__ = "dr_db_account_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="계정이력ID")
    source_id = Column(UUID(as_uuid=True), ForeignKey("collection_data_source.id", ondelete="CASCADE"), comment="데이터소스ID")
    account_name = Column(String(200), nullable=False, comment="계정명")
    action = Column(String(30), nullable=False, comment="조치 (CREATE/ALTER/DROP/GRANT/REVOKE/PASSWORD_CHANGE)")
    privileges = Column(JSONB, comment="권한상세")
    changed_by = Column(UUID(as_uuid=True), comment="변경자ID")
    changed_at = Column(DateTime, default=datetime.now, comment="변경일시")
    note = Column(Text, comment="비고")

    __table_args__ = (
        Index("ix_dr_acct_source", "source_id"),
        Index("ix_dr_acct_changed", "changed_at"),
        {"comment": "DB 계정 변경 이력"},
    )


class MigrationAuditLog(Base):
    """이관/복제 감사 로그"""
    __tablename__ = "migration_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="이관감사ID")
    migration_id = Column(UUID(as_uuid=True), ForeignKey("collection_migration.id", ondelete="CASCADE"), comment="이관ID")
    action = Column(String(50), nullable=False, comment="행위 (CREATE/START/PAUSE/RESUME/FAIL/COMPLETE/VALIDATE/ROLLBACK)")
    phase = Column(String(50), comment="단계 (SCHEMA_COPY/DATA_COPY/INDEX_REBUILD/VALIDATION/CUTOVER)")
    actor_id = Column(UUID(as_uuid=True), comment="실행자ID")
    started_at = Column(DateTime, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    duration_ms = Column(Integer, comment="소요MS")
    table_name = Column(String(300), comment="테이블명")
    row_count = Column(BigInteger, comment="건수")
    details = Column(JSONB, comment="상세 (source/target checksum, row_diff, schema_diff 등)")
    severity = Column(String(20), default="INFO", comment="심각도 (INFO/WARNING/ERROR)")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    __table_args__ = (
        Index("ix_mig_audit_migration", "migration_id"),
        Index("ix_mig_audit_action", "action"),
        Index("ix_mig_audit_created", "created_at"),
        {"comment": "이관 감사 로그"},
    )


class MigrationValidationResult(Base):
    """이관 검증 결과"""
    __tablename__ = "migration_validation_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="검증결과ID")
    migration_id = Column(UUID(as_uuid=True), ForeignKey("collection_migration.id", ondelete="CASCADE"), comment="이관ID")
    table_name = Column(String(300), nullable=False, comment="테이블명")
    validation_type = Column(String(30), nullable=False, comment="검증유형 (ROW_COUNT/CHECKSUM/SCHEMA_DIFF/PK_CONSISTENCY)")
    source_value = Column(Text, comment="원본값")
    target_value = Column(Text, comment="복구대상값")
    match_status = Column(String(20), comment="일치여부 (MATCH/MISMATCH/ERROR/SKIPPED)")
    diff_count = Column(BigInteger, comment="차이건수")
    diff_details = Column(JSONB, comment="차이상세")
    executed_at = Column(DateTime, default=datetime.now, comment="실행일시")
    duration_ms = Column(Integer, comment="소요MS")

    __table_args__ = (
        Index("ix_mig_val_migration", "migration_id"),
        Index("ix_mig_val_status", "match_status"),
        {"comment": "이관 검증 결과"},
    )


class OpenmetadataSyncLog(Base):
    """OpenMetadata 동기화 로그"""
    __tablename__ = "openmetadata_sync_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="OM동기화로그ID")
    entity_type = Column(String(50), nullable=False, comment="엔티티유형 (TABLE/COLUMN/LINEAGE/TAG/AUDIT/PIPELINE)")
    entity_id = Column(UUID(as_uuid=True), comment="엔티티ID (로컬)")
    entity_name = Column(String(300), comment="엔티티명")
    sync_direction = Column(String(30), default="PUSH", comment="동기화방향 (PUSH/PULL)")
    operation = Column(String(30), comment="작업 (CREATE/UPDATE/DELETE/UPSERT)")
    om_entity_id = Column(String(300), comment="OM 엔티티 FQN/ID")
    status = Column(String(30), comment="상태 (SUCCESS/FAIL/SKIPPED/PENDING)")
    http_status = Column(Integer, comment="HTTP상태코드")
    error_message = Column(Text, comment="오류메시지")
    payload = Column(JSONB, comment="송신페이로드")
    response = Column(JSONB, comment="응답")
    started_at = Column(DateTime, default=datetime.now, comment="시작일시")
    duration_ms = Column(Integer, comment="소요MS")

    __table_args__ = (
        Index("ix_om_sync_entity", "entity_type", "entity_id"),
        Index("ix_om_sync_status", "status"),
        Index("ix_om_sync_started", "started_at"),
        {"comment": "OpenMetadata 동기화 로그"},
    )
