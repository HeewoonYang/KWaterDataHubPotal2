from datetime import datetime
from decimal import Decimal

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
