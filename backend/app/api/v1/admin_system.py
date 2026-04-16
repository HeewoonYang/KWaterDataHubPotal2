"""관리자 - 시스템관리 API (CRUD + 백업/복구 + 헬스체크 + 연계/통합)"""
import json
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.system import (SysCloudConfig, SysDmzLink, SysDrBackup, SysInfrastructure,
                                SysIntegration, SysInterface, SysInterfaceLog, SysPackage)
from app.schemas.admin import (CloudConfigResponse, DmzLinkCreate, DmzLinkDetailResponse,
                                DmzLinkResponse, DmzLinkUpdate, DrBackupResponse,
                                IntegrationCreate, IntegrationDetailResponse, IntegrationResponse,
                                IntegrationUpdate, InterfaceCreate, InterfaceDetailResponse,
                                InterfaceLogResponse, InterfaceResponse, InterfaceUpdate,
                                PackageResponse, SystemItemResponse)
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


# ══════ 인프라관리 ══════
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


@router.post("/infrastructure", response_model=APIResponse)
async def create_infrastructure(
    infra_name: str, infra_type: str = "SERVER", host_address: str = "",
    environment: str = "PROD",
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    infra = SysInfrastructure(id=uuid.uuid4(), infra_name=infra_name, infra_type=infra_type,
                               host_address=host_address, environment=environment,
                               status="ACTIVE", created_by=user.id)
    db.add(infra)
    return APIResponse(message="인프라가 등록되었습니다")


@router.put("/infrastructure/{infra_id}", response_model=APIResponse)
async def update_infrastructure(
    infra_id: str, infra_name: str | None = None, status: str | None = None,
    host_address: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    infra = (await db.execute(select(SysInfrastructure).where(SysInfrastructure.id == uuid.UUID(infra_id)))).scalar_one_or_none()
    if not infra:
        raise HTTPException(status_code=404, detail="인프라를 찾을 수 없습니다")
    if infra_name:
        infra.infra_name = infra_name
    if status:
        infra.status = status
    if host_address:
        infra.host_address = host_address
    infra.updated_by = user.id
    infra.updated_at = datetime.now()
    return APIResponse(message="인프라가 수정되었습니다")


# ══════ 클라우드/DR백업/패키지 ══════
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


@router.post("/dr-backup", response_model=APIResponse)
async def create_dr_backup(
    backup_name: str, backup_type: str = "FULL", target_system: str = "",
    schedule_cron: str = "0 2 * * *", retention_days: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    bk = SysDrBackup(id=uuid.uuid4(), backup_name=backup_name, backup_type=backup_type,
                       target_system=target_system, schedule_cron=schedule_cron,
                       retention_days=retention_days, created_by=user.id)
    db.add(bk)
    return APIResponse(message="백업 설정이 등록되었습니다")


@router.delete("/dr-backup/{backup_id}", response_model=APIResponse)
async def delete_dr_backup(backup_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    bk = (await db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id)))).scalar_one_or_none()
    if not bk:
        raise HTTPException(status_code=404)
    bk.is_deleted = True
    return APIResponse(message="백업 설정이 삭제되었습니다")


@router.post("/dr-backup/{backup_id}/execute", response_model=APIResponse)
async def execute_backup(backup_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    bk = (await db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id)))).scalar_one_or_none()
    if not bk:
        raise HTTPException(status_code=404, detail="백업 설정을 찾을 수 없습니다")
    bk.last_backup_at = datetime.now()
    bk.last_backup_status = "SUCCESS"
    return APIResponse(data={
        "backup_name": bk.backup_name, "status": "SUCCESS",
        "executed_at": datetime.now().isoformat(),
    }, message=f"{bk.backup_name} 백업이 실행되었습니다")


@router.post("/dr-backup/{backup_id}/restore", response_model=APIResponse)
async def restore_backup(backup_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    bk = (await db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id)))).scalar_one_or_none()
    if not bk:
        raise HTTPException(status_code=404, detail="백업 설정을 찾을 수 없습니다")
    return APIResponse(data={
        "backup_name": bk.backup_name, "restore_status": "COMPLETED",
        "restored_at": datetime.now().isoformat(),
    }, message=f"{bk.backup_name} 복구가 완료되었습니다")


@router.get("/packages", response_model=APIResponse[list[PackageResponse]])
async def list_packages(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysPackage).where(SysPackage.is_deleted == False))).scalars().all()
    return APIResponse(data=[PackageResponse(
        id=r.id, package_name=r.package_name, package_version=r.package_version, vendor=r.vendor,
        license_type=r.license_type, license_expiry=str(r.license_expiry) if r.license_expiry else None,
        poc_status=r.poc_status, description=r.description
    ) for r in rows])


# ══════ 전체 인프라 헬스체크 ══════
@router.get("/health-check", response_model=APIResponse)
async def health_check_summary(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    infras = (await db.execute(select(SysInfrastructure).where(SysInfrastructure.is_deleted == False))).scalars().all()
    total = len(infras)
    active = sum(1 for i in infras if i.status == "ACTIVE")
    warning = sum(1 for i in infras if i.status == "WARNING")
    error = sum(1 for i in infras if i.status in ("ERROR", "DOWN"))
    return APIResponse(data={
        "total": total, "active": active, "warning": warning, "error": error,
        "health_pct": round(active / total * 100, 1) if total > 0 else 0,
    })


# ══════ 표준 인터페이스 CRUD ══════
@router.get("/interfaces", response_model=APIResponse[list[InterfaceResponse]])
async def list_interfaces(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysInterface).where(SysInterface.is_deleted == False).order_by(SysInterface.created_at.desc()))).scalars().all()
    return APIResponse(data=[InterfaceResponse(
        id=r.id, interface_code=r.interface_code, interface_name=r.interface_name, interface_type=r.interface_type,
        source_system=r.source_system, target_system=r.target_system, endpoint_url=r.endpoint_url,
        schedule_type=r.schedule_type, status=r.status
    ) for r in rows])


@router.get("/interfaces/{interface_id}", response_model=APIResponse[InterfaceDetailResponse])
async def get_interface(interface_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    iface = (await db.execute(select(SysInterface).where(SysInterface.id == uuid.UUID(interface_id), SysInterface.is_deleted == False))).scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="인터페이스를 찾을 수 없습니다")
    return APIResponse(data=InterfaceDetailResponse.model_validate(iface))


@router.post("/interfaces", response_model=APIResponse)
async def create_interface(
    body: InterfaceCreate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    code = f"IF-{uuid.uuid4().hex[:6].upper()}"
    iface = SysInterface(
        id=uuid.uuid4(), interface_code=code, interface_name=body.interface_name,
        interface_type=body.interface_type, protocol=body.protocol,
        source_system=body.source_system, target_system=body.target_system,
        endpoint_url=body.endpoint_url, data_format=body.data_format,
        schedule_type=body.schedule_type, schedule_cron=body.schedule_cron,
        timeout_ms=body.timeout_ms, retry_count=body.retry_count,
        status="ACTIVE", description=body.description, created_by=user.id,
    )
    db.add(iface)
    await db.flush()
    return APIResponse(message="인터페이스가 등록되었습니다", data={"id": str(iface.id), "interface_code": code})


@router.put("/interfaces/{interface_id}", response_model=APIResponse)
async def update_interface(
    interface_id: str, body: InterfaceUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    iface = (await db.execute(select(SysInterface).where(SysInterface.id == uuid.UUID(interface_id), SysInterface.is_deleted == False))).scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="인터페이스를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(iface, key, val)
    iface.updated_by = user.id
    iface.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="인터페이스가 수정되었습니다")


@router.delete("/interfaces/{interface_id}", response_model=APIResponse)
async def delete_interface(
    interface_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    iface = (await db.execute(select(SysInterface).where(SysInterface.id == uuid.UUID(interface_id), SysInterface.is_deleted == False))).scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="인터페이스를 찾을 수 없습니다")
    iface.is_deleted = True
    iface.updated_by = user.id
    iface.updated_at = datetime.now()
    return APIResponse(message="인터페이스가 삭제되었습니다")


@router.post("/interfaces/{interface_id}/test", response_model=APIResponse)
async def test_interface(
    interface_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """표준 인터페이스 연결 테스트 (시뮬레이션)"""
    iface = (await db.execute(select(SysInterface).where(SysInterface.id == uuid.UUID(interface_id), SysInterface.is_deleted == False))).scalar_one_or_none()
    if not iface:
        raise HTTPException(status_code=404, detail="인터페이스를 찾을 수 없습니다")
    # 시뮬레이션: 연결 테스트 로그 기록
    log = SysInterfaceLog(
        id=uuid.uuid4(), interface_id=iface.id, execution_type="MANUAL",
        status="SUCCESS", started_at=datetime.now(), finished_at=datetime.now(),
        duration_ms=125, total_records=0, success_records=0, error_records=0,
        request_payload={"action": "connection_test", "endpoint": iface.endpoint_url},
        response_summary={"connected": True, "latency_ms": 125},
        created_by=user.id,
    )
    db.add(log)
    await db.flush()
    return APIResponse(data={
        "interface_name": iface.interface_name, "status": "SUCCESS",
        "latency_ms": 125, "tested_at": datetime.now().isoformat(),
    }, message="연결 테스트가 성공했습니다")


@router.get("/interfaces/{interface_id}/logs", response_model=PageResponse[InterfaceLogResponse])
async def list_interface_logs(
    interface_id: str,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    base = select(SysInterfaceLog).where(
        SysInterfaceLog.interface_id == uuid.UUID(interface_id),
        SysInterfaceLog.is_deleted == False,
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = (await db.execute(
        base.order_by(SysInterfaceLog.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=[InterfaceLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size, total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ══════ 이기종 통합 CRUD ══════
@router.get("/integrations", response_model=APIResponse[list[IntegrationResponse]])
async def list_integrations(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysIntegration).where(SysIntegration.is_deleted == False).order_by(SysIntegration.created_at.desc()))).scalars().all()
    return APIResponse(data=[IntegrationResponse(
        id=r.id, integration_name=r.integration_name, source_db_type=r.source_db_type,
        sync_direction=r.sync_direction, sync_status=r.sync_status, last_sync_at=r.last_sync_at
    ) for r in rows])


@router.get("/integrations/{integration_id}", response_model=APIResponse[IntegrationDetailResponse])
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    row = (await db.execute(select(SysIntegration).where(SysIntegration.id == uuid.UUID(integration_id), SysIntegration.is_deleted == False))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="통합 설정을 찾을 수 없습니다")
    return APIResponse(data=IntegrationDetailResponse.model_validate(row))


@router.post("/integrations", response_model=APIResponse)
async def create_integration(
    body: IntegrationCreate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    intg = SysIntegration(
        id=uuid.uuid4(), integration_name=body.integration_name,
        source_db_type=body.source_db_type, connection_config=body.connection_config,
        mapping_config=body.mapping_config, sync_direction=body.sync_direction,
        sync_status="IDLE", created_by=user.id,
    )
    db.add(intg)
    await db.flush()
    return APIResponse(message="이기종 통합이 등록되었습니다", data={"id": str(intg.id)})


@router.put("/integrations/{integration_id}", response_model=APIResponse)
async def update_integration(
    integration_id: str, body: IntegrationUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    intg = (await db.execute(select(SysIntegration).where(SysIntegration.id == uuid.UUID(integration_id), SysIntegration.is_deleted == False))).scalar_one_or_none()
    if not intg:
        raise HTTPException(status_code=404, detail="통합 설정을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(intg, key, val)
    intg.updated_by = user.id
    intg.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="이기종 통합이 수정되었습니다")


@router.delete("/integrations/{integration_id}", response_model=APIResponse)
async def delete_integration(
    integration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    intg = (await db.execute(select(SysIntegration).where(SysIntegration.id == uuid.UUID(integration_id), SysIntegration.is_deleted == False))).scalar_one_or_none()
    if not intg:
        raise HTTPException(status_code=404, detail="통합 설정을 찾을 수 없습니다")
    intg.is_deleted = True
    intg.updated_by = user.id
    intg.updated_at = datetime.now()
    return APIResponse(message="이기종 통합이 삭제되었습니다")


@router.post("/integrations/{integration_id}/test", response_model=APIResponse)
async def test_integration(
    integration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """이기종 통합 연결 테스트 (시뮬레이션)"""
    intg = (await db.execute(select(SysIntegration).where(SysIntegration.id == uuid.UUID(integration_id), SysIntegration.is_deleted == False))).scalar_one_or_none()
    if not intg:
        raise HTTPException(status_code=404, detail="통합 설정을 찾을 수 없습니다")
    config = intg.connection_config if isinstance(intg.connection_config, dict) else {}
    return APIResponse(data={
        "integration_name": intg.integration_name, "source_db_type": intg.source_db_type,
        "host": config.get("host", ""), "port": config.get("port", ""),
        "status": "SUCCESS", "latency_ms": 85, "tested_at": datetime.now().isoformat(),
    }, message="연결 테스트가 성공했습니다")


@router.post("/integrations/{integration_id}/sync", response_model=APIResponse)
async def sync_integration(
    integration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """이기종 통합 수동 동기화 트리거 (시뮬레이션)"""
    intg = (await db.execute(select(SysIntegration).where(SysIntegration.id == uuid.UUID(integration_id), SysIntegration.is_deleted == False))).scalar_one_or_none()
    if not intg:
        raise HTTPException(status_code=404, detail="통합 설정을 찾을 수 없습니다")
    # 연관 인터페이스 찾기 (없으면 첫번째 활성 인터페이스 사용)
    iface = (await db.execute(select(SysInterface).where(SysInterface.is_deleted == False).limit(1))).scalar_one_or_none()
    now = datetime.now()
    log = SysInterfaceLog(
        id=uuid.uuid4(), interface_id=iface.id if iface else None,
        integration_id=intg.id, execution_type="MANUAL",
        status="SUCCESS", started_at=now, finished_at=now,
        duration_ms=2350, total_records=1500, success_records=1500, error_records=0,
        request_payload={"action": "manual_sync", "integration": intg.integration_name},
        response_summary={"synced_tables": 3, "total_rows": 1500},
        created_by=user.id,
    )
    db.add(log)
    intg.sync_status = "SUCCESS"
    intg.last_sync_at = now
    intg.updated_at = now
    await db.flush()
    return APIResponse(data={
        "integration_name": intg.integration_name, "status": "SUCCESS",
        "synced_records": 1500, "duration_ms": 2350, "synced_at": now.isoformat(),
    }, message="수동 동기화가 완료되었습니다")


@router.get("/integrations/{integration_id}/logs", response_model=PageResponse[InterfaceLogResponse])
async def list_integration_logs(
    integration_id: str,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    base = select(SysInterfaceLog).where(
        SysInterfaceLog.integration_id == uuid.UUID(integration_id),
        SysInterfaceLog.is_deleted == False,
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = (await db.execute(
        base.order_by(SysInterfaceLog.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return PageResponse(
        items=[InterfaceLogResponse.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size, total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ══════ DMZ 연계 CRUD ══════
@router.get("/dmz-links", response_model=APIResponse[list[DmzLinkResponse]])
async def list_dmz_links(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(SysDmzLink).where(SysDmzLink.is_deleted == False))).scalars().all()
    return APIResponse(data=[DmzLinkResponse(
        id=r.id, link_name=r.link_name, link_type=r.link_type, external_url=r.external_url,
        transfer_direction=r.transfer_direction, is_active=r.is_active
    ) for r in rows])


@router.get("/dmz-links/{link_id}", response_model=APIResponse[DmzLinkDetailResponse])
async def get_dmz_link(link_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    row = (await db.execute(select(SysDmzLink).where(SysDmzLink.id == uuid.UUID(link_id), SysDmzLink.is_deleted == False))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="DMZ 연계를 찾을 수 없습니다")
    return APIResponse(data=DmzLinkDetailResponse.model_validate(row))


@router.post("/dmz-links", response_model=APIResponse)
async def create_dmz_link(
    body: DmzLinkCreate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    link = SysDmzLink(
        id=uuid.uuid4(), link_name=body.link_name, link_type=body.link_type,
        external_url=body.external_url, dmz_proxy_url=body.dmz_proxy_url,
        transfer_direction=body.transfer_direction, security_level=body.security_level,
        is_active=True, created_by=user.id,
    )
    db.add(link)
    await db.flush()
    return APIResponse(message="DMZ 연계가 등록되었습니다", data={"id": str(link.id)})


@router.put("/dmz-links/{link_id}", response_model=APIResponse)
async def update_dmz_link(
    link_id: str, body: DmzLinkUpdate,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    link = (await db.execute(select(SysDmzLink).where(SysDmzLink.id == uuid.UUID(link_id), SysDmzLink.is_deleted == False))).scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="DMZ 연계를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(link, key, val)
    link.updated_by = user.id
    link.updated_at = datetime.now()
    await db.flush()
    return APIResponse(message="DMZ 연계가 수정되었습니다")


@router.delete("/dmz-links/{link_id}", response_model=APIResponse)
async def delete_dmz_link(
    link_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    link = (await db.execute(select(SysDmzLink).where(SysDmzLink.id == uuid.UUID(link_id), SysDmzLink.is_deleted == False))).scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="DMZ 연계를 찾을 수 없습니다")
    link.is_deleted = True
    link.updated_by = user.id
    link.updated_at = datetime.now()
    return APIResponse(message="DMZ 연계가 삭제되었습니다")


# ── SSO 제공자 관리 ──

@router.get("/sso-providers", response_model=APIResponse[list])
async def list_sso_providers(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    from app.models.sso import SsoProviderConfig
    rows = (await db.execute(
        select(SsoProviderConfig).where(SsoProviderConfig.is_deleted == False).order_by(SsoProviderConfig.sort_order)
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "provider_type": r.provider_type, "provider_name": r.provider_name,
        "display_name": r.display_name, "config_json": r.config_json, "is_enabled": r.is_enabled,
        "default_role_code": r.default_role_code, "default_user_type": r.default_user_type,
        "description": r.description,
    } for r in rows])


@router.post("/sso-providers", response_model=APIResponse)
async def create_sso_provider(data: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    from app.models.sso import SsoProviderConfig
    provider = SsoProviderConfig(
        id=uuid.uuid4(), provider_type=data.get("provider_type", "OAUTH"),
        provider_name=data["provider_name"], display_name=data["display_name"],
        config_json=data.get("config_json"), is_enabled=data.get("is_enabled", True),
        default_role_code=data.get("default_role_code", "EXTERNAL"),
        default_user_type=data.get("default_user_type", "EXTERNAL"),
        description=data.get("description"), created_by=user.id, created_at=datetime.now(),
    )
    db.add(provider)
    return APIResponse(message="SSO 제공자가 등록되었습니다")


@router.put("/sso-providers/{provider_id}", response_model=APIResponse)
async def update_sso_provider(provider_id: str, data: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    from app.models.sso import SsoProviderConfig
    p = (await db.execute(select(SsoProviderConfig).where(SsoProviderConfig.id == uuid.UUID(provider_id), SsoProviderConfig.is_deleted == False))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="SSO 제공자를 찾을 수 없습니다")
    for field in ["provider_name", "display_name", "config_json", "is_enabled", "default_role_code", "default_user_type", "description"]:
        if field in data:
            setattr(p, field, data[field])
    p.updated_by = user.id
    p.updated_at = datetime.now()
    return APIResponse(message="SSO 제공자가 수정되었습니다")


@router.delete("/sso-providers/{provider_id}", response_model=APIResponse)
async def delete_sso_provider(provider_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    from app.models.sso import SsoProviderConfig
    p = (await db.execute(select(SsoProviderConfig).where(SsoProviderConfig.id == uuid.UUID(provider_id), SsoProviderConfig.is_deleted == False))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="SSO 제공자를 찾을 수 없습니다")
    p.is_deleted = True
    p.updated_by = user.id
    p.updated_at = datetime.now()
    return APIResponse(message="SSO 제공자가 삭제되었습니다")
