"""관리자 - 데이터정제 API"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.cleansing import (AnonymizationConfig, CleansingJob, CleansingJobRule, CleansingRule, TransformModel)
from app.schemas.admin import AnonymizationResponse, CleansingJobResponse, CleansingRuleResponse, TransformResponse
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
        # 중간 테이블에서 rule_ids 조회 (없으면 deprecated JSONB fallback)
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


@router.get("/anonymization", response_model=APIResponse[list[AnonymizationResponse]])
async def list_anonymization(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(AnonymizationConfig).where(AnonymizationConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[AnonymizationResponse(
        id=r.id, config_name=r.config_name, method=r.method, is_active=r.is_active,
    ) for r in rows])


@router.get("/transforms", response_model=APIResponse[list[TransformResponse]])
async def list_transforms(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(TransformModel).where(TransformModel.is_deleted == False))).scalars().all()
    return APIResponse(data=[TransformResponse(
        id=r.id, model_name=r.model_name, transform_type=r.transform_type, status=r.status,
    ) for r in rows])
