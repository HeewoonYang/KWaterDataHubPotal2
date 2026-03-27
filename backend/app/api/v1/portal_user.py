"""포털 사용자 API (마이페이지, 즐겨찾기, 알림)"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.auth import UserProfileResponse
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.portal import (
    BookmarkCreate, BookmarkResponse, DistDownloadItem,
    NotificationResponse, NotificationSettingItem, NotificationSettingsUpdate, RecentViewResponse,
)
from app.services import auth_service, portal_user_service

router = APIRouter()


# ── 프로필 ──
@router.get("/profile", response_model=APIResponse[UserProfileResponse])
async def get_profile(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    profile = await auth_service.get_user_profile(db, user.id)
    return APIResponse(data=profile)


# ── 즐겨찾기 ──
@router.get("/favorites", response_model=PageResponse[BookmarkResponse])
async def list_favorites(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return await portal_user_service.get_favorites(db, user.id, PageRequest(page=page, page_size=page_size))


@router.post("/favorites", response_model=APIResponse[BookmarkResponse])
async def add_favorite(
    body: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await portal_user_service.add_favorite(db, user.id, body)
    return APIResponse(data=data, message="즐겨찾기에 추가되었습니다")


@router.delete("/favorites/{bookmark_id}", response_model=APIResponse)
async def remove_favorite(
    bookmark_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    ok = await portal_user_service.remove_favorite(db, user.id, bookmark_id)
    if not ok:
        raise HTTPException(status_code=404, detail="즐겨찾기를 찾을 수 없습니다")
    return APIResponse(message="즐겨찾기에서 제거되었습니다")


# ── 최근 조회 ──
@router.get("/recent-views", response_model=PageResponse[RecentViewResponse])
async def list_recent_views(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return await portal_user_service.get_recent_views(db, user.id, PageRequest(page=page, page_size=page_size))


# ── 다운로드 이력 ──
@router.get("/downloads", response_model=PageResponse[DistDownloadItem])
async def list_downloads(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return await portal_user_service.get_downloads(db, user.id, PageRequest(page=page, page_size=page_size))


# ── 알림 ──
@router.get("/notifications", response_model=PageResponse[NotificationResponse])
async def list_notifications(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return await portal_user_service.get_notifications(db, user.id, PageRequest(page=page, page_size=page_size))


@router.put("/notifications/{noti_id}/read", response_model=APIResponse)
async def mark_notification_read(
    noti_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    ok = await portal_user_service.mark_notification_read(db, user.id, noti_id)
    if not ok:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
    return APIResponse(message="읽음 처리되었습니다")


# ── 알림 설정 ──
@router.get("/notification-settings", response_model=APIResponse[list[NotificationSettingItem]])
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await portal_user_service.get_notification_settings(db, user.id)
    return APIResponse(data=data)


@router.put("/notification-settings", response_model=APIResponse)
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    await portal_user_service.update_notification_settings(db, user.id, body.settings)
    return APIResponse(message="알림 설정이 저장되었습니다")
