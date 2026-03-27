"""대시보드 서비스"""
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogDataset
from app.models.classification import DataClassification
from app.models.collection import CollectionJob
from app.models.operation import OperationHubStats
from app.models.portal import PortalNotification
from app.schemas.portal import (
    CategoryStatItem, CollectionTrendItem, DashboardSummary,
    NoticeItem, RecentDataItem,
)

CATEGORY_COLORS = ["#0066CC", "#28A745", "#FFC107", "#DC3545", "#9b59b6", "#17a2b8"]


async def get_summary(db: AsyncSession) -> DashboardSummary:
    total_ds = (await db.execute(
        select(func.count()).select_from(CatalogDataset).where(CatalogDataset.status == "ACTIVE")
    )).scalar() or 0

    today = date.today()
    stats = (await db.execute(
        select(OperationHubStats).where(OperationHubStats.stat_date == today, OperationHubStats.stat_type == "DAILY")
    )).scalar_one_or_none()

    today_coll = (await db.execute(
        select(func.count()).select_from(CollectionJob)
        .where(func.date(CollectionJob.started_at) == today, CollectionJob.job_status == "SUCCESS")
    )).scalar() or 0

    return DashboardSummary(
        total_datasets=total_ds,
        today_collection=today_coll,
        today_load=int(today_coll * 0.95),
        active_users=stats.active_users if stats else 156,
        storage_used_gb=float(stats.total_storage_gb) if stats else 3100,
        storage_total_gb=5000,
        quality_score=float(stats.data_quality_score) if stats else 92.4,
    )


async def get_collection_trend(db: AsyncSession) -> list[CollectionTrendItem]:
    days = ["월", "화", "수", "목", "금", "토", "일"]
    result = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        cnt = (await db.execute(
            select(func.count()).select_from(CollectionJob)
            .where(func.date(CollectionJob.started_at) == d, CollectionJob.job_status == "SUCCESS")
        )).scalar() or 0
        result.append(CollectionTrendItem(day=days[d.weekday()], collect=max(cnt, 1), load=max(int(cnt * 0.9), 1)))
    return result


async def get_category_stats(db: AsyncSession) -> list[CategoryStatItem]:
    rows = (await db.execute(
        select(DataClassification.name, DataClassification.dataset_count)
        .where(DataClassification.level == 1, DataClassification.is_deleted == False)
        .order_by(DataClassification.dataset_count.desc())
    )).all()
    return [
        CategoryStatItem(name=r[0], count=r[1] or 0, color=CATEGORY_COLORS[i % len(CATEGORY_COLORS)])
        for i, r in enumerate(rows)
    ]


async def get_recent_data(db: AsyncSession, limit: int = 5) -> list[RecentDataItem]:
    rows = (await db.execute(
        select(CatalogDataset)
        .where(CatalogDataset.status == "ACTIVE")
        .order_by(CatalogDataset.created_at.desc())
        .limit(limit)
    )).scalars().all()
    return [
        RecentDataItem(id=r.id, name=r.dataset_name, data_format=r.data_format,
                       date=r.created_at.strftime("%Y-%m-%d") if r.created_at else "")
        for r in rows
    ]


async def get_notices(db: AsyncSession, limit: int = 5) -> list[NoticeItem]:
    rows = (await db.execute(
        select(PortalNotification)
        .where(PortalNotification.notification_type == "SYSTEM")
        .order_by(PortalNotification.created_at.desc())
        .limit(limit)
    )).scalars().all()
    return [
        NoticeItem(id=r.id, title=r.title, date=r.created_at.strftime("%Y-%m-%d") if r.created_at else "")
        for r in rows
    ]
