"""품질검증 배치 태스크

담당:
- quality.execute_check: 카탈로그 데이터셋 대상 품질 검증
- quality.execute_distribution_check: 유통 데이터셋 대상 품질 검증
- quality.dispatch_ai_feedback: PENDING 상태 AI 피드백을 일괄 발송
- quality.scheduler_dispatch: QualitySchedule 메타데이터 기반 due 한 작업 trigger
- quality.compliance_check: 표준 용어/도메인 준수율 (기존)
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import redis
from croniter import croniter
from sqlalchemy import select

from app.config import settings
from app.database import SyncSessionLocal
from app.models.distribution import DistributionDataset
from app.models.quality import QualityCheckResult, QualityRule, QualitySchedule
from app.services import quality_ai_feedback_service, quality_service
from app.tasks import celery_app

logger = logging.getLogger(__name__)


# ── 카탈로그 검증 (기존 + AI 피드백 연계) ────────────────────────────
@celery_app.task(name="quality.execute_check")
def execute_quality_check(
    rule_id: int | None = None,
    dataset_name: str | None = None,
    catalog_dataset_id: str | None = None,
    collection_job_id: str | None = None,
):
    """카탈로그 품질 검증. 결과에 따라 AI 피드백도 자동 큐잉.

    collection_job_id 가 전달되면 결과를 해당 수집잡에 역참조로 기록하고,
    collection_job 의 quality_score / quality_check_at 도 갱신한다(REQ-004-004 + 005-002 결합).
    """
    db = SyncSessionLocal()
    try:
        results: list[QualityCheckResult] = []

        if catalog_dataset_id:
            r = quality_service.check_catalog_completeness(db, catalog_dataset_id)
            if r is not None:
                results.append(r)

        if dataset_name or catalog_dataset_id:
            uuid_value = catalog_dataset_id
            rule_results = quality_service.execute_active_rules_for_dataset(
                db,
                dataset_name=dataset_name or (results[0].dataset_name if results else "unknown"),
                catalog_dataset_id=uuid_value,
            )
            results.extend(rule_results)
        else:
            # rule_id 또는 dataset 정보 없이 호출된 경우 활성 규칙 전체 실행 (이전 호환)
            pass

        # collection_job_id 전파: 결과에 FK 기록 + 잡 점수 갱신
        if collection_job_id and results:
            import uuid as _uuid
            from datetime import datetime as _dt
            from app.models.collection import CollectionJob as _CollectionJob
            try:
                cj_id = _uuid.UUID(collection_job_id)
                for r in results:
                    if r is not None:
                        r.collection_job_id = cj_id
                avg_score = sum(float(r.score or 0) for r in results) / len(results)
                cj = db.execute(select(_CollectionJob).where(_CollectionJob.id == cj_id)).scalar_one_or_none()
                if cj is not None:
                    cj.quality_score = round(avg_score, 2)
                    cj.quality_check_at = _dt.now()
            except (ValueError, TypeError):
                logger.warning("invalid collection_job_id: %s", collection_job_id)

        db.commit()

        # 저점수/실패 결과에 대해 AI 피드백 큐잉
        for r in results:
            try:
                quality_ai_feedback_service.enqueue_feedback_for_result(db, r)
            except Exception:
                logger.exception("AI feedback enqueue failed: result_id=%s", r.id)
        db.commit()

        # 저점수 알림
        if results and catalog_dataset_id:
            avg_score = sum(float(r.score or 0) for r in results) / len(results)
            if avg_score < 80:
                from app.services.notification_service import notify_quality_result
                try:
                    notify_quality_result(
                        db,
                        dataset_name or (results[0].dataset_name or "unknown"),
                        avg_score,
                        catalog_dataset_id,
                    )
                    db.commit()
                except Exception:
                    logger.exception("notify_quality_result failed")

        logger.info(
            "품질 검증 완료: %d건, dataset=%s, catalog_id=%s",
            len(results), dataset_name, catalog_dataset_id,
        )
        return {
            "status": "completed",
            "results_count": len(results),
            "catalog_dataset_id": catalog_dataset_id,
        }

    except Exception:
        db.rollback()
        logger.exception("품질 검증 실패: rule_id=%s, dataset=%s", rule_id, dataset_name)
        raise
    finally:
        db.close()


# ── 유통 검증 ─────────────────────────────────────────────────────────
@celery_app.task(name="quality.execute_distribution_check")
def execute_distribution_quality_check(distribution_dataset_id: str):
    """유통 데이터셋 품질 검증 + AI 피드백 큐잉."""
    db = SyncSessionLocal()
    try:
        result = quality_service.check_distribution_dataset(db, distribution_dataset_id)
        if result is None:
            logger.warning("distribution_dataset not found: %s", distribution_dataset_id)
            return {"status": "not_found"}
        db.commit()

        try:
            quality_ai_feedback_service.enqueue_feedback_for_result(db, result)
            db.commit()
        except Exception:
            logger.exception("AI feedback enqueue failed: result_id=%s", result.id)

        return {
            "status": "completed",
            "result_id": result.id,
            "score": float(result.score or 0),
        }
    except Exception:
        db.rollback()
        logger.exception("유통 품질 검증 실패: dist_id=%s", distribution_dataset_id)
        raise
    finally:
        db.close()


@celery_app.task(name="quality.execute_distribution_check_all")
def execute_distribution_quality_check_all():
    """활성 상태 유통 데이터셋 전체에 대해 품질 검증 dispatch."""
    db = SyncSessionLocal()
    try:
        ids = db.execute(
            select(DistributionDataset.id).where(
                DistributionDataset.is_deleted == False,  # noqa: E712
            )
        ).scalars().all()
        count = 0
        for did in ids:
            execute_distribution_quality_check.delay(str(did))
            count += 1
        logger.info("distribution check-all dispatched: %d items", count)
        return {"status": "dispatched", "count": count}
    finally:
        db.close()


# ── AI 피드백 발송 ────────────────────────────────────────────────────
@celery_app.task(name="quality.dispatch_ai_feedback")
def dispatch_quality_ai_feedback():
    """PENDING 상태 AI 피드백 일괄 발송 (30분마다 Celery Beat 로 호출)."""
    db = SyncSessionLocal()
    try:
        summary = quality_ai_feedback_service.dispatch_pending(db)
        db.commit()
        return summary
    except Exception:
        db.rollback()
        logger.exception("dispatch_quality_ai_feedback 실패")
        raise
    finally:
        db.close()


# ── 스케줄러 디스패처 (매분) ──────────────────────────────────────────
_SCHED_LOCK_KEY = "quality:scheduler:lock"
_SCHED_LOCK_TTL = 55  # seconds


@celery_app.task(name="quality.scheduler_dispatch")
def scheduler_dispatch():
    """QualitySchedule 메타데이터 기반 due 한 검증 작업을 dispatch.

    Redis 락으로 멀티 워커 동시 실행 방지 (K8s 멀티 레플리카 안전).
    """
    try:
        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        acquired = r.set(_SCHED_LOCK_KEY, "1", nx=True, ex=_SCHED_LOCK_TTL)
        if not acquired:
            logger.debug("scheduler_dispatch: lock held by other worker, skipping")
            return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning("scheduler_dispatch: redis lock failed (%s), proceeding without lock", e)

    db = SyncSessionLocal()
    try:
        now = datetime.now()
        schedules = db.execute(
            select(QualitySchedule).where(
                QualitySchedule.is_active == True,  # noqa: E712
                QualitySchedule.is_deleted == False,  # noqa: E712
            )
        ).scalars().all()

        triggered = 0
        for s in schedules:
            due = _is_due(s, now)
            if not due:
                continue
            _trigger(s)
            s.last_run_at = now
            s.next_run_at = _calc_next_run(s.schedule_cron, now)
            triggered += 1

        db.commit()
        logger.info("scheduler_dispatch: triggered=%d total=%d", triggered, len(schedules))
        return {"status": "ok", "triggered": triggered, "total": len(schedules)}
    except Exception:
        db.rollback()
        logger.exception("scheduler_dispatch 실패")
        raise
    finally:
        db.close()


def _is_due(s: QualitySchedule, now: datetime) -> bool:
    if not s.schedule_cron:
        return False
    if s.next_run_at is None:
        # 처음 실행 기록이 없으면 cron 기준으로 지난 1분 내에 tick 이 있었는지 확인
        nxt = _calc_next_run(s.schedule_cron, now - timedelta(minutes=2))
        return nxt is not None and nxt <= now
    return s.next_run_at <= now


def _calc_next_run(cron_expr: str, base: datetime) -> Optional[datetime]:
    try:
        it = croniter(cron_expr, base)
        return it.get_next(datetime)
    except Exception as e:
        logger.warning("invalid cron expression %r: %s", cron_expr, e)
        return None


def _trigger(s: QualitySchedule) -> None:
    """스케줄 엔트리에 맞춰 적절한 태스크 dispatch.

    단순 규칙: target_dataset 이 "DISTRIBUTION:*" 으로 시작하면 유통 검증,
    그 외에는 기존 카탈로그 검증(`execute_quality_check`)을 rule_id 로 호출.
    """
    target = (s.target_dataset or "").strip()
    if target.startswith("DISTRIBUTION:") and len(target) > len("DISTRIBUTION:"):
        dist_id = target.split(":", 1)[1].strip()
        if dist_id.upper() == "ALL":
            execute_distribution_quality_check_all.delay()
        else:
            execute_distribution_quality_check.delay(dist_id)
    elif target.upper() == "CATALOG:ALL":
        # 카탈로그 전량 — execute_quality_check 를 dataset 별로 호출
        db = SyncSessionLocal()
        try:
            from app.models.catalog import CatalogDataset
            ids = db.execute(
                select(CatalogDataset.id, CatalogDataset.dataset_name).where(
                    CatalogDataset.is_deleted == False,  # noqa: E712
                    CatalogDataset.status == "ACTIVE",
                )
            ).all()
        finally:
            db.close()
        for cid, cname in ids:
            execute_quality_check.delay(rule_id=s.rule_id, dataset_name=cname, catalog_dataset_id=str(cid))
    else:
        # target_dataset 이 단일 카탈로그 UUID 또는 dataset_name
        execute_quality_check.delay(rule_id=s.rule_id, dataset_name=target or None)


# ── 기존 유지 ─────────────────────────────────────────────────────────
@celery_app.task(name="quality.compliance_check")
def run_compliance_check():
    """표준 준수 검사 배치 (TODO - 기존 placeholder)."""
    return {"status": "completed"}
