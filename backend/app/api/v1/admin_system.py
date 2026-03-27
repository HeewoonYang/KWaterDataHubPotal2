"""관리자 - 시스템관리 API"""
import json
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.system import (SysCloudConfig, SysDmzLink, SysDrBackup, SysInfrastructure,
                                SysIntegration, SysInterface, SysPackage)
from app.schemas.admin import (CloudConfigResponse, DmzLinkResponse, DrBackupResponse,
                                IntegrationResponse, InterfaceResponse, PackageResponse, SystemItemResponse)
from app.schemas.common import APIResponse, PageRequest, PageResponse

router = APIRouter()


@router.get("/infrastructure", response_model=APIResponse[list[SystemItemResponse]])
async def list_infrastructure(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysInfrastructure).where(SysInfrastructure.is_deleted == False).order_by(SysInfrastructure.infra_name))).scalars().all()
    items = []
    for r in rows:
        specs = r.specs if isinstance(r.specs, dict) else (json.loads(r.specs) if r.specs else {})
        items.append(SystemItemResponse(
            id=r.id, name=r.infra_name, type=r.infra_type, host=r.host_address, status=r.status,
            environment=r.environment, cpu=specs.get("cpu_usage", 0), memory=specs.get("memory_usage", 0),
            disk=specs.get("disk_usage", 0), last_check=r.last_health_check.strftime("%Y-%m-%d %H:%M") if r.last_health_check else None))
    return APIResponse(data=items)


@router.get("/cloud", response_model=APIResponse[list[CloudConfigResponse]])
async def list_cloud(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysCloudConfig).where(SysCloudConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[CloudConfigResponse(
        id=r.id, cloud_provider=r.cloud_provider, resource_type=r.resource_type, resource_name=r.resource_name,
        resource_id=r.resource_id, region=r.region, status=r.status, monthly_cost=float(r.monthly_cost) if r.monthly_cost else None
    ) for r in rows])


@router.get("/dr-backup", response_model=APIResponse[list[DrBackupResponse]])
async def list_dr_backup(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysDrBackup).where(SysDrBackup.is_deleted == False))).scalars().all()
    return APIResponse(data=[DrBackupResponse(
        id=r.id, backup_name=r.backup_name, backup_type=r.backup_type, target_system=r.target_system,
        schedule_cron=r.schedule_cron, retention_days=r.retention_days, last_backup_at=r.last_backup_at,
        last_backup_status=r.last_backup_status
    ) for r in rows])


@router.get("/packages", response_model=APIResponse[list[PackageResponse]])
async def list_packages(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysPackage).where(SysPackage.is_deleted == False))).scalars().all()
    return APIResponse(data=[PackageResponse(
        id=r.id, package_name=r.package_name, package_version=r.package_version, vendor=r.vendor,
        license_type=r.license_type, license_expiry=str(r.license_expiry) if r.license_expiry else None,
        poc_status=r.poc_status, description=r.description
    ) for r in rows])


@router.get("/interfaces", response_model=APIResponse[list[InterfaceResponse]])
async def list_interfaces(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysInterface).where(SysInterface.is_deleted == False))).scalars().all()
    return APIResponse(data=[InterfaceResponse(
        id=r.id, interface_code=r.interface_code, interface_name=r.interface_name, interface_type=r.interface_type,
        source_system=r.source_system, target_system=r.target_system, endpoint_url=r.endpoint_url,
        schedule_type=r.schedule_type, status=r.status
    ) for r in rows])


@router.get("/integrations", response_model=APIResponse[list[IntegrationResponse]])
async def list_integrations(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysIntegration).where(SysIntegration.is_deleted == False))).scalars().all()
    return APIResponse(data=[IntegrationResponse(
        id=r.id, integration_name=r.integration_name, source_db_type=r.source_db_type,
        sync_direction=r.sync_direction, sync_status=r.sync_status, last_sync_at=r.last_sync_at
    ) for r in rows])


@router.get("/dmz-links", response_model=APIResponse[list[DmzLinkResponse]])
async def list_dmz_links(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysDmzLink).where(SysDmzLink.is_deleted == False))).scalars().all()
    return APIResponse(data=[DmzLinkResponse(
        id=r.id, link_name=r.link_name, link_type=r.link_type, external_url=r.external_url,
        transfer_direction=r.transfer_direction, is_active=r.is_active
    ) for r in rows])
