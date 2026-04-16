"""관리자 - 데이터유통 API"""
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.distribution import (DistributionApiEndpoint, DistributionConfig, DistributionFormat,
                                      DistributionFusionModel, DistributionMcpConfig, DistributionRequest,
                                      DistributionStats)
from app.schemas.admin import (ApiEndpointResponse, DistConfigResponse, DistFormatResponse,
                                DistStatsResponse, FusionModelResponse, McpConfigResponse)
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


@router.get("/requests", response_model=PageResponse)
async def list_requests(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """유통 신청 목록 (관리자용)"""
    query = select(DistributionRequest).where(DistributionRequest.is_deleted == False)
    if status:
        query = query.where(DistributionRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(DistributionRequest.created_at.desc()).offset(offset).limit(page_size))).scalars().all()
    items = [{
        "id": str(r.id), "request_type": r.request_type, "requested_format": r.requested_format,
        "purpose": r.purpose, "status": r.status, "requester_id": str(r.requester_id) if r.requester_id else None,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
        "approved_at": r.approved_at.strftime("%Y-%m-%d %H:%M") if r.approved_at else None,
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.put("/requests/{request_id}/approve", response_model=APIResponse)
async def approve_request(
    request_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """유통 신청 승인"""
    import uuid
    req = (await db.execute(
        select(DistributionRequest).where(DistributionRequest.id == uuid.UUID(request_id))
    )).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")
    req.status = "APPROVED"
    req.approved_at = datetime.now()
    req.approved_by = user.id
    return APIResponse(message="승인되었습니다")


@router.put("/requests/{request_id}/reject", response_model=APIResponse)
async def reject_request(
    request_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """유통 신청 반려"""
    import uuid
    req = (await db.execute(
        select(DistributionRequest).where(DistributionRequest.id == uuid.UUID(request_id))
    )).scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="신청을 찾을 수 없습니다")
    req.status = "REJECTED"
    return APIResponse(message="반려되었습니다")


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


# ══════ 융합 모델 CRUD ══════
@router.post("/fusion-models", response_model=APIResponse)
async def create_fusion_model(
    model_name: str, source_datasets: str = None, fusion_type: str = "JOIN", schedule: str = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """융합 모델 등록"""
    fm = DistributionFusionModel(
        id=uuid.uuid4(), model_name=model_name, fusion_type=fusion_type,
        source_config={"datasets": source_datasets, "schedule": schedule} if source_datasets else None,
        status="ACTIVE", created_by=user.id, created_at=datetime.now(),
    )
    db.add(fm)
    await db.flush()
    return APIResponse(message="융합 모델이 등록되었습니다")


@router.put("/fusion-models/{model_id}", response_model=APIResponse)
async def update_fusion_model(
    model_id: str, model_name: str = None, fusion_type: str = None, status: str = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """융합 모델 수정"""
    fm = (await db.execute(select(DistributionFusionModel).where(DistributionFusionModel.id == uuid.UUID(model_id)))).scalar_one_or_none()
    if not fm:
        raise HTTPException(status_code=404, detail="융합 모델을 찾을 수 없습니다")
    if model_name is not None:
        fm.model_name = model_name
    if fusion_type is not None:
        fm.fusion_type = fusion_type
    if status is not None:
        fm.status = status
    fm.updated_at = datetime.now()
    fm.updated_by = user.id
    await db.flush()
    return APIResponse(message="융합 모델이 수정되었습니다")


@router.delete("/fusion-models/{model_id}", response_model=APIResponse)
async def delete_fusion_model(
    model_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """융합 모델 삭제"""
    fm = (await db.execute(select(DistributionFusionModel).where(DistributionFusionModel.id == uuid.UUID(model_id)))).scalar_one_or_none()
    if not fm:
        raise HTTPException(status_code=404, detail="융합 모델을 찾을 수 없습니다")
    fm.is_deleted = True
    fm.updated_at = datetime.now()
    return APIResponse(message="융합 모델이 삭제되었습니다")


# ══════ MCP 서버 CRUD ══════
@router.post("/mcp-configs", response_model=APIResponse)
async def create_mcp_config(
    mcp_name: str, server_url: str = None, description: str = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """MCP 서버 등록"""
    mc = DistributionMcpConfig(
        id=uuid.uuid4(), mcp_name=mcp_name, server_url=server_url,
        transport_type="SSE", status="ACTIVE", description=description,
        created_by=user.id, created_at=datetime.now(),
    )
    db.add(mc)
    await db.flush()
    return APIResponse(message="MCP 서버가 등록되었습니다")


@router.put("/mcp-configs/{config_id}", response_model=APIResponse)
async def update_mcp_config(
    config_id: str, mcp_name: str = None, server_url: str = None, status: str = None, description: str = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """MCP 서버 수정"""
    mc = (await db.execute(select(DistributionMcpConfig).where(DistributionMcpConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not mc:
        raise HTTPException(status_code=404, detail="MCP 서버를 찾을 수 없습니다")
    if mcp_name is not None:
        mc.mcp_name = mcp_name
    if server_url is not None:
        mc.server_url = server_url
    if status is not None:
        mc.status = status
    if description is not None:
        mc.description = description
    mc.updated_at = datetime.now()
    mc.updated_by = user.id
    await db.flush()
    return APIResponse(message="MCP 서버가 수정되었습니다")


@router.delete("/mcp-configs/{config_id}", response_model=APIResponse)
async def delete_mcp_config(
    config_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """MCP 서버 삭제"""
    mc = (await db.execute(select(DistributionMcpConfig).where(DistributionMcpConfig.id == uuid.UUID(config_id)))).scalar_one_or_none()
    if not mc:
        raise HTTPException(status_code=404, detail="MCP 서버를 찾을 수 없습니다")
    mc.is_deleted = True
    mc.updated_at = datetime.now()
    return APIResponse(message="MCP 서버가 삭제되었습니다")
