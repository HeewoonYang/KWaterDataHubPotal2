"""관리자 - 데이터수집 API"""
import math
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.collection import (CollectionDataSource, CollectionDatasetConfig, CollectionExternalAgency,
                                    CollectionJob, CollectionMigration, CollectionSpatialConfig, CollectionStrategy)
from app.schemas.admin import (CollectionConfigResponse, CollectionJobResponse, DataSourceResponse,
                                ExternalAgencyResponse, MigrationResponse, SpatialConfigResponse, StrategyResponse)
from app.schemas.common import APIResponse, PageRequest, PageResponse

router = APIRouter()


@router.get("/strategies", response_model=APIResponse[list[StrategyResponse]])
async def list_strategies(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionStrategy).where(CollectionStrategy.is_deleted == False))).scalars().all()
    return APIResponse(data=[StrategyResponse(
        id=r.id, strategy_name=r.strategy_name, strategy_type=r.strategy_type,
        target_data_type=r.target_data_type, priority=r.priority, is_active=r.is_active,
    ) for r in rows])


@router.get("/data-sources", response_model=APIResponse[list[DataSourceResponse]])
async def list_data_sources(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.is_deleted == False))).scalars().all()
    return APIResponse(data=[DataSourceResponse(
        id=r.id, source_name=r.source_name, source_type=r.source_type, db_type=r.db_type,
        connection_host=r.connection_host, connection_port=r.connection_port, connection_db=r.connection_db,
        last_test_result=r.last_test_result, status=r.status,
    ) for r in rows])


@router.get("/dataset-configs", response_model=APIResponse[list[CollectionConfigResponse]])
async def list_dataset_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(CollectionDatasetConfig, CollectionDataSource.source_name)
        .outerjoin(CollectionDataSource, CollectionDatasetConfig.source_id == CollectionDataSource.id)
        .where(CollectionDatasetConfig.is_deleted == False)
    )).all()
    return APIResponse(data=[CollectionConfigResponse(
        id=r[0].id, dataset_name=r[0].dataset_name, source_name=r[1],
        source_table=r[0].source_table, status=r[0].status,
    ) for r in rows])


@router.get("/jobs", response_model=PageResponse[CollectionJobResponse])
async def list_jobs(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(CollectionJob, CollectionDatasetConfig.dataset_name)
        .outerjoin(CollectionDatasetConfig, CollectionJob.dataset_config_id == CollectionDatasetConfig.id)
    )
    if status:
        query = query.where(CollectionJob.job_status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(CollectionJob.started_at.desc()).offset(offset).limit(page_size))).all()
    items = [CollectionJobResponse(
        id=r[0].id, dataset_name=r[1], job_status=r[0].job_status,
        started_at=r[0].started_at, finished_at=r[0].finished_at,
        total_rows=r[0].total_rows, success_rows=r[0].success_rows, error_rows=r[0].error_rows,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/migrations", response_model=APIResponse[list[MigrationResponse]])
async def list_migrations(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionMigration).where(CollectionMigration.is_deleted == False))).scalars().all()
    return APIResponse(data=[MigrationResponse(
        id=r.id, migration_name=r.migration_name, migration_type=r.migration_type,
        status=r.status, total_tables=r.total_tables, completed_tables=r.completed_tables,
    ) for r in rows])


@router.get("/external-agencies", response_model=APIResponse[list[ExternalAgencyResponse]])
async def list_external_agencies(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionExternalAgency).where(CollectionExternalAgency.is_deleted == False))).scalars().all()
    return APIResponse(data=[ExternalAgencyResponse(
        id=r.id, agency_name=r.agency_name, agency_code=r.agency_code,
        api_endpoint=r.api_endpoint, protocol=r.protocol, status=r.status,
    ) for r in rows])


@router.get("/spatial-configs", response_model=APIResponse[list[SpatialConfigResponse]])
async def list_spatial_configs(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(CollectionSpatialConfig).where(CollectionSpatialConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[SpatialConfigResponse(
        id=r.id, config_name=r.config_name, spatial_data_type=r.spatial_data_type,
        source_url=r.source_url, coordinate_system=r.coordinate_system, status=r.status,
    ) for r in rows])
