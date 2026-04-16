"""마이그레이션 코어 엔진 (REQ-DHUB-005-004-007).

청크 스트리밍 + bulk insert 기반 ETL 엔진.

사용법(동기, Celery worker 내부):
    from app.database import SyncSessionLocal
    from app.services.migration_engine import MigrationEngine

    with SyncSessionLocal() as s:
        engine = MigrationEngine(s, migration_id, actor_id)
        result = engine.run()

특징:
- source 는 CollectionDataSource 로부터 동적 연결 (db_connectors 프레임워크)
- target 은 CollectionMigration.table_list['target_source_id'] 로 지정, 미지정 시 "데이터허브 내부 PG" (HUB_TARGET_*)
- 테이블 당 DDL 자동 생성(미존재 시) → source TRUNCATE skip, target TRUNCATE(FULL) → chunk fetch → COPY
- 진행률은 CollectionMigration.error_log(JSONB) 에 실시간 기록 (progress 키)
- 행·건별 에러는 해당 chunk 전체 롤백 후 다음 chunk 로 계속 (에러는 error_log.errors 에 누적, 최대 50건)
- 각 테이블별 MigrationAuditLog (SCHEMA_COPY/DATA_COPY/COMPLETE) 자동 기록
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.collection import CollectionDataSource, CollectionMigration
from app.models.dr import MigrationAuditLog
from app.services.db_connectors import UnsupportedError, get_connector
from app.services.db_connectors.base import (BaseConnector, ConnectionConfig,
                                                 ConnectionError as DbConnError)
from app.services.db_connectors.registry import _REGISTRY  # noqa: F401  - force loading

logger = logging.getLogger(__name__)

# 기본 설정 — env 로 오버라이드 가능
DEFAULT_CHUNK_SIZE = int(os.environ.get("MIGRATION_CHUNK_SIZE", "1000"))
DEFAULT_TARGET_SCHEMA = os.environ.get("MIGRATION_TARGET_SCHEMA", "collection_zone")
MAX_ERRORS_PER_TABLE = 50


def _hub_target_connector() -> BaseConnector:
    """데이터허브 내부 PG 를 target 으로 사용하는 커넥터. 환경변수 HUB_TARGET_* 또는 DATABASE_URL_SYNC 로부터 파싱."""
    from urllib.parse import urlparse
    from app.config import settings
    url = os.environ.get("HUB_TARGET_DB_URL", settings.DATABASE_URL_SYNC)
    # postgresql+psycopg://user:pw@host:port/db
    u = urlparse(url.replace("+psycopg", "").replace("+asyncpg", ""))
    from app.services.db_connectors.postgres import PostgresConnector
    cfg = ConnectionConfig(
        db_type="POSTGRESQL",
        host=u.hostname or "localhost",
        port=u.port or 5432,
        database=(u.path or "/datahub").lstrip("/"),
        user=u.username,
        password=u.password,
    )
    return PostgresConnector(cfg)


class MigrationEngine:
    """청크 스트리밍 마이그레이션 엔진."""

    def __init__(self, db: Session, migration_id: uuid.UUID, actor_id: uuid.UUID | None):
        self.db = db
        self.migration_id = migration_id
        self.actor_id = actor_id
        self.migration: CollectionMigration | None = None
        self.progress: dict[str, Any] = {}

    # ── 진행률 기록 (error_log JSONB 에 병합) ──
    # SQLAlchemy JSONB 는 mutable 내부 dict 변경을 감지하지 못하므로,
    # 매번 새 dict 로 재할당 + flag_modified 로 명시적 dirty 처리
    def _save_progress(self, **extra) -> None:
        if not self.migration:
            return
        self.progress.update(extra)
        prev = self.migration.error_log or {}
        new_log = {**prev, "progress": dict(self.progress)}
        self.migration.error_log = new_log
        flag_modified(self.migration, "error_log")
        self.db.commit()

    def _add_error(self, table: str, phase: str, err: str) -> None:
        if not self.migration:
            return
        prev = self.migration.error_log or {}
        errors = list(prev.get("errors") or [])
        if len(errors) < MAX_ERRORS_PER_TABLE * 5:  # 글로벌 상한
            errors.append({
                "table": table, "phase": phase, "error": err[:500],
                "at": datetime.now().isoformat(),
            })
            new_log = {**prev, "errors": errors}
            self.migration.error_log = new_log
            flag_modified(self.migration, "error_log")
            self.db.commit()

    def _audit(self, action: str, phase: str | None = None, severity: str = "INFO",
                 table: str | None = None, row_count: int | None = None,
                 details: dict | None = None, duration_ms: int | None = None) -> None:
        a = MigrationAuditLog(
            id=uuid.uuid4(), migration_id=self.migration_id,
            action=action, phase=phase, actor_id=self.actor_id,
            started_at=datetime.now(), finished_at=datetime.now(),
            duration_ms=duration_ms, table_name=table, row_count=row_count,
            details=details or {}, severity=severity, created_at=datetime.now(),
        )
        self.db.add(a)
        self.db.commit()

    # ── 실행 ──
    def run(self) -> dict[str, Any]:
        self.migration = self.db.execute(
            select(CollectionMigration).where(CollectionMigration.id == self.migration_id)
        ).scalar_one_or_none()
        if not self.migration:
            return {"ok": False, "error": "마이그레이션을 찾을 수 없습니다"}

        cfg = self.migration.table_list or {}
        # table_list 레거시 호환: list → dict 포맷으로 승격
        if isinstance(cfg, list):
            cfg = {"tables": [{"source_schema": None, "source_table": t} if isinstance(t, str) else t for t in cfg]}
        tables: list[dict[str, Any]] = cfg.get("tables") or []
        target_source_id = cfg.get("target_source_id")  # 선택: 없으면 hub 내부 PG
        target_schema = cfg.get("target_schema") or DEFAULT_TARGET_SCHEMA
        chunk_size = int(cfg.get("chunk_size") or DEFAULT_CHUNK_SIZE)
        mode = (cfg.get("mode") or self.migration.migration_type or "FULL").upper()

        if not tables:
            self.migration.status = "FAILED"
            self._audit("FAIL", severity="ERROR", details={"error": "tables 비어 있음"})
            return {"ok": False, "error": "tables 비어 있음"}

        # source
        src_row = self.db.execute(select(CollectionDataSource).where(CollectionDataSource.id == self.migration.source_id)).scalar_one_or_none()
        if not src_row:
            self.migration.status = "FAILED"
            self._audit("FAIL", severity="ERROR", details={"error": "source 데이터소스 없음"})
            return {"ok": False, "error": "source 데이터소스 없음"}
        src_conn = get_connector(src_row)

        # target
        if target_source_id:
            tgt_row = self.db.execute(select(CollectionDataSource).where(CollectionDataSource.id == uuid.UUID(str(target_source_id)))).scalar_one_or_none()
            if not tgt_row:
                self._audit("FAIL", severity="ERROR", details={"error": "target 데이터소스 없음"})
                self.migration.status = "FAILED"
                return {"ok": False, "error": "target 데이터소스 없음"}
            tgt_conn = get_connector(tgt_row)
        else:
            tgt_conn = _hub_target_connector()

        # 초기 상태
        self.migration.status = "RUNNING"
        self.migration.started_at = datetime.now()
        self.migration.total_tables = len(tables)
        self.migration.completed_tables = 0
        self.progress = {
            "mode": mode, "chunk_size": chunk_size, "target_schema": target_schema,
            "total_tables": len(tables), "completed_tables": 0,
            "total_rows": 0, "processed_rows": 0,
            "current_table": None, "current_phase": "INIT",
            "started_at": self.migration.started_at.isoformat(),
        }
        self._save_progress()
        self._audit("START", phase="INIT",
                      details={"mode": mode, "chunk_size": chunk_size, "target_schema": target_schema, "tables": len(tables)})

        total_rows_all = 0
        tables_done = 0
        tables_failed = 0

        try:
            with src_conn.connect() as s_c, tgt_conn.connect() as t_c:
                # target schema 선행 생성
                try:
                    t_c.create_schema_if_not_exists(target_schema)
                except Exception as e:
                    self._add_error(target_schema, "SCHEMA_CREATE", str(e))

                for spec in tables:
                    ss = spec.get("source_schema") or (src_row.connection_schema or "public")
                    st = spec["source_table"]
                    ts = spec.get("target_schema") or target_schema
                    tt = spec.get("target_table") or st
                    t_mode = (spec.get("mode") or mode).upper()
                    fq = f"{ss}.{st}"

                    self.progress["current_table"] = f"{fq}→{ts}.{tt}"
                    self.progress["current_phase"] = "SCHEMA_COPY"
                    self._save_progress()

                    # 1) SCHEMA_COPY: target DDL 자동 생성
                    t_schema_start = time.time()
                    try:
                        meta = s_c.describe_table(ss, st)
                        try:
                            t_c.create_schema_if_not_exists(ts)
                        except Exception:
                            pass
                        try:
                            t_c.create_table_from_meta(ts, tt, meta)
                        except UnsupportedError:
                            # target 이 DDL 미지원이면 존재한다고 가정
                            pass
                        self._audit("START", phase="SCHEMA_COPY", table=fq,
                                      details={"columns": len(meta.columns)},
                                      duration_ms=int((time.time() - t_schema_start) * 1000))
                    except Exception as e:
                        logger.exception("schema copy failed for %s", fq)
                        self._add_error(fq, "SCHEMA_COPY", str(e))
                        self._audit("FAIL", phase="SCHEMA_COPY", table=fq, severity="ERROR",
                                      details={"error": str(e)[:500]})
                        tables_failed += 1
                        continue

                    # 2) FULL 이면 target truncate
                    if t_mode == "FULL":
                        try:
                            t_c.truncate_table(ts, tt)
                        except Exception as e:
                            self._add_error(fq, "TRUNCATE", str(e))

                    # 3) DATA_COPY: 청크 fetch → bulk insert
                    self.progress["current_phase"] = "DATA_COPY"
                    self._save_progress()
                    t_data_start = time.time()
                    table_rows = 0
                    chunks = 0
                    where = spec.get("where")
                    columns_override = spec.get("columns")
                    try:
                        total_src = s_c.row_count(ss, st)
                    except Exception:
                        total_src = None
                    self.progress["current_table_total"] = total_src
                    self.progress["current_table_processed"] = 0
                    self._save_progress()

                    try:
                        for cols, rows in s_c.fetch_chunks(ss, st, chunk_size=chunk_size,
                                                                 columns=columns_override, where=where):
                            try:
                                inserted = t_c.bulk_insert(ts, tt, cols, rows)
                                table_rows += inserted
                                total_rows_all += inserted
                                chunks += 1
                                self.progress["processed_rows"] = total_rows_all
                                self.progress["current_table_processed"] = table_rows
                                self.progress["current_chunks"] = chunks
                                self._save_progress()
                            except Exception as e:
                                # chunk 단위 실패 — 기록하고 다음 chunk 로
                                logger.exception("chunk insert failed %s chunk=%s", fq, chunks)
                                self._add_error(fq, "DATA_COPY_CHUNK", str(e))
                        duration_ms = int((time.time() - t_data_start) * 1000)
                        self._audit("COMPLETE", phase="DATA_COPY", table=fq,
                                      row_count=table_rows,
                                      details={"chunks": chunks, "source_rows": total_src,
                                                 "target_rows": table_rows},
                                      duration_ms=duration_ms,
                                      severity="INFO" if (total_src is None or total_src == table_rows) else "WARNING")
                        tables_done += 1
                        self.migration.completed_tables = (self.migration.completed_tables or 0) + 1
                        self.progress["completed_tables"] = self.migration.completed_tables
                        self._save_progress()
                    except Exception as e:
                        logger.exception("data copy failed for %s", fq)
                        self._add_error(fq, "DATA_COPY", str(e))
                        self._audit("FAIL", phase="DATA_COPY", table=fq, severity="ERROR",
                                      details={"error": str(e)[:500]})
                        tables_failed += 1
                        continue

            # 마무리
            self.migration.completed_at = datetime.now()
            self.migration.status = "COMPLETED" if tables_failed == 0 else "FAILED"
            self.progress["current_phase"] = "DONE"
            self.progress["tables_done"] = tables_done
            self.progress["tables_failed"] = tables_failed
            self.progress["total_rows"] = total_rows_all
            self.progress["completed_at"] = self.migration.completed_at.isoformat()
            self._save_progress()
            self._audit("COMPLETE" if tables_failed == 0 else "FAIL",
                          phase="CUTOVER",
                          severity="INFO" if tables_failed == 0 else "ERROR",
                          details={"tables_done": tables_done, "tables_failed": tables_failed,
                                     "total_rows": total_rows_all})
            return {"ok": tables_failed == 0, "tables_done": tables_done,
                    "tables_failed": tables_failed, "total_rows": total_rows_all,
                    "status": self.migration.status}

        except (UnsupportedError, DbConnError) as e:
            self.migration.status = "FAILED"
            self._audit("FAIL", severity="ERROR", details={"error": str(e)[:500]})
            return {"ok": False, "error": str(e)[:500]}
        except Exception as e:
            logger.exception("migration run failed")
            self.migration.status = "FAILED"
            self._audit("FAIL", severity="ERROR", details={"error": str(e)[:500]})
            return {"ok": False, "error": str(e)[:500]}
