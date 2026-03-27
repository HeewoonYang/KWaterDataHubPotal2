"""시각화 서비스"""
import math
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.portal import PortalVisualizationChart
from app.models.user import UserAccount
from app.schemas.common import PageRequest, PageResponse
from app.schemas.portal import ChartCreate, ChartResponse, DataSourceItem, DatasetColumnItem


async def get_data_sources(db: AsyncSession, user_grades: list[int]) -> list[DataSourceItem]:
    rows = (await db.execute(
        select(CatalogDataset)
        .where(CatalogDataset.status == "ACTIVE", CatalogDataset.grade_id.in_(user_grades))
        .order_by(CatalogDataset.dataset_name)
    )).scalars().all()
    return [DataSourceItem(id=r.id, dataset_name=r.dataset_name, data_format=r.data_format) for r in rows]


async def get_dataset_columns(db: AsyncSession, dataset_id) -> list[DatasetColumnItem]:
    rows = (await db.execute(
        select(CatalogColumn).where(CatalogColumn.dataset_id == dataset_id).order_by(CatalogColumn.sort_order)
    )).scalars().all()
    return [DatasetColumnItem(column_name=r.column_name, column_name_kr=r.column_name_kr, data_type=r.data_type) for r in rows]


async def list_charts(db: AsyncSession, params: PageRequest, chart_type: str | None = None) -> PageResponse:
    query = (
        select(PortalVisualizationChart, UserAccount.name.label("owner_name"))
        .outerjoin(UserAccount, PortalVisualizationChart.owner_id == UserAccount.id)
        .where(PortalVisualizationChart.is_deleted == False)
    )
    if chart_type:
        query = query.where(PortalVisualizationChart.chart_type == chart_type)
    if params.search:
        query = query.where(PortalVisualizationChart.chart_name.ilike(f"%{params.search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.order_by(PortalVisualizationChart.created_at.desc()).offset(offset).limit(params.page_size))).all()

    items = [ChartResponse(
        id=r[0].id, chart_name=r[0].chart_name, chart_type=r[0].chart_type,
        dataset_id=r[0].dataset_id, chart_config=r[0].chart_config or {}, is_public=r[0].is_public,
        view_count=r[0].view_count or 0, owner_name=r[1], created_at=r[0].created_at,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def create_chart(db: AsyncSession, user_id, data: ChartCreate) -> ChartResponse:
    chart = PortalVisualizationChart(
        id=uuid.uuid4(), chart_name=data.chart_name, chart_type=data.chart_type,
        dataset_id=data.dataset_id, chart_config=data.chart_config,
        is_public=data.is_public, owner_id=user_id, created_at=datetime.now(),
    )
    db.add(chart)
    await db.flush()
    return ChartResponse(id=chart.id, chart_name=chart.chart_name, chart_type=chart.chart_type,
                         dataset_id=chart.dataset_id, chart_config=chart.chart_config, is_public=chart.is_public, created_at=chart.created_at)


async def get_chart(db: AsyncSession, chart_id) -> ChartResponse | None:
    row = (await db.execute(
        select(PortalVisualizationChart, UserAccount.name.label("owner_name"))
        .outerjoin(UserAccount, PortalVisualizationChart.owner_id == UserAccount.id)
        .where(PortalVisualizationChart.id == chart_id)
    )).first()
    if not row:
        return None
    c = row[0]
    return ChartResponse(id=c.id, chart_name=c.chart_name, chart_type=c.chart_type,
                         dataset_id=c.dataset_id, chart_config=c.chart_config or {}, is_public=c.is_public,
                         view_count=c.view_count or 0, owner_name=row[1], created_at=c.created_at)


async def delete_chart(db: AsyncSession, chart_id, user_id) -> bool:
    result = await db.execute(select(PortalVisualizationChart).where(PortalVisualizationChart.id == chart_id))
    chart = result.scalar_one_or_none()
    if not chart:
        return False
    chart.is_deleted = True
    return True


async def clone_chart(db: AsyncSession, chart_id, user_id) -> ChartResponse | None:
    original = (await db.execute(select(PortalVisualizationChart).where(PortalVisualizationChart.id == chart_id))).scalar_one_or_none()
    if not original:
        return None
    new_chart = PortalVisualizationChart(
        id=uuid.uuid4(), chart_name=f"{original.chart_name} (복사)",
        chart_type=original.chart_type, dataset_id=original.dataset_id,
        chart_config=original.chart_config, is_public=False,
        owner_id=user_id, created_at=datetime.now(),
    )
    db.add(new_chart)
    await db.flush()
    return ChartResponse(id=new_chart.id, chart_name=new_chart.chart_name, chart_type=new_chart.chart_type,
                         dataset_id=new_chart.dataset_id, chart_config=new_chart.chart_config or {}, created_at=new_chart.created_at)
