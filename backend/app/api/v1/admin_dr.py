"""재해복구/PIT/이관감사/OM동기화 API (REQ-DHUB-005-003)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.collection import CollectionDataSource, CollectionMigration
from app.models.dr import (DrDbAccountHistory, DrPitRecovery, DrRestoreLog,
                             MigrationAuditLog, MigrationValidationResult,
                             OpenmetadataSyncLog)
from app.models.system import SysDrBackup
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


# ══════ 커넥터 상태 조회 ══════
@router.get("/connectors", response_model=APIResponse)
async def list_connectors(user: CurrentUser = Depends(get_current_user)):
    """설치된 DB 커넥터 드라이버 목록과 상태."""
    from app.services.db_connectors import available_drivers
    return APIResponse(data=available_drivers())


@router.post("/connectors/test", response_model=APIResponse)
async def test_connector(body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """특정 data_source_id 로 커넥터 연결 테스트."""
    from app.services.db_connectors import get_connector
    src_id = body.get("data_source_id")
    if not src_id:
        raise HTTPException(status_code=400, detail="data_source_id 필요")
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(src_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        conn = get_connector(src)
        with conn.connect() as c:
            result = c.test()
        # 성공 시 last_test_* 갱신
        src.last_test_at = datetime.now()
        src.last_test_result = "SUCCESS" if result.get("ok") else "FAIL"
        await db.commit()
        return APIResponse(data=result)
    except Exception as e:
        src.last_test_at = datetime.now()
        src.last_test_result = "FAIL"
        await db.commit()
        raise HTTPException(status_code=502, detail=f"커넥터 테스트 실패: {e}")


@router.post("/connectors/test-config", response_model=APIResponse)
async def test_connector_config(body: dict, user: CurrentUser = Depends(get_current_user)):
    """저장 없이 입력값으로 즉시 연결 테스트 (등록 모달 용).

    body: {
        db_type: "POSTGRESQL" | "ORACLE" | "SAP_HANA" | "MSSQL" | "TIBERO",
        host: "...", port: 5432, database: "...", schema: "...",
        user: "...", password: "평문비밀번호"
    }
    비밀번호는 DB 에 저장되지 않고 메모리에서 1회 사용 후 폐기된다.
    """
    from app.services.db_connectors import get_connector, UnsupportedError
    from app.services.db_connectors.base import ConnectionError as DbConnError
    db_type = (body.get("db_type") or "").strip()
    host = (body.get("host") or body.get("connection_host") or "").strip()
    if not db_type or not host:
        raise HTTPException(status_code=400, detail="db_type, host 필수")
    config = {
        "db_type": db_type,
        "host": host,
        "port": int(body.get("port") or body.get("connection_port") or 0),
        "database": body.get("database") or body.get("connection_db"),
        "schema": body.get("schema") or body.get("connection_schema"),
        "user": body.get("user") or body.get("connection_user"),
        "password": body.get("password") or body.get("connection_password"),
        "options": body.get("options") or {},
    }
    try:
        conn = get_connector(config)
        with conn.connect() as c:
            result = c.test()
        return APIResponse(data=result, message="연결 성공" if result.get("ok") else "연결 실패")
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=f"미지원 드라이버: {e}")
    except DbConnError as e:
        raise HTTPException(status_code=502, detail=f"연결 실패: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"연결 실패: {str(e)[:300]}")


@router.get("/data-sources/{source_id}/schemas", response_model=APIResponse)
async def list_schemas(source_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    from app.services.db_connectors import get_connector
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            return APIResponse(data=c.list_schemas())
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/data-sources/{source_id}/schemas/{schema}/tables", response_model=APIResponse)
async def list_tables(source_id: str, schema: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """특정 스키마 하위 테이블 목록 조회 (원본DB 설정 화면 트리뷰 용)."""
    from app.services.db_connectors import get_connector
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            return APIResponse(data=c.list_tables(schema))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════ DB 탐색기: 테이블 상세(컬럼 메타) / DDL / 리드온리 쿼리 ══════
@router.get("/data-sources/{source_id}/schemas/{schema}/tables/{table}/columns", response_model=APIResponse)
async def describe_columns(source_id: str, schema: str, table: str,
                                 db: AsyncSession = Depends(get_db),
                                 user: CurrentUser = Depends(get_current_user)):
    """테이블 컬럼 속성(이름/타입/길이/nullable/PK) 조회."""
    from app.services.db_connectors import get_connector
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            meta = c.describe_table(schema, table)
            return APIResponse(data={
                "schema": meta.schema, "table": meta.name,
                "columns": meta.columns,
                "pk_columns": meta.pk_columns,
                "row_count_estimate": meta.row_count_estimate,
                "table_comment": meta.table_comment,
            })
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/data-sources/{source_id}/schemas/{schema}/tables/{table}/ddl", response_model=APIResponse)
async def get_table_ddl(source_id: str, schema: str, table: str,
                              db: AsyncSession = Depends(get_db),
                              user: CurrentUser = Depends(get_current_user)):
    """테이블 DDL(CREATE TABLE) 조회."""
    from app.services.db_connectors import get_connector
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            ddl = c.get_ddl(schema, table)
            return APIResponse(data={"schema": schema, "table": table, "ddl": ddl})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/data-sources/{source_id}/query", response_model=APIResponse)
async def run_query(source_id: str, body: dict,
                       db: AsyncSession = Depends(get_db),
                       user: CurrentUser = Depends(get_current_user)):
    """읽기 전용 SQL 실행. SELECT/WITH/SHOW/DESC/EXPLAIN 만 허용, 최대 limit 행 반환.

    body: {"sql": "...", "limit": 500}
    """
    import logging
    from app.services.db_connectors import get_connector
    log = logging.getLogger(__name__)
    sql = (body.get("sql") or "").strip()
    limit = int(body.get("limit") or 500)
    if limit < 1 or limit > 10000:
        raise HTTPException(status_code=400, detail="limit 은 1~10000")
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            result = c.run_readonly_query(sql, limit=limit)
            return APIResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 상세 오류 메시지를 UI 로 전달 (서버 로그엔 전체 traceback)
        log.exception("run_query failed src=%s sql=%r", source_id, sql[:200])
        raise HTTPException(status_code=502, detail=f"쿼리 실행 실패: {type(e).__name__}: {str(e)[:500]}")


@router.get("/data-sources/{source_id}/accounts", response_model=APIResponse)
async def list_accounts(source_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """대상 DB 의 계정 목록 조회 (원본 → 복구 계정 비교용)."""
    from app.services.db_connectors import get_connector
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    try:
        with get_connector(src).connect() as c:
            return APIResponse(data=c.accounts())
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════ 백업 관리 (스케줄러 기반) ══════
@router.get("/backups", response_model=APIResponse)
async def list_backups(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(SysDrBackup).where(SysDrBackup.is_deleted == False).order_by(SysDrBackup.created_at.desc())  # noqa: E712
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "backup_name": r.backup_name, "backup_type": r.backup_type,
        "target_system": r.target_system, "schedule_cron": r.schedule_cron, "retention_days": r.retention_days,
        "storage_path": r.storage_path, "last_backup_at": r.last_backup_at.isoformat() if r.last_backup_at else None,
        "last_backup_size_mb": float(r.last_backup_size_mb) if r.last_backup_size_mb else None,
        "last_backup_status": r.last_backup_status, "is_active": r.is_active,
        "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
        "source_id": str(r.source_id) if r.source_id else None,
        "backup_command": r.backup_command, "last_error_message": r.last_error_message,
    } for r in rows])


@router.post("/backups", response_model=APIResponse)
async def upsert_backup(body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    bid = body.get("id")
    if bid:
        b = (await db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(bid)))).scalar_one_or_none()
        if not b:
            raise HTTPException(status_code=404, detail="백업 없음")
    else:
        b = SysDrBackup(id=uuid.uuid4(), created_by=user.id)
        db.add(b)
    b.backup_name = body.get("backup_name") or b.backup_name or "Backup"
    b.backup_type = body.get("backup_type") or b.backup_type or "FULL"
    b.target_system = body.get("target_system")
    b.schedule_cron = body.get("schedule_cron")
    b.retention_days = body.get("retention_days") or 30
    b.storage_path = body.get("storage_path")
    b.is_active = bool(body.get("is_active", True))
    b.backup_command = body.get("backup_command")
    sid = body.get("source_id")
    b.source_id = uuid.UUID(sid) if sid else None
    b.updated_by = user.id
    await db.flush()
    return APIResponse(data={"id": str(b.id)}, message="백업 설정이 저장되었습니다")


@router.post("/backups/{backup_id}/execute", response_model=APIResponse)
async def execute_backup(backup_id: str, user: CurrentUser = Depends(get_current_user)):
    from app.tasks.backup_tasks import execute_backup as task
    task.delay(backup_id)
    return APIResponse(message="백업이 비동기로 실행됩니다")


@router.delete("/backups/{backup_id}", response_model=APIResponse)
async def delete_backup(backup_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    b = (await db.execute(select(SysDrBackup).where(SysDrBackup.id == uuid.UUID(backup_id)))).scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="백업 없음")
    b.is_deleted = True
    b.updated_by = user.id
    return APIResponse(message="삭제되었습니다")


# ══════ PIT 복구 ══════
@router.get("/pit-recoveries", response_model=APIResponse)
async def list_pit(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(DrPitRecovery).where(DrPitRecovery.is_deleted == False).order_by(DrPitRecovery.created_at.desc())  # noqa: E712
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "recovery_name": r.recovery_name,
        "target_source_id": str(r.target_source_id) if r.target_source_id else None,
        "target_backup_id": str(r.target_backup_id) if r.target_backup_id else None,
        "target_timestamp": r.target_timestamp.isoformat() if r.target_timestamp else None,
        "simulation_only": r.simulation_only, "approval_status": r.approval_status,
        "status": r.status, "executed_at": r.executed_at.isoformat() if r.executed_at else None,
        "simulation_result": r.simulation_result, "execution_result": r.execution_result,
        "error_message": r.error_message,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows])


@router.post("/pit-recoveries", response_model=APIResponse)
async def upsert_pit(body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    pid = body.get("id")
    if pid:
        p = (await db.execute(select(DrPitRecovery).where(DrPitRecovery.id == uuid.UUID(pid)))).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="PIT 복구 없음")
    else:
        p = DrPitRecovery(id=uuid.uuid4(), created_by=user.id)
        db.add(p)
    p.recovery_name = body.get("recovery_name") or p.recovery_name or "Untitled"
    tsid = body.get("target_source_id")
    p.target_source_id = uuid.UUID(tsid) if tsid else None
    tbid = body.get("target_backup_id")
    p.target_backup_id = uuid.UUID(tbid) if tbid else None
    ts = body.get("target_timestamp")
    if ts:
        p.target_timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts
    p.simulation_only = bool(body.get("simulation_only", True))
    p.updated_by = user.id
    if p.status is None:
        p.status = "DRAFT"
    await db.flush()
    return APIResponse(data={"id": str(p.id)}, message="PIT 복구가 저장되었습니다")


@router.post("/pit-recoveries/{pid}/simulate", response_model=APIResponse)
async def simulate_pit(pid: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """시뮬레이션만 실행 (실복구 금지)."""
    p = (await db.execute(select(DrPitRecovery).where(DrPitRecovery.id == uuid.UUID(pid)))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="PIT 복구 없음")
    # 간단한 예상치 계산: 대상 소스의 각 테이블 row_count 집계 (실환경: WAL segment 분석)
    estimated = {"estimated_rows": 0, "estimated_size_mb": 0.0, "estimated_duration_sec": 0, "warnings": []}
    if p.target_source_id:
        from app.services.db_connectors import get_connector
        src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == p.target_source_id))).scalar_one_or_none()
        if src:
            try:
                with get_connector(src).connect() as c:
                    schemas = c.list_schemas()[:3]
                    total_rows = 0
                    tbl_cnt = 0
                    for s in schemas:
                        for t in c.list_tables(s)[:5]:
                            try:
                                total_rows += c.row_count(s, t)
                                tbl_cnt += 1
                            except Exception:
                                estimated["warnings"].append(f"{s}.{t} row_count 실패")
                    estimated["estimated_rows"] = total_rows
                    estimated["estimated_size_mb"] = round(total_rows * 0.001, 2)
                    estimated["estimated_duration_sec"] = max(10, total_rows // 1000)
                    estimated["sampled_tables"] = tbl_cnt
            except Exception as e:
                estimated["warnings"].append(f"시뮬레이션 중 오류: {str(e)[:300]}")
        else:
            estimated["warnings"].append("target_source_id 미유효")
    else:
        estimated["warnings"].append("target_source_id 미지정 — 예상치 계산 불가")

    p.simulation_result = estimated
    p.status = "SIMULATED"
    await db.commit()

    # 시뮬레이션 restore 로그
    from app.tasks.backup_tasks import execute_restore
    if p.target_backup_id:
        execute_restore.delay(str(p.target_backup_id), pit_recovery_id=str(p.id),
                                 target_system=None, simulation=True, executed_by=str(user.id))

    return APIResponse(data=estimated, message="시뮬레이션이 완료되었습니다")


@router.post("/pit-recoveries/{pid}/approve", response_model=APIResponse)
async def approve_pit(pid: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    p = (await db.execute(select(DrPitRecovery).where(DrPitRecovery.id == uuid.UUID(pid)))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="PIT 복구 없음")
    p.approval_status = "APPROVED"
    p.approved_by = user.id
    p.approved_at = datetime.now()
    p.status = "READY"
    return APIResponse(message="승인되었습니다")


@router.post("/pit-recoveries/{pid}/execute", response_model=APIResponse)
async def execute_pit(pid: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    p = (await db.execute(select(DrPitRecovery).where(DrPitRecovery.id == uuid.UUID(pid)))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="PIT 복구 없음")
    if p.simulation_only:
        raise HTTPException(status_code=400, detail="시뮬레이션 전용으로 설정된 복구는 실행할 수 없습니다")
    if p.approval_status != "APPROVED":
        raise HTTPException(status_code=400, detail="승인되지 않은 복구는 실행할 수 없습니다")
    p.status = "EXECUTING"
    p.executed_at = datetime.now()
    from app.tasks.backup_tasks import execute_restore
    if p.target_backup_id:
        execute_restore.delay(str(p.target_backup_id), pit_recovery_id=str(p.id),
                                 target_system=None, simulation=False, executed_by=str(user.id))
    return APIResponse(message="PIT 복구가 비동기로 실행됩니다")


# ══════ 복구 이력/대시보드 ══════
@router.get("/restore-logs", response_model=PageResponse)
async def list_restore_logs(
    page: int = 1, page_size: int = 20, status: str | None = None,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    q = select(DrRestoreLog)
    if status:
        q = q.where(DrRestoreLog.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    rows = (await db.execute(q.order_by(DrRestoreLog.started_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    items = [{
        "id": str(r.id), "pit_recovery_id": str(r.pit_recovery_id) if r.pit_recovery_id else None,
        "backup_id": str(r.backup_id) if r.backup_id else None,
        "restore_type": r.restore_type, "source_system": r.source_system, "target_system": r.target_system,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "duration_sec": r.duration_sec, "restored_rows": r.restored_rows,
        "restored_tables": r.restored_tables,
        "restored_size_mb": float(r.restored_size_mb) if r.restored_size_mb else None,
        "status": r.status, "error_message": r.error_message,
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                         total_pages=(total + page_size - 1) // page_size if page_size else 0)


@router.get("/restore-dashboard", response_model=APIResponse)
async def restore_dashboard(days: int = 30, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """복원 통계 대시보드 (기간별 성공/실패, 복구유형, 평균 소요시간)."""
    since = datetime.now() - timedelta(days=days)
    total = (await db.execute(select(func.count()).where(DrRestoreLog.started_at >= since))).scalar() or 0
    success = (await db.execute(select(func.count()).where(DrRestoreLog.started_at >= since, DrRestoreLog.status == "SUCCESS"))).scalar() or 0
    failed = (await db.execute(select(func.count()).where(DrRestoreLog.started_at >= since, DrRestoreLog.status == "FAIL"))).scalar() or 0
    partial = (await db.execute(select(func.count()).where(DrRestoreLog.started_at >= since, DrRestoreLog.status == "PARTIAL"))).scalar() or 0
    avg_dur = (await db.execute(select(func.coalesce(func.avg(DrRestoreLog.duration_sec), 0)).where(DrRestoreLog.started_at >= since))).scalar() or 0
    total_rows = (await db.execute(select(func.coalesce(func.sum(DrRestoreLog.restored_rows), 0)).where(DrRestoreLog.started_at >= since))).scalar() or 0

    by_type_rows = (await db.execute(
        select(DrRestoreLog.restore_type, func.count()).where(DrRestoreLog.started_at >= since).group_by(DrRestoreLog.restore_type)
    )).all()
    by_type = [{"type": r[0], "count": r[1]} for r in by_type_rows]

    # PIT recovery 상태 분포
    pit_rows = (await db.execute(
        select(DrPitRecovery.status, func.count()).where(DrPitRecovery.is_deleted == False).group_by(DrPitRecovery.status)  # noqa: E712
    )).all()
    pit_status = [{"status": r[0], "count": r[1]} for r in pit_rows]

    return APIResponse(data={
        "period_days": days,
        "total": total, "success": success, "failed": failed, "partial": partial,
        "success_rate": round((success / total * 100), 1) if total else 0,
        "avg_duration_sec": float(avg_dur), "total_restored_rows": int(total_rows),
        "by_type": by_type, "pit_status": pit_status,
    })


# ══════ 계정 이력 ══════
@router.get("/account-history", response_model=PageResponse)
async def list_account_history(
    source_id: str | None = None, page: int = 1, page_size: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    q = select(DrDbAccountHistory)
    if source_id:
        q = q.where(DrDbAccountHistory.source_id == uuid.UUID(source_id))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    rows = (await db.execute(q.order_by(DrDbAccountHistory.changed_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    items = [{
        "id": str(r.id), "source_id": str(r.source_id) if r.source_id else None,
        "account_name": r.account_name, "action": r.action,
        "privileges": r.privileges, "note": r.note,
        "changed_at": r.changed_at.isoformat() if r.changed_at else None,
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                         total_pages=(total + page_size - 1) // page_size if page_size else 0)


# ══════ DB 계정·권한 관리 (REQ-DHUB-005-004-002) ══════
async def _load_source_or_404(db: AsyncSession, source_id: str) -> CollectionDataSource:
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(source_id)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")
    return src


def _log_account_change(db: AsyncSession, source_id: uuid.UUID, account_name: str,
                           action: str, privileges: dict | None, user_id: uuid.UUID,
                           note: str | None = None) -> None:
    """DrDbAccountHistory 자동 기록."""
    row = DrDbAccountHistory(
        id=uuid.uuid4(), source_id=source_id, account_name=account_name,
        action=action, privileges=privileges, changed_by=user_id, note=note,
    )
    db.add(row)


@router.post("/data-sources/{source_id}/accounts", response_model=APIResponse)
async def create_db_account(source_id: str, body: dict,
                                 db: AsyncSession = Depends(get_db),
                                 user: CurrentUser = Depends(get_current_user)):
    """대상 DB 에 신규 계정 생성 + 이력 자동 기록."""
    from app.services.db_connectors import get_connector
    from app.services.db_connectors.base import UnsupportedError
    src = await _load_source_or_404(db, source_id)
    account_name = (body.get("account_name") or "").strip()
    password = body.get("password") or ""
    note = body.get("note")
    if not account_name or not password:
        raise HTTPException(status_code=400, detail="account_name, password 필요")
    try:
        with get_connector(src).connect() as c:
            result = c.create_account(account_name, password)
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"계정 생성 실패: {e}")
    _log_account_change(db, src.id, account_name, "CREATE",
                          {"created": True}, user.id, note)
    await db.commit()
    return APIResponse(data=result, message=f"계정 '{account_name}' 이 생성되었습니다")


@router.delete("/data-sources/{source_id}/accounts/{account_name}", response_model=APIResponse)
async def drop_db_account(source_id: str, account_name: str,
                               db: AsyncSession = Depends(get_db),
                               user: CurrentUser = Depends(get_current_user)):
    """대상 DB 계정 제거 + 이력 기록."""
    from app.services.db_connectors import get_connector
    from app.services.db_connectors.base import UnsupportedError
    src = await _load_source_or_404(db, source_id)
    try:
        with get_connector(src).connect() as c:
            result = c.drop_account(account_name)
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"계정 삭제 실패: {e}")
    _log_account_change(db, src.id, account_name, "DROP", None, user.id, None)
    await db.commit()
    return APIResponse(data=result, message=f"계정 '{account_name}' 이 삭제되었습니다")


@router.post("/data-sources/{source_id}/accounts/{account_name}/password", response_model=APIResponse)
async def change_db_account_password(source_id: str, account_name: str, body: dict,
                                          db: AsyncSession = Depends(get_db),
                                          user: CurrentUser = Depends(get_current_user)):
    """대상 DB 계정 비밀번호 변경."""
    from app.services.db_connectors import get_connector
    from app.services.db_connectors.base import UnsupportedError
    src = await _load_source_or_404(db, source_id)
    new_password = body.get("new_password") or ""
    if not new_password:
        raise HTTPException(status_code=400, detail="new_password 필요")
    try:
        with get_connector(src).connect() as c:
            result = c.change_password(account_name, new_password)
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"비밀번호 변경 실패: {e}")
    _log_account_change(db, src.id, account_name, "PASSWORD_CHANGE",
                          {"changed": True}, user.id, body.get("note"))
    await db.commit()
    return APIResponse(data=result, message="비밀번호가 변경되었습니다")


@router.post("/data-sources/{source_id}/accounts/{account_name}/grant", response_model=APIResponse)
async def grant_db_privileges(source_id: str, account_name: str, body: dict,
                                    db: AsyncSession = Depends(get_db),
                                    user: CurrentUser = Depends(get_current_user)):
    """대상 DB 계정에 권한 부여. body: {privileges:[...], schema?, table?, note?}"""
    from app.services.db_connectors import get_connector
    from app.services.db_connectors.base import UnsupportedError
    src = await _load_source_or_404(db, source_id)
    privileges = body.get("privileges") or []
    schema = body.get("schema")
    table = body.get("table")
    if not privileges:
        raise HTTPException(status_code=400, detail="privileges 배열 필요")
    try:
        with get_connector(src).connect() as c:
            result = c.grant(account_name, privileges, schema, table)
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"권한 부여 실패: {e}")
    _log_account_change(db, src.id, account_name, "GRANT",
                          {"privileges": privileges, "schema": schema, "table": table,
                             "scope": result.get("scope"), "target": result.get("target")},
                          user.id, body.get("note"))
    await db.commit()
    return APIResponse(data=result, message="권한이 부여되었습니다")


@router.post("/data-sources/{source_id}/accounts/{account_name}/revoke", response_model=APIResponse)
async def revoke_db_privileges(source_id: str, account_name: str, body: dict,
                                     db: AsyncSession = Depends(get_db),
                                     user: CurrentUser = Depends(get_current_user)):
    """대상 DB 계정 권한 회수. body: {privileges:[...], schema?, table?, note?}"""
    from app.services.db_connectors import get_connector
    from app.services.db_connectors.base import UnsupportedError
    src = await _load_source_or_404(db, source_id)
    privileges = body.get("privileges") or []
    schema = body.get("schema")
    table = body.get("table")
    if not privileges:
        raise HTTPException(status_code=400, detail="privileges 배열 필요")
    try:
        with get_connector(src).connect() as c:
            result = c.revoke(account_name, privileges, schema, table)
    except UnsupportedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"권한 회수 실패: {e}")
    _log_account_change(db, src.id, account_name, "REVOKE",
                          {"privileges": privileges, "schema": schema, "table": table,
                             "scope": result.get("scope"), "target": result.get("target")},
                          user.id, body.get("note"))
    await db.commit()
    return APIResponse(data=result, message="권한이 회수되었습니다")


@router.post("/account-history/snapshot", response_model=APIResponse)
async def account_snapshot(body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """현재 DB 계정 현황을 스냅샷으로 기록 (변경점 없어도 SNAPSHOT 액션으로 저장)."""
    sid = body.get("source_id")
    if not sid:
        raise HTTPException(status_code=400, detail="source_id 필요")
    src = (await db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(sid)))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="데이터소스 없음")

    from app.services.db_connectors import get_connector
    try:
        with get_connector(src).connect() as c:
            accts = c.accounts()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    saved = 0
    for a in accts:
        row = DrDbAccountHistory(
            id=uuid.uuid4(),
            source_id=src.id,
            account_name=a.get("account_name") or "unknown",
            action="SNAPSHOT",
            privileges=a,
            changed_by=user.id,
            note="수동 스냅샷",
        )
        db.add(row)
        saved += 1
    await db.commit()
    return APIResponse(data={"saved": saved, "source_id": str(src.id)}, message=f"{saved}개 계정 스냅샷 저장")


# ══════ 이관 감사/검증 ══════
@router.get("/migrations/{migration_id}/audit-logs", response_model=APIResponse)
async def migration_audit(migration_id: str, limit: int = 100, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(MigrationAuditLog).where(MigrationAuditLog.migration_id == uuid.UUID(migration_id))
        .order_by(MigrationAuditLog.created_at.desc()).limit(limit)
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "action": r.action, "phase": r.phase,
        "severity": r.severity, "table_name": r.table_name, "row_count": r.row_count,
        "details": r.details,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "duration_ms": r.duration_ms,
    } for r in rows])


@router.get("/migrations/{migration_id}/validation", response_model=APIResponse)
async def migration_validation(migration_id: str, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(
        select(MigrationValidationResult).where(MigrationValidationResult.migration_id == uuid.UUID(migration_id))
        .order_by(MigrationValidationResult.executed_at.desc())
    )).scalars().all()
    by_status = {"MATCH": 0, "MISMATCH": 0, "ERROR": 0, "SKIPPED": 0}
    for r in rows:
        st = r.match_status or "SKIPPED"
        by_status[st] = by_status.get(st, 0) + 1
    return APIResponse(data={
        "total": len(rows), "by_status": by_status,
        "results": [{
            "id": str(r.id), "table_name": r.table_name, "validation_type": r.validation_type,
            "source_value": r.source_value, "target_value": r.target_value,
            "match_status": r.match_status, "diff_count": r.diff_count,
            "diff_details": r.diff_details, "duration_ms": r.duration_ms,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None,
        } for r in rows[:200]],
    })


@router.post("/migrations/{migration_id}/validate", response_model=APIResponse)
async def migration_validate(migration_id: str, body: dict, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """이관 검증 실행 (동기). 실환경 대량은 Celery 로 위임 권장."""
    src_id = body.get("source_id")
    tgt_id = body.get("target_id")
    tables = body.get("tables") or []
    if not (src_id and tgt_id and tables):
        raise HTTPException(status_code=400, detail="source_id, target_id, tables 필요")

    # async db session 을 동기 컨텍스트로 — 검증 서비스는 sync 세션 기반이므로 별도 세션 사용
    from app.database import SyncSessionLocal
    from app.services.migration_validation_service import validate_migration
    s = SyncSessionLocal()
    try:
        summary = validate_migration(s, uuid.UUID(migration_id), uuid.UUID(src_id), uuid.UUID(tgt_id),
                                          tables, actor_id=user.id)
        s.commit()
        return APIResponse(data=summary)
    except Exception as e:
        s.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        s.close()


# ══════ OpenMetadata 동기화 ══════
@router.get("/openmetadata/status", response_model=APIResponse)
async def om_status(user: CurrentUser = Depends(get_current_user)):
    from app.services.openmetadata_client import OpenMetadataClient
    c = OpenMetadataClient()
    return APIResponse(data={
        "configured": c.enabled,
        "base_url": c.base_url or None,
        "token_set": bool(c.token),
    })


@router.get("/openmetadata/sync-logs", response_model=PageResponse)
async def om_logs(
    status: str | None = None, entity_type: str | None = None,
    page: int = 1, page_size: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    q = select(OpenmetadataSyncLog)
    if status:
        q = q.where(OpenmetadataSyncLog.status == status)
    if entity_type:
        q = q.where(OpenmetadataSyncLog.entity_type == entity_type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    rows = (await db.execute(q.order_by(OpenmetadataSyncLog.started_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    items = [{
        "id": str(r.id), "entity_type": r.entity_type,
        "entity_id": str(r.entity_id) if r.entity_id else None, "entity_name": r.entity_name,
        "sync_direction": r.sync_direction, "operation": r.operation,
        "om_entity_id": r.om_entity_id, "status": r.status, "http_status": r.http_status,
        "error_message": r.error_message, "duration_ms": r.duration_ms,
        "started_at": r.started_at.isoformat() if r.started_at else None,
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                         total_pages=(total + page_size - 1) // page_size if page_size else 0)


@router.post("/openmetadata/sync-dataset/{dataset_id}", response_model=APIResponse)
async def om_sync_dataset(dataset_id: str, user: CurrentUser = Depends(get_current_user)):
    from app.tasks.openmetadata_tasks import sync_dataset
    sync_dataset.delay(dataset_id)
    return APIResponse(message="OpenMetadata 동기화가 비동기로 실행됩니다")


@router.post("/openmetadata/sync-pending", response_model=APIResponse)
async def om_sync_pending_now(user: CurrentUser = Depends(get_current_user)):
    from app.tasks.openmetadata_tasks import sync_pending
    sync_pending.delay()
    return APIResponse(message="대기 중 OM 동기화가 비동기로 실행됩니다")


@router.get("/openmetadata/dashboard", response_model=APIResponse)
async def om_dashboard(days: int = 7, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """OpenMetadata 연동 현황 대시보드."""
    since = datetime.now() - timedelta(days=days)
    total = (await db.execute(select(func.count()).where(OpenmetadataSyncLog.started_at >= since))).scalar() or 0
    success = (await db.execute(select(func.count()).where(OpenmetadataSyncLog.started_at >= since, OpenmetadataSyncLog.status == "SUCCESS"))).scalar() or 0
    failed = (await db.execute(select(func.count()).where(OpenmetadataSyncLog.started_at >= since, OpenmetadataSyncLog.status == "FAIL"))).scalar() or 0
    skipped = (await db.execute(select(func.count()).where(OpenmetadataSyncLog.started_at >= since, OpenmetadataSyncLog.status == "SKIPPED"))).scalar() or 0

    by_entity_rows = (await db.execute(
        select(OpenmetadataSyncLog.entity_type, func.count()).where(OpenmetadataSyncLog.started_at >= since).group_by(OpenmetadataSyncLog.entity_type)
    )).all()

    return APIResponse(data={
        "period_days": days,
        "total": total, "success": success, "failed": failed, "skipped": skipped,
        "success_rate": round((success / total * 100), 1) if total else 0,
        "by_entity_type": [{"type": r[0], "count": r[1]} for r in by_entity_rows],
    })
