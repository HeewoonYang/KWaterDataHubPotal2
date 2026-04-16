"""수집 완료 → 카탈로그 자동등록 서비스 (Celery 동기 컨텍스트용)"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.models.base import new_uuid
from app.models.catalog import CatalogColumn, CatalogDataset, CatalogLineage, CatalogSearchIndex
from app.models.classification import DataClassification
from app.models.collection import CollectionDataSource, CollectionDatasetConfig, CollectionJob, CollectionSchedule

logger = logging.getLogger(__name__)


def register_dataset_from_collection(
    db: Session,
    job: CollectionJob,
    config: CollectionDatasetConfig,
    source: CollectionDataSource,
) -> CatalogDataset:
    """수집 데이터셋 설정으로부터 카탈로그 데이터셋 생성/갱신 (upsert)"""
    existing = db.execute(
        select(CatalogDataset).where(
            CatalogDataset.source_system == source.source_name,
            CatalogDataset.dataset_name == config.dataset_name,
            CatalogDataset.is_deleted == False,
        )
    ).scalar_one_or_none()

    # 갱신주기 결정: 스케줄 존재 시 참조
    refresh_freq = _derive_refresh_frequency(db, config.id)

    if existing:
        existing.row_count = job.success_rows
        existing.last_updated_data_at = job.finished_at
        existing.classification_id = config.target_classification_id or existing.classification_id
        existing.grade_id = config.target_grade_id or existing.grade_id
        existing.refresh_frequency = refresh_freq or existing.refresh_frequency
        existing.updated_at = datetime.now()
        existing.status = "ACTIVE"
        logger.info("카탈로그 데이터셋 갱신: %s (id=%s)", config.dataset_name, existing.id)
        db.flush()
        return existing

    dataset = CatalogDataset(
        id=new_uuid(),
        dataset_name=config.dataset_name,
        dataset_name_kr=config.dataset_name,
        classification_id=config.target_classification_id,
        grade_id=config.target_grade_id,
        source_system=source.source_name,
        data_format="TABLE",
        row_count=job.success_rows,
        last_updated_data_at=job.finished_at,
        refresh_frequency=refresh_freq,
        schema_info=config.column_mapping,
        status="ACTIVE",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(dataset)
    db.flush()
    logger.info("카탈로그 데이터셋 신규 등록: %s (id=%s)", config.dataset_name, dataset.id)
    return dataset


def extract_columns_from_config(
    db: Session,
    catalog_dataset_id: UUID,
    config: CollectionDatasetConfig,
) -> list[CatalogColumn]:
    """column_mapping JSONB로부터 CatalogColumn 메타데이터 생성"""
    # 기존 컬럼 삭제 후 재생성
    db.execute(delete(CatalogColumn).where(CatalogColumn.dataset_id == catalog_dataset_id))

    mapping = config.column_mapping
    if not mapping or not isinstance(mapping, list):
        logger.warning("column_mapping 없음: config_id=%s", config.id)
        return []

    columns = []
    for idx, col in enumerate(mapping):
        catalog_col = CatalogColumn(
            id=new_uuid(),
            dataset_id=catalog_dataset_id,
            column_name=col.get("source_column", col.get("column_name", f"col_{idx}")),
            column_name_kr=col.get("target_column_kr", col.get("column_name_kr", "")),
            data_type=col.get("data_type", "VARCHAR"),
            length=col.get("length"),
            is_pk=col.get("is_pk", False),
            is_nullable=col.get("is_nullable", True),
            sort_order=idx,
        )
        db.add(catalog_col)
        columns.append(catalog_col)

    db.flush()
    logger.info("컬럼 메타데이터 %d건 등록: dataset_id=%s", len(columns), catalog_dataset_id)
    return columns


def create_search_index(
    db: Session,
    dataset: CatalogDataset,
    columns: list[CatalogColumn],
) -> None:
    """검색인덱스 생성/갱신"""
    parts = [dataset.dataset_name or "", dataset.dataset_name_kr or "", dataset.description or ""]
    for col in columns:
        parts.extend([col.column_name or "", col.column_name_kr or ""])
    search_text = " ".join(p for p in parts if p)

    existing = db.execute(
        select(CatalogSearchIndex).where(CatalogSearchIndex.dataset_id == dataset.id)
    ).scalar_one_or_none()

    if existing:
        existing.search_text = search_text
        existing.indexed_at = datetime.now()
    else:
        db.add(CatalogSearchIndex(
            id=new_uuid(),
            dataset_id=dataset.id,
            search_text=search_text,
            indexed_at=datetime.now(),
        ))
    db.flush()


def create_lineage_record(
    db: Session,
    catalog_dataset_id: UUID,
    source_name: str,
    config: CollectionDatasetConfig,
) -> CatalogLineage | None:
    """수집 리니지 기록 생성 (외부 원천 → 카탈로그)"""
    pipeline = f"수집파이프라인: {config.dataset_name}"

    # 이미 같은 파이프라인명으로 리니지가 있으면 스킵
    existing = db.execute(
        select(CatalogLineage).where(
            CatalogLineage.downstream_dataset_id == catalog_dataset_id,
            CatalogLineage.pipeline_name == pipeline,
            CatalogLineage.is_deleted == False,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    lineage = CatalogLineage(
        id=new_uuid(),
        upstream_dataset_id=None,  # 외부 소스는 카탈로그 엔트리 없음
        downstream_dataset_id=catalog_dataset_id,
        lineage_type="COPY",
        pipeline_name=pipeline,
        description=f"원천: {source_name} / 테이블: {config.source_table or 'N/A'}",
        created_at=datetime.now(),
    )
    db.add(lineage)
    db.flush()
    return lineage


def update_classification_count(db: Session, classification_id: int | None) -> None:
    """분류체계 데이터셋 수 재집계"""
    if not classification_id:
        return
    count = db.execute(
        select(func.count()).where(
            CatalogDataset.classification_id == classification_id,
            CatalogDataset.is_deleted == False,
        )
    ).scalar() or 0
    db.execute(
        text("UPDATE data_classification SET dataset_count = :cnt WHERE id = :cid"),
        {"cnt": count, "cid": classification_id},
    )
    db.flush()


def _derive_refresh_frequency(db: Session, config_id: UUID) -> str | None:
    """수집 스케줄로부터 갱신주기 추론"""
    schedule = db.execute(
        select(CollectionSchedule).where(
            CollectionSchedule.dataset_config_id == config_id,
            CollectionSchedule.is_active == True,
        )
    ).scalar_one_or_none()

    if not schedule:
        return "MANUAL"
    if schedule.schedule_type == "ONCE":
        return "MANUAL"
    if schedule.interval_seconds and schedule.interval_seconds <= 60:
        return "REALTIME"
    if schedule.interval_seconds and schedule.interval_seconds <= 3600:
        return "HOURLY"
    if schedule.schedule_cron:
        # 간단한 cron 해석: 일 단위 이상이면 DAILY
        return "DAILY"
    return "DAILY"
