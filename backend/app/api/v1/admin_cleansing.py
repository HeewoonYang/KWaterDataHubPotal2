"""관리자 - 데이터정제 API (비식별화 CRUD + 실행 포함)"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.cleansing import (
    AnonymizationConfig, AnonymizationLog, CleansingJob, CleansingJobRule, CleansingRule, TransformModel,
)
from app.schemas.admin import (
    AnonymizationCreate, AnonymizationResponse, AnonymizationUpdate,
    CleansingJobResponse, CleansingRuleResponse, TransformResponse,
)
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/rules", response_model=APIResponse[list[CleansingRuleResponse]])
async def list_rules(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CleansingRule).where(CleansingRule.is_deleted == False).order_by(CleansingRule.sort_order))).scalars().all()
    return APIResponse(data=[CleansingRuleResponse(
        id=r.id, rule_name=r.rule_name, rule_type=r.rule_type,
        target_column_type=r.target_column_type, severity=r.severity, is_active=r.is_active,
    ) for r in rows])


@router.get("/jobs", response_model=APIResponse[list[CleansingJobResponse]])
async def list_jobs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CleansingJob).where(CleansingJob.is_deleted == False).order_by(CleansingJob.created_at.desc()))).scalars().all()
    items = []
    for r in rows:
        rule_rows = (await db.execute(
            select(CleansingJobRule.rule_id).where(CleansingJobRule.job_id == r.id).order_by(CleansingJobRule.sort_order)
        )).scalars().all()
        r_ids = [str(rid) for rid in rule_rows] if rule_rows else (r.rule_ids or [])
        items.append(CleansingJobResponse(
            id=r.id, job_name=r.job_name, job_status=r.job_status,
            total_rows=r.total_rows, cleansed_rows=r.cleansed_rows, error_rows=r.error_rows,
            started_at=r.started_at, rule_ids=r_ids,
        ))
    return APIResponse(data=items)


# ── 비식별화 CRUD ──
@router.get("/anonymization", response_model=APIResponse[list[AnonymizationResponse]])
async def list_anonymization(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(AnonymizationConfig).where(AnonymizationConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[AnonymizationResponse(
        id=r.id, config_name=r.config_name, method=r.method, is_active=r.is_active,
        target_columns=r.target_columns,
    ) for r in rows])


@router.post("/anonymization", response_model=APIResponse[AnonymizationResponse])
async def create_anonymization(body: AnonymizationCreate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    config = AnonymizationConfig(
        id=uuid.uuid4(), config_name=body.config_name, dataset_id=body.dataset_id,
        target_columns=body.target_columns or [], method=body.method,
        method_config=body.method_config, is_active=True, created_by=user.id,
    )
    db.add(config)
    await db.flush()
    return APIResponse(data=AnonymizationResponse(
        id=config.id, config_name=config.config_name, method=config.method,
        is_active=True, target_columns=config.target_columns,
    ), message="비식별화 설정이 등록되었습니다")


@router.put("/anonymization/{config_id}", response_model=APIResponse)
async def update_anonymization(config_id: str, body: AnonymizationUpdate, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    config = (await db.execute(select(AnonymizationConfig).where(AnonymizationConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="비식별화 설정을 찾을 수 없습니다")
    if body.config_name is not None:
        config.config_name = body.config_name
    if body.target_columns is not None:
        config.target_columns = body.target_columns
    if body.method is not None:
        config.method = body.method
    if body.method_config is not None:
        config.method_config = body.method_config
    if body.is_active is not None:
        config.is_active = body.is_active
    if body.description is not None:
        config.description = body.description
    config.updated_by = user.id
    config.updated_at = datetime.now()
    return APIResponse(message="비식별화 설정이 수정되었습니다")


@router.delete("/anonymization/{config_id}", response_model=APIResponse)
async def delete_anonymization(config_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    config = (await db.execute(select(AnonymizationConfig).where(AnonymizationConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="비식별화 설정을 찾을 수 없습니다")
    config.is_deleted = True
    return APIResponse(message="비식별화 설정이 삭제되었습니다")


@router.post("/anonymization/{config_id}/execute", response_model=APIResponse)
async def execute_anonymization(config_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """비식별화 실행 (시뮬레이션)"""
    config = (await db.execute(select(AnonymizationConfig).where(AnonymizationConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="비식별화 설정을 찾을 수 없습니다")
    if not config.is_active:
        raise HTTPException(status_code=400, detail="비활성 상태의 설정은 실행할 수 없습니다")

    # 대상 컬럼 수 기반 시뮬레이션
    target_count = len(config.target_columns) if config.target_columns else 0
    processed = target_count * 100  # 시뮬레이션: 컬럼당 100건 처리

    # 실행 로그 저장
    log = AnonymizationLog(
        id=uuid.uuid4(), config_id=config.id,
        executed_at=datetime.now(), executed_by=user.id,
        total_rows=processed, processed_rows=processed,
        status="SUCCESS",
    )
    db.add(log)

    return APIResponse(data={
        "config_name": config.config_name,
        "method": config.method,
        "processed_rows": processed,
        "target_columns": config.target_columns,
    }, message=f"비식별화 실행 완료 ({processed}건 처리)")


@router.get("/transforms", response_model=APIResponse[list[TransformResponse]])
async def list_transforms(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(TransformModel).where(TransformModel.is_deleted == False))).scalars().all()
    return APIResponse(data=[TransformResponse(
        id=r.id, model_name=r.model_name, transform_type=r.transform_type, status=r.status,
    ) for r in rows])
