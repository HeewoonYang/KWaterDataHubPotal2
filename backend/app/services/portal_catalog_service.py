"""카탈로그 서비스"""
import math

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.classification import DataClassification, DataGrade
from app.schemas.common import PageRequest, PageResponse
from app.schemas.portal import CatalogColumnResponse, CatalogDatasetDetail, CatalogDatasetListItem, CategoryTreeItem


async def get_datasets(
    db: AsyncSession, params: PageRequest, user_grades: list[int],
    classification_id: int | None = None, grade_id: int | None = None, data_format: str | None = None,
    category_name: str | None = None,
) -> PageResponse:
    query = (
        select(
            CatalogDataset,
            DataClassification.name.label("cls_name"),
            DataGrade.grade_code.label("grade_code"),
        )
        .outerjoin(DataClassification, CatalogDataset.classification_id == DataClassification.id)
        .outerjoin(DataGrade, CatalogDataset.grade_id == DataGrade.id)
        .where(CatalogDataset.status == "ACTIVE")
        .where(CatalogDataset.grade_id.in_(user_grades))
    )

    if category_name:
        query = query.where(DataClassification.name == category_name)
    elif classification_id:
        query = query.where(CatalogDataset.classification_id == classification_id)
    if grade_id:
        query = query.where(CatalogDataset.grade_id == grade_id)
    if data_format:
        query = query.where(CatalogDataset.data_format == data_format)
    if params.search:
        kw = f"%{params.search}%"
        query = query.where(or_(CatalogDataset.dataset_name.ilike(kw), CatalogDataset.dataset_name_kr.ilike(kw), CatalogDataset.description.ilike(kw)))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    if params.sort_by == "name":
        query = query.order_by(CatalogDataset.dataset_name.asc() if params.sort_order == "asc" else CatalogDataset.dataset_name.desc())
    else:
        query = query.order_by(CatalogDataset.created_at.desc())

    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).all()

    items = []
    for row in rows:
        ds = row[0]
        items.append(CatalogDatasetListItem(
            id=ds.id, dataset_name=ds.dataset_name, dataset_name_kr=ds.dataset_name_kr,
            classification_name=row[1], grade_code=row[2],
            source_system=ds.source_system, owner_department=ds.owner_department,
            data_format=ds.data_format, refresh_frequency=ds.refresh_frequency,
            row_count=ds.row_count, size_bytes=ds.size_bytes,
            tags=ds.tags, description=ds.description, created_at=ds.created_at,
        ))

    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def get_dataset_detail(db: AsyncSession, dataset_id, user_grades: list[int]) -> CatalogDatasetDetail | None:
    row = (await db.execute(
        select(CatalogDataset, DataClassification.name.label("cls_name"), DataGrade.grade_code.label("grade_code"))
        .outerjoin(DataClassification, CatalogDataset.classification_id == DataClassification.id)
        .outerjoin(DataGrade, CatalogDataset.grade_id == DataGrade.id)
        .where(CatalogDataset.id == dataset_id, CatalogDataset.grade_id.in_(user_grades))
    )).first()
    if not row:
        return None

    ds = row[0]
    cols = (await db.execute(
        select(CatalogColumn).where(CatalogColumn.dataset_id == dataset_id).order_by(CatalogColumn.sort_order)
    )).scalars().all()

    return CatalogDatasetDetail(
        id=ds.id, dataset_name=ds.dataset_name, dataset_name_kr=ds.dataset_name_kr,
        classification_name=row[1], grade_code=row[2],
        source_system=ds.source_system, owner_department=ds.owner_department,
        data_format=ds.data_format, refresh_frequency=ds.refresh_frequency,
        row_count=ds.row_count, size_bytes=ds.size_bytes,
        tags=ds.tags, description=ds.description, created_at=ds.created_at,
        columns=[CatalogColumnResponse.model_validate(c) for c in cols],
    )


async def get_categories(db: AsyncSession) -> list[CategoryTreeItem]:
    top = (await db.execute(
        select(DataClassification)
        .where(DataClassification.level == 1, DataClassification.is_deleted == False)
        .order_by(DataClassification.sort_order)
    )).scalars().all()

    result = []
    for t in top:
        children_rows = (await db.execute(
            select(DataClassification)
            .where(DataClassification.parent_id == t.id, DataClassification.is_deleted == False)
            .order_by(DataClassification.sort_order)
        )).scalars().all()
        children = [CategoryTreeItem(id=c.id, name=c.name, code=c.code, count=c.dataset_count or 0) for c in children_rows]
        result.append(CategoryTreeItem(id=t.id, name=t.name, code=t.code, count=t.dataset_count or 0, children=children))
    return result
