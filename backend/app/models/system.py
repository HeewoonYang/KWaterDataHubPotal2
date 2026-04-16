"""SA-01. 공통/시스템 (8개 테이블)"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class SysConfig(AuditMixin, Base):
    """시스템설정"""
    __tablename__ = "sys_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="시스템설정ID")
    config_key = Column(String(200), nullable=False, unique=True, comment="설정키")
    config_value = Column(Text, comment="설정값")
    config_type = Column(String(20), comment="설정유형 (STRING/NUMBER/BOOLEAN/JSON)")
    category = Column(String(100), comment="설정카테고리")
    description = Column(Text, comment="설명")
    is_encrypted = Column(Boolean, default=False, comment="암호화여부")

    __table_args__ = (
        Index("ix_sys_config_key", "config_key"),
        Index("ix_sys_config_category", "category"),
        {"comment": "시스템설정"},
    )


class SysInfrastructure(AuditMixin, Base):
    """인프라관리"""
    __tablename__ = "sys_infrastructure"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="인프라ID")
    infra_name = Column(String(200), nullable=False, comment="인프라명")
    infra_type = Column(String(50), nullable=False, comment="인프라유형 (SERVER/DB/STORAGE/NETWORK/CLOUD)")
    host_address = Column(String(500), comment="호스트주소")
    status = Column(String(20), default="ACTIVE", comment="운영상태 (ACTIVE/INACTIVE/MAINTENANCE)")
    environment = Column(String(20), comment="운영환경 (DEV/STG/PRD/DR)")
    specs = Column(JSONB, comment="사양정보")
    monitoring_url = Column(String(500), comment="모니터링URL")
    last_health_check = Column(DateTime, comment="최근헬스체크일시")

    __table_args__ = (
        Index("ix_sys_infra_type", "infra_type"),
        Index("ix_sys_infra_env", "environment"),
        {"comment": "인프라관리"},
    )


class SysCloudConfig(AuditMixin, Base):
    """클라우드구성"""
    __tablename__ = "sys_cloud_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="클라우드구성ID")
    cloud_provider = Column(String(50), nullable=False, comment="클라우드공급자 (NCP/AWS/AZURE/ON_PREMISE)")
    resource_type = Column(String(50), comment="리소스유형 (VM/K8S/STORAGE/DB/LB)")
    resource_name = Column(String(200), nullable=False, comment="리소스명")
    resource_id = Column(String(200), comment="클라우드리소스ID")
    region = Column(String(50), comment="리전")
    configuration = Column(JSONB, comment="구성상세")
    status = Column(String(20), default="ACTIVE", comment="상태")
    monthly_cost = Column(Numeric(12, 2), comment="월비용")

    __table_args__ = (
        Index("ix_sys_cloud_provider", "cloud_provider"),
        {"comment": "클라우드구성"},
    )


class SysDrBackup(AuditMixin, Base):
    """DR백업관리"""
    __tablename__ = "sys_dr_backup"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="DR백업ID")
    backup_name = Column(String(200), nullable=False, comment="백업명")
    backup_type = Column(String(50), nullable=False, comment="백업유형 (FULL/INCREMENTAL/DIFFERENTIAL)")
    target_system = Column(String(200), comment="대상시스템")
    schedule_cron = Column(String(100), comment="스케줄CRON")
    retention_days = Column(Integer, default=30, comment="보관기간일수")
    storage_path = Column(String(500), comment="저장경로")
    last_backup_at = Column(DateTime, comment="최근백업일시")
    last_backup_size_mb = Column(Numeric(12, 2), comment="최근백업크기MB")
    last_backup_status = Column(String(20), comment="최근백업상태 (SUCCESS/FAIL/RUNNING)")
    # REQ-DHUB-005-003 확장
    is_active = Column(Boolean, default=True, comment="스케줄활성여부")
    next_run_at = Column(DateTime, comment="다음실행일시")
    backup_command = Column(Text, comment="백업명령어 템플릿")
    source_id = Column(UUID(as_uuid=True), comment="대상데이터소스ID")
    last_error_message = Column(Text, comment="최근실패메시지")

    __table_args__ = (
        Index("ix_sys_dr_active", "is_active", postgresql_where=text("is_active = true")),
        {"comment": "DR백업관리"},
    )


class SysPackage(AuditMixin, Base):
    """패키지검증"""
    __tablename__ = "sys_package"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="패키지ID")
    package_name = Column(String(200), nullable=False, comment="패키지명")
    package_version = Column(String(50), comment="패키지버전")
    vendor = Column(String(200), comment="공급업체")
    license_type = Column(String(100), comment="라이선스유형")
    license_expiry = Column(Date, comment="라이선스만료일")
    poc_status = Column(String(20), comment="PoC상태 (NOT_STARTED/IN_PROGRESS/PASSED/FAILED)")
    poc_result = Column(JSONB, comment="PoC결과")
    verification_date = Column(Date, comment="검증완료일")
    description = Column(Text, comment="설명")

    __table_args__ = (
        {"comment": "패키지검증"},
    )


class SysInterface(AuditMixin, Base):
    """표준인터페이스"""
    __tablename__ = "sys_interface"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="인터페이스ID")
    interface_code = Column(String(50), nullable=False, unique=True, comment="인터페이스코드")
    interface_name = Column(String(200), nullable=False, comment="인터페이스명")
    interface_type = Column(String(50), nullable=False, comment="인터페이스유형 (REST/SOAP/KAFKA/FILE/DB_LINK)")
    source_system = Column(String(200), comment="송신시스템")
    target_system = Column(String(200), comment="수신시스템")
    protocol = Column(String(50), comment="프로토콜 (HTTP/HTTPS/TCP/MQ)")
    endpoint_url = Column(String(500), comment="엔드포인트URL")
    data_format = Column(String(50), comment="데이터포맷 (JSON/XML/CSV/BINARY)")
    schedule_type = Column(String(20), comment="스케줄유형 (REALTIME/BATCH/EVENT)")
    schedule_cron = Column(String(100), comment="스케줄CRON")
    timeout_ms = Column(Integer, default=30000, comment="타임아웃MS")
    retry_count = Column(Integer, default=3, comment="재시도횟수")
    status = Column(String(20), default="ACTIVE", comment="상태")
    description = Column(Text, comment="설명")

    __table_args__ = (
        Index("ix_sys_if_code", "interface_code"),
        Index("ix_sys_if_type", "interface_type"),
        {"comment": "표준인터페이스"},
    )


class SysIntegration(AuditMixin, Base):
    """이기종통합"""
    __tablename__ = "sys_integration"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="통합ID")
    integration_name = Column(String(200), nullable=False, comment="통합명")
    source_db_type = Column(String(50), nullable=False, comment="원본DB유형 (SAP/ORACLE/TIBERO/POSTGRESQL)")
    connection_config = Column(JSONB, nullable=False, comment="연결설정")
    mapping_config = Column(JSONB, comment="매핑설정")
    sync_direction = Column(String(20), comment="동기화방향 (INBOUND/OUTBOUND/BIDIRECTIONAL)")
    sync_status = Column(String(20), default="IDLE", comment="동기화상태 (IDLE/RUNNING/SUCCESS/FAIL)")
    last_sync_at = Column(DateTime, comment="최근동기화일시")

    __table_args__ = (
        {"comment": "이기종통합"},
    )


class SysDmzLink(AuditMixin, Base):
    """DMZ연계"""
    __tablename__ = "sys_dmz_link"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="DMZ연계ID")
    link_name = Column(String(200), nullable=False, comment="연계명")
    link_type = Column(String(50), comment="연계유형 (PROXY/ONE_WAY/FILE_TRANSFER)")
    external_url = Column(String(500), comment="외부URL")
    dmz_proxy_url = Column(String(500), comment="DMZ프록시URL")
    transfer_direction = Column(String(20), comment="전송방향 (INBOUND/OUTBOUND)")
    security_level = Column(String(20), comment="보안등급")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "DMZ연계"},
    )


class SysSmsLog(AuditMixin, Base):
    """SMS발송이력"""
    __tablename__ = "sys_sms_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="SMS발송이력ID")
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), nullable=True, comment="대상사용자ID")
    recipient_phone_masked = Column(String(30), nullable=False, comment="수신번호(마스킹)")
    purpose = Column(String(30), nullable=False, comment="발송목적 (INITIAL_PWD/RESET_PWD/FIND_ID_OTP)")
    payload_template = Column(String(50), comment="사용템플릿키")
    status = Column(String(20), default="SENT", comment="발송상태 (SENT/FAIL)")
    provider = Column(String(30), default="STUB", comment="발송채널 (STUB/DMZ_PROXY/EXTERNAL)")
    error_message = Column(Text, comment="오류메시지")
    sent_at = Column(DateTime, default=datetime.now, comment="발송일시")

    __table_args__ = (
        Index("ix_sys_sms_log_user", "target_user_id"),
        Index("ix_sys_sms_log_purpose", "purpose"),
        Index("ix_sys_sms_log_sent", "sent_at"),
        Index("ix_sys_sms_log_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "SMS발송이력"},
    )


class SysInterfaceLog(AuditMixin, Base):
    """연계실행이력"""
    __tablename__ = "sys_interface_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="이력ID")
    interface_id = Column(UUID(as_uuid=True), ForeignKey("sys_interface.id", ondelete="CASCADE"), nullable=False, comment="인터페이스ID")
    integration_id = Column(UUID(as_uuid=True), ForeignKey("sys_integration.id", ondelete="SET NULL"), nullable=True, comment="통합ID")
    execution_type = Column(String(20), nullable=False, comment="실행유형 (MANUAL/SCHEDULED/EVENT)")
    status = Column(String(20), nullable=False, comment="실행상태 (RUNNING/SUCCESS/FAIL/TIMEOUT)")
    started_at = Column(DateTime, nullable=False, comment="시작일시")
    finished_at = Column(DateTime, comment="종료일시")
    duration_ms = Column(Integer, comment="소요시간MS")
    total_records = Column(Integer, default=0, comment="전체건수")
    success_records = Column(Integer, default=0, comment="성공건수")
    error_records = Column(Integer, default=0, comment="오류건수")
    error_message = Column(Text, comment="오류메시지")
    request_payload = Column(JSONB, comment="요청정보")
    response_summary = Column(JSONB, comment="응답요약")

    __table_args__ = (
        Index("ix_sys_if_log_interface", "interface_id"),
        Index("ix_sys_if_log_integration", "integration_id"),
        Index("ix_sys_if_log_started", "started_at"),
        Index("ix_sys_if_log_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "연계실행이력"},
    )
