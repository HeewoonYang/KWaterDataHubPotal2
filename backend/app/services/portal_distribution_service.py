"""유통 서비스"""
import csv
import io
import json
import math
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.classification import DataClassification, DataGrade
from app.models.distribution import (
    DistributionDataset, DistributionDownloadLog, DistributionRequest, DistributionRequestDataset,
)
from app.schemas.common import PageRequest, PageResponse
from app.schemas.portal import DistDatasetListItem, DistDownloadItem, DistRequestCreate, DistRequestResponse


async def get_dist_datasets(
    db: AsyncSession, params: PageRequest, user_grades: list[int],
    classification_id: int | None = None, grade_id: int | None = None, data_format: str | None = None,
) -> PageResponse:
    query = (
        select(DistributionDataset, CatalogDataset.dataset_name, DataClassification.name.label("cls"), DataGrade.grade_code, CatalogDataset.owner_department)
        .join(CatalogDataset, DistributionDataset.dataset_id == CatalogDataset.id)
        .outerjoin(DataClassification, DistributionDataset.classification_id == DataClassification.id)
        .outerjoin(DataGrade, DistributionDataset.grade_id == DataGrade.id)
        .where(DistributionDataset.status == "ACTIVE")
        .where(or_(DistributionDataset.grade_id.in_(user_grades), DistributionDataset.grade_id.is_(None)))
    )
    if params.search:
        kw = f"%{params.search}%"
        query = query.where(or_(DistributionDataset.distribution_name.ilike(kw), CatalogDataset.dataset_name.ilike(kw)))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.order_by(DistributionDataset.created_at.desc()).offset(offset).limit(params.page_size))).all()

    items = [DistDatasetListItem(
        id=r[0].id, distribution_name=r[0].distribution_name, dataset_name=r[1],
        classification_name=r[2], grade_code=r[3], owner_department=r[4],
        is_downloadable=r[0].is_downloadable, allowed_formats=r[0].allowed_formats,
        requires_approval=r[0].requires_approval, view_count=r[0].view_count, download_count=r[0].download_count,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def create_request(db: AsyncSession, user_id, data: DistRequestCreate) -> DistRequestResponse:
    # L3 공개 데이터는 자동 승인
    auto_approve = data.request_type == "DOWNLOAD"
    req_id = uuid.uuid4()
    req = DistributionRequest(
        id=req_id, requester_id=user_id,
        dataset_ids=json.dumps([str(d) for d in data.dataset_ids]),  # deprecated: 하위호환
        request_type=data.request_type, requested_format=data.requested_format,
        purpose=data.purpose, status="APPROVED" if auto_approve else "PENDING",
        approved_at=datetime.now() if auto_approve else None,
    )
    db.add(req)
    await db.flush()

    # 중간 테이블에도 저장 (정규화)
    for ds_id in data.dataset_ids:
        db.add(DistributionRequestDataset(
            id=uuid.uuid4(), request_id=req_id, dataset_id=ds_id,
        ))
    await db.flush()

    return DistRequestResponse(
        id=req.id, request_type=req.request_type, requested_format=req.requested_format,
        purpose=req.purpose, status=req.status, dataset_ids=[str(d) for d in data.dataset_ids],
        created_at=datetime.now(),
    )


async def get_user_requests(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
    query = select(DistributionRequest).where(DistributionRequest.requester_id == user_id).order_by(DistributionRequest.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (params.page - 1) * params.page_size
    rows = (await db.execute(query.offset(offset).limit(params.page_size))).scalars().all()

    items = []
    for r in rows:
        # 중간 테이블에서 dataset_ids 조회 (없으면 deprecated JSONB fallback)
        ds_rows = (await db.execute(
            select(DistributionRequestDataset.dataset_id).where(DistributionRequestDataset.request_id == r.id)
        )).scalars().all()
        if ds_rows:
            ds_ids = [str(d) for d in ds_rows]
        else:
            ds_ids = json.loads(r.dataset_ids) if r.dataset_ids else []

        items.append(DistRequestResponse(
            id=r.id, request_type=r.request_type, requested_format=r.requested_format,
            purpose=r.purpose, status=r.status, dataset_ids=ds_ids,
            created_at=r.created_at, approved_at=r.approved_at,
        ))

    return PageResponse(items=items, total=total, page=params.page, page_size=params.page_size,
                        total_pages=math.ceil(total / params.page_size) if params.page_size else 0)


async def get_user_downloads(db: AsyncSession, user_id, params: PageRequest) -> PageResponse:
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


async def generate_download(db: AsyncSession, dataset_id, fmt: str, user_id) -> tuple[str, bytes, str]:
    """데이터셋 다운로드 파일 생성 (샘플 데이터 기반)"""
    ds = (await db.execute(select(CatalogDataset).where(CatalogDataset.id == dataset_id))).scalar_one_or_none()
    if not ds:
        return None, None, None

    cols = (await db.execute(
        select(CatalogColumn).where(CatalogColumn.dataset_id == dataset_id).order_by(CatalogColumn.sort_order)
    )).scalars().all()
    col_names = [c.column_name for c in cols] or ["col1", "col2", "col3"]

    # 샘플 데이터 생성
    rows_data = [[f"sample_{i}_{j}" for j in range(len(col_names))] for i in range(10)]

    if fmt == "JSON":
        content = json.dumps([dict(zip(col_names, row)) for row in rows_data], ensure_ascii=False, indent=2)
        return ds.dataset_name + ".json", content.encode("utf-8"), "application/json"
    else:  # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(col_names)
        writer.writerows(rows_data)
        return ds.dataset_name + ".csv", output.getvalue().encode("utf-8"), "text/csv"
