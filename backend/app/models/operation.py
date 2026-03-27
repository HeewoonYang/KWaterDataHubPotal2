"""SA-10. 운영/감사 (7개 테이블)"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class OperationHubStats(Base):
    """허브운영통계"""
    __tablename__ = "operation_hub_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="허브통계ID")
    stat_date = Column(Date, nullable=False, comment="통계일자")
    stat_type = Column(String(20), nullable=False, comment="통계유형 (DAILY/WEEKLY/MONTHLY)")
    total_datasets = Column(Integer, default=0, comment="총데이터셋수")
    total_users = Column(Integer, default=0, comment="총사용자수")
    active_users = Column(Integer, default=0, comment="활성사용자수")
    total_downloads = Column(Integer, default=0, comment="총다운로드수")
    total_api_calls = Column(Integer, default=0, comment="총API호출수")
    total_storage_gb = Column(Numeric(12, 2), comment="총저장용량GB")
    data_quality_score = Column(Numeric(5, 2), comment="데이터품질점수")
    collection_success_rate = Column(Numeric(5, 2), comment="수집성공률")
    detail_data = Column(JSONB, comment="상세통계데이터")

    __table_args__ = (
        Index("uq_hub_stats", "stat_date", "stat_type", unique=True),
        {"comment": "허브운영통계"},
    )


class OperationReportTemplate(AuditMixin, Base):
    """리포트템플릿"""
    __tablename__ = "operation_report_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="리포트템플릿ID")
    template_name = Column(String(200), nullable=False, comment="템플릿명")
    template_type = Column(String(50), comment="템플릿유형 (STATISTICS/QUALITY/USAGE/CUSTOM)")
    output_format = Column(String(20), comment="출력포맷 (PDF/EXCEL)")
    template_config = Column(JSONB, comment="템플릿설정")
    description = Column(Text, comment="설명")

    __table_args__ = (
        {"comment": "리포트템플릿"},
    )


class OperationReportGeneration(Base):
    """리포트생성이력"""
    __tablename__ = "operation_report_generation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="리포트생성ID")
    template_id = Column(UUID(as_uuid=True), ForeignKey("operation_report_template.id", ondelete="SET NULL"), comment="템플릿ID")
    report_name = Column(String(300), nullable=False, comment="리포트명")
    parameters = Column(JSONB, comment="생성파라미터")
    output_format = Column(String(20), comment="출력포맷")
    file_path = Column(String(500), comment="파일경로")
    file_size_bytes = Column(BigInteger, comment="파일크기")
    generation_status = Column(String(20), comment="생성상태 (QUEUED/GENERATING/COMPLETED/FAILED)")
    generated_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="생성자ID")
    generated_at = Column(DateTime, comment="생성일시")
    celery_task_id = Column(String(200), comment="Celery작업ID")

    __table_args__ = (
        Index("ix_report_gen_template", "template_id"),
        Index("ix_report_gen_status", "generation_status"),
        {"comment": "리포트생성이력"},
    )


class OperationAiQueryLog(Base):
    """AI검색로그"""
    __tablename__ = "operation_ai_query_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="AI질의로그ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="사용자ID")
    query_text = Column(Text, nullable=False, comment="질의내용")
    query_type = Column(String(50), comment="질의유형 (NATURAL_LANGUAGE/SQL/STRUCTURED)")
    response_text = Column(Text, comment="응답내용")
    model_name = Column(String(100), comment="사용모델명")
    token_count = Column(Integer, comment="토큰수")
    response_time_ms = Column(Integer, comment="응답시간MS")
    satisfaction_rating = Column(Integer, comment="만족도평점")
    queried_at = Column(DateTime, default=datetime.now, comment="질의일시")

    __table_args__ = (
        Index("ix_ai_log_user", "user_id"),
        Index("ix_ai_log_date", "queried_at"),
        {"comment": "AI검색로그"},
    )


class OperationAiModelConfig(AuditMixin, Base):
    """AI모델설정"""
    __tablename__ = "operation_ai_model_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="AI모델설정ID")
    model_name = Column(String(200), nullable=False, comment="모델명")
    model_type = Column(String(50), comment="모델유형 (LLM/EMBEDDING/CLASSIFICATION)")
    provider = Column(String(100), comment="제공자 (OPENAI/CLAUDE/LOCAL)")
    endpoint_url = Column(String(500), comment="엔드포인트URL")
    api_key_enc = Column(String(500), comment="API키")
    model_config = Column(JSONB, comment="모델설정")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "AI모델설정"},
    )


class OperationAccessLog(Base):
    """접근감사로그"""
    __tablename__ = "operation_access_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="접근로그ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="사용자ID")
    action = Column(String(50), nullable=False, comment="수행작업 (READ/DOWNLOAD/API_CALL/LOGIN/LOGOUT/ADMIN_ACTION)")
    resource_type = Column(String(50), comment="리소스유형 (DATASET/API/REPORT/SYSTEM)")
    resource_id = Column(String(200), comment="리소스ID")
    resource_name = Column(String(300), comment="리소스명")
    client_ip = Column(String(45), comment="클라이언트IP")
    user_agent = Column(String(500), comment="사용자에이전트")
    request_method = Column(String(10), comment="HTTP메서드")
    request_path = Column(String(500), comment="요청경로")
    response_status = Column(Integer, comment="응답상태코드")
    result = Column(String(20), comment="결과 (SUCCESS/FAIL/DENIED)")
    detail = Column(JSONB, comment="상세정보")
    logged_at = Column(DateTime, default=datetime.now, comment="기록일시")

    __table_args__ = (
        Index("ix_access_log_user", "user_id"),
        Index("ix_access_log_date", "logged_at"),
        Index("ix_access_log_action", "action"),
        {"comment": "접근감사로그"},
    )


class OperationSystemEvent(Base):
    """시스템이벤트"""
    __tablename__ = "operation_system_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="시스템이벤트ID")
    event_type = Column(String(50), nullable=False, comment="이벤트유형 (PERFORMANCE/ERROR/MAINTENANCE/OPTIMIZATION)")
    event_source = Column(String(200), comment="이벤트소스")
    severity = Column(String(20), comment="심각도 (INFO/WARNING/ERROR/CRITICAL)")
    title = Column(String(300), nullable=False, comment="제목")
    description = Column(Text, comment="설명")
    metrics = Column(JSONB, comment="관련메트릭")
    resolution = Column(Text, comment="해결방안")
    occurred_at = Column(DateTime, default=datetime.now, comment="발생일시")
    resolved_at = Column(DateTime, comment="해결일시")

    __table_args__ = (
        Index("ix_sys_event_type", "event_type"),
        Index("ix_sys_event_date", "occurred_at"),
        {"comment": "시스템이벤트"},
    )
