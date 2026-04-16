"""품질검증 API"""
import math
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.distribution import DistributionDataset
from app.models.quality import (
    QualityAiFeedback, QualityCheckResult, QualityRule, QualitySchedule, StdComplianceResult,
)
from app.models.standard import StdTerm
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.quality import (
    ComplianceResultResponse, QualityAiFeedbackResponse,
    QualityCheckResultResponse, QualityDashboardSummary,
    QualityRuleCreate, QualityRuleFailure, QualityRuleResponse,
    QualityScheduleCreate, QualityScheduleResponse, QualityScheduleUpdate,
    QualityTrendPoint,
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


# ── 품질 검증 실행 (동기 방식 - 즉시 결과 반환) ──
@router.post("/execute", response_model=APIResponse)
async def execute_quality_check(db: AsyncSession = Depends(get_db)):
    """전체 카탈로그 데이터셋에 대해 품질 검증 실행"""
    datasets = (await db.execute(
        select(CatalogDataset).where(CatalogDataset.status == "ACTIVE")
    )).scalars().all()

    results_count = 0
    for ds in datasets:
        # 각 데이터셋의 컬럼 메타데이터 완전성 체크
        cols = (await db.execute(
            select(CatalogColumn).where(CatalogColumn.dataset_id == ds.id)
        )).scalars().all()

        total_cols = len(cols)
        if total_cols == 0:
            score = 0
        else:
            filled = sum(1 for c in cols if c.column_name_kr and c.data_type)
            score = round(filled / total_cols * 100, 1)

        error_count = total_cols - int(total_cols * score / 100) if total_cols > 0 else 0

        result = QualityCheckResult(
            dataset_name=ds.dataset_name,
            check_type="COMPLETENESS",
            rule_id=None,
            total_count=total_cols,
            error_count=error_count,
            score=score,
            executed_at=datetime.now(),
            details={"dataset_id": str(ds.id), "check": "column_metadata_completeness"},
        )
        db.add(result)
        results_count += 1

    return APIResponse(data={"checked_datasets": results_count}, message=f"{results_count}개 데이터셋 품질검증 완료")


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


@router.get("/compliance/summary", response_model=APIResponse)
async def compliance_summary(db: AsyncSession = Depends(get_db)):
    """표준 준수율 요약 통계"""
    rows = (await db.execute(select(StdComplianceResult))).scalars().all()
    total = len(rows)
    if total == 0:
        return APIResponse(data={"total": 0, "compliant": 0, "non_compliant": 0, "avg_rate": 0})

    compliant = sum(1 for r in rows if (r.compliance_rate or 0) >= 80)
    avg_rate = round(sum(r.compliance_rate or 0 for r in rows) / total, 1)
    return APIResponse(data={
        "total": total,
        "compliant": compliant,
        "non_compliant": total - compliant,
        "avg_rate": avg_rate,
    })


@router.post("/compliance/check", response_model=APIResponse)
async def run_compliance_check(db: AsyncSession = Depends(get_db)):
    """표준 준수율 검사: 카탈로그 컬럼명이 용어사전에 존재하는지 체크"""
    datasets = (await db.execute(
        select(CatalogDataset).where(CatalogDataset.status == "ACTIVE")
    )).scalars().all()

    # 용어사전에서 영문명 목록 가져오기 (검증 기준)
    term_names = set()
    term_rows = (await db.execute(select(StdTerm.physical_name))).scalars().all()
    for t in term_rows:
        if t:
            term_names.add(t.upper())

    results_count = 0
    for ds in datasets:
        cols = (await db.execute(
            select(CatalogColumn).where(CatalogColumn.dataset_id == ds.id)
        )).scalars().all()

        total = len(cols)
        if total == 0:
            continue

        passed = sum(1 for c in cols if c.column_name and c.column_name.upper() in term_names)
        rate = round(passed / total * 100, 1)

        result = StdComplianceResult(
            standard_name=ds.dataset_name,
            category="용어",
            total_items=total,
            passed_items=passed,
            failed_items=total - passed,
            compliance_rate=rate,
            checked_at=datetime.now(),
            details={"dataset_id": str(ds.id), "check_type": "TERM_COMPLIANCE"},
        )
        db.add(result)
        results_count += 1

    return APIResponse(data={"checked_datasets": results_count}, message=f"{results_count}개 데이터셋 준수율 검사 완료")


# ════════════════════════════════════════════════════════════════════
# 카탈로그 단일 대상 + 유통 품질 검증 (비동기 Celery dispatch)
# ════════════════════════════════════════════════════════════════════
@router.post("/catalog/{catalog_dataset_id}/check", response_model=APIResponse)
async def trigger_catalog_check(catalog_dataset_id: str, db: AsyncSession = Depends(get_db)):
    """특정 카탈로그 데이터셋에 대한 품질 검증을 비동기 dispatch."""
    try:
        uid = uuid.UUID(catalog_dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="catalog_dataset_id 형식 오류")
    ds = (await db.execute(
        select(CatalogDataset).where(CatalogDataset.id == uid, CatalogDataset.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="catalog dataset not found")
    from app.tasks.quality_tasks import execute_quality_check
    execute_quality_check.delay(dataset_name=ds.dataset_name, catalog_dataset_id=str(ds.id))
    return APIResponse(message="카탈로그 품질 검증을 dispatch 했습니다", data={"catalog_dataset_id": str(ds.id)})


@router.post("/distribution/{distribution_dataset_id}/check", response_model=APIResponse)
async def trigger_distribution_check(distribution_dataset_id: str, db: AsyncSession = Depends(get_db)):
    """특정 유통 데이터셋 품질 검증 dispatch."""
    try:
        uid = uuid.UUID(distribution_dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="distribution_dataset_id 형식 오류")
    ds = (await db.execute(
        select(DistributionDataset).where(
            DistributionDataset.id == uid,
            DistributionDataset.is_deleted == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="distribution dataset not found")
    from app.tasks.quality_tasks import execute_distribution_quality_check
    execute_distribution_quality_check.delay(str(ds.id))
    return APIResponse(message="유통 품질 검증을 dispatch 했습니다", data={"distribution_dataset_id": str(ds.id)})


@router.post("/distribution/check-all", response_model=APIResponse)
async def trigger_distribution_check_all():
    """활성 유통 데이터셋 전체에 대해 품질 검증 dispatch."""
    from app.tasks.quality_tasks import execute_distribution_quality_check_all
    execute_distribution_quality_check_all.delay()
    return APIResponse(message="유통 전체 품질 검증을 dispatch 했습니다")


# ════════════════════════════════════════════════════════════════════
# 대시보드
# ════════════════════════════════════════════════════════════════════
@router.get("/dashboard/summary", response_model=APIResponse[QualityDashboardSummary])
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    """관리자 품질 대시보드 KPI."""
    now = datetime.now()
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    avg7_row = (await db.execute(
        select(func.avg(QualityCheckResult.score), func.count(QualityCheckResult.id))
        .where(QualityCheckResult.executed_at >= d7)
    )).first()
    avg30_row = (await db.execute(
        select(func.avg(QualityCheckResult.score), func.count(QualityCheckResult.id))
        .where(QualityCheckResult.executed_at >= d30)
    )).first()

    failing_rules = (await db.execute(
        select(func.count(func.distinct(QualityCheckResult.rule_id)))
        .where(
            QualityCheckResult.executed_at >= d7,
            QualityCheckResult.rule_id.isnot(None),
            QualityCheckResult.score < 80,
        )
    )).scalar() or 0

    pending = (await db.execute(
        select(func.count(QualityAiFeedback.id)).where(
            QualityAiFeedback.dispatch_status == "PENDING",
            QualityAiFeedback.is_deleted == False,  # noqa: E712
        )
    )).scalar() or 0
    sent_7d = (await db.execute(
        select(func.count(QualityAiFeedback.id)).where(
            QualityAiFeedback.dispatch_status == "SENT",
            QualityAiFeedback.dispatched_at >= d7,
        )
    )).scalar() or 0
    failed_7d = (await db.execute(
        select(func.count(QualityAiFeedback.id)).where(
            QualityAiFeedback.dispatch_status == "FAILED",
            QualityAiFeedback.created_at >= d7,
        )
    )).scalar() or 0

    low_score_datasets_7d = (await db.execute(
        select(func.count(func.distinct(QualityCheckResult.dataset_name)))
        .where(
            QualityCheckResult.executed_at >= d7,
            QualityCheckResult.score < 80,
        )
    )).scalar() or 0

    return APIResponse(data=QualityDashboardSummary(
        avg_score_7d=float(avg7_row[0] or 0),
        avg_score_30d=float(avg30_row[0] or 0),
        checks_7d=int(avg7_row[1] or 0),
        checks_30d=int(avg30_row[1] or 0),
        failing_rules_count=int(failing_rules),
        ai_feedback_pending=int(pending),
        ai_feedback_sent_7d=int(sent_7d),
        ai_feedback_failed_7d=int(failed_7d),
        low_score_datasets_7d=int(low_score_datasets_7d),
    ))


@router.get("/dashboard/trend", response_model=APIResponse[list[QualityTrendPoint]])
async def dashboard_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    """일별 평균 점수 추이."""
    days = max(1, min(days, 90))
    since = datetime.now() - timedelta(days=days)
    rows = (await db.execute(sql_text(
        """
        SELECT to_char(date_trunc('day', executed_at), 'YYYY-MM-DD') AS day,
               AVG(score)::float AS avg_score,
               COUNT(*)::int     AS cnt
          FROM quality_check_result
         WHERE executed_at >= :since
         GROUP BY 1
         ORDER BY 1
        """
    ), {"since": since})).all()
    points = [
        QualityTrendPoint(day=r[0], avg_score=float(r[1] or 0), check_count=int(r[2] or 0))
        for r in rows
    ]
    return APIResponse(data=points)


@router.get("/dashboard/rule-failures", response_model=APIResponse[list[QualityRuleFailure]])
async def dashboard_rule_failures(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """최근 7일 실패(80점 미만) 건수 기준 규칙별 Top N."""
    limit = max(1, min(limit, 50))
    since = datetime.now() - timedelta(days=7)
    rows = (await db.execute(
        select(
            QualityCheckResult.rule_id,
            QualityRule.rule_name,
            func.count(QualityCheckResult.id).label("cnt"),
            func.avg(QualityCheckResult.score).label("avg_score"),
        )
        .select_from(QualityCheckResult)
        .join(QualityRule, QualityRule.id == QualityCheckResult.rule_id, isouter=True)
        .where(
            QualityCheckResult.executed_at >= since,
            QualityCheckResult.score < 80,
        )
        .group_by(QualityCheckResult.rule_id, QualityRule.rule_name)
        .order_by(func.count(QualityCheckResult.id).desc())
        .limit(limit)
    )).all()
    data = [
        QualityRuleFailure(
            rule_id=r[0],
            rule_name=r[1] or ("규칙 없음" if r[0] is None else f"rule-{r[0]}"),
            failure_count=int(r[2] or 0),
            avg_score=float(r[3] or 0),
        )
        for r in rows
    ]
    return APIResponse(data=data)


# ════════════════════════════════════════════════════════════════════
# AI 피드백 조회/재발송
# ════════════════════════════════════════════════════════════════════
@router.get("/ai-feedback", response_model=PageResponse[QualityAiFeedbackResponse])
async def list_ai_feedback(
    status: str | None = None,
    target_system: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    q = select(QualityAiFeedback).where(QualityAiFeedback.is_deleted == False)  # noqa: E712
    if status:
        q = q.where(QualityAiFeedback.dispatch_status == status.upper())
    if target_system:
        q = q.where(QualityAiFeedback.target_system == target_system.upper())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    offset = (max(page, 1) - 1) * page_size
    rows = (await db.execute(
        q.order_by(QualityAiFeedback.created_at.desc()).offset(offset).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=rows, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size else 0,
    )


@router.post("/ai-feedback/{feedback_id}/retry", response_model=APIResponse)
async def retry_ai_feedback(feedback_id: str, db: AsyncSession = Depends(get_db)):
    """실패/전송 완료 항목을 PENDING 으로 되돌려 재발송 대기열에 올림."""
    try:
        uid = uuid.UUID(feedback_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 feedback_id 형식")
    row = (await db.execute(
        select(QualityAiFeedback).where(QualityAiFeedback.id == uid)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="feedback not found")
    row.dispatch_status = "PENDING"
    row.dispatch_error = None
    row.dispatched_at = None
    return APIResponse(message="재발송 대기열에 올렸습니다")


@router.post("/ai-feedback/dispatch-now", response_model=APIResponse)
async def dispatch_ai_feedback_now():
    """관리자 수동 트리거: PENDING 즉시 일괄 발송 (Celery 비동기)."""
    from app.tasks.quality_tasks import dispatch_quality_ai_feedback
    dispatch_quality_ai_feedback.delay()
    return APIResponse(message="AI 피드백 일괄 발송을 dispatch 했습니다")


# ════════════════════════════════════════════════════════════════════
# 스케줄 CRUD
# ════════════════════════════════════════════════════════════════════
@router.get("/schedules", response_model=APIResponse[list[QualityScheduleResponse]])
async def list_schedules(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(QualitySchedule).where(QualitySchedule.is_deleted == False)  # noqa: E712
        .order_by(QualitySchedule.id)
    )).scalars().all()
    return APIResponse(data=rows)


@router.post("/schedules", response_model=APIResponse[QualityScheduleResponse])
async def create_schedule(body: QualityScheduleCreate, db: AsyncSession = Depends(get_db)):
    # cron 유효성 검사
    try:
        from croniter import croniter
        if not croniter.is_valid(body.schedule_cron):
            raise ValueError("invalid cron")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"schedule_cron 오류: {e}")

    sched = QualitySchedule(
        rule_id=body.rule_id,
        schedule_name=body.schedule_name,
        schedule_cron=body.schedule_cron,
        target_dataset=body.target_dataset,
        is_active=body.is_active,
    )
    # 다음 실행시각 미리 계산
    try:
        from croniter import croniter
        sched.next_run_at = croniter(body.schedule_cron, datetime.now()).get_next(datetime)
    except Exception:
        sched.next_run_at = None
    db.add(sched)
    await db.flush()
    await db.refresh(sched)
    return APIResponse(data=sched, message="스케줄이 생성되었습니다")


@router.put("/schedules/{schedule_id}", response_model=APIResponse[QualityScheduleResponse])
async def update_schedule(schedule_id: int, body: QualityScheduleUpdate, db: AsyncSession = Depends(get_db)):
    sched = (await db.execute(
        select(QualitySchedule).where(QualitySchedule.id == schedule_id, QualitySchedule.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="schedule not found")
    data = body.model_dump(exclude_none=True)
    for k, v in data.items():
        setattr(sched, k, v)
    # cron 변경 시 다음 실행시각 재계산
    if "schedule_cron" in data:
        try:
            from croniter import croniter
            if not croniter.is_valid(sched.schedule_cron):
                raise ValueError("invalid cron")
            sched.next_run_at = croniter(sched.schedule_cron, datetime.now()).get_next(datetime)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"schedule_cron 오류: {e}")
    await db.flush()
    await db.refresh(sched)
    return APIResponse(data=sched, message="스케줄이 수정되었습니다")


@router.delete("/schedules/{schedule_id}", response_model=APIResponse)
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    sched = (await db.execute(
        select(QualitySchedule).where(QualitySchedule.id == schedule_id, QualitySchedule.is_deleted == False)  # noqa: E712
    )).scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="schedule not found")
    sched.is_deleted = True
    sched.is_active = False
    return APIResponse(message="스케줄이 삭제되었습니다")
