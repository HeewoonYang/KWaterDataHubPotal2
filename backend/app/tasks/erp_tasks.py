"""ERP 조직/사용자 동기화 Celery 태스크"""
from app.tasks import celery_app


@celery_app.task(
    name="erp.org_sync",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def erp_org_sync_task(self) -> dict:
    """ERP 인사·조직도 일일 동기화 태스크 (Celery Beat 스케줄)"""
    import asyncio
    from app.database import async_session
    from app.services import erp_sync_service

    async def _run():
        async with async_session() as db:
            log = await erp_sync_service.run_sync(
                db, sync_type="SCHEDULED", scope="ALL",
            )
            await db.commit()
            return {
                "sync_log_id": str(log.id),
                "status": log.status,
                "added": log.added,
                "updated": log.updated,
                "deactivated": log.deactivated,
                "errors": log.errors,
                "duration_ms": log.duration_ms,
            }

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
