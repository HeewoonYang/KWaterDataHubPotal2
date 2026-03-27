"""사용자 서비스 (마이페이지, 즐겨찾기, 알림)"""
import math
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.distribution import DistributionDataset, DistributionDownloadLog
from app.models.portal import (
    PortalBookmark, PortalNotification, PortalNotificationSubscription, PortalRecentView,
)
from app.schemas.common import PageRequest, PageResponse
from app.schemas.portal import (
    BookmarkCreate, BookmarkResponse, DistDownloadItem,
    NotificationResponse, NotificationSettingItem, RecentViewResponse,
)


# ── 즐겨찾기 ──
async def get_favorites(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
    query = select(PortalBookmark).where(PortalBookmark.user_id == user_id).order_by(PortalBookmark.bookmarked_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).scalars().all()
    items = [BookmarkResponse.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def add_favorite(db: AsyncSession, user_id, data: BookmarkCreate) -> BookmarkResponse:
    bm = PortalBookmark(
        id=uuid.uuid4(), user_id=user_id, resource_type=data.resource_type,
        resource_id=data.resource_id, resource_name=data.resource_name, bookmarked_at=datetime.now(),
    )
    db.add(bm)
    await db.flush()
    return BookmarkResponse.model_validate(bm)


async def remove_favorite(db: AsyncSession, user_id, bookmark_id) -> bool:
    result = await db.execute(select(PortalBookmark).where(PortalBookmark.id == bookmark_id, PortalBookmark.user_id == user_id))
    bm = result.scalar_one_or_none()
    if not bm:
        return False
    await db.delete(bm)
    return True


# ── 최근 조회 ──
async def get_recent_views(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
    query = select(PortalRecentView).where(PortalRecentView.user_id == user_id).order_by(PortalRecentView.viewed_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).scalars().all()
    items = [RecentViewResponse.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def record_view(db: AsyncSession, user_id, resource_type: str, resource_id, resource_name: str | None):
    rv = PortalRecentView(
        id=uuid.uuid4(), user_id=user_id, resource_type=resource_type,
        resource_id=resource_id, resource_name=resource_name, viewed_at=datetime.now(),
    )
    db.add(rv)


# ── 다운로드 이력 ──
async def get_downloads(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
    query = (
        select(DistributionDownloadLog, DistributionDataset.distribution_name)
        .outerjoin(DistributionDataset, DistributionDownloadLog.dataset_id == DistributionDataset.id)
        .where(DistributionDownloadLog.user_id == user_id)
        .order_by(DistributionDownloadLog.downloaded_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).all()
    items = [DistDownloadItem(
        id=r[0].id, dataset_name=r[1], download_format=r[0].download_format,
        row_count=r[0].row_count, file_size_bytes=r[0].file_size_bytes, downloaded_at=r[0].downloaded_at,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


# ── 알림 ──
async def get_notifications(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
    query = select(PortalNotification).where(PortalNotification.user_id == user_id).order_by(PortalNotification.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).scalars().all()
    items = [NotificationResponse.model_validate(r) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def mark_notification_read(db: AsyncSession, user_id, noti_id) -> bool:
    result = await db.execute(select(PortalNotification).where(PortalNotification.id == noti_id, PortalNotification.user_id == user_id))
    noti = result.scalar_one_or_none()
    if not noti:
        return False
    noti.is_read = True
    noti.read_at = datetime.now()
    return True


# ── 알림 설정 ──
async def get_notification_settings(db: AsyncSession, user_id) -> list[NotificationSettingItem]:
    rows = (await db.execute(
        select(PortalNotificationSubscription).where(PortalNotificationSubscription.user_id == user_id)
    )).scalars().all()
    return [NotificationSettingItem(notification_type=r.notification_type, is_enabled=r.is_enabled, channel=r.channel) for r in rows]


async def update_notification_settings(db: AsyncSession, user_id, settings: list[NotificationSettingItem]):
    for s in settings:
        existing = (await db.execute(
            select(PortalNotificationSubscription)
            .where(PortalNotificationSubscription.user_id == user_id,
                   PortalNotificationSubscription.notification_type == s.notification_type,
                   PortalNotificationSubscription.channel == s.channel)
        )).scalar_one_or_none()
        if existing:
            existing.is_enabled = s.is_enabled
        else:
            db.add(PortalNotificationSubscription(
                id=uuid.uuid4(), user_id=user_id,
                notification_type=s.notification_type, is_enabled=s.is_enabled, channel=s.channel,
            ))
