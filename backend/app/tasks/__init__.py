from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("datahub", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=False,
    # ── 클라우드 네이티브 튜닝 ──
    # 결과 TTL: 1시간 후 자동 삭제 (Redis 메모리 누수 방지)
    result_expires=3600,
    # 메시지 수신 후 즉시 ACK 하지 않고 작업 완료 후 ACK (at-least-once)
    task_acks_late=True,
    # 워커가 한 번에 1개씩만 선점 → 롱잡 중 재시작 시 다른 워커 재배분 용이
    worker_prefetch_multiplier=1,
    # broker 연결 재시도
    broker_connection_retry_on_startup=True,
)

# 태스크 모듈 자동 등록
import app.tasks.quality_tasks  # noqa: E402, F401
import app.tasks.collection_tasks  # noqa: E402, F401
import app.tasks.erp_tasks  # noqa: E402, F401
import app.tasks.backup_tasks  # noqa: E402, F401
import app.tasks.openmetadata_tasks  # noqa: E402, F401
import app.tasks.migration_tasks  # noqa: E402, F401
import app.tasks.external_agency_tasks  # noqa: E402, F401

# Celery Beat 스케줄
# ❗ schedule 값은 반드시 crontab() 또는 timedelta/schedule 객체여야 한다 (dict 금지)
celery_app.conf.beat_schedule = {
    "erp-org-sync-daily": {
        "task": "erp.org_sync",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "default"},
    },
    # 품질검증 스케줄러 디스패처 - QualitySchedule 메타데이터를 읽어 due 한 작업을 실행
    "quality-scheduler-dispatch": {
        "task": "quality.scheduler_dispatch",
        "schedule": crontab(minute="*"),  # 매분
        "options": {"queue": "default"},
    },
    # AI 학습 피드백 발송 - PENDING 상태 피드백을 30분마다 일괄 전송
    "quality-ai-feedback-dispatch": {
        "task": "quality.dispatch_ai_feedback",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "default"},
    },
    # 수집 실패 자동 분류 + 알람 평가/발송 (REQ-DHUB-005-002-003) - 5분마다
    "collection-classify-and-alert": {
        "task": "collection.classify_and_alert",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "default"},
    },
    # 백업 스케줄러 (REQ-DHUB-005-003) - 매분 evaluate
    "backup-run-scheduled": {
        "task": "backup.run_scheduled",
        "schedule": crontab(minute="*"),
        "options": {"queue": "default"},
    },
    # 백업 retention 정리 - 매일 04:00
    "backup-cleanup-retention": {
        "task": "backup.cleanup_retention",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "default"},
    },
    # OpenMetadata 대기중 동기화 발송 - 매 10분
    "openmetadata-sync-pending": {
        "task": "openmetadata.sync_pending",
        "schedule": crontab(minute="*/10"),
        "options": {"queue": "default"},
    },
    # 외부기관 연계포인트 자동 점검 (REQ-DHUB-005-005-001) - 매분
    "external-agency-health-check-all": {
        "task": "external_agency.health_check_all",
        "schedule": crontab(minute="*"),
        "options": {"queue": "default"},
    },
    # 외부기관 재시도 큐 처리 - 매분
    "external-agency-retry-pending": {
        "task": "external_agency.retry_pending",
        "schedule": crontab(minute="*"),
        "options": {"queue": "default"},
    },
}
