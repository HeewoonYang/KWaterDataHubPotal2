"""품질검증 API"""
import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.quality import QualityCheckResult, QualityRule, StdComplianceResult
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.quality import (
    ComplianceResultResponse, QualityCheckResultResponse, QualityRuleCreate, QualityRuleResponse,
)

router = APIRouter()


# ── 품질 규칙 ──
@router.get("/rules", response_model=APIResponse[list[QualityRuleResponse]])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QualityRule).order_by(QualityRule.id))
    items = result.scalars().all()
    return APIResponse(data=items)


@router.post("/rules", response_model=APIResponse[QualityRuleResponse])
async def create_rule(body: QualityRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = QualityRule(**body.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return APIResponse(data=rule, message="Created")


# ── 품질 검증 실행 ──
@router.post("/execute", response_model=APIResponse)
async def execute_quality_check(db: AsyncSession = Depends(get_db)):
    # TODO: Celery 태스크로 비동기 품질검증 실행
    return APIResponse(message="Quality check triggered")


# ── 품질 검증 결과 ──
@router.get("/results", response_model=PageResponse[QualityCheckResultResponse])
async def list_results(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(QualityCheckResult).order_by(QualityCheckResult.executed_at.desc())
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return PageResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size > 0 else 0,
    )


@router.get("/results/{result_id}", response_model=APIResponse[QualityCheckResultResponse])
async def get_result(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QualityCheckResult).where(QualityCheckResult.id == result_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Result not found")
    return APIResponse(data=item)


# ── 표준 준수 ──
@router.get("/compliance", response_model=APIResponse[list[ComplianceResultResponse]])
async def list_compliance(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StdComplianceResult).order_by(StdComplianceResult.checked_at.desc()).limit(100)
    )
    items = result.scalars().all()
    return APIResponse(data=items)


@router.post("/compliance/check", response_model=APIResponse)
async def run_compliance_check(db: AsyncSession = Depends(get_db)):
    # TODO: 표준 준수 검사 실행 로직
    return APIResponse(message="Compliance check triggered")
