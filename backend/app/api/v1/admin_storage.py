"""관리자 - 데이터저장 API"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.storage import StorageHighspeedDb, StorageUnstructured, StorageZone
from app.schemas.admin import HighspeedDbResponse, StorageZoneResponse, UnstructuredResponse
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/zones", response_model=APIResponse[list[StorageZoneResponse]])
async def list_zones(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageZone).where(StorageZone.is_deleted == False))).scalars().all()
    return APIResponse(data=[StorageZoneResponse(
        id=r.id, zone_name=r.zone_name, zone_code=r.zone_code, zone_type=r.zone_type,
        storage_type=r.storage_type, max_capacity_gb=float(r.max_capacity_gb) if r.max_capacity_gb else None,
        used_capacity_gb=float(r.used_capacity_gb) if r.used_capacity_gb else None, status=r.status,
    ) for r in rows])


@router.get("/highspeed", response_model=APIResponse[list[HighspeedDbResponse]])
async def list_highspeed(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageHighspeedDb).where(StorageHighspeedDb.is_deleted == False))).scalars().all()
    return APIResponse(data=[HighspeedDbResponse(
        id=r.id, db_name=r.db_name, db_type=r.db_type, purpose=r.purpose,
        max_memory_gb=float(r.max_memory_gb) if r.max_memory_gb else None, status=r.status,
    ) for r in rows])


@router.get("/unstructured", response_model=APIResponse[list[UnstructuredResponse]])
async def list_unstructured(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(StorageUnstructured).where(StorageUnstructured.is_deleted == False))).scalars().all()
    return APIResponse(data=[UnstructuredResponse(
        id=r.id, storage_name=r.storage_name, storage_type=r.storage_type, bucket_name=r.bucket_name,
        total_capacity_gb=float(r.total_capacity_gb) if r.total_capacity_gb else None,
        used_capacity_gb=float(r.used_capacity_gb) if r.used_capacity_gb else None, status=r.status,
    ) for r in rows])
