"""관리자 - 데이터저장 API (CRUD + 용량 모니터링)"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.storage import StorageHighspeedDb, StorageUnstructured, StorageZone
from app.schemas.admin import HighspeedDbResponse, StorageZoneResponse, UnstructuredResponse
from app.schemas.common import APIResponse

router = APIRouter()


# ══════ 저장소 존 CRUD ══════
@router.get("/zones", response_model=APIResponse[list[StorageZoneResponse]])
async def list_zones(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageZone).where(StorageZone.is_deleted == False))).scalars().all()
    return APIResponse(data=[StorageZoneResponse(
        id=r.id, zone_name=r.zone_name, zone_code=r.zone_code, zone_type=r.zone_type,
        storage_type=r.storage_type, max_capacity_gb=float(r.max_capacity_gb) if r.max_capacity_gb else None,
        used_capacity_gb=float(r.used_capacity_gb) if r.used_capacity_gb else None, status=r.status,
    ) for r in rows])


@router.post("/zones", response_model=APIResponse)
async def create_zone(zone_name: str, zone_code: str, zone_type: str = "RAW", storage_type: str = "POSTGRESQL",
                       max_capacity_gb: float = 100,
                       db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    z = StorageZone(id=uuid.uuid4(), zone_name=zone_name, zone_code=zone_code, zone_type=zone_type,
                     storage_type=storage_type, max_capacity_gb=max_capacity_gb, used_capacity_gb=0,
                     status="ACTIVE", created_by=user.id)
    db.add(z)
    return APIResponse(message="저장소 존이 등록되었습니다")


@router.delete("/zones/{zone_id}", response_model=APIResponse)
async def delete_zone(zone_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    z = (await db.execute(select(StorageZone).where(StorageZone.id == uuid.UUID(zone_id)))).scalar_one_or_none()
    if not z:
        raise HTTPException(status_code=404)
    z.is_deleted = True
    return APIResponse(message="저장소 존이 삭제되었습니다")


# ══════ 고속 DB CRUD ══════
@router.get("/highspeed", response_model=APIResponse[list[HighspeedDbResponse]])
async def list_highspeed(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageHighspeedDb).where(StorageHighspeedDb.is_deleted == False))).scalars().all()
    return APIResponse(data=[HighspeedDbResponse(
        id=r.id, db_name=r.db_name, db_type=r.db_type, purpose=r.purpose,
        max_memory_gb=float(r.max_memory_gb) if r.max_memory_gb else None, status=r.status,
    ) for r in rows])


@router.post("/highspeed", response_model=APIResponse)
async def create_highspeed(db_name: str, db_type: str = "REDIS", purpose: str = "CACHE",
                            max_memory_gb: float = 16,
                            db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    h = StorageHighspeedDb(id=uuid.uuid4(), db_name=db_name, db_type=db_type, purpose=purpose,
                            max_memory_gb=max_memory_gb, status="ACTIVE", created_by=user.id)
    db.add(h)
    return APIResponse(message="고속 DB가 등록되었습니다")


@router.delete("/highspeed/{db_id}", response_model=APIResponse)
async def delete_highspeed(db_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    h = (await db.execute(select(StorageHighspeedDb).where(StorageHighspeedDb.id == uuid.UUID(db_id)))).scalar_one_or_none()
    if not h:
        raise HTTPException(status_code=404)
    h.is_deleted = True
    return APIResponse(message="고속 DB가 삭제되었습니다")


# ══════ 비정형 저장소 CRUD ══════
@router.get("/unstructured", response_model=APIResponse[list[UnstructuredResponse]])
async def list_unstructured(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageUnstructured).where(StorageUnstructured.is_deleted == False))).scalars().all()
    return APIResponse(data=[UnstructuredResponse(
        id=r.id, storage_name=r.storage_name, storage_type=r.storage_type, bucket_name=r.bucket_name,
        total_capacity_gb=float(r.total_capacity_gb) if r.total_capacity_gb else None,
        used_capacity_gb=float(r.used_capacity_gb) if r.used_capacity_gb else None, status=r.status,
    ) for r in rows])


@router.post("/unstructured", response_model=APIResponse)
async def create_unstructured(storage_name: str, storage_type: str = "S3", bucket_name: str = "",
                               total_capacity_gb: float = 500,
                               db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    u = StorageUnstructured(id=uuid.uuid4(), storage_name=storage_name, storage_type=storage_type,
                             bucket_name=bucket_name, total_capacity_gb=total_capacity_gb, used_capacity_gb=0,
                             status="ACTIVE", created_by=user.id)
    db.add(u)
    return APIResponse(message="비정형 저장소가 등록되었습니다")


@router.delete("/unstructured/{storage_id}", response_model=APIResponse)
async def delete_unstructured(storage_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    u = (await db.execute(select(StorageUnstructured).where(StorageUnstructured.id == uuid.UUID(storage_id)))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404)
    u.is_deleted = True
    return APIResponse(message="비정형 저장소가 삭제되었습니다")


# ══════ 전체 용량 요약 ══════
@router.get("/summary", response_model=APIResponse)
async def storage_summary(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    zones = (await db.execute(select(StorageZone).where(StorageZone.is_deleted == False))).scalars().all()
    total_cap = sum(float(z.max_capacity_gb or 0) for z in zones)
    total_used = sum(float(z.used_capacity_gb or 0) for z in zones)

    highspeed_cnt = (await db.execute(select(func.count()).where(StorageHighspeedDb.is_deleted == False))).scalar() or 0
    unstructured_cnt = (await db.execute(select(func.count()).where(StorageUnstructured.is_deleted == False))).scalar() or 0

    return APIResponse(data={
        "zone_count": len(zones),
        "total_capacity_gb": round(total_cap, 1),
        "total_used_gb": round(total_used, 1),
        "usage_pct": round(total_used / total_cap * 100, 1) if total_cap > 0 else 0,
        "highspeed_count": highspeed_cnt,
        "unstructured_count": unstructured_cnt,
    })
