"""이관 검증 서비스 — row count / checksum / schema diff / PK consistency (REQ-DHUB-005-003-4)."""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection import CollectionDataSource, CollectionMigration
from app.models.dr import MigrationAuditLog, MigrationValidationResult
from app.services.db_connectors import UnsupportedError, get_connector
from app.services.db_connectors.base import ConnectionError as DbConnError

logger = logging.getLogger(__name__)


def _get_source(db: Session, source_id: uuid.UUID | None) -> CollectionDataSource | None:
    if not source_id:
        return None
    return db.execute(select(CollectionDataSource).where(CollectionDataSource.id == source_id)).scalar_one_or_none()


def validate_migration(db: Session, migration_id: uuid.UUID, source_id: uuid.UUID, target_id: uuid.UUID,
                            tables: list[dict[str, str]], actor_id: uuid.UUID | None = None) -> dict[str, Any]:
    """이관 검증 실행.

    tables: [{"source_schema": "HR", "source_table": "EMP", "target_schema": "public", "target_table": "emp"}, ...]
    """
    src_meta = _get_source(db, source_id)
    tgt_meta = _get_source(db, target_id)
    if not src_meta or not tgt_meta:
        return {"ok": False, "error": "source/target 데이터소스를 찾을 수 없습니다"}

    _audit(db, migration_id, action="VALIDATE", phase="VALIDATION", actor_id=actor_id,
             details={"source": str(source_id), "target": str(target_id), "tables": len(tables)})

    src_conn = get_connector(src_meta)
    tgt_conn = get_connector(tgt_meta)

    summary = {"total": 0, "match": 0, "mismatch": 0, "error": 0, "details": []}

    try:
        with src_conn.connect() as s_c, tgt_conn.connect() as t_c:
            for spec in tables:
                ss = spec.get("source_schema") or ""
                st = spec["source_table"]
                ts = spec.get("target_schema") or ""
                tt = spec.get("target_table") or st
                summary["total"] += 1
                row_result = _check_row_count(db, migration_id, s_c, t_c, ss, st, ts, tt)
                _record(summary, row_result)

                chk_result = _check_checksum(db, migration_id, s_c, t_c, ss, st, ts, tt)
                summary["total"] += 1
                _record(summary, chk_result)

                sdiff = _check_schema(db, migration_id, s_c, t_c, ss, st, ts, tt)
                summary["total"] += 1
                _record(summary, sdiff)

                summary["details"].append({
                    "table": f"{ss}.{st}→{ts}.{tt}",
                    "row_count": row_result["match_status"],
                    "checksum": chk_result["match_status"],
                    "schema": sdiff["match_status"],
                })
    except (UnsupportedError, DbConnError) as e:
        _audit(db, migration_id, action="VALIDATE", phase="VALIDATION", actor_id=actor_id,
                 severity="ERROR", details={"error": str(e)})
        return {"ok": False, "error": str(e)[:500], **summary}
    except Exception as e:
        logger.exception("validate_migration failed")
        return {"ok": False, "error": str(e)[:500], **summary}

    _audit(db, migration_id, action="VALIDATE", phase="VALIDATION", actor_id=actor_id,
             details=summary, severity="INFO" if summary["mismatch"] == 0 and summary["error"] == 0 else "WARNING")
    return {"ok": True, **summary}


def _record(summary: dict, result: dict) -> None:
    st = result.get("match_status")
    if st == "MATCH":
        summary["match"] += 1
    elif st == "MISMATCH":
        summary["mismatch"] += 1
    else:
        summary["error"] += 1


def _check_row_count(db: Session, migration_id: uuid.UUID, src, tgt, ss: str, st: str, ts: str, tt: str) -> dict:
    t0 = time.time()
    try:
        s_cnt = src.row_count(ss, st)
        t_cnt = tgt.row_count(ts, tt)
        status = "MATCH" if s_cnt == t_cnt else "MISMATCH"
        diff = abs(s_cnt - t_cnt)
        res = _save_val(db, migration_id, f"{ss}.{st}", "ROW_COUNT", str(s_cnt), str(t_cnt), status,
                             diff_count=diff, duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": status, "diff": diff, "id": str(res.id)}
    except Exception as e:
        res = _save_val(db, migration_id, f"{ss}.{st}", "ROW_COUNT", None, None, "ERROR",
                             diff_details={"error": str(e)[:500]}, duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": "ERROR", "error": str(e)[:300], "id": str(res.id)}


def _check_checksum(db: Session, migration_id: uuid.UUID, src, tgt, ss: str, st: str, ts: str, tt: str) -> dict:
    t0 = time.time()
    try:
        s_hash = src.checksum(ss, st)
        t_hash = tgt.checksum(ts, tt)
        status = "MATCH" if s_hash == t_hash else "MISMATCH"
        res = _save_val(db, migration_id, f"{ss}.{st}", "CHECKSUM", s_hash, t_hash, status,
                             duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": status, "source_hash": s_hash, "target_hash": t_hash, "id": str(res.id)}
    except Exception as e:
        res = _save_val(db, migration_id, f"{ss}.{st}", "CHECKSUM", None, None, "ERROR",
                             diff_details={"error": str(e)[:500]}, duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": "ERROR", "error": str(e)[:300], "id": str(res.id)}


def _check_schema(db: Session, migration_id: uuid.UUID, src, tgt, ss: str, st: str, ts: str, tt: str) -> dict:
    t0 = time.time()
    try:
        s_meta = src.describe_table(ss, st)
        t_meta = tgt.describe_table(ts, tt)
        s_cols = {c["name"].lower(): c for c in s_meta.columns}
        t_cols = {c["name"].lower(): c for c in t_meta.columns}
        missing_in_target = sorted(set(s_cols) - set(t_cols))
        extra_in_target = sorted(set(t_cols) - set(s_cols))
        type_mismatches = []
        for name in set(s_cols) & set(t_cols):
            s_t = (s_cols[name].get("type") or "").upper()
            t_t = (t_cols[name].get("type") or "").upper()
            # 관대한 비교: 문자열 타입/숫자 타입 family 일치 허용
            if not _type_compatible(s_t, t_t):
                type_mismatches.append({"column": name, "source": s_t, "target": t_t})

        status = "MATCH" if not (missing_in_target or extra_in_target or type_mismatches) else "MISMATCH"
        details = {"missing": missing_in_target, "extra": extra_in_target, "type_mismatches": type_mismatches}
        res = _save_val(db, migration_id, f"{ss}.{st}", "SCHEMA_DIFF",
                             f"{len(s_meta.columns)} cols", f"{len(t_meta.columns)} cols", status,
                             diff_count=len(missing_in_target) + len(extra_in_target) + len(type_mismatches),
                             diff_details=details, duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": status, "details": details, "id": str(res.id)}
    except Exception as e:
        res = _save_val(db, migration_id, f"{ss}.{st}", "SCHEMA_DIFF", None, None, "ERROR",
                             diff_details={"error": str(e)[:500]}, duration_ms=int((time.time() - t0) * 1000))
        return {"match_status": "ERROR", "error": str(e)[:300], "id": str(res.id)}


_NUM_FAMILY = {"INT", "INTEGER", "BIGINT", "SMALLINT", "NUMERIC", "DECIMAL", "NUMBER", "DOUBLE", "FLOAT", "REAL"}
_STR_FAMILY = {"CHAR", "VARCHAR", "VARCHAR2", "TEXT", "NVARCHAR", "NVARCHAR2", "CLOB"}
_TIME_FAMILY = {"DATE", "TIMESTAMP", "DATETIME", "TIME", "TIMESTAMPTZ"}


def _type_compatible(a: str, b: str) -> bool:
    if a == b:
        return True
    def _fam(x):
        xu = x.upper().split("(")[0].strip()
        if xu in _NUM_FAMILY:
            return "NUM"
        if xu in _STR_FAMILY:
            return "STR"
        if xu in _TIME_FAMILY:
            return "TIME"
        return xu
    return _fam(a) == _fam(b)


def _save_val(db: Session, migration_id: uuid.UUID, table_name: str, validation_type: str,
                   source_value, target_value, match_status: str, diff_count: int | None = None,
                   diff_details: dict | None = None, duration_ms: int | None = None) -> MigrationValidationResult:
    r = MigrationValidationResult(
        id=uuid.uuid4(),
        migration_id=migration_id,
        table_name=table_name,
        validation_type=validation_type,
        source_value=str(source_value) if source_value is not None else None,
        target_value=str(target_value) if target_value is not None else None,
        match_status=match_status,
        diff_count=diff_count,
        diff_details=diff_details,
        duration_ms=duration_ms,
        executed_at=datetime.now(),
    )
    db.add(r)
    db.flush()
    return r


def _audit(db: Session, migration_id: uuid.UUID, action: str, phase: str | None = None,
             actor_id: uuid.UUID | None = None, details: dict | None = None,
             severity: str = "INFO") -> MigrationAuditLog:
    a = MigrationAuditLog(
        id=uuid.uuid4(),
        migration_id=migration_id,
        action=action,
        phase=phase,
        actor_id=actor_id,
        started_at=datetime.now(),
        details=details,
        severity=severity,
        created_at=datetime.now(),
    )
    db.add(a)
    db.flush()
    return a
