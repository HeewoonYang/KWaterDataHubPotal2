"""수집 완료 → 카탈로그 자동등록 파이프라인 태스크"""
import logging

from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models.collection import CollectionDataSource, CollectionDatasetConfig, CollectionJob
from app.services import catalog_registration_service, collection_failure_service, notification_service
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ── 실패 분류 + 알람 디스패치 (REQ-DHUB-005-002-003) ─────────────────
@celery_app.task(name="collection.classify_and_alert")
def classify_recent_failures_and_alert():
    """최근 미분류 실패 잡 자동 분류 + 알람 평가/발송.

    Celery Beat 으로 5분마다 호출 권장.
    """
    db = SyncSessionLocal()
    try:
        # 1) 미분류 실패 잡 자동 분류
        unclassified = db.execute(
            select(CollectionJob).where(
                CollectionJob.job_status == "FAIL",
                CollectionJob.failure_category.is_(None),
            ).limit(500)
        ).scalars().all()
        for job in unclassified:
            collection_failure_service.annotate_job_failure(job)
        if unclassified:
            db.commit()
            logger.info("classify_recent_failures: classified %d jobs", len(unclassified))

        # 2) 알람 평가/발송
        summary = collection_failure_service.evaluate_and_dispatch_alerts(db)
        logger.info("collection alerts: %s", summary)
        return {"classified": len(unclassified), **summary}
    except Exception:
        db.rollback()
        logger.exception("classify_and_alert 실패")
        raise
    finally:
        db.close()


@celery_app.task(
    name="collection.on_complete",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def on_collection_complete(self, job_id: str) -> dict:
    """수집 완료 후 카탈로그 자동등록 파이프라인

    1. CollectionJob → Config → DataSource 조회
    2. CatalogDataset 생성/갱신
    3. CatalogColumn 메타데이터 추출
    4. CatalogSearchIndex 갱신
    5. CatalogLineage 생성
    6. DataClassification.dataset_count 갱신
    7. 알림 발송
    8. 품질 검증 체이닝
    """
    db = SyncSessionLocal()
    try:
        # 1. 수집 작업 조회
        job = db.execute(
            select(CollectionJob).where(CollectionJob.id == job_id)
        ).scalar_one_or_none()

        if not job:
            logger.error("수집 작업 미존재: job_id=%s", job_id)
            return {"status": "error", "message": f"CollectionJob not found: {job_id}"}

        if job.job_status != "SUCCESS":
            logger.warning("수집 작업 상태가 SUCCESS가 아님: %s", job.job_status)
            return {"status": "skipped", "message": f"Job status: {job.job_status}"}

        config = db.execute(
            select(CollectionDatasetConfig).where(CollectionDatasetConfig.id == job.dataset_config_id)
        ).scalar_one_or_none()

        if not config:
            logger.error("수집 데이터셋 구성 미존재: config_id=%s", job.dataset_config_id)
            return {"status": "error", "message": "CollectionDatasetConfig not found"}

        source = db.execute(
            select(CollectionDataSource).where(CollectionDataSource.id == config.source_id)
        ).scalar_one_or_none()

        if not source:
            logger.error("데이터소스 미존재: source_id=%s", config.source_id)
            return {"status": "error", "message": "CollectionDataSource not found"}

        # 2. 카탈로그 데이터셋 등록/갱신
        dataset = catalog_registration_service.register_dataset_from_collection(db, job, config, source)

        # 3. 컬럼 메타데이터 추출
        columns = catalog_registration_service.extract_columns_from_config(db, dataset.id, config)

        # 4. 검색인덱스 갱신
        catalog_registration_service.create_search_index(db, dataset, columns)

        # 5. 리니지 생성
        catalog_registration_service.create_lineage_record(db, dataset.id, source.source_name, config)

        # 6. 분류 데이터셋 수 갱신
        catalog_registration_service.update_classification_count(db, dataset.classification_id)

        # 7. CollectionJob에 카탈로그 ID 연결
        job.catalog_dataset_id = dataset.id
        _append_execution_log(job, "catalog_registered", str(dataset.id))

        # 8. 알림 발송
        notification_service.notify_data_registered(db, dataset, job)

        db.commit()

        # 9. 품질 검증 비동기 체이닝 (collection_job_id 전달 → quality_check_result 추적성 확보)
        from app.tasks.quality_tasks import execute_quality_check
        execute_quality_check.delay(
            dataset_name=config.dataset_name,
            catalog_dataset_id=str(dataset.id),
            collection_job_id=str(job.id),
        )

        # 10. OpenMetadata 자동 동기화 (REQ-DHUB-005-003-6)
        try:
            from app.tasks.openmetadata_tasks import sync_dataset as om_sync_dataset
            om_sync_dataset.delay(str(dataset.id))
        except Exception:
            logger.exception("OpenMetadata sync dispatch failed")

        logger.info(
            "카탈로그 자동등록 파이프라인 완료: job=%s → dataset=%s (%d건)",
            job_id, dataset.id, job.success_rows or 0,
        )
        return {
            "status": "completed",
            "catalog_dataset_id": str(dataset.id),
            "dataset_name": config.dataset_name,
            "rows": job.success_rows,
            "columns": len(columns),
        }

    except Exception as e:
        db.rollback()
        logger.exception("카탈로그 자동등록 실패: job_id=%s", job_id)
        raise
    finally:
        db.close()


def _append_execution_log(job: CollectionJob, key: str, value: str) -> None:
    """CollectionJob.execution_log JSONB에 파이프라인 로그 추가"""
    if not job.execution_log:
        job.execution_log = {}
    job.execution_log[key] = value
