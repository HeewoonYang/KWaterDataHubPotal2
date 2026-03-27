"""관리자 - 운영관리 API"""
import math
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.operation import (OperationAiModelConfig, OperationAiQueryLog, OperationHubStats, OperationSystemEvent)
from app.schemas.admin import AiMonitorResponse, HubStatsResponse, SystemEventResponse
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


@router.get("/hub-stats", response_model=PageResponse[HubStatsResponse])
async def list_hub_stats(
    page: int = 1, page_size: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = select(OperationHubStats).order_by(OperationHubStats.stat_date.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [HubStatsResponse(
        id=r.id, stat_date=str(r.stat_date) if r.stat_date else None, stat_type=r.stat_type,
        total_datasets=r.total_datasets, total_users=r.total_users, active_users=r.active_users,
        total_downloads=r.total_downloads, total_api_calls=r.total_api_calls,
        data_quality_score=float(r.data_quality_score) if r.data_quality_score else None,
        collection_success_rate=float(r.collection_success_rate) if r.collection_success_rate else None,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/ai-logs", response_model=PageResponse[AiMonitorResponse])
async def list_ai_logs(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = select(OperationAiQueryLog).order_by(OperationAiQueryLog.queried_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [AiMonitorResponse(
        id=r.id, query_type=r.query_type, model_name=r.model_name,
        token_count=r.token_count, response_time_ms=r.response_time_ms,
        satisfaction_rating=r.satisfaction_rating, queried_at=r.queried_at,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/ai-models", response_model=APIResponse[list])
async def list_ai_models(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(OperationAiModelConfig).where(OperationAiModelConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[{"id": str(r.id), "model_name": r.model_name, "model_type": r.model_type,
                              "provider": r.provider, "is_active": r.is_active} for r in rows])


@router.get("/system-events", response_model=APIResponse[list[SystemEventResponse]])
async def list_system_events(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(OperationSystemEvent).order_by(OperationSystemEvent.occurred_at.desc()).limit(50))).scalars().all()
    return APIResponse(data=[SystemEventResponse(
        id=r.id, event_type=r.event_type, severity=r.severity, title=r.title,
        description=r.description, occurred_at=r.occurred_at, resolved_at=r.resolved_at,
    ) for r in rows])
