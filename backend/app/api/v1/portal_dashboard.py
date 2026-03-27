"""포털 대시보드 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import APIResponse
from app.schemas.portal import CategoryStatItem, CollectionTrendItem, DashboardSummary, NoticeItem, RecentDataItem
from app.services import portal_dashboard_service

router = APIRouter()


@router.get("/summary", response_model=APIResponse[DashboardSummary])
async def get_summary(db: AsyncSession = Depends(get_db)):
    data = await portal_dashboard_service.get_summary(db)
    return APIResponse(data=data)


@router.get("/collection-trend", response_model=APIResponse[list[CollectionTrendItem]])
async def get_collection_trend(db: AsyncSession = Depends(get_db)):
    data = await portal_dashboard_service.get_collection_trend(db)
    return APIResponse(data=data)


@router.get("/category-stats", response_model=APIResponse[list[CategoryStatItem]])
async def get_category_stats(db: AsyncSession = Depends(get_db)):
    data = await portal_dashboard_service.get_category_stats(db)
    return APIResponse(data=data)


@router.get("/recent-data", response_model=APIResponse[list[RecentDataItem]])
async def get_recent_data(db: AsyncSession = Depends(get_db)):
    data = await portal_dashboard_service.get_recent_data(db)
    return APIResponse(data=data)


@router.get("/notices", response_model=APIResponse[list[NoticeItem]])
async def get_notices(db: AsyncSession = Depends(get_db)):
    data = await portal_dashboard_service.get_notices(db)
    return APIResponse(data=data)
