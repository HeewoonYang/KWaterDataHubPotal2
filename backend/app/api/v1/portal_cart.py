"""포털 - 데이터 장바구니 API"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user, CurrentUser
from app.models.portal import PortalCartItem
from app.models.catalog import CatalogDataset
from app.schemas.common import APIResponse

router = APIRouter()


# ── 장바구니 조회 ──
@router.get("", summary="장바구니 목록")
async def list_cart(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 장바구니 항목을 조회합니다."""
    result = await db.execute(
        select(PortalCartItem)
        .where(PortalCartItem.user_id == current_user.id)
        .order_by(PortalCartItem.added_at.desc())
    )
    items = result.scalars().all()

    data = []
    for item in items:
        # 카탈로그에서 최신 정보 가져오기
        ds_result = await db.execute(
            select(CatalogDataset).where(CatalogDataset.id == item.dataset_id)
        )
        ds = ds_result.scalar_one_or_none()

        data.append({
            "id": str(item.id),
            "dataset_id": str(item.dataset_id),
            "dataset_name": item.dataset_name or (ds.dataset_name if ds else ""),
            "dataset_name_kr": ds.dataset_name_kr if ds else "",
            "data_format": item.data_format or (ds.data_format if ds else ""),
            "grade": item.grade,
            "columns": 0,
            "rows": str(ds.row_count) if ds and ds.row_count else "-",
            "tags": ds.tags if ds and ds.tags else [],
            "date_from": item.date_from or "",
            "date_to": item.date_to or "",
            "max_rows": item.max_rows or "",
            "request_format": item.request_format or "CSV",
            "memo": item.memo or "",
            "added_at": item.added_at.strftime("%Y-%m-%d") if item.added_at else "",
        })

    return APIResponse(success=True, message="OK", data=data)


# ── 장바구니에 추가 ──
@router.post("", summary="장바구니 추가")
async def add_to_cart(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """데이터셋을 장바구니에 추가합니다."""
    dataset_id = body.get("dataset_id")
    if not dataset_id:
        return APIResponse(success=False, message="dataset_id 필수")

    # 중복 체크
    exists = await db.execute(
        select(func.count()).select_from(PortalCartItem).where(
            PortalCartItem.user_id == current_user.id,
            PortalCartItem.dataset_id == UUID(str(dataset_id)),
        )
    )
    if exists.scalar() > 0:
        return APIResponse(success=True, message="이미 장바구니에 있습니다", data=None)

    # 카탈로그에서 정보 가져오기
    ds_result = await db.execute(
        select(CatalogDataset).where(CatalogDataset.id == UUID(str(dataset_id)))
    )
    ds = ds_result.scalar_one_or_none()

    item = PortalCartItem(
        user_id=current_user.id,
        dataset_id=UUID(str(dataset_id)),
        dataset_name=body.get("dataset_name") or (ds.dataset_name_kr or ds.dataset_name if ds else ""),
        data_format=body.get("data_format") or (ds.data_format if ds else ""),
        grade=body.get("grade") or 3,
        date_from=body.get("date_from"),
        date_to=body.get("date_to"),
        max_rows=body.get("max_rows"),
        request_format=body.get("request_format", "CSV"),
        memo=body.get("memo"),
        added_at=datetime.now(),
    )
    db.add(item)
    await db.commit()

    return APIResponse(success=True, message="장바구니에 추가되었습니다", data={"id": str(item.id)})


# ── 장바구니에서 삭제 ──
@router.delete("/{item_id}", summary="장바구니 항목 삭제")
async def remove_from_cart(
    item_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """장바구니에서 특정 항목을 삭제합니다."""
    await db.execute(
        delete(PortalCartItem).where(
            PortalCartItem.user_id == current_user.id,
            PortalCartItem.id == UUID(item_id),
        )
    )
    await db.commit()
    return APIResponse(success=True, message="삭제되었습니다")


# ── 장바구니 전체 비우기 ──
@router.delete("", summary="장바구니 비우기")
async def clear_cart(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """장바구니를 전체 비웁니다."""
    await db.execute(
        delete(PortalCartItem).where(PortalCartItem.user_id == current_user.id)
    )
    await db.commit()
    return APIResponse(success=True, message="장바구니를 비웠습니다")


# ── 장바구니 항목 수정 (기간/포맷 등) ──
@router.put("/{item_id}", summary="장바구니 항목 수정")
async def update_cart_item(
    item_id: str,
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """장바구니 항목의 기간, 포맷, 메모 등을 수정합니다."""
    result = await db.execute(
        select(PortalCartItem).where(
            PortalCartItem.user_id == current_user.id,
            PortalCartItem.id == UUID(item_id),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        return APIResponse(success=False, message="항목을 찾을 수 없습니다")

    for key in ("date_from", "date_to", "max_rows", "request_format", "memo"):
        if key in body:
            setattr(item, key, body[key])

    await db.commit()
    return APIResponse(success=True, message="수정되었습니다")
