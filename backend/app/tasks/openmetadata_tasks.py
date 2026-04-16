"""OpenMetadata 동기화 Celery 태스크."""
from __future__ import annotations

import logging
import uuid

from app.database import SyncSessionLocal
from app.services import openmetadata_client as om
from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="openmetadata.sync_dataset")
def sync_dataset(catalog_dataset_id: str):
    db = SyncSessionLocal()
    try:
        log = om.sync_catalog_dataset(db, uuid.UUID(catalog_dataset_id))
        db.commit()
        return {"status": log.status, "http": log.http_status}
    except Exception:
        db.rollback()
        logger.exception("OM sync_dataset failed: %s", catalog_dataset_id)
        raise
    finally:
        db.close()


@celery_app.task(name="openmetadata.sync_lineage")
def sync_lineage(lineage_id: str):
    db = SyncSessionLocal()
    try:
        log = om.sync_catalog_lineage(db, uuid.UUID(lineage_id))
        db.commit()
        return {"status": log.status, "http": log.http_status}
    except Exception:
        db.rollback()
        logger.exception("OM sync_lineage failed: %s", lineage_id)
        raise
    finally:
        db.close()


@celery_app.task(name="openmetadata.sync_pending")
def sync_pending():
    db = SyncSessionLocal()
    try:
        summary = om.sync_pending_all(db)
        return summary
    except Exception:
        db.rollback()
        logger.exception("OM sync_pending failed")
        raise
    finally:
        db.close()
