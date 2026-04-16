"""유통 서비스"""
import csv
import hashlib
import io
import json
import math
import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import CatalogColumn, CatalogDataset
from app.models.classification import DataClassification, DataGrade
from app.models.distribution import (
    DistributionApiKey, DistributionApiUsageLog,
    DistributionDataset, DistributionDownloadLog, DistributionRequest, DistributionRequestDataset,
)
from app.schemas.common import PageRequest, PageResponse
from app.config import settings
from app.schemas.portal import ApiKeyResponse, DistDatasetListItem, DistDownloadItem, DistRequestCreate, DistRequestResponse


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
    # L3 공개 데이터 및 API 접근은 자동 승인
    if data.requested_format == "API":
        data.request_type = "API_ACCESS"
    auto_approve = data.request_type == "DOWNLOAD" or data.requested_format == "API"
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
    # dataset_ids는 catalog_dataset.id일 수 있으므로, distribution_dataset.id로 매핑 시도
    for ds_id in data.dataset_ids:
        # 먼저 distribution_dataset에서 직접 찾기
        dist_ds = (await db.execute(
            select(DistributionDataset).where(DistributionDataset.id == ds_id)
        )).scalar_one_or_none()

        if not dist_ds:
            # catalog_dataset.id → distribution_dataset 매핑
            dist_ds = (await db.execute(
                select(DistributionDataset).where(DistributionDataset.dataset_id == ds_id)
            )).scalar_one_or_none()

        if dist_ds:
            db.add(DistributionRequestDataset(
                id=uuid.uuid4(), request_id=req_id, dataset_id=dist_ds.id,
            ))
        # 매핑 안 되면 건너뛰기 (deprecated JSONB에는 이미 저장됨)
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

        # 첫 번째 데이터셋의 한글명/영문명 조회
        ds_name = None
        ds_name_kr = None
        if ds_ids:
            first_id = ds_ids[0]
            # distribution_dataset → catalog_dataset 조인으로 한글명 조회
            cat_row = (await db.execute(
                select(CatalogDataset.dataset_name, CatalogDataset.dataset_name_kr)
                .join(DistributionDataset, DistributionDataset.dataset_id == CatalogDataset.id)
                .where(DistributionDataset.id == first_id)
            )).first()
            if not cat_row:
                # catalog_dataset.id로 직접 조회
                cat_row = (await db.execute(
                    select(CatalogDataset.dataset_name, CatalogDataset.dataset_name_kr)
                    .where(CatalogDataset.id == first_id)
                )).first()
            if cat_row:
                ds_name = cat_row[0]
                ds_name_kr = cat_row[1]

        items.append(DistRequestResponse(
            id=r.id, request_type=r.request_type, requested_format=r.requested_format,
            purpose=r.purpose, status=r.status, dataset_ids=ds_ids,
            dataset_name=ds_name, dataset_name_kr=ds_name_kr,
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
    """데이터셋 다운로드 파일 생성 + 다운로드 이력 기록
    dataset_id: catalog_dataset.id 또는 distribution_dataset.id 모두 허용
    """
    ds = (await db.execute(select(CatalogDataset).where(CatalogDataset.id == dataset_id))).scalar_one_or_none()
    if not ds:
        # distribution_dataset.id로 시도 → catalog_dataset.id 매핑
        dist_ds = (await db.execute(
            select(DistributionDataset).where(DistributionDataset.id == dataset_id)
        )).scalar_one_or_none()
        if dist_ds:
            dataset_id = dist_ds.dataset_id
            ds = (await db.execute(select(CatalogDataset).where(CatalogDataset.id == dataset_id))).scalar_one_or_none()
    if not ds:
        return None, None, None

    cols = (await db.execute(
        select(CatalogColumn).where(CatalogColumn.dataset_id == dataset_id).order_by(CatalogColumn.sort_order)
    )).scalars().all()
    col_names = [c.column_name for c in cols] or ["col1", "col2", "col3"]

    # 시나리오 데이터가 있으면 실제 데이터 사용, 없으면 샘플
    rows_data = []
    scenario_tables = {
        'smart_metering_realtime': 'scenario_smart_metering',
        'rwis_road_weather': 'scenario_rwis',
    }
    scenario_table = scenario_tables.get(ds.dataset_name)
    if scenario_table:
        try:
            from sqlalchemy import text
            result = await db.execute(text(f"SELECT * FROM {scenario_table} ORDER BY id DESC LIMIT 100"))
            db_rows = result.fetchall()
            if db_rows:
                col_names = list(result.keys())
                rows_data = [list(row) for row in db_rows]
        except Exception:
            pass  # fallback to sample

    if not rows_data:
        rows_data = [[f"sample_{i}_{j}" for j in range(len(col_names))] for i in range(10)]

    if fmt == "JSON":
        def _serialize(obj):
            """JSON 시리얼라이즈 헬퍼 (datetime, Decimal 지원)"""
            import decimal
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            return str(obj)
        content = json.dumps([dict(zip(col_names, [_serialize(v) for v in row])) for row in rows_data], ensure_ascii=False, indent=2)
        filename = ds.dataset_name + ".json"
        media_type = "application/json"
    else:  # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(col_names)
        writer.writerows(rows_data)
        content = output.getvalue()
        filename = ds.dataset_name + ".csv"
        media_type = "text/csv"

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content

    # 다운로드 이력 기록
    # distribution_dataset에서 해당 dataset_id에 매핑된 유통 데이터셋 찾기
    dist_ds = (await db.execute(
        select(DistributionDataset).where(DistributionDataset.dataset_id == dataset_id)
    )).scalar_one_or_none()

    log = DistributionDownloadLog(
        id=uuid.uuid4(),
        dataset_id=dist_ds.id if dist_ds else dataset_id,
        user_id=user_id,
        download_format=fmt,
        row_count=len(rows_data),
        file_size_bytes=len(content_bytes),
        downloaded_at=datetime.now(),
    )
    db.add(log)

    return filename, content_bytes, media_type


# ═══════════════════════════════════════════════════
# API 키 관리
# ═══════════════════════════════════════════════════

async def issue_api_key(db: AsyncSession, user_id, request_id) -> ApiKeyResponse:
    """승인된 API_ACCESS 요청에 API 키 발급"""
    req = (await db.execute(
        select(DistributionRequest).where(
            DistributionRequest.id == request_id,
            DistributionRequest.requester_id == user_id,
        )
    )).scalar_one_or_none()
    if not req:
        raise ValueError("요청을 찾을 수 없습니다.")
    if req.status != "APPROVED":
        raise ValueError("승인된 요청만 API 키를 발급할 수 있습니다.")

    # 기존 활성 키 확인
    existing = (await db.execute(
        select(DistributionApiKey).where(
            DistributionApiKey.created_by == str(user_id),
            DistributionApiKey.name == f"req-{request_id}",
            DistributionApiKey.is_active == True,
            DistributionApiKey.is_deleted == False,
        )
    )).scalar_one_or_none()
    if existing:
        return ApiKeyResponse(
            id=existing.id, api_key_prefix=existing.api_key_prefix or "",
            name=existing.name or "", endpoint=settings.DISTRIBUTION_API_ENDPOINT,
            rate_limit_per_min=existing.rate_limit_per_min or 60,
            expires_at=existing.expires_at, issued_at=existing.created_at,
            last_used_at=existing.last_used_at, is_active=existing.is_active,
        )

    raw_key = f"kw_live_{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:14]
    now = datetime.now()
    expires = now + timedelta(days=365)

    api_key = DistributionApiKey(
        id=uuid.uuid4(), user_id=user_id, api_key_hash=key_hash,
        api_key_prefix=key_prefix, name=f"req-{request_id}",
        rate_limit_per_min=60, expires_at=expires, is_active=True,
        created_by=str(user_id),
    )
    db.add(api_key)
    await db.flush()

    return ApiKeyResponse(
        id=api_key.id, api_key=raw_key, api_key_prefix=key_prefix,
        name=api_key.name, endpoint=settings.DISTRIBUTION_API_ENDPOINT,
        rate_limit_per_min=60, expires_at=expires, issued_at=now, is_active=True,
    )


async def get_api_key_info(db: AsyncSession, user_id, request_id) -> ApiKeyResponse | None:
    """API 키 정보 조회 (마스킹)"""
    key = (await db.execute(
        select(DistributionApiKey).where(
            DistributionApiKey.created_by == str(user_id),
            DistributionApiKey.name == f"req-{request_id}",
            DistributionApiKey.is_deleted == False,
        ).order_by(DistributionApiKey.created_at.desc())
    )).scalars().first()
    if not key:
        return None

    total_calls = (await db.execute(
        select(func.count()).where(DistributionApiUsageLog.api_key_id == key.id)
    )).scalar() or 0

    return ApiKeyResponse(
        id=key.id, api_key_prefix=key.api_key_prefix or "",
        name=key.name or "", endpoint=settings.DISTRIBUTION_API_ENDPOINT,
        rate_limit_per_min=key.rate_limit_per_min or 60,
        expires_at=key.expires_at, issued_at=key.created_at,
        last_used_at=key.last_used_at, total_calls=total_calls, is_active=key.is_active,
    )


async def regenerate_api_key(db: AsyncSession, user_id, request_id) -> ApiKeyResponse:
    """API 키 재발급"""
    old_key = (await db.execute(
        select(DistributionApiKey).where(
            DistributionApiKey.created_by == str(user_id),
            DistributionApiKey.name == f"req-{request_id}",
            DistributionApiKey.is_active == True,
            DistributionApiKey.is_deleted == False,
        )
    )).scalar_one_or_none()
    if old_key:
        old_key.is_active = False
        await db.flush()

    raw_key = f"kw_live_{secrets.token_hex(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:14]
    now = datetime.now()
    expires = now + timedelta(days=365)

    new_key = DistributionApiKey(
        id=uuid.uuid4(), user_id=user_id, api_key_hash=key_hash,
        api_key_prefix=key_prefix, name=f"req-{request_id}",
        rate_limit_per_min=60, expires_at=expires, is_active=True,
        created_by=str(user_id),
    )
    db.add(new_key)
    await db.flush()

    return ApiKeyResponse(
        id=new_key.id, api_key=raw_key, api_key_prefix=key_prefix,
        name=new_key.name, endpoint=settings.DISTRIBUTION_API_ENDPOINT,
        rate_limit_per_min=60, expires_at=expires, issued_at=now, is_active=True,
    )


async def revoke_api_key(db: AsyncSession, user_id, api_key_id) -> bool:
    """API 키 폐기"""
    key = (await db.execute(
        select(DistributionApiKey).where(
            DistributionApiKey.id == api_key_id,
            DistributionApiKey.created_by == str(user_id),
            DistributionApiKey.is_deleted == False,
        )
    )).scalar_one_or_none()
    if not key:
        return False
    key.is_active = False
    await db.flush()
    return True
