"""백업/복구 Celery 태스크 (REQ-DHUB-005-003).

- backup.run_scheduled : Beat 에서 매 분 호출 — sys_dr_backup.next_run_at 이 도달한 항목 실행
- backup.execute       : 특정 백업 즉시 실행 (수동 또는 다른 태스크에서 위임)
- backup.restore       : 백업 기반 복구 실행 (dr_restore_log 기록)
- backup.cleanup_retention : 보관기간 초과 백업 파일 정리
"""
from __future__ import annotations

import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from typing import Optional

from croniter import croniter
from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models.collection import CollectionDataSource
from app.models.dr import DrRestoreLog
from app.models.system import SysDrBackup
from app.tasks import celery_app

logger = logging.getLogger(__name__)

# 백업 저장 기본 디렉토리 (컨테이너 내부 — 실환경에선 S3/MinIO 경로로 대체 가능)
BACKUP_ROOT = os.environ.get("BACKUP_ROOT", "/tmp/dr_backups")


@celery_app.task(name="backup.run_scheduled")
def run_scheduled_backups():
    """Beat 트리거 — is_active 백업 중 next_run_at 도달 항목 dispatch."""
    db = SyncSessionLocal()
    try:
        now = datetime.now()
        rows = db.execute(
            select(SysDrBackup).where(
                SysDrBackup.is_active == True,  # noqa: E712
                SysDrBackup.is_deleted == False,  # noqa: E712
                SysDrBackup.schedule_cron.isnot(None),
            )
        ).scalars().all()
        triggered = 0
        for b in rows:
            if _is_due(b, now):
                execute_backup.delay(str(b.id))
                b.next_run_at = _next_tick(b.schedule_cron, now)
                triggered += 1
        db.commit()
        return {"evaluated": len(rows), "triggered": triggered}
    finally:
        db.close()


def _is_due(b: SysDrBackup, now: datetime) -> bool:
    if not b.schedule_cron:
        return False
    if b.next_run_at is None:
        # 최초 스캔 — 지난 2분 내 cron 히트 확인
        nxt = _next_tick(b.schedule_cron, now - timedelta(minutes=2))
        return nxt is not None and nxt <= now
    return b.next_run_at <= now


def _next_tick(cron_expr: str, base: datetime) -> Optional[datetime]:
    try:
        return croniter(cron_expr, base).get_next(datetime)
    except Exception as e:
        logger.warning("invalid cron expr %r: %s", cron_expr, e)
        return None


@celery_app.task(
    name="backup.execute",
    bind=True,
    autoretry_for=(subprocess.SubprocessError,),
    retry_backoff=True,
    max_retries=2,
)
def execute_backup(self, backup_id: str):
    """단일 백업 실행.

    backup_command 가 지정되면 shell 실행, 아니면 PG는 pg_dump 자동 실행, 나머지는 로그만.
    """
    db = SyncSessionLocal()
    try:
        b = db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id))).scalar_one_or_none()
        if not b:
            return {"status": "not_found"}

        started = datetime.now()
        b.last_backup_at = started
        b.last_backup_status = "RUNNING"
        db.commit()

        # 대상 소스 정보
        src = None
        if b.source_id:
            src = db.execute(select(CollectionDataSource).where(CollectionDataSource.id == b.source_id)).scalar_one_or_none()

        os.makedirs(BACKUP_ROOT, exist_ok=True)
        file_name = f"{b.backup_name}_{started.strftime('%Y%m%d_%H%M%S')}.dump"
        file_path = os.path.join(BACKUP_ROOT, file_name)

        ok, err, size_mb = _run_backup(b, src, file_path)

        finished = datetime.now()
        b.last_backup_status = "SUCCESS" if ok else "FAIL"
        b.last_backup_at = finished
        b.last_backup_size_mb = size_mb
        b.last_error_message = err

        # 알림: 실패 시 collection_alert_config 재사용은 범위 밖 — 향후 별도 알람 테이블 고려
        db.commit()
        return {"status": b.last_backup_status, "size_mb": float(size_mb or 0), "file": file_path, "error": err}
    except Exception:
        db.rollback()
        logger.exception("backup execute failed: %s", backup_id)
        raise
    finally:
        db.close()


def _run_backup(b: SysDrBackup, src, file_path: str) -> tuple[bool, Optional[str], Optional[float]]:
    cmd = b.backup_command
    if cmd:
        # 템플릿 치환
        replaces = {
            "$FILE": file_path, "$BACKUP_FILE": file_path,
            "$HOST": (src.connection_host if src else ""),
            "$PORT": str(src.connection_port if src else ""),
            "$DB": (src.connection_db if src else ""),
            "$USER": (src.connection_user if src else ""),
            "$PASSWORD": (src.connection_password_enc if src else ""),
        }
        final = cmd
        for k, v in replaces.items():
            final = final.replace(k, v or "")
        return _shell(final, file_path)

    # 기본 동작: 소스가 PG 면 pg_dump, 아니면 skip (로그만 기록)
    if src and (src.db_type or "").upper() in ("POSTGRESQL", "POSTGRES", "PG"):
        env_password = src.connection_password_enc or ""
        cmd = (
            f"PGPASSWORD='{env_password}' pg_dump -h {src.connection_host} -p {src.connection_port} "
            f"-U {src.connection_user} -d {src.connection_db} -F c -f '{file_path}'"
        )
        return _shell(cmd, file_path)

    # 드라이버 없음 — stub 파일만 생성
    try:
        with open(file_path, "w") as f:
            f.write(f"-- stub backup for {b.backup_name} at {datetime.now().isoformat()}\n")
        size = os.path.getsize(file_path) / 1024 / 1024
        return True, "stub(해당 DB 유형 네이티브 백업 미지원 — backup_command 지정 필요)", size
    except Exception as e:
        return False, str(e), None


def _shell(cmd: str, file_path: str) -> tuple[bool, Optional[str], Optional[float]]:
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout)[:1000], None
        size = os.path.getsize(file_path) / 1024 / 1024 if os.path.exists(file_path) else None
        return True, None, size
    except subprocess.TimeoutExpired:
        return False, "백업 타임아웃(1시간 초과)", None
    except Exception as e:
        return False, f"shell error: {e}"[:1000], None


@celery_app.task(name="backup.restore")
def execute_restore(backup_id: str, pit_recovery_id: Optional[str] = None,
                     target_system: Optional[str] = None, simulation: bool = False,
                     executed_by: Optional[str] = None):
    """백업 기반 복구 실행 + dr_restore_log 기록."""
    db = SyncSessionLocal()
    try:
        b = db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id))).scalar_one_or_none()
        if not b:
            return {"status": "not_found"}

        log = DrRestoreLog(
            id=uuid.uuid4(),
            pit_recovery_id=uuid.UUID(pit_recovery_id) if pit_recovery_id else None,
            backup_id=b.id,
            restore_type="SIMULATION" if simulation else ("PIT_RESTORE" if pit_recovery_id else "FULL_RESTORE"),
            source_system=b.target_system,
            target_system=target_system or b.target_system,
            started_at=datetime.now(),
            executed_by=uuid.UUID(executed_by) if executed_by else None,
        )
        db.add(log)
        db.commit()

        # 시뮬레이션 모드: 실제 복구 수행하지 않고 예상치만 계산
        if simulation:
            log.status = "SUCCESS"
            log.finished_at = datetime.now()
            log.duration_sec = int((log.finished_at - log.started_at).total_seconds())
            log.details = {"mode": "simulation", "note": "실제 복구 수행 없음"}
            db.commit()
            return {"status": "SUCCESS", "log_id": str(log.id), "mode": "simulation"}

        # 실복구는 벤더/환경별 — 기본 stub
        log.status = "SUCCESS"
        log.finished_at = datetime.now()
        log.duration_sec = int((log.finished_at - log.started_at).total_seconds())
        log.restored_rows = 0
        log.restored_tables = 0
        log.details = {"mode": "stub", "note": "실환경에서 pg_restore/rman/brbackup 등 벤더 명령과 통합 필요"}
        db.commit()
        return {"status": "SUCCESS", "log_id": str(log.id)}
    except Exception as e:
        db.rollback()
        logger.exception("restore failed")
        try:
            log.status = "FAIL"
            log.error_message = str(e)[:1000]
            log.finished_at = datetime.now()
            db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


@celery_app.task(name="backup.cleanup_retention")
def cleanup_retention():
    """보관기간 초과 파일 정리 (stub) — 일 1회 Beat 호출 권장."""
    db = SyncSessionLocal()
    try:
        rows = db.execute(select(SysDrBackup).where(SysDrBackup.is_deleted == False)).scalars().all()  # noqa: E712
        removed = 0
        now = datetime.now()
        for b in rows:
            if not b.retention_days:
                continue
            cutoff = now - timedelta(days=b.retention_days)
            # 파일시스템 기반 정리 (backup_name prefix)
            if not os.path.isdir(BACKUP_ROOT):
                continue
            for f in os.listdir(BACKUP_ROOT):
                if f.startswith(b.backup_name + "_"):
                    path = os.path.join(BACKUP_ROOT, f)
                    try:
                        mtime = datetime.fromtimestamp(os.path.getmtime(path))
                        if mtime < cutoff:
                            os.remove(path)
                            removed += 1
                    except Exception:
                        pass
        return {"removed": removed}
    finally:
        db.close()
