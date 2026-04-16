from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


# ── 품질 규칙 ──
class QualityRuleCreate(BaseModel):
    rule_name: str
    rule_type: str  # COMPLETENESS/VALIDITY/ACCURACY/CONSISTENCY
    target_type: str | None = None
    rule_expression: str | None = None
    severity: str = "WARNING"
    schedule_cron: str | None = None


class QualityRuleResponse(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    target_type: str | None = None
    rule_expression: str | None = None
    severity: str
    is_active: bool
    schedule_cron: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 품질 검증 결과 ──
class QualityCheckResultResponse(BaseModel):
    id: int
    rule_id: int | None = None
    dataset_name: str | None = None
    check_type: str | None = None
    total_count: int | None = None
    error_count: int | None = None
    score: Decimal | None = None
    executed_at: datetime | None = None
    execution_time_ms: int | None = None
    details: dict | None = None
    # 추적성 (신규)
    catalog_dataset_id: UUID | None = None
    distribution_dataset_id: UUID | None = None
    collection_job_id: UUID | None = None
    ai_feedback_used: bool = False
    ai_feedback_at: datetime | None = None
    ai_training_score: Decimal | None = None

    model_config = {"from_attributes": True}


# ── AI 학습 피드백 ──
class QualityAiFeedbackResponse(BaseModel):
    id: UUID
    source_result_id: int
    target_system: str
    feedback_type: str
    payload: dict
    dispatch_status: str
    dispatched_at: datetime | None = None
    dispatch_error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 대시보드 ──
class QualityDashboardSummary(BaseModel):
    avg_score_7d: float
    avg_score_30d: float
    checks_7d: int
    checks_30d: int
    failing_rules_count: int
    ai_feedback_pending: int
    ai_feedback_sent_7d: int
    ai_feedback_failed_7d: int
    low_score_datasets_7d: int


class QualityTrendPoint(BaseModel):
    day: str  # YYYY-MM-DD
    avg_score: float
    check_count: int


class QualityRuleFailure(BaseModel):
    rule_id: int | None = None
    rule_name: str | None = None
    failure_count: int
    avg_score: float


# ── 스케줄 ──
class QualityScheduleCreate(BaseModel):
    rule_id: int | None = None
    schedule_name: str
    schedule_cron: str
    target_dataset: str | None = None  # 예: "CATALOG:ALL", "DISTRIBUTION:ALL", 또는 dataset_name
    is_active: bool = True


class QualityScheduleUpdate(BaseModel):
    schedule_name: str | None = None
    schedule_cron: str | None = None
    target_dataset: str | None = None
    is_active: bool | None = None
    rule_id: int | None = None


class QualityScheduleResponse(BaseModel):
    id: int
    rule_id: int | None = None
    schedule_name: str
    schedule_cron: str
    target_dataset: str | None = None
    is_active: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── 표준 준수 결과 ──
class ComplianceResultResponse(BaseModel):
    id: int
    standard_name: str
    category: str
    total_items: int | None = None
    passed_items: int | None = None
    failed_items: int | None = None
    compliance_rate: Decimal | None = None
    checked_at: datetime | None = None
    details: dict | None = None

    model_config = {"from_attributes": True}
