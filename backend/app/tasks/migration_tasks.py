"""마이그레이션 비동기 태스크 (REQ-DHUB-005-004-007).

- migration.execute: MigrationEngine.run() 을 Celery 워커에서 실행
"""
from __future__ import annotations

import logging
import uuid

from celery import shared_task

from app.database import SyncSessionLocal
from app.services.migration_engine import MigrationEngine

logger = logging.getLogger(__name__)


@shared_task(name="migration.execute", bind=True, max_retries=0)
def execute_migration(self, migration_id: str, actor_id: str | None = None) -> dict:
    """청크 스트리밍 마이그레이션 실행.

    장시간 실행이므로 soft/hard time limit 은 운영에서 QUEUE 별로 별도 설정.
    Celery acks_late=True + prefetch=1 조합으로 워커 재시작 시 재배분 가능.
    """
    s = SyncSessionLocal()
    try:
        actor = uuid.UUID(actor_id) if actor_id else None
        engine = MigrationEngine(s, uuid.UUID(migration_id), actor)
        result = engine.run()
        return result
    except Exception as e:
        logger.exception("migration task failed")
        s.rollback()
        return {"ok": False, "error": str(e)[:500]}
    finally:
        s.close()
