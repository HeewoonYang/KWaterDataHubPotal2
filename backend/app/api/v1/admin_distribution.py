"""관리자 - 데이터유통 API"""
import math
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.distribution import (DistributionApiEndpoint, DistributionConfig, DistributionFormat,
                                      DistributionFusionModel, DistributionMcpConfig, DistributionStats)
from app.schemas.admin import (ApiEndpointResponse, DistConfigResponse, DistFormatResponse,
                                DistStatsResponse, FusionModelResponse, McpConfigResponse)
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


@router.get("/configs", response_model=APIResponse[list[DistConfigResponse]])
async def list_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(DistributionConfig).where(DistributionConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[DistConfigResponse(
        id=r.id, config_name=r.config_name, column_change_policy=r.column_change_policy, status=r.status,
    ) for r in rows])


@router.get("/formats", response_model=APIResponse[list[DistFormatResponse]])
async def list_formats(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(DistributionFormat))).scalars().all()
    return APIResponse(data=[DistFormatResponse(
        id=r.id, format_code=r.format_code, format_name=r.format_name,
        mime_type=r.mime_type, file_extension=r.file_extension, is_active=r.is_active,
    ) for r in rows])


@router.get("/api-endpoints", response_model=APIResponse[list[ApiEndpointResponse]])
async def list_api_endpoints(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(DistributionApiEndpoint).where(DistributionApiEndpoint.is_deleted == False))).scalars().all()
    return APIResponse(data=[ApiEndpointResponse(
        id=r.id, api_name=r.api_name, api_path=r.api_path, http_method=r.http_method,
        rate_limit_per_min=r.rate_limit_per_min, requires_auth=r.requires_auth, status=r.status,
    ) for r in rows])


@router.get("/mcp-configs", response_model=APIResponse[list[McpConfigResponse]])
async def list_mcp_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(DistributionMcpConfig).where(DistributionMcpConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[McpConfigResponse(
        id=r.id, mcp_name=r.mcp_name, server_url=r.server_url, transport_type=r.transport_type, status=r.status,
    ) for r in rows])


@router.get("/fusion-models", response_model=APIResponse[list[FusionModelResponse]])
async def list_fusion_models(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(DistributionFusionModel).where(DistributionFusionModel.is_deleted == False))).scalars().all()
    return APIResponse(data=[FusionModelResponse(
        id=r.id, model_name=r.model_name, fusion_type=r.fusion_type, poc_status=r.poc_status, status=r.status,
    ) for r in rows])


@router.get("/stats", response_model=PageResponse[DistStatsResponse])
async def list_stats(
    page: int = 1, page_size: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = select(DistributionStats).order_by(DistributionStats.stat_date.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [DistStatsResponse(
        id=r.id, stat_date=str(r.stat_date) if r.stat_date else None, stat_type=r.stat_type,
        view_count=r.view_count, download_count=r.download_count,
        api_call_count=r.api_call_count, unique_users=r.unique_users,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)
