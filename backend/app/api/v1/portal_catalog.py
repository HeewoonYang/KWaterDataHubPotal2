"""포털 카탈로그 API"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_current_user_optional
from app.database import get_db
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.portal import CatalogDatasetDetail, CatalogDatasetListItem, CategoryTreeItem
from app.services import portal_catalog_service

router = APIRouter()


@router.get("/datasets", response_model=PageResponse[CatalogDatasetListItem])
async def list_datasets(
    page: int = 1, page_size: int = 20, search: str | None = None,
    sort_by: str | None = None, sort_order: str = "desc",
    classification_id: int | None = None, grade_id: int | None = None, data_format: str | None = None,
    category: str | None = None, type: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    params = PageRequest(page=page, page_size=page_size, search=search, sort_by=sort_by, sort_order=sort_order)
    # type 파라미터를 data_format으로 매핑
    fmt = data_format or (type if type and type != '전체' else None)
    return await portal_catalog_service.get_datasets(db, params, grades, classification_id, grade_id, fmt, category)


@router.get("/datasets/{dataset_id}", response_model=APIResponse[CatalogDatasetDetail])
async def get_dataset(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    detail = await portal_catalog_service.get_dataset_detail(db, dataset_id, grades)
    if not detail:
        raise HTTPException(status_code=404, detail="데이터셋을 찾을 수 없습니다")
    return APIResponse(data=detail)


@router.get("/categories", response_model=APIResponse[list[CategoryTreeItem]])
async def get_categories(db: AsyncSession = Depends(get_db)):
    data = await portal_catalog_service.get_categories(db)
    return APIResponse(data=data)


@router.get("/search", response_model=PageResponse[CatalogDatasetListItem])
async def search_datasets(
    keyword: str = "", page: int = 1, page_size: int = 20,
    data_format: str | None = None, grade_id: int | None = None,
    sort_by: str | None = None, sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    user: CurrentUser | None = Depends(get_current_user_optional),
):
    grades = user.data_grades if user else [3]
    params = PageRequest(page=page, page_size=page_size, search=keyword, sort_by=sort_by, sort_order=sort_order)
    return await portal_catalog_service.get_datasets(db, params, grades, data_format=data_format, grade_id=grade_id)
