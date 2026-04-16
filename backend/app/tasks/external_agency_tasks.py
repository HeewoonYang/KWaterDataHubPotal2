"""외부기관 연계포인트 자동 점검/재시도 태스크 (REQ-DHUB-005-005-001)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models.collection import (
    CollectionExternalAgency,
    CollectionExternalAgencyRetryQueue,
)
from app.services.external_agency_health_service import (
    dispatch_health_alert,
    perform_health_check,
    sync_to_openmetadata,
)
from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="external_agency.health_check_all")
def run_health_check_all() -> dict:
    """모든 health_check_enabled + ACTIVE/FAILED 기관에 대해 점검 실행.

    Celery Beat 으로 1분마다 호출 → 각 기관의 health_check_interval_sec 에 따라 필터링.
    """
    db = SyncSessionLocal()
    summary = {"total": 0, "checked": 0, "healthy": 0, "unhealthy": 0, "skipped": 0}
    try:
        agencies = db.execute(
            select(CollectionExternalAgency).where(
                CollectionExternalAgency.is_deleted == False,
                CollectionExternalAgency.health_check_enabled == True,
                CollectionExternalAgency.status.in_(["ACTIVE", "FAILED"]),
            )
        ).scalars().all()
        summary["total"] = len(agencies)
        now = datetime.now()

        for ag in agencies:
            interval = ag.health_check_interval_sec or 300
            if ag.last_health_check_at and (now - ag.last_health_check_at).total_seconds() < interval:
                summary["skipped"] += 1
                continue
            try:
                log = perform_health_check(db, ag, check_type="SCHEDULED", commit=False)
                summary["checked"] += 1
                if log.status == "HEALTHY":
                    summary["healthy"] += 1
                else:
                    summary["unhealthy"] += 1

                # 임계 도달 + 장애 → 알림 + OM 동기화
                threshold = ag.alert_threshold_failures or 3
                if log.status != "HEALTHY" and (ag.consecutive_failures or 0) >= threshold:
                    # 알림 중복 방지: 30분 이내 재발송 억제
                    last = ag.alert_last_sent_at
                    if not last or (now - last).total_seconds() > 1800:
                        dispatch_health_alert(db, ag, log)
                sync_to_openmetadata(db, ag)
            except Exception as e:
                logger.exception("health_check 실패 agency=%s: %s", ag.id, e)
        db.commit()
        logger.info("external_agency.health_check_all summary=%s", summary)
        return summary
    except Exception:
        db.rollback()
        logger.exception("health_check_all 실패")
        raise
    finally:
        db.close()


@celery_app.task(name="external_agency.retry_pending")
def run_retry_pending() -> dict:
    """재시도 큐에서 due 한 항목을 처리. (Celery Beat: 매분)"""
    db = SyncSessionLocal()
    summary = {"picked": 0, "done": 0, "dead": 0}
    try:
        now = datetime.now()
        items = db.execute(
            select(CollectionExternalAgencyRetryQueue).where(
                CollectionExternalAgencyRetryQueue.status == "PENDING",
                CollectionExternalAgencyRetryQueue.next_run_at <= now,
            ).limit(100)
        ).scalars().all()
        summary["picked"] = len(items)

        for item in items:
            item.status = "RUNNING"
            item.attempt = (item.attempt or 0) + 1
            db.flush()
            try:
                # 실제 재시도 로직은 payload 기반으로 확장 (여기서는 health-check 로 대체)
                ag = db.get(CollectionExternalAgency, item.agency_id)
                if ag:
                    log = perform_health_check(db, ag, check_type="RETRY", commit=False)
                    if log.status == "HEALTHY":
                        item.status = "DONE"
                        summary["done"] += 1
                    elif item.attempt >= (item.max_attempts or 3):
                        item.status = "DEAD"
                        item.last_error = log.message
                        summary["dead"] += 1
                    else:
                        item.status = "PENDING"
                        # 지수 백오프: 60s, 120s, 240s ...
                        delay = 60 * (2 ** (item.attempt - 1))
                        item.next_run_at = now + timedelta(seconds=delay)
                        item.last_error = log.message
                else:
                    item.status = "DEAD"
                    item.last_error = "agency not found"
                    summary["dead"] += 1
            except Exception as e:
                item.status = "PENDING" if item.attempt < (item.max_attempts or 3) else "DEAD"
                item.last_error = str(e)[:500]

        db.commit()
        logger.info("external_agency.retry_pending summary=%s", summary)
        return summary
    except Exception:
        db.rollback()
        logger.exception("retry_pending 실패")
        raise
    finally:
        db.close()
