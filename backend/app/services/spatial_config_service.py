"""공간정보 수집 설정 서비스

Phase 1: CRUD, 조회, 연결테스트/레이어탐색/즉시실행은 stub (Phase 2에서 실제 커넥터 주입).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import (
    CollectionSpatialConfig,
    CollectionSpatialHistory,
    CollectionSpatialLayer,
)
from app.schemas.admin import (
    SpatialConfigCreate,
    SpatialConfigDetailResponse,
    SpatialConfigResponse,
    SpatialConfigUpdate,
    SpatialConnectionTestResponse,
    SpatialDiscoverLayersResponse,
    SpatialHistoryResponse,
    SpatialLayerResponse,
    SpatialRunResponse,
)


def _to_response(row: CollectionSpatialConfig) -> SpatialConfigResponse:
    return SpatialConfigResponse.model_validate(row)


async def list_configs(db: AsyncSession) -> list[SpatialConfigResponse]:
    rows = (
        await db.execute(
            select(CollectionSpatialConfig)
            .where(CollectionSpatialConfig.is_deleted.is_(False))
            .order_by(desc(CollectionSpatialConfig.created_at))
        )
    ).scalars().all()
    return [_to_response(r) for r in rows]


async def get_detail(db: AsyncSession, config_id: uuid.UUID) -> SpatialConfigDetailResponse | None:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None

    layers = (
        await db.execute(
            select(CollectionSpatialLayer)
            .where(
                CollectionSpatialLayer.config_id == config_id,
                CollectionSpatialLayer.is_deleted.is_(False),
            )
            .order_by(CollectionSpatialLayer.layer_name)
        )
    ).scalars().all()

    history = (
        await db.execute(
            select(CollectionSpatialHistory)
            .where(CollectionSpatialHistory.config_id == config_id)
            .order_by(desc(CollectionSpatialHistory.started_at))
            .limit(10)
        )
    ).scalars().all()

    base = SpatialConfigResponse.model_validate(row).model_dump()
    return SpatialConfigDetailResponse(
        **base,
        layers=[SpatialLayerResponse.model_validate(l) for l in layers],
        recent_history=[SpatialHistoryResponse.model_validate(h) for h in history],
    )


async def create_config(
    db: AsyncSession, body: SpatialConfigCreate, user_id: str | None
) -> SpatialConfigResponse:
    row = CollectionSpatialConfig(
        id=uuid.uuid4(),
        created_by=user_id,
        **body.model_dump(exclude_unset=True),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _to_response(row)


async def update_config(
    db: AsyncSession, config_id: uuid.UUID, body: SpatialConfigUpdate, user_id: str | None
) -> SpatialConfigResponse | None:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_by = user_id
    row.updated_at = datetime.utcnow()
    await db.flush()
    return _to_response(row)


async def soft_delete_config(
    db: AsyncSession, config_id: uuid.UUID, user_id: str | None
) -> bool:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    row.is_deleted = True
    row.updated_by = user_id
    row.updated_at = datetime.utcnow()
    await db.flush()
    return True


async def list_history(
    db: AsyncSession, config_id: uuid.UUID, limit: int = 20
) -> list[SpatialHistoryResponse]:
    rows = (
        await db.execute(
            select(CollectionSpatialHistory)
            .where(CollectionSpatialHistory.config_id == config_id)
            .order_by(desc(CollectionSpatialHistory.started_at))
            .limit(limit)
        )
    ).scalars().all()
    return [SpatialHistoryResponse.model_validate(r) for r in rows]


# ── Phase 2에서 실제 커넥터 호출로 교체될 stub 3종 ──────────────

async def test_connection(
    db: AsyncSession, config_id: uuid.UUID
) -> SpatialConnectionTestResponse:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return SpatialConnectionTestResponse(success=False, message="설정을 찾을 수 없습니다.")
    return SpatialConnectionTestResponse(
        success=True,
        message=f"[stub] {row.source_system or 'UNKNOWN'} 연결 구성이 확인되었습니다. (Phase 2에서 실제 연결 테스트 구현 예정)",
        detected_version=None,
        layers_preview=None,
    )


async def discover_layers(
    db: AsyncSession, config_id: uuid.UUID
) -> SpatialDiscoverLayersResponse:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return SpatialDiscoverLayersResponse(success=False, message="설정을 찾을 수 없습니다.")

    existing = (
        await db.execute(
            select(CollectionSpatialLayer)
            .where(
                CollectionSpatialLayer.config_id == config_id,
                CollectionSpatialLayer.is_deleted.is_(False),
            )
        )
    ).scalars().all()
    return SpatialDiscoverLayersResponse(
        success=True,
        message=f"[stub] 레이어 탐색은 Phase 2에서 구현됩니다. 현재 등록된 레이어 {len(existing)}개를 반환합니다.",
        layers=[SpatialLayerResponse.model_validate(l) for l in existing],
    )


async def run_collection(
    db: AsyncSession,
    config_id: uuid.UUID,
    triggered_by: str = "MANUAL",
    user_id: str | None = None,
) -> SpatialRunResponse:
    row = (
        await db.execute(
            select(CollectionSpatialConfig).where(
                CollectionSpatialConfig.id == config_id,
                CollectionSpatialConfig.is_deleted.is_(False),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return SpatialRunResponse(success=False, message="설정을 찾을 수 없습니다.")

    hist = CollectionSpatialHistory(
        id=uuid.uuid4(),
        config_id=config_id,
        started_at=datetime.utcnow(),
        status="RUNNING",
        triggered_by=triggered_by,
    )
    db.add(hist)
    row.last_status = "RUNNING"
    await db.flush()

    # Phase 2: Celery 태스크로 위임 (spatial_collection_tasks.run_spatial_collection.delay(config_id))
    return SpatialRunResponse(
        success=True,
        message="[stub] 수집 작업이 큐에 등록되었습니다. (Phase 2에서 실제 Celery 태스크 실행)",
        history_id=hist.id,
    )
