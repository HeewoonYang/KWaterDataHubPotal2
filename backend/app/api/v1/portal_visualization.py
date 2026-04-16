"""포털 시각화 API"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.common import APIResponse, PageRequest, PageResponse
from app.schemas.portal import ChartCreate, ChartResponse, DataSourceItem, DatasetColumnItem
from app.services import portal_visualization_service

router = APIRouter()


@router.get("/data-sources", response_model=APIResponse[list[DataSourceItem]])
async def get_data_sources(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await portal_visualization_service.get_data_sources(db, user.data_grades)
    return APIResponse(data=data)


@router.get("/datasets/{dataset_id}/columns", response_model=APIResponse[list[DatasetColumnItem]])
async def get_columns(
    dataset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    data = await portal_visualization_service.get_dataset_columns(db, dataset_id)
    return APIResponse(data=data)


@router.get("/charts", response_model=PageResponse[ChartResponse])
async def list_charts(
    page: int = 1, page_size: int = 20, search: str | None = None,
    chart_type: str | None = None, dataset_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    params = PageRequest(page=page, page_size=page_size, search=search)
    return await portal_visualization_service.list_charts(db, params, chart_type, dataset_id)


@router.get("/charts/{chart_id}", response_model=APIResponse[ChartResponse])
async def get_chart(chart_id: UUID, db: AsyncSession = Depends(get_db)):
    data = await portal_visualization_service.get_chart(db, chart_id)
    if not data:
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다")
    return APIResponse(data=data)


@router.post("/charts", response_model=APIResponse[ChartResponse])
async def create_chart(
    body: ChartCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await portal_visualization_service.create_chart(db, user.id, body)
    return APIResponse(data=data, message="차트가 저장되었습니다")


@router.put("/charts/{chart_id}", response_model=APIResponse[ChartResponse])
async def update_chart(
    chart_id: UUID, body: ChartCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    # 간소화: delete + create
    await portal_visualization_service.delete_chart(db, chart_id, user.id)
    data = await portal_visualization_service.create_chart(db, user.id, body)
    return APIResponse(data=data, message="차트가 수정되었습니다")


@router.delete("/charts/{chart_id}", response_model=APIResponse)
async def delete_chart(
    chart_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    ok = await portal_visualization_service.delete_chart(db, chart_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다")
    return APIResponse(message="차트가 삭제되었습니다")


@router.post("/charts/{chart_id}/clone", response_model=APIResponse[ChartResponse])
async def clone_chart(
    chart_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    data = await portal_visualization_service.clone_chart(db, chart_id, user.id)
    if not data:
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다")
    return APIResponse(data=data, message="차트가 복제되었습니다")
