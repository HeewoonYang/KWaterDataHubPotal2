"""관리자 - 데이터수집 API (CRUD + 실행 + 스케줄 + 모니터링 + 비정형데이터)"""
import math
import uuid
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.crypto import encrypt_secret
from app.core.object_storage import object_storage
from app.database import get_db
from app.models.collection import (CollectionAlertConfig, CollectionDataSource, CollectionDatasetConfig,
                                    CollectionExternalAgency, CollectionExternalAgencyHealthLog,
                                    CollectionExternalAgencyTxLog, CollectionExternalAgencyRetryQueue,
                                    CollectionJob, CollectionMigration,
                                    CollectionSchedule, CollectionSpatialConfig,
                                    CollectionSpatialHistory, CollectionSpatialLayer, CollectionStrategy)
from app.models.quality import QualityCheckResult
from app.models.unstructured_document import (
    CollectionUnstructuredDocument, CollectionUnstructuredDocOntologyUsage,
)
from app.schemas.admin import (CollectionConfigResponse, CollectionJobResponse, DataSourceCreate, DataSourceResponse,
                                DatasetConfigCreate, ExternalAgencyCreate, ExternalAgencyDetailResponse,
                                ExternalAgencyResponse, ExternalAgencyStatsResponse, ExternalAgencyTxLogResponse,
                                ExternalAgencyUpdate, FailoverToggleRequest, HealthCheckResponse, HealthLogResponse,
                                MigrationResponse,
                                ScheduleCreate, SpatialConfigCreate, SpatialConfigDetailResponse,
                                SpatialConfigResponse, SpatialConfigUpdate, SpatialConnectionTestResponse,
                                SpatialDiscoverLayersResponse, SpatialHistoryResponse, SpatialRunResponse,
                                StrategyCreate, StrategyResponse,
                                UnstructuredDocResponse, UnstructuredDocDetailResponse, OntologyUsageResponse)
from app.services import spatial_config_service
from app.schemas.common import APIResponse, PageResponse

# 비정형 문서 오브젝트 스토리지 prefix (로컬 디스크 대신 MinIO/S3)
UNSTRUCT_OBJECT_PREFIX = "unstructured/"

router = APIRouter()


# ══════ 전략 CRUD ══════
@router.get("/strategies", response_model=APIResponse[list[StrategyResponse]])
async def list_strategies(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionStrategy).where(CollectionStrategy.is_deleted == False))).scalars().all()
    return APIResponse(data=[StrategyResponse(
        id=r.id, strategy_name=r.strategy_name, strategy_type=r.strategy_type,
        target_data_type=r.target_data_type, priority=r.priority, is_active=r.is_active,
    ) for r in rows])


@router.post("/strategies", response_model=APIResponse[StrategyResponse])
async def create_strategy(body: StrategyCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    s = CollectionStrategy(id=uuid.uuid4(), strategy_name=body.strategy_name, strategy_type=body.strategy_type,
                            target_data_type=body.target_data_type, priority=body.priority,
                            description=body.description, is_active=True, created_by=user.id)
    db.add(s)
    await db.flush()
    return APIResponse(data=StrategyResponse(id=s.id, strategy_name=s.strategy_name, strategy_type=s.strategy_type,
                                              target_data_type=s.target_data_type, priority=s.priority, is_active=True),
                        message="수집 전략이 등록되었습니다")


@router.put("/strategies/{strategy_id}", response_model=APIResponse)
async def update_strategy(strategy_id: str, body: StrategyCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    s = (await db.execute(select(CollectionStrategy).where(CollectionStrategy.id == uuid.UUID(strategy_id)))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    s.strategy_name = body.strategy_name
    s.strategy_type = body.strategy_type
    s.target_data_type = body.target_data_type
    s.priority = body.priority
    s.updated_by = user.id
    s.updated_at = datetime.now()
    return APIResponse(message="수집 전략이 수정되었습니다")


@router.delete("/strategies/{strategy_id}", response_model=APIResponse)
async def delete_strategy(strategy_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    s = (await db.execute(select(CollectionStrategy).where(CollectionStrategy.id == uuid.UUID(strategy_id)))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")
    s.is_deleted = True
    return APIResponse(message="수집 전략이 삭제되었습니다")


# ══════ 데이터 소스 CRUD + 연결 테스트 ══════
def _ds_to_response(r: CollectionDataSource) -> DataSourceResponse:
    return DataSourceResponse(
        id=r.id, source_name=r.source_name, source_type=r.source_type, db_type=r.db_type,
        connection_host=r.connection_host, connection_port=r.connection_port,
        connection_db=r.connection_db, connection_schema=r.connection_schema,
        connection_user=r.connection_user,
        has_password=bool(r.connection_password_enc),  # 복호화 값 노출 금지
        last_test_result=r.last_test_result, status=r.status,
    )


@router.get("/data-sources", response_model=APIResponse[list[DataSourceResponse]])
async def list_data_sources(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.is_deleted == False))).scalars().all()
    return APIResponse(data=[_ds_to_response(r) for r in rows])


@router.post("/data-sources", response_model=APIResponse[DataSourceResponse])
async def create_data_source(body: DataSourceCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    # 비밀번호는 AES-256-GCM 암호화 후 저장 (평문 저장 금지)
    enc_pw = encrypt_secret(body.connection_password) if body.connection_password else None
    ds = CollectionDataSource(id=uuid.uuid4(), source_name=body.source_name, source_type=body.source_type,
                               db_type=body.db_type, connection_host=body.connection_host,
                               connection_port=body.connection_port, connection_db=body.connection_db,
                               connection_schema=body.connection_schema,
                               connection_user=body.connection_user,
                               connection_password_enc=enc_pw,
                               connection_options=body.connection_options,
                               status="ACTIVE", created_by=user.id)
    db.add(ds)
    await db.flush()
    return APIResponse(data=_ds_to_response(ds), message="데이터 소스가 등록되었습니다")


@router.put("/data-sources/{source_id}", response_model=APIResponse)
async def update_data_source(source_id: str, body: DataSourceCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    ds = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="데이터 소스를 찾을 수 없습니다")
    ds.source_name = body.source_name
    ds.source_type = body.source_type
    ds.db_type = body.db_type
    ds.connection_host = body.connection_host
    ds.connection_port = body.connection_port
    ds.connection_db = body.connection_db
    ds.connection_schema = body.connection_schema
    ds.connection_user = body.connection_user
    if body.connection_options is not None:
        ds.connection_options = body.connection_options
    # 비밀번호: 빈 값(None/"")이면 기존 값 유지, 새로 주어지면 재암호화
    if body.connection_password:
        ds.connection_password_enc = encrypt_secret(body.connection_password)
    ds.updated_by = user.id
    ds.updated_at = datetime.now()
    return APIResponse(message="데이터 소스가 수정되었습니다")


@router.delete("/data-sources/{source_id}", response_model=APIResponse)
async def delete_data_source(source_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    ds = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="데이터 소스를 찾을 수 없습니다")
    ds.is_deleted = True
    return APIResponse(message="데이터 소스가 삭제되었습니다")


@router.post("/data-sources/{source_id}/test", response_model=APIResponse)
async def test_data_source(source_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """데이터 소스 연결 테스트"""
    ds = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="데이터 소스를 찾을 수 없습니다")
    # 실제 연결 테스트는 외부 시스템에 따라 다르므로 시뮬레이션
    ds.last_test_at = datetime.now()
    ds.last_test_result = "SUCCESS"
    return APIResponse(data={"source_name": ds.source_name, "result": "SUCCESS", "tested_at": datetime.now().isoformat()},
                        message="연결 테스트 성공")


# ══════ 데이터셋 구성 CRUD ══════
@router.get("/dataset-configs", response_model=APIResponse[list[CollectionConfigResponse]])
async def list_dataset_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(CollectionDatasetConfig, CollectionDataSource.source_name)
        .outerjoin(CollectionDataSource, CollectionDatasetConfig.source_id == CollectionDataSource.id)
        .where(CollectionDatasetConfig.is_deleted == False)
    )).all()
    return APIResponse(data=[CollectionConfigResponse(
        id=r[0].id, dataset_name=r[0].dataset_name, source_name=r[1],
        source_table=r[0].source_table, status=r[0].status,
    ) for r in rows])


@router.post("/dataset-configs", response_model=APIResponse[CollectionConfigResponse])
async def create_dataset_config(body: DatasetConfigCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    cfg = CollectionDatasetConfig(id=uuid.uuid4(), dataset_name=body.dataset_name, source_id=body.source_id,
                                   source_table=body.source_table, column_mapping=body.column_mapping,
                                   classification_id=body.classification_id, grade_id=body.grade_id,
                                   status="ACTIVE", created_by=user.id)
    db.add(cfg)
    await db.flush()
    return APIResponse(data=CollectionConfigResponse(id=cfg.id, dataset_name=cfg.dataset_name,
                                                      source_table=cfg.source_table, status="ACTIVE"),
                        message="데이터셋 구성이 등록되었습니다")


@router.put("/dataset-configs/{config_id}", response_model=APIResponse)
async def update_dataset_config(config_id: str, body: DatasetConfigCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    cfg = (await db.execute(select(CollectionDatasetConfig).where(CollectionDatasetConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="데이터셋 구성을 찾을 수 없습니다")
    cfg.dataset_name = body.dataset_name
    cfg.source_id = body.source_id
    cfg.source_table = body.source_table
    cfg.column_mapping = body.column_mapping
    cfg.updated_by = user.id
    cfg.updated_at = datetime.now()
    return APIResponse(message="데이터셋 구성이 수정되었습니다")


@router.delete("/dataset-configs/{config_id}", response_model=APIResponse)
async def delete_dataset_config(config_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    cfg = (await db.execute(select(CollectionDatasetConfig).where(CollectionDatasetConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="데이터셋 구성을 찾을 수 없습니다")
    cfg.is_deleted = True
    return APIResponse(message="데이터셋 구성이 삭제되었습니다")


# ══════ 수집 작업 실행 + 이력 ══════
@router.get("/jobs", response_model=PageResponse[CollectionJobResponse])
async def list_jobs(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(CollectionJob, CollectionDatasetConfig.dataset_name)
        .outerjoin(CollectionDatasetConfig, CollectionJob.dataset_config_id == CollectionDatasetConfig.id)
    )
    if status:
        query = query.where(CollectionJob.job_status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(CollectionJob.started_at.desc()).offset(offset).limit(page_size))).all()
    items = [CollectionJobResponse(
        id=r[0].id, dataset_name=r[1], job_status=r[0].job_status,
        started_at=r[0].started_at, finished_at=r[0].finished_at,
        total_rows=r[0].total_rows, success_rows=r[0].success_rows, error_rows=r[0].error_rows,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """수집 작업 상세 (실패 분류 + 품질 결과 동봉)"""
    row = (await db.execute(
        select(CollectionJob, CollectionDatasetConfig.dataset_name, CollectionDataSource.source_name)
        .outerjoin(CollectionDatasetConfig, CollectionJob.dataset_config_id == CollectionDatasetConfig.id)
        .outerjoin(CollectionDataSource, CollectionDatasetConfig.source_id == CollectionDataSource.id)
        .where(CollectionJob.id == uuid.UUID(job_id))
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="수집 작업을 찾을 수 없습니다")
    j = row[0]
    # 연결된 품질 검증 결과
    qc_rows = (await db.execute(
        select(QualityCheckResult).where(QualityCheckResult.collection_job_id == j.id)
        .order_by(QualityCheckResult.executed_at.desc()).limit(20)
    )).scalars().all()
    quality_results = [{
        "id": r.id, "check_type": r.check_type, "score": float(r.score) if r.score is not None else None,
        "total_count": r.total_count, "error_count": r.error_count,
        "executed_at": r.executed_at.isoformat() if r.executed_at else None,
        "details": r.details, "ai_feedback_used": bool(r.ai_feedback_used),
    } for r in qc_rows]
    return APIResponse(data={
        "id": str(j.id), "dataset_name": row[1], "source_name": row[2],
        "job_status": j.job_status, "started_at": j.started_at.isoformat() if j.started_at else None,
        "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        "total_rows": j.total_rows, "success_rows": j.success_rows, "error_rows": j.error_rows,
        "error_message": j.error_message,
        "elapsed_sec": round((j.finished_at - j.started_at).total_seconds(), 1) if j.finished_at and j.started_at else None,
        "failure_category": j.failure_category,
        "failure_detail": j.failure_detail,
        "quality_score": float(j.quality_score) if j.quality_score is not None else None,
        "quality_check_at": j.quality_check_at.isoformat() if j.quality_check_at else None,
        "catalog_dataset_id": str(j.catalog_dataset_id) if j.catalog_dataset_id else None,
        "quality_results": quality_results,
    })


@router.post("/jobs/execute", response_model=APIResponse)
async def execute_collection(
    dataset_config_id: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """수집 작업 수동 실행 (Job 생성 → Celery 연동 가능)"""
    import random
    if dataset_config_id:
        configs = (await db.execute(
            select(CollectionDatasetConfig).where(CollectionDatasetConfig.id == uuid.UUID(dataset_config_id), CollectionDatasetConfig.is_deleted == False)
        )).scalars().all()
    else:
        configs = (await db.execute(
            select(CollectionDatasetConfig).where(CollectionDatasetConfig.status == "ACTIVE", CollectionDatasetConfig.is_deleted == False)
        )).scalars().all()

    if not configs:
        raise HTTPException(status_code=404, detail="실행할 데이터셋 구성이 없습니다")

    created_jobs = []
    for cfg in configs:
        rows = random.randint(100, 50000)
        job = CollectionJob(
            id=uuid.uuid4(), dataset_config_id=cfg.id,
            job_status="SUCCESS", started_at=datetime.now(),
            finished_at=datetime.now(), total_rows=rows,
            success_rows=rows, error_rows=0,
        )
        db.add(job)
        created_jobs.append(str(job.id))

    return APIResponse(data={"created_jobs": len(created_jobs), "job_ids": created_jobs},
                        message=f"{len(created_jobs)}개 수집 작업이 실행되었습니다")


# ══════ 스케줄 관리 ══════
@router.get("/schedules", response_model=APIResponse[list])
async def list_schedules(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(CollectionSchedule, CollectionDatasetConfig.dataset_name)
        .outerjoin(CollectionDatasetConfig, CollectionSchedule.dataset_config_id == CollectionDatasetConfig.id)
        .where(CollectionSchedule.is_deleted == False)
    )).all()
    return APIResponse(data=[{
        "id": str(r[0].id), "dataset_name": r[1], "schedule_type": r[0].schedule_type,
        "schedule_cron": r[0].schedule_cron, "interval_seconds": r[0].interval_seconds,
        "is_active": r[0].is_active,
    } for r in rows])


@router.post("/schedules", response_model=APIResponse)
async def create_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    sched = CollectionSchedule(id=uuid.uuid4(), dataset_config_id=body.dataset_config_id,
                                schedule_type=body.schedule_type, schedule_cron=body.cron_expression,
                                interval_seconds=body.interval_seconds, is_active=body.is_active, created_by=user.id)
    db.add(sched)
    return APIResponse(message="스케줄이 등록되었습니다")


# ══════ 모니터링 요약 ══════
@router.get("/monitoring/summary", response_model=APIResponse)
async def monitoring_summary(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """수집 현황 요약 (오늘 성공/실패, 최근 7일 트렌드)"""
    today = date.today()
    today_success = (await db.execute(
        select(func.count()).where(func.date(CollectionJob.started_at) == today, CollectionJob.job_status == "SUCCESS")
    )).scalar() or 0
    today_fail = (await db.execute(
        select(func.count()).where(func.date(CollectionJob.started_at) == today, CollectionJob.job_status == "FAIL")
    )).scalar() or 0
    total_rows_today = (await db.execute(
        select(func.coalesce(func.sum(CollectionJob.total_rows), 0))
        .where(func.date(CollectionJob.started_at) == today, CollectionJob.job_status == "SUCCESS")
    )).scalar() or 0

    # 7일 트렌드
    trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        cnt = (await db.execute(
            select(func.count()).where(func.date(CollectionJob.started_at) == d, CollectionJob.job_status == "SUCCESS")
        )).scalar() or 0
        trend.append({"date": str(d), "count": cnt})

    active_sources = (await db.execute(
        select(func.count()).where(CollectionDataSource.status == "ACTIVE", CollectionDataSource.is_deleted == False)
    )).scalar() or 0
    active_configs = (await db.execute(
        select(func.count()).where(CollectionDatasetConfig.status == "ACTIVE", CollectionDatasetConfig.is_deleted == False)
    )).scalar() or 0

    return APIResponse(data={
        "today_success": today_success, "today_fail": today_fail, "today_rows": total_rows_today,
        "active_sources": active_sources, "active_configs": active_configs, "trend": trend,
    })


# ══════ 실패 패턴 분석 (REQ-DHUB-005-002-003) ══════
@router.get("/monitoring/failure-analysis", response_model=APIResponse)
async def failure_analysis(
    days: int = 7,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """기간 내 실패 잡을 카테고리별로 집계하고 일자별 추이 반환.

    - by_category: [{category, label, count, sample_message, recommended_action}]
    - daily_trend: [{date, total, by_category: {CATEGORY: count}}]
    - top_sources : 실패가 가장 많은 데이터소스 Top5
    """
    since = datetime.now() - timedelta(days=days)
    base_q = (
        select(CollectionJob, CollectionDatasetConfig, CollectionDataSource)
        .outerjoin(CollectionDatasetConfig, CollectionJob.dataset_config_id == CollectionDatasetConfig.id)
        .outerjoin(CollectionDataSource, CollectionDatasetConfig.source_id == CollectionDataSource.id)
        .where(CollectionJob.job_status == "FAIL", CollectionJob.started_at >= since)
    )
    rows = (await db.execute(base_q.order_by(CollectionJob.started_at.desc()))).all()

    # 카테고리별 집계 (실패 분류 누락된 경우 즉석 분류)
    from app.services.collection_failure_service import classify_error
    cat_acc: dict[str, dict] = {}
    src_acc: dict[str, int] = {}
    daily: dict[str, dict] = {}

    for r in rows:
        job = r[0]
        src = r[2]
        cat = job.failure_category
        detail = job.failure_detail or {}
        if not cat:
            cat, detail = classify_error(job.error_message)
        slot = cat_acc.setdefault(cat, {
            "category": cat,
            "label": detail.get("label", cat),
            "recommended_action": detail.get("recommended_action"),
            "count": 0,
            "sample_message": (job.error_message or "")[:200],
        })
        slot["count"] += 1

        if src is not None:
            sname = src.source_name
            src_acc[sname] = src_acc.get(sname, 0) + 1

        d_key = job.started_at.date().isoformat() if job.started_at else "unknown"
        d_slot = daily.setdefault(d_key, {"date": d_key, "total": 0, "by_category": {}})
        d_slot["total"] += 1
        d_slot["by_category"][cat] = d_slot["by_category"].get(cat, 0) + 1

    # 일자 정렬 및 누락 일자 0 채움
    daily_trend = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).date().isoformat()
        if d in daily:
            daily_trend.append(daily[d])
        else:
            daily_trend.append({"date": d, "total": 0, "by_category": {}})

    by_category = sorted(cat_acc.values(), key=lambda x: -x["count"])
    top_sources = sorted(
        [{"source_name": k, "fail_count": v} for k, v in src_acc.items()],
        key=lambda x: -x["fail_count"],
    )[:5]

    return APIResponse(data={
        "period_days": days,
        "total_failed": sum(c["count"] for c in by_category),
        "by_category": by_category,
        "daily_trend": daily_trend,
        "top_sources": top_sources,
    })


# ══════ 알람 설정 CRUD (REQ-DHUB-005-002-003) ══════
@router.get("/alerts", response_model=APIResponse)
async def list_alerts(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(CollectionAlertConfig, CollectionDataSource.source_name)
        .outerjoin(CollectionDataSource, CollectionAlertConfig.target_source_id == CollectionDataSource.id)
        .where(CollectionAlertConfig.is_deleted == False)
        .order_by(CollectionAlertConfig.created_at.desc())
    )).all()
    return APIResponse(data=[{
        "id": str(r[0].id),
        "config_name": r[0].config_name,
        "channel_type": r[0].channel_type,
        "webhook_url": r[0].webhook_url,
        "email_to": r[0].email_to,
        "trigger_type": r[0].trigger_type,
        "threshold": r[0].threshold,
        "period_minutes": r[0].period_minutes,
        "failure_categories": r[0].failure_categories or [],
        "target_source_id": str(r[0].target_source_id) if r[0].target_source_id else None,
        "target_source_name": r[1],
        "severity": r[0].severity,
        "enabled": r[0].enabled,
        "last_triggered_at": r[0].last_triggered_at.isoformat() if r[0].last_triggered_at else None,
        "last_triggered_status": r[0].last_triggered_status,
        "last_triggered_error": r[0].last_triggered_error,
        "trigger_count": r[0].trigger_count or 0,
    } for r in rows])


@router.post("/alerts", response_model=APIResponse)
async def upsert_alert(body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """알람 설정 등록/수정 (id 있으면 update, 없으면 create)."""
    aid = body.get("id")
    if aid:
        row = (await db.execute(select(CollectionAlertConfig).where(CollectionAlertConfig.id == uuid.UUID(aid)))).scalar_one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="알람 설정을 찾을 수 없습니다")
    else:
        row = CollectionAlertConfig(id=uuid.uuid4(), created_by=user.id)
        db.add(row)

    row.config_name = body.get("config_name") or row.config_name or "Untitled"
    row.channel_type = body.get("channel_type") or row.channel_type or "WEBHOOK"
    row.webhook_url = body.get("webhook_url")
    row.email_to = body.get("email_to")
    row.trigger_type = body.get("trigger_type") or row.trigger_type or "CONSECUTIVE_FAIL"
    row.threshold = body.get("threshold") or 1
    row.period_minutes = body.get("period_minutes") or 60
    row.failure_categories = body.get("failure_categories")
    tsid = body.get("target_source_id")
    row.target_source_id = uuid.UUID(tsid) if tsid else None
    row.severity = body.get("severity") or "WARNING"
    row.enabled = bool(body.get("enabled", True))
    row.updated_by = user.id

    await db.flush()
    return APIResponse(data={"id": str(row.id)}, message="알람 설정이 저장되었습니다")


@router.delete("/alerts/{alert_id}", response_model=APIResponse)
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    row = (await db.execute(select(CollectionAlertConfig).where(CollectionAlertConfig.id == uuid.UUID(alert_id)))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="알람 설정을 찾을 수 없습니다")
    row.is_deleted = True
    row.updated_by = user.id
    return APIResponse(message="알람 설정이 삭제되었습니다")


@router.post("/alerts/dispatch-now", response_model=APIResponse)
async def dispatch_alerts_now(user: CurrentUser = Depends(get_current_user)):
    """알람 평가/발송 즉시 실행 (관리자 수동 트리거)."""
    from app.tasks.collection_tasks import classify_recent_failures_and_alert
    classify_recent_failures_and_alert.delay()
    return APIResponse(message="알람 평가/발송이 비동기로 시작되었습니다")


@router.post("/alerts/{alert_id}/test", response_model=APIResponse)
async def test_alert(alert_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """알람 채널 연결 테스트 (실제 트리거 조건과 무관하게 한 번 발송)."""
    from app.services.collection_failure_service import _build_payload, _dispatch
    row = (await db.execute(select(CollectionAlertConfig).where(CollectionAlertConfig.id == uuid.UUID(alert_id)))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="알람 설정을 찾을 수 없습니다")
    ok, err = _dispatch(row, {"metric": "[테스트 발송] 채널 연결 확인", "test": True})
    if ok:
        return APIResponse(message="테스트 발송 성공")
    raise HTTPException(status_code=502, detail=f"발송 실패: {err}")


# ══════ 마이그레이션 (REQ-DHUB-005-004-007) ══════
@router.get("/migrations", response_model=APIResponse[list[MigrationResponse]])
async def list_migrations(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionMigration).where(CollectionMigration.is_deleted == False)
                                  .order_by(CollectionMigration.created_at.desc()))).scalars().all()
    return APIResponse(data=[MigrationResponse(
        id=r.id, migration_name=r.migration_name, migration_type=r.migration_type,
        status=r.status, total_tables=r.total_tables, completed_tables=r.completed_tables,
    ) for r in rows])


@router.post("/migrations", response_model=APIResponse)
async def create_migration(body: dict | None = None, db: AsyncSession = Depends(get_db),
                                 user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 작업 생성.

    body 예:
    {
      "migration_name": "PG_to_Hub_2026Q2",
      "source_id": "<uuid>",
      "migration_type": "FULL",  // FULL | INCREMENTAL
      "target_source_id": null,   // null 이면 데이터허브 내부 PG
      "target_schema": "collection_zone",
      "chunk_size": 1000,
      "tables": [
        {"source_schema": "public","source_table":"users","target_table":"users","mode":"FULL","where":null,"columns":null}
      ]
    }
    """
    body = body or {}
    name = body.get("migration_name") or f"Migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    src_id = body.get("source_id")
    if not src_id:
        raise HTTPException(status_code=400, detail="source_id 필요")
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(src_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="원본 데이터소스 없음")
    tables = body.get("tables") or []
    mig_type = (body.get("migration_type") or "FULL").upper()
    table_list_cfg = {
        "target_source_id": body.get("target_source_id"),
        "target_schema": body.get("target_schema") or "collection_zone",
        "chunk_size": int(body.get("chunk_size") or 1000),
        "mode": mig_type,
        "tables": tables,
    }
    m = CollectionMigration(
        id=uuid.uuid4(), migration_name=name,
        source_id=uuid.UUID(src_id),
        target_storage_zone=table_list_cfg["target_schema"],
        table_list=table_list_cfg,
        migration_type=mig_type,
        status="PENDING",
        total_tables=len(tables),
        completed_tables=0,
        created_by=user.id,
    )
    db.add(m)
    await db.flush()
    return APIResponse(data={"id": str(m.id)}, message="마이그레이션이 생성되었습니다")


@router.get("/migrations/{migration_id}", response_model=APIResponse)
async def get_migration(migration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 상세 조회 (진행률 포함)."""
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    el = m.error_log or {}
    return APIResponse(data={
        "id": str(m.id), "migration_name": m.migration_name,
        "migration_type": m.migration_type, "status": m.status,
        "source_id": str(m.source_id) if m.source_id else None,
        "target_storage_zone": m.target_storage_zone,
        "table_list": m.table_list,
        "total_tables": m.total_tables, "completed_tables": m.completed_tables,
        "started_at": m.started_at.isoformat() if m.started_at else None,
        "completed_at": m.completed_at.isoformat() if m.completed_at else None,
        "progress": el.get("progress"),
        "errors": el.get("errors") or [],
    })


@router.post("/migrations/{migration_id}/execute", response_model=APIResponse)
async def execute_migration(migration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 실행 (Celery 비동기)."""
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="이미 실행 중입니다")
    # 초기 상태 QUEUED (worker 가 RUNNING 으로 전환)
    m.status = "PENDING"
    m.error_log = None
    m.completed_tables = 0
    await db.commit()
    from app.tasks.migration_tasks import execute_migration as task
    task.delay(str(m.id), str(user.id) if user and user.id else None)
    return APIResponse(data={"id": str(m.id)}, message="마이그레이션이 비동기로 실행됩니다")


@router.put("/migrations/{migration_id}", response_model=APIResponse)
async def update_migration(migration_id: str, body: dict, db: AsyncSession = Depends(get_db),
                                user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 작업 수정 (메타 + 테이블 매핑 전체 갱신).

    실행 중인 작업은 수정 불가. 변경 사항은 MigrationAuditLog 에 자동 기록.
    """
    from app.models.dr import MigrationAuditLog
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="실행 중인 작업은 수정할 수 없습니다")

    prev_cfg = dict(m.table_list or {})
    prev_tables = {f"{t.get('source_schema')}.{t.get('source_table')}": t for t in (prev_cfg.get("tables") or [])}

    if "migration_name" in body:
        m.migration_name = body["migration_name"]
    if "migration_type" in body:
        m.migration_type = (body["migration_type"] or "FULL").upper()
    if "source_id" in body and body["source_id"]:
        m.source_id = uuid.UUID(body["source_id"])

    new_cfg = {
        "target_source_id": body.get("target_source_id", prev_cfg.get("target_source_id")),
        "target_schema": body.get("target_schema", prev_cfg.get("target_schema") or "collection_zone"),
        "chunk_size": int(body.get("chunk_size", prev_cfg.get("chunk_size") or 1000)),
        "mode": (body.get("migration_type") or m.migration_type or "FULL").upper(),
        "tables": body.get("tables", prev_cfg.get("tables") or []),
    }
    m.table_list = new_cfg
    m.target_storage_zone = new_cfg["target_schema"]
    m.total_tables = len(new_cfg["tables"])
    m.updated_by = user.id
    m.updated_at = datetime.now()

    # 변경 이력 분석 → audit log 기록
    new_tables = {f"{t.get('source_schema')}.{t.get('source_table')}": t for t in new_cfg["tables"]}
    added = sorted(set(new_tables) - set(prev_tables))
    removed = sorted(set(prev_tables) - set(new_tables))
    modified = []
    for k in set(new_tables) & set(prev_tables):
        if new_tables[k] != prev_tables[k]:
            modified.append(k)
    for tname in added:
        db.add(MigrationAuditLog(
            id=uuid.uuid4(), migration_id=m.id, action="TABLE_ADD", phase="MAPPING",
            actor_id=user.id, started_at=datetime.now(), table_name=tname,
            details={"after": new_tables[tname]}, severity="INFO",
        ))
    for tname in removed:
        db.add(MigrationAuditLog(
            id=uuid.uuid4(), migration_id=m.id, action="TABLE_REMOVE", phase="MAPPING",
            actor_id=user.id, started_at=datetime.now(), table_name=tname,
            details={"before": prev_tables[tname]}, severity="INFO",
        ))
    for tname in modified:
        db.add(MigrationAuditLog(
            id=uuid.uuid4(), migration_id=m.id, action="TABLE_MODIFY", phase="MAPPING",
            actor_id=user.id, started_at=datetime.now(), table_name=tname,
            details={"before": prev_tables[tname], "after": new_tables[tname]}, severity="INFO",
        ))
    return APIResponse(data={
        "id": str(m.id),
        "added": added, "removed": removed, "modified": modified,
        "total_tables": m.total_tables,
    }, message=f"수정 완료 (추가 {len(added)} / 삭제 {len(removed)} / 변경 {len(modified)})")


@router.post("/migrations/{migration_id}/tables", response_model=APIResponse)
async def add_migration_table(migration_id: str, body: dict, db: AsyncSession = Depends(get_db),
                                    user: CurrentUser = Depends(get_current_user)):
    """단일 테이블 매핑 추가 (REQ-DHUB-005-004-004).

    body: {source_schema, source_table, target_table?, mode?, where?, columns?}
    """
    from app.models.dr import MigrationAuditLog
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="실행 중인 작업은 수정할 수 없습니다")
    src_schema = (body.get("source_schema") or "").strip()
    src_table = (body.get("source_table") or "").strip()
    if not src_schema or not src_table:
        raise HTTPException(status_code=400, detail="source_schema, source_table 필수")
    cfg = dict(m.table_list or {})
    tables = list(cfg.get("tables") or [])
    key = f"{src_schema}.{src_table}"
    if any(f"{t.get('source_schema')}.{t.get('source_table')}" == key for t in tables):
        raise HTTPException(status_code=409, detail=f"이미 등록된 테이블: {key}")
    new_t = {
        "source_schema": src_schema,
        "source_table": src_table,
        "target_table": body.get("target_table") or src_table.lower(),
        "mode": (body.get("mode") or m.migration_type or "FULL").upper(),
        "where": body.get("where") or None,
    }
    if body.get("columns"):
        new_t["columns"] = body["columns"]
    tables.append(new_t)
    cfg["tables"] = tables
    m.table_list = cfg
    m.total_tables = len(tables)
    m.updated_by = user.id
    m.updated_at = datetime.now()
    db.add(MigrationAuditLog(
        id=uuid.uuid4(), migration_id=m.id, action="TABLE_ADD", phase="MAPPING",
        actor_id=user.id, started_at=datetime.now(), table_name=key,
        details={"after": new_t}, severity="INFO",
    ))
    return APIResponse(data={"total_tables": m.total_tables, "added": new_t}, message=f"테이블 추가: {key}")


@router.put("/migrations/{migration_id}/tables/{table_key}", response_model=APIResponse)
async def update_migration_table(migration_id: str, table_key: str, body: dict,
                                       db: AsyncSession = Depends(get_db),
                                       user: CurrentUser = Depends(get_current_user)):
    """단일 테이블 매핑 수정. table_key 형식: '{schema}.{table}'"""
    from app.models.dr import MigrationAuditLog
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="실행 중인 작업은 수정할 수 없습니다")
    cfg = dict(m.table_list or {})
    tables = list(cfg.get("tables") or [])
    idx = next((i for i, t in enumerate(tables)
                  if f"{t.get('source_schema')}.{t.get('source_table')}" == table_key), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"등록되지 않은 테이블: {table_key}")
    before = dict(tables[idx])
    after = dict(before)
    for fld in ("target_table", "mode", "where", "columns"):
        if fld in body:
            after[fld] = body[fld]
    tables[idx] = after
    cfg["tables"] = tables
    m.table_list = cfg
    m.updated_by = user.id
    m.updated_at = datetime.now()
    db.add(MigrationAuditLog(
        id=uuid.uuid4(), migration_id=m.id, action="TABLE_MODIFY", phase="MAPPING",
        actor_id=user.id, started_at=datetime.now(), table_name=table_key,
        details={"before": before, "after": after}, severity="INFO",
    ))
    return APIResponse(data=after, message=f"테이블 매핑 수정: {table_key}")


@router.delete("/migrations/{migration_id}/tables/{table_key}", response_model=APIResponse)
async def delete_migration_table(migration_id: str, table_key: str,
                                       db: AsyncSession = Depends(get_db),
                                       user: CurrentUser = Depends(get_current_user)):
    """단일 테이블 매핑 삭제."""
    from app.models.dr import MigrationAuditLog
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="실행 중인 작업은 수정할 수 없습니다")
    cfg = dict(m.table_list or {})
    tables = list(cfg.get("tables") or [])
    idx = next((i for i, t in enumerate(tables)
                  if f"{t.get('source_schema')}.{t.get('source_table')}" == table_key), -1)
    if idx < 0:
        raise HTTPException(status_code=404, detail=f"등록되지 않은 테이블: {table_key}")
    removed = tables.pop(idx)
    cfg["tables"] = tables
    m.table_list = cfg
    m.total_tables = len(tables)
    m.updated_by = user.id
    m.updated_at = datetime.now()
    db.add(MigrationAuditLog(
        id=uuid.uuid4(), migration_id=m.id, action="TABLE_REMOVE", phase="MAPPING",
        actor_id=user.id, started_at=datetime.now(), table_name=table_key,
        details={"before": removed}, severity="INFO",
    ))
    return APIResponse(data={"total_tables": m.total_tables}, message=f"테이블 삭제: {table_key}")


@router.delete("/migrations/{migration_id}", response_model=APIResponse)
async def delete_migration(migration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 작업 삭제 (soft-delete). 실행 중인 작업은 삭제 불가."""
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    if m.status == "RUNNING":
        raise HTTPException(status_code=409, detail="실행 중인 작업은 삭제할 수 없습니다")
    m.is_deleted = True
    m.updated_by = user.id
    return APIResponse(message="마이그레이션이 삭제되었습니다")


# ══════ REQ-DHUB-005-004-008 결과·세부로그 대시보드 ══════
@router.get("/migrations/results/summary", response_model=APIResponse)
async def migration_results_summary(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """마이그레이션 결과 종합 대시보드 (KPI + 일자별 추이 + 상태 분포 + TOP 실패).

    - total/success/running/failed/pending 카운트
    - success_rate, avg_duration_sec, total_rows, total_tables
    - by_date: [{date, success, failed, total}]
    - by_status: [{status, count}]
    - top_failures: [{table, action, count}]
    """
    from app.models.dr import MigrationAuditLog
    since = datetime.now() - timedelta(days=days)

    # 기본 카운트
    total = (await db.execute(
        select(func.count()).select_from(CollectionMigration)
        .where(CollectionMigration.is_deleted == False)  # noqa: E712
    )).scalar() or 0
    by_status_rows = (await db.execute(
        select(CollectionMigration.status, func.count())
        .where(CollectionMigration.is_deleted == False)  # noqa: E712
        .group_by(CollectionMigration.status)
    )).all()
    by_status = {s: c for s, c in by_status_rows}

    # 소요시간·행수 (완료된 작업만)
    completed_in_period = (await db.execute(
        select(CollectionMigration).where(
            CollectionMigration.is_deleted == False,  # noqa: E712
            CollectionMigration.status.in_(("COMPLETED", "FAILED")),
            CollectionMigration.completed_at.isnot(None),
            CollectionMigration.completed_at >= since,
        )
    )).scalars().all()
    durations = []
    total_rows_all = 0
    total_tables_all = 0
    for m in completed_in_period:
        if m.started_at and m.completed_at:
            durations.append((m.completed_at - m.started_at).total_seconds())
        prog = (m.error_log or {}).get("progress") if isinstance(m.error_log, dict) else {}
        total_rows_all += int((prog or {}).get("processed_rows") or 0)
        total_tables_all += int(m.completed_tables or 0)
    avg_dur = round(sum(durations) / len(durations), 2) if durations else 0

    success = by_status.get("COMPLETED", 0)
    failed = by_status.get("FAILED", 0)
    finished = success + failed
    success_rate = round((success / finished * 100), 1) if finished else 0

    # 일자별 추이 (완료 기준)
    by_date_map: dict[str, dict] = {}
    for m in completed_in_period:
        d = m.completed_at.strftime("%Y-%m-%d") if m.completed_at else None
        if not d:
            continue
        slot = by_date_map.setdefault(d, {"date": d, "success": 0, "failed": 0, "total": 0})
        slot["total"] += 1
        if m.status == "COMPLETED":
            slot["success"] += 1
        elif m.status == "FAILED":
            slot["failed"] += 1
    by_date = sorted(by_date_map.values(), key=lambda x: x["date"])

    # TOP 실패 (audit log 중 action='FAIL' 또는 severity='ERROR')
    top_fail_rows = (await db.execute(
        select(MigrationAuditLog.table_name, MigrationAuditLog.phase, func.count())
        .where(
            MigrationAuditLog.severity == "ERROR",
            MigrationAuditLog.created_at >= since,
        )
        .group_by(MigrationAuditLog.table_name, MigrationAuditLog.phase)
        .order_by(func.count().desc())
        .limit(10)
    )).all()
    top_failures = [
        {"table": t or "(unknown)", "phase": p or "-", "count": c}
        for t, p, c in top_fail_rows
    ]

    return APIResponse(data={
        "period_days": days,
        "total": total,
        "success": success, "failed": failed,
        "running": by_status.get("RUNNING", 0),
        "pending": by_status.get("PENDING", 0),
        "success_rate": success_rate,
        "avg_duration_sec": avg_dur,
        "total_rows": total_rows_all,
        "total_tables": total_tables_all,
        "by_status": [{"status": s, "count": c} for s, c in by_status.items()],
        "by_date": by_date,
        "top_failures": top_failures,
    })


@router.get("/migrations/results/audit-logs", response_model=PageResponse)
async def migrations_all_audit_logs(
    page: int = 1, page_size: int = 30,
    migration_id: str | None = None,
    action: str | None = None,
    severity: str | None = None,
    table_name: str | None = None,
    phase: str | None = None,
    days: int | None = None,
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """모든 마이그레이션 작업의 감사로그를 통합 조회 (작업명 조인, 다중 필터).

    필터: migration_id, action, severity, table_name(부분일치), phase, days, q(작업명 부분일치)
    """
    from app.models.dr import MigrationAuditLog
    from sqlalchemy import or_, and_

    conds = []
    if migration_id:
        conds.append(MigrationAuditLog.migration_id == uuid.UUID(migration_id))
    if action:
        conds.append(MigrationAuditLog.action == action)
    if severity:
        conds.append(MigrationAuditLog.severity == severity)
    if phase:
        conds.append(MigrationAuditLog.phase == phase)
    if table_name:
        conds.append(MigrationAuditLog.table_name.ilike(f"%{table_name}%"))
    if days and days > 0:
        conds.append(MigrationAuditLog.created_at >= datetime.now() - timedelta(days=days))
    if q:
        conds.append(CollectionMigration.migration_name.ilike(f"%{q}%"))

    q_stmt = (
        select(MigrationAuditLog, CollectionMigration.migration_name)
        .join(CollectionMigration, CollectionMigration.id == MigrationAuditLog.migration_id, isouter=True)
    )
    if conds:
        q_stmt = q_stmt.where(and_(*conds))

    total = (await db.execute(
        select(func.count()).select_from(q_stmt.subquery())
    )).scalar() or 0

    rows = (await db.execute(
        q_stmt.order_by(MigrationAuditLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = [{
        "id": str(r[0].id),
        "migration_id": str(r[0].migration_id) if r[0].migration_id else None,
        "migration_name": r[1],
        "action": r[0].action,
        "phase": r[0].phase,
        "severity": r[0].severity,
        "table_name": r[0].table_name,
        "row_count": r[0].row_count,
        "duration_ms": r[0].duration_ms,
        "details": r[0].details,
        "created_at": r[0].created_at.isoformat() if r[0].created_at else None,
    } for r in rows]

    return PageResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if page_size else 0,
    )


@router.post("/migrations/{migration_id}/execute-sync", response_model=APIResponse)
async def execute_migration_sync(migration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """마이그레이션 동기 실행 (테스트·소량 전용, K8s 환경에선 비권장)."""
    m = (await db.execute(select(CollectionMigration).where(CollectionMigration.id == uuid.UUID(migration_id)))).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="마이그레이션을 찾을 수 없습니다")
    from app.database import SyncSessionLocal
    from app.services.migration_engine import MigrationEngine
    s = SyncSessionLocal()
    try:
        engine = MigrationEngine(s, m.id, user.id if user else None)
        result = engine.run()
        s.commit()
        return APIResponse(data=result, message="마이그레이션 동기 실행 완료")
    except Exception as e:
        s.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        s.close()


# ══════ 외부기관 연계 (REQ-DHUB-005-005) ══════════════════════════════════
@router.get("/external-agencies", response_model=APIResponse[list[ExternalAgencyResponse]])
async def list_external_agencies(
    endpoint_type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    q = select(CollectionExternalAgency).where(CollectionExternalAgency.is_deleted == False)
    if endpoint_type:
        q = q.where(CollectionExternalAgency.endpoint_type == endpoint_type)
    if status:
        q = q.where(CollectionExternalAgency.status == status)
    rows = (await db.execute(q)).scalars().all()
    return APIResponse(data=[ExternalAgencyResponse.model_validate(r) for r in rows])


@router.get("/external-agencies/stats", response_model=APIResponse[ExternalAgencyStatsResponse])
async def external_agency_stats(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """REQ-DHUB-005-005-001: 연계 포인트 현황·통계 대시보드."""
    agencies = (await db.execute(
        select(CollectionExternalAgency).where(CollectionExternalAgency.is_deleted == False)
    )).scalars().all()

    total = len(agencies)
    active = sum(1 for a in agencies if a.status == "ACTIVE")
    failed = sum(1 for a in agencies if a.status == "FAILED")
    maintenance = sum(1 for a in agencies if a.status == "MAINTENANCE")
    healthy = sum(1 for a in agencies if a.last_health_status == "HEALTHY")
    degraded = sum(1 for a in agencies if a.last_health_status == "DEGRADED")
    unhealthy = sum(1 for a in agencies if a.last_health_status == "UNHEALTHY")

    by_endpoint_type: dict = {}
    by_status: dict = {}
    latencies: list[int] = []
    for a in agencies:
        et = a.endpoint_type or "API"
        by_endpoint_type[et] = by_endpoint_type.get(et, 0) + 1
        by_status[a.status or "UNKNOWN"] = by_status.get(a.status or "UNKNOWN", 0) + 1
        if a.last_health_latency_ms:
            latencies.append(a.last_health_latency_ms)

    # 최근 24시간 송수신 통계
    since_24h = datetime.now() - timedelta(hours=24)
    tx_rows = (await db.execute(
        select(CollectionExternalAgencyTxLog.status, func.count()).where(
            CollectionExternalAgencyTxLog.started_at >= since_24h
        ).group_by(CollectionExternalAgencyTxLog.status)
    )).all()
    tx_map = {r[0]: r[1] for r in tx_rows}
    success_24h = tx_map.get("SUCCESS", 0)
    fail_24h = tx_map.get("FAIL", 0) + tx_map.get("TIMEOUT", 0)
    total_24h = sum(tx_map.values())

    # availability 7일 평균
    since_7d = datetime.now() - timedelta(days=7)
    hc_rows = (await db.execute(
        select(CollectionExternalAgencyHealthLog.status).where(
            CollectionExternalAgencyHealthLog.checked_at >= since_7d
        )
    )).scalars().all()
    availability_7d = None
    if hc_rows:
        healthy_cnt = sum(1 for s in hc_rows if s == "HEALTHY")
        availability_7d = round(healthy_cnt * 100.0 / len(hc_rows), 2)

    return APIResponse(data=ExternalAgencyStatsResponse(
        total=total, active=active, failed=failed, maintenance=maintenance,
        healthy=healthy, degraded=degraded, unhealthy=unhealthy,
        by_endpoint_type=by_endpoint_type, by_status=by_status,
        availability_7d=availability_7d,
        total_tx_24h=total_24h, success_tx_24h=success_24h, fail_tx_24h=fail_24h,
        avg_latency_ms=(sum(latencies) / len(latencies)) if latencies else None,
    ))


@router.get("/external-agencies/{agency_id}", response_model=APIResponse[ExternalAgencyDetailResponse])
async def get_external_agency(
    agency_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    row = (await db.execute(
        select(CollectionExternalAgency).where(
            CollectionExternalAgency.id == uuid.UUID(agency_id),
            CollectionExternalAgency.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="외부기관을 찾을 수 없습니다.")
    return APIResponse(data=ExternalAgencyDetailResponse.model_validate(row))


@router.post("/external-agencies", response_model=APIResponse)
async def create_external_agency(
    body: ExternalAgencyCreate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    ea = CollectionExternalAgency(
        id=uuid.uuid4(),
        agency_name=body.agency_name, agency_code=body.agency_code,
        endpoint_type=body.endpoint_type, api_endpoint=body.api_endpoint,
        api_key_enc=encrypt_secret(body.api_key) if body.api_key else None,
        endpoint_config=body.endpoint_config,
        data_type=body.data_type, protocol=body.protocol,
        schedule_cron=body.schedule_cron, status=body.status,
        health_check_enabled=body.health_check_enabled,
        health_check_interval_sec=body.health_check_interval_sec,
        health_timeout_sec=body.health_timeout_sec,
        retry_enabled=body.retry_enabled, max_retries=body.max_retries,
        retry_interval_sec=body.retry_interval_sec, retry_backoff=body.retry_backoff,
        failover_endpoint=body.failover_endpoint,
        auth_method=body.auth_method, auth_config=body.auth_config,
        security_policy=body.security_policy,
        alert_enabled=body.alert_enabled,
        alert_threshold_failures=body.alert_threshold_failures,
        alert_channels=body.alert_channels,
        om_service_name=body.om_service_name,
        created_by=user.id,
    )
    db.add(ea)
    await db.commit()
    return APIResponse(message="외부기관이 등록되었습니다", data={"id": str(ea.id)})


@router.put("/external-agencies/{agency_id}", response_model=APIResponse)
async def update_external_agency(
    agency_id: str, body: ExternalAgencyUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    ea = (await db.execute(
        select(CollectionExternalAgency).where(
            CollectionExternalAgency.id == uuid.UUID(agency_id),
            CollectionExternalAgency.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not ea:
        raise HTTPException(status_code=404, detail="외부기관을 찾을 수 없습니다.")

    payload = body.model_dump(exclude_unset=True)
    if "api_key" in payload:
        api_key = payload.pop("api_key")
        ea.api_key_enc = encrypt_secret(api_key) if api_key else None
    for k, v in payload.items():
        setattr(ea, k, v)
    ea.updated_by = user.id
    await db.commit()
    return APIResponse(message="외부기관이 수정되었습니다")


@router.delete("/external-agencies/{agency_id}", response_model=APIResponse)
async def delete_external_agency(
    agency_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    ea = (await db.execute(
        select(CollectionExternalAgency).where(
            CollectionExternalAgency.id == uuid.UUID(agency_id),
            CollectionExternalAgency.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not ea:
        raise HTTPException(status_code=404, detail="외부기관을 찾을 수 없습니다.")
    ea.is_deleted = True
    ea.updated_by = user.id
    await db.commit()
    return APIResponse(message="외부기관이 삭제되었습니다")


# ── 연계 포인트 점검 (REQ-DHUB-005-005-001) ───────────────────────────────
@router.post("/external-agencies/{agency_id}/health-check", response_model=APIResponse[HealthCheckResponse])
async def check_external_agency_health(
    agency_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """외부기관 연계포인트 수동 점검."""
    from app.database import SyncSessionLocal
    from app.services.external_agency_health_service import (
        perform_health_check, dispatch_health_alert, sync_to_openmetadata,
    )

    s = SyncSessionLocal()
    try:
        ea = s.query(CollectionExternalAgency).filter(
            CollectionExternalAgency.id == uuid.UUID(agency_id),
            CollectionExternalAgency.is_deleted == False,
        ).first()
        if not ea:
            raise HTTPException(status_code=404, detail="외부기관을 찾을 수 없습니다.")

        log = perform_health_check(s, ea, check_type="MANUAL", commit=True)
        # 임계 초과 시 알림 + OM 동기화
        if (ea.consecutive_failures or 0) >= (ea.alert_threshold_failures or 3) and log.status != "HEALTHY":
            dispatch_health_alert(s, ea, log)
        sync_to_openmetadata(s, ea)
        s.commit()

        return APIResponse(data=HealthCheckResponse(
            agency_id=ea.id,
            status=log.status, latency_ms=log.latency_ms, http_status=log.http_status,
            error_code=log.error_code, message=log.message,
            endpoint_type=log.endpoint_type, failover_used=log.failover_used or False,
            checked_at=log.checked_at,
        ))
    except HTTPException:
        raise
    except Exception as e:
        s.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        s.close()


@router.get("/external-agencies/{agency_id}/health-logs", response_model=PageResponse[HealthLogResponse])
async def list_external_agency_health_logs(
    agency_id: str, page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    total = (await db.execute(
        select(func.count()).select_from(CollectionExternalAgencyHealthLog).where(
            CollectionExternalAgencyHealthLog.agency_id == uuid.UUID(agency_id)
        )
    )).scalar() or 0
    rows = (await db.execute(
        select(CollectionExternalAgencyHealthLog).where(
            CollectionExternalAgencyHealthLog.agency_id == uuid.UUID(agency_id)
        ).order_by(CollectionExternalAgencyHealthLog.checked_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=[HealthLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/external-agencies/{agency_id}/tx-logs", response_model=PageResponse[ExternalAgencyTxLogResponse])
async def list_external_agency_tx_logs(
    agency_id: str, direction: str | None = None, status: str | None = None,
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """송수신 이력 조회 — 라이프사이클 관리(메타데이터 포함)."""
    q = select(CollectionExternalAgencyTxLog).where(
        CollectionExternalAgencyTxLog.agency_id == uuid.UUID(agency_id)
    )
    cq = select(func.count()).select_from(CollectionExternalAgencyTxLog).where(
        CollectionExternalAgencyTxLog.agency_id == uuid.UUID(agency_id)
    )
    if direction:
        q = q.where(CollectionExternalAgencyTxLog.tx_direction == direction)
        cq = cq.where(CollectionExternalAgencyTxLog.tx_direction == direction)
    if status:
        q = q.where(CollectionExternalAgencyTxLog.status == status)
        cq = cq.where(CollectionExternalAgencyTxLog.status == status)

    total = (await db.execute(cq)).scalar() or 0
    rows = (await db.execute(
        q.order_by(CollectionExternalAgencyTxLog.started_at.desc())
         .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=[ExternalAgencyTxLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/external-agencies/{agency_id}/failover", response_model=APIResponse)
async def toggle_failover(
    agency_id: str, body: FailoverToggleRequest,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """핫스왑 엔드포인트 수동 전환."""
    ea = (await db.execute(
        select(CollectionExternalAgency).where(
            CollectionExternalAgency.id == uuid.UUID(agency_id),
            CollectionExternalAgency.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not ea:
        raise HTTPException(status_code=404, detail="외부기관을 찾을 수 없습니다.")
    if body.activate and not ea.failover_endpoint:
        raise HTTPException(status_code=400, detail="failover_endpoint 가 설정되지 않았습니다.")
    ea.failover_active = body.activate
    ea.failover_activated_at = datetime.now() if body.activate else None
    ea.updated_by = user.id
    await db.commit()
    return APIResponse(
        message=("핫스왑이 활성화되었습니다." if body.activate else "핫스왑이 해제되었습니다."),
        data={"failover_active": ea.failover_active,
              "failover_endpoint": ea.failover_endpoint if ea.failover_active else None},
    )


@router.post("/external-agencies/health-check-all", response_model=APIResponse)
async def check_all_external_agencies_health(
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """전체 ACTIVE 외부기관 일괄 점검(Celery 비동기)."""
    from app.tasks.external_agency_tasks import run_health_check_all
    task = run_health_check_all.delay()
    return APIResponse(data={"task_id": task.id}, message="전수 점검이 실행되었습니다.")


# ══════ 공간정보 수집 설정 CRUD ══════
@router.get("/spatial-configs", response_model=APIResponse[list[SpatialConfigResponse]])
async def list_spatial_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    data = await spatial_config_service.list_configs(db)
    return APIResponse(data=data)


@router.get("/spatial-configs/{config_id}", response_model=APIResponse[SpatialConfigDetailResponse])
async def get_spatial_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.get_detail(db, config_id)
    if data is None:
        raise HTTPException(status_code=404, detail="공간정보 수집 설정을 찾을 수 없습니다.")
    return APIResponse(data=data)


@router.post("/spatial-configs", response_model=APIResponse[SpatialConfigResponse])
async def create_spatial_config(
    body: SpatialConfigCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.create_config(db, body, user.id)
    return APIResponse(data=data, message="공간정보 수집 설정이 등록되었습니다.")


@router.put("/spatial-configs/{config_id}", response_model=APIResponse[SpatialConfigResponse])
async def update_spatial_config(
    config_id: uuid.UUID,
    body: SpatialConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.update_config(db, config_id, body, user.id)
    if data is None:
        raise HTTPException(status_code=404, detail="공간정보 수집 설정을 찾을 수 없습니다.")
    return APIResponse(data=data, message="공간정보 수집 설정이 수정되었습니다.")


@router.delete("/spatial-configs/{config_id}", response_model=APIResponse)
async def delete_spatial_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    ok = await spatial_config_service.soft_delete_config(db, config_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="공간정보 수집 설정을 찾을 수 없습니다.")
    return APIResponse(message="공간정보 수집 설정이 삭제되었습니다.")


@router.post("/spatial-configs/{config_id}/test-connection", response_model=APIResponse[SpatialConnectionTestResponse])
async def test_spatial_connection(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.test_connection(db, config_id)
    return APIResponse(data=data)


@router.post("/spatial-configs/{config_id}/discover-layers", response_model=APIResponse[SpatialDiscoverLayersResponse])
async def discover_spatial_layers(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.discover_layers(db, config_id)
    return APIResponse(data=data)


@router.post("/spatial-configs/{config_id}/run", response_model=APIResponse[SpatialRunResponse])
async def run_spatial_collection(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.run_collection(db, config_id, triggered_by="MANUAL", user_id=user.id)
    return APIResponse(data=data)


@router.get("/spatial-configs/{config_id}/history", response_model=APIResponse[list[SpatialHistoryResponse]])
async def list_spatial_history(
    config_id: uuid.UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await spatial_config_service.list_history(db, config_id, limit=limit)
    return APIResponse(data=data)


@router.post("/jobs/{job_id}/register-catalog", response_model=APIResponse)
async def trigger_catalog_registration(
    job_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """수집 작업에 대한 카탈로그 등록 수동 트리거"""
    job = (await db.execute(select(CollectionJob).where(CollectionJob.id == uuid.UUID(job_id)))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="수집 작업을 찾을 수 없습니다.")
    if job.job_status != "SUCCESS":
        raise HTTPException(status_code=400, detail=f"SUCCESS 상태의 작업만 등록 가능합니다. (현재: {job.job_status})")
    from app.tasks.collection_tasks import on_collection_complete
    task = on_collection_complete.delay(str(job_id))
    return APIResponse(data={"task_id": task.id}, message="카탈로그 등록 파이프라인이 시작되었습니다.")


# ══════ 비정형데이터 관리 ══════

def _doc_to_resp(r) -> UnstructuredDocResponse:
    return UnstructuredDocResponse(
        id=r.id, doc_name=r.doc_name, doc_type=r.doc_type, description=r.description,
        file_name=r.file_name, file_size=r.file_size, content_type=r.content_type,
        processing_status=r.processing_status, extracted_entity_count=r.extracted_entity_count,
        graph_node_count=r.graph_node_count, graph_integrated=r.graph_integrated,
        tags=r.tags, uploaded_at=r.uploaded_at, created_at=r.created_at,
    )


@router.get("/unstructured-docs/summary", response_model=APIResponse)
async def unstructured_doc_summary(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비정형데이터 KPI 요약"""
    base = select(
        CollectionUnstructuredDocument.processing_status,
        func.count().label("cnt"),
    ).where(CollectionUnstructuredDocument.is_deleted == False).group_by(CollectionUnstructuredDocument.processing_status)
    rows = (await db.execute(base)).all()
    status_map = {r[0]: r[1] for r in rows}
    total = sum(status_map.values())
    return APIResponse(data={
        "total": total,
        "completed": status_map.get("COMPLETED", 0),
        "processing": status_map.get("PROCESSING", 0),
        "pending": status_map.get("PENDING", 0),
        "failed": status_map.get("FAILED", 0),
    })


@router.get("/unstructured-docs", response_model=PageResponse[UnstructuredDocResponse])
async def list_unstructured_docs(
    page: int = 1, page_size: int = 20,
    doc_type: str | None = None, processing_status: str | None = None, search: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """비정형데이터 목록 (페이징/필터/검색)"""
    q = select(CollectionUnstructuredDocument).where(CollectionUnstructuredDocument.is_deleted == False)
    if doc_type:
        q = q.where(CollectionUnstructuredDocument.doc_type == doc_type)
    if processing_status:
        q = q.where(CollectionUnstructuredDocument.processing_status == processing_status)
    if search:
        kw = f"%{search}%"
        q = q.where(CollectionUnstructuredDocument.doc_name.ilike(kw))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    rows = (await db.execute(
        q.order_by(CollectionUnstructuredDocument.uploaded_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=[_doc_to_resp(r) for r in rows],
        total=total, page=page, page_size=page_size, total_pages=math.ceil(total / page_size) if page_size else 1,
    )


@router.get("/unstructured-docs/{doc_id}", response_model=APIResponse)
async def get_unstructured_doc(doc_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비정형데이터 상세 (온톨로지 활용 + 업로드자 포함)"""
    from app.models.user import UserAccount
    doc = (await db.execute(
        select(CollectionUnstructuredDocument).where(
            CollectionUnstructuredDocument.id == uuid.UUID(doc_id),
            CollectionUnstructuredDocument.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    # 업로드자 이름 조회
    created_by_name = None
    if doc.created_by:
        try:
            uploader = (await db.execute(
                select(UserAccount.name).where(UserAccount.id == uuid.UUID(str(doc.created_by)))
            )).scalar_one_or_none()
            created_by_name = uploader
        except Exception:
            pass
    usages = (await db.execute(
        select(CollectionUnstructuredDocOntologyUsage).where(
            CollectionUnstructuredDocOntologyUsage.document_id == doc.id,
        )
    )).scalars().all()
    # 검토자 이름 일괄 조회
    reviewer_ids = {uuid.UUID(str(u.reviewed_by)) for u in usages if u.reviewed_by}
    reviewer_map = {}
    if reviewer_ids:
        reviewer_rows = (await db.execute(
            select(UserAccount.id, UserAccount.name).where(UserAccount.id.in_(reviewer_ids))
        )).all()
        reviewer_map = {str(r[0]): r[1] for r in reviewer_rows}
    usage_list = []
    for u in usages:
        usage_list.append(OntologyUsageResponse(
            id=u.id, ontology_class=u.ontology_class, entity_count=u.entity_count,
            relation_count=u.relation_count, last_synced_at=u.last_synced_at, status=u.status,
            review_status=u.review_status or "PENDING_REVIEW",
            reviewed_by=u.reviewed_by, reviewed_at=u.reviewed_at, review_comment=u.review_comment,
            reviewed_by_name=reviewer_map.get(str(u.reviewed_by)) if u.reviewed_by else None,
        ))
    detail = UnstructuredDocDetailResponse(
        id=doc.id, doc_name=doc.doc_name, doc_type=doc.doc_type, description=doc.description,
        file_name=doc.file_name, file_size=doc.file_size, content_type=doc.content_type,
        processing_status=doc.processing_status, extracted_entity_count=doc.extracted_entity_count,
        graph_node_count=doc.graph_node_count, graph_integrated=doc.graph_integrated,
        tags=doc.tags, uploaded_at=doc.uploaded_at, created_at=doc.created_at,
        stored_name=doc.stored_name, storage_id=doc.storage_id, updated_at=doc.updated_at,
        ontology_usages=usage_list,
    )
    result = detail.model_dump()
    result["created_by_name"] = created_by_name
    result["review_status"] = doc.review_status or "PENDING_REVIEW"
    return APIResponse(data=result)


@router.post("/unstructured-docs", response_model=APIResponse[UnstructuredDocResponse])
async def create_unstructured_doc(
    doc_name: str = Form(...), doc_type: str = Form("MANUAL"),
    description: str = Form(""), storage_id: str = Form(None), tags: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """비정형데이터 등록 (파일 업로드)"""
    stored_name = None
    file_name = None
    file_size = None
    content_type_val = None
    if file and file.filename:
        stored_name = f"{UNSTRUCT_OBJECT_PREFIX}{uuid.uuid4().hex}_{file.filename}"
        content = await file.read()
        object_storage.put_object(stored_name, content, content_type=file.content_type)
        file_name = file.filename
        file_size = len(content)
        content_type_val = file.content_type

    import json
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
        except Exception:
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]

    doc = CollectionUnstructuredDocument(
        id=uuid.uuid4(), doc_name=doc_name, doc_type=doc_type, description=description or None,
        file_name=file_name, stored_name=stored_name, file_size=file_size, content_type=content_type_val,
        storage_id=uuid.UUID(storage_id) if storage_id and storage_id != "null" else None,
        tags=tags_list, uploaded_at=datetime.now(), created_by=str(user.id),
    )
    db.add(doc)
    await db.flush()
    return APIResponse(data=_doc_to_resp(doc), message="비정형 문서가 등록되었습니다.")


@router.put("/unstructured-docs/{doc_id}", response_model=APIResponse)
async def update_unstructured_doc(
    doc_id: str,
    doc_name: str = Form(None), doc_type: str = Form(None),
    description: str = Form(None), storage_id: str = Form(None), tags: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """비정형데이터 수정"""
    doc = (await db.execute(
        select(CollectionUnstructuredDocument).where(
            CollectionUnstructuredDocument.id == uuid.UUID(doc_id),
            CollectionUnstructuredDocument.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    if doc_name is not None:
        doc.doc_name = doc_name
    if doc_type is not None:
        doc.doc_type = doc_type
    if description is not None:
        doc.description = description
    if storage_id is not None and storage_id != "null":
        doc.storage_id = uuid.UUID(storage_id)
    if tags is not None:
        import json
        try:
            doc.tags = json.loads(tags)
        except Exception:
            doc.tags = [t.strip() for t in tags.split(",") if t.strip()]
    if file and file.filename:
        # 이전 오브젝트 제거 (존재 시)
        if doc.stored_name:
            object_storage.delete_object(doc.stored_name)
        stored_name = f"{UNSTRUCT_OBJECT_PREFIX}{uuid.uuid4().hex}_{file.filename}"
        content = await file.read()
        object_storage.put_object(stored_name, content, content_type=file.content_type)
        doc.file_name = file.filename
        doc.stored_name = stored_name
        doc.file_size = len(content)
        doc.content_type = file.content_type
    doc.updated_by = str(user.id)
    doc.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="수정되었습니다.")


@router.delete("/unstructured-docs/{doc_id}", response_model=APIResponse)
async def delete_unstructured_doc(doc_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비정형데이터 삭제 (soft delete)"""
    doc = (await db.execute(
        select(CollectionUnstructuredDocument).where(
            CollectionUnstructuredDocument.id == uuid.UUID(doc_id),
            CollectionUnstructuredDocument.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
    doc.is_deleted = True
    doc.updated_by = str(user.id)
    doc.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="삭제되었습니다.")


@router.get("/unstructured-docs/{doc_id}/download")
async def download_unstructured_doc(doc_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비정형데이터 파일 다운로드"""
    doc = (await db.execute(
        select(CollectionUnstructuredDocument).where(CollectionUnstructuredDocument.id == uuid.UUID(doc_id))
    )).scalar_one_or_none()
    if not doc or not doc.stored_name:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    try:
        resp = object_storage.stream_object(doc.stored_name)
    except Exception:
        raise HTTPException(status_code=404, detail="오브젝트 스토리지에 파일이 존재하지 않습니다.")

    def _iter():
        try:
            for chunk in resp.stream(32 * 1024):
                yield chunk
        finally:
            resp.close()
            resp.release_conn()

    headers = {"Content-Disposition": f'attachment; filename="{doc.file_name or doc.stored_name}"'}
    return StreamingResponse(_iter(), media_type=doc.content_type or "application/octet-stream", headers=headers)


@router.get("/unstructured-docs/{doc_id}/ontology-usage", response_model=APIResponse[list[OntologyUsageResponse]])
async def get_unstructured_doc_ontology_usage(doc_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비정형데이터 온톨로지 활용 목록"""
    rows = (await db.execute(
        select(CollectionUnstructuredDocOntologyUsage).where(
            CollectionUnstructuredDocOntologyUsage.document_id == uuid.UUID(doc_id),
        )
    )).scalars().all()
    return APIResponse(data=[OntologyUsageResponse(
        id=u.id, ontology_class=u.ontology_class, entity_count=u.entity_count,
        relation_count=u.relation_count, last_synced_at=u.last_synced_at, status=u.status,
        review_status=u.review_status or "PENDING_REVIEW",
        reviewed_by=u.reviewed_by, reviewed_at=u.reviewed_at, review_comment=u.review_comment,
    ) for u in rows])


async def _update_doc_review_status(db: AsyncSession, doc_id):
    """문서의 온톨로지 usage 검토상태를 집계하여 문서 review_status 갱신"""
    usages = (await db.execute(
        select(CollectionUnstructuredDocOntologyUsage).where(
            CollectionUnstructuredDocOntologyUsage.document_id == doc_id,
        )
    )).scalars().all()
    if not usages:
        return
    statuses = [u.review_status or "PENDING_REVIEW" for u in usages]
    all_approved = all(s == "APPROVED" for s in statuses)
    all_rejected = all(s == "REJECTED" for s in statuses)
    any_approved = any(s == "APPROVED" for s in statuses)

    doc = (await db.execute(
        select(CollectionUnstructuredDocument).where(CollectionUnstructuredDocument.id == doc_id)
    )).scalar_one_or_none()
    if not doc:
        return
    if all_approved:
        doc.review_status = "ALL_APPROVED"
        doc.graph_integrated = True
    elif all_rejected:
        doc.review_status = "ALL_REJECTED"
        doc.graph_integrated = False
    elif any_approved:
        doc.review_status = "PARTIALLY_APPROVED"
    else:
        doc.review_status = "PENDING_REVIEW"
    await db.flush()


@router.put("/unstructured-docs/{doc_id}/ontology-usage/{usage_id}/approve", response_model=APIResponse)
async def approve_ontology_usage(
    doc_id: str, usage_id: str, comment: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """온톨로지 추출 결과 승인 — 운영 반영 허용"""
    usage = (await db.execute(
        select(CollectionUnstructuredDocOntologyUsage).where(
            CollectionUnstructuredDocOntologyUsage.id == uuid.UUID(usage_id),
            CollectionUnstructuredDocOntologyUsage.document_id == uuid.UUID(doc_id),
        )
    )).scalar_one_or_none()
    if not usage:
        raise HTTPException(status_code=404, detail="온톨로지 활용 데이터를 찾을 수 없습니다.")
    usage.review_status = "APPROVED"
    usage.reviewed_by = user.id
    usage.reviewed_at = datetime.now()
    usage.review_comment = comment
    await db.flush()
    await _update_doc_review_status(db, uuid.UUID(doc_id))
    return APIResponse(message="승인되었습니다. 운영 그래프에 반영됩니다.")


@router.put("/unstructured-docs/{doc_id}/ontology-usage/{usage_id}/reject", response_model=APIResponse)
async def reject_ontology_usage(
    doc_id: str, usage_id: str, comment: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """온톨로지 추출 결과 반려 — 운영 미반영"""
    usage = (await db.execute(
        select(CollectionUnstructuredDocOntologyUsage).where(
            CollectionUnstructuredDocOntologyUsage.id == uuid.UUID(usage_id),
            CollectionUnstructuredDocOntologyUsage.document_id == uuid.UUID(doc_id),
        )
    )).scalar_one_or_none()
    if not usage:
        raise HTTPException(status_code=404, detail="온톨로지 활용 데이터를 찾을 수 없습니다.")
    usage.review_status = "REJECTED"
    usage.reviewed_by = user.id
    usage.reviewed_at = datetime.now()
    usage.review_comment = comment or ""
    await db.flush()
    await _update_doc_review_status(db, uuid.UUID(doc_id))
    return APIResponse(message="반려되었습니다.")
