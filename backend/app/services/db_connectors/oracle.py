"""Oracle 커넥터 (python-oracledb Thin/Thick 자동 전환).

Oracle 11g 이하 서버는 Thin 모드 미지원 (DPY-3010) → Instant Client 있으면 Thick 모드로 자동 전환.
- ORACLE_CLIENT_LIB_DIR 환경변수로 Instant Client 경로 지정 (Dockerfile 에서 /opt/oracle/instantclient 주입)
- 접속방식은 connection_options.dsn_mode 로 service_name|sid 선택, 미지정 시 자동 폴백
"""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    import oracledb
    _AVAILABLE = True
except ImportError:
    oracledb = None
    _AVAILABLE = False

from app.services.db_connectors.base import BaseConnector, ConnectionError, TableMeta, UnsupportedError

logger = logging.getLogger(__name__)

# Thick 모드 초기화는 프로세스당 1회만 허용 (두 번째 호출은 에러)
_THICK_INIT_STATE = {"done": False, "ok": False, "error": None}


def _ensure_thick_mode() -> bool:
    """Instant Client 가 설치돼 있으면 Thick 모드로 초기화. 이미 초기화됐거나 라이브러리가 없으면 no-op."""
    if not _AVAILABLE:
        return False
    if _THICK_INIT_STATE["done"]:
        return _THICK_INIT_STATE["ok"]
    lib_dir = os.environ.get("ORACLE_CLIENT_LIB_DIR")
    if not lib_dir or not os.path.isdir(lib_dir):
        _THICK_INIT_STATE["done"] = True
        return False
    try:
        oracledb.init_oracle_client(lib_dir=lib_dir)
        _THICK_INIT_STATE["done"] = True
        _THICK_INIT_STATE["ok"] = True
        logger.info("Oracle Thick 모드 활성화: %s", lib_dir)
        return True
    except Exception as e:
        _THICK_INIT_STATE["done"] = True
        _THICK_INIT_STATE["error"] = str(e)
        logger.warning("Oracle Thick 모드 초기화 실패 (Thin 으로 폴백): %s", e)
        return False


class OracleConnector(BaseConnector):
    driver_name = "oracle"
    driver_version = oracledb.__version__ if _AVAILABLE else "n/a"
    native_available = _AVAILABLE

    def _open(self):
        if not _AVAILABLE:
            raise UnsupportedError("oracledb 미설치")

        # 구버전 Oracle 접속 가능성 대비 Thick 모드 초기화 시도 (lib 없으면 Thin 유지)
        _ensure_thick_mode()

        db = self.config.database or None
        opts = (self.config.options or {}) if isinstance(self.config.options, dict) else {}
        dsn_mode = (opts.get("dsn_mode") or "").lower()  # "service_name" | "sid" | "" (auto)

        last_err: Exception | None = None
        attempts: list[tuple[str, str]] = []
        if dsn_mode == "sid":
            attempts.append(("sid", oracledb.makedsn(self.config.host, self.config.port, sid=db)))
        elif dsn_mode == "service_name":
            attempts.append(("service_name", oracledb.makedsn(self.config.host, self.config.port, service_name=db)))
        else:
            # 자동: service_name → sid 순서로 시도 (일반적으로 12c+ 는 service_name, 11g 이하는 sid)
            attempts.append(("service_name", oracledb.makedsn(self.config.host, self.config.port, service_name=db)))
            attempts.append(("sid", oracledb.makedsn(self.config.host, self.config.port, sid=db)))

        for mode, dsn in attempts:
            try:
                return oracledb.connect(user=self.config.user, password=self.config.password, dsn=dsn)
            except Exception as e:
                last_err = e
                # ORA-12514(service_name unknown), ORA-12505(SID unknown), DPY-3010(thin unsupported) 인 경우 다음 모드 시도
                msg = str(e)
                if any(k in msg for k in ("ORA-12514", "ORA-12505", "DPY-3010")):
                    continue
                # 권한/비밀번호 오류 등은 즉시 종료
                break
        # 모든 시도 실패
        thick_hint = ""
        if _THICK_INIT_STATE.get("error"):
            thick_hint = f" (Thick mode init: {_THICK_INIT_STATE['error']})"
        raise ConnectionError(f"Oracle connection failed: {last_err}{thick_hint}") from last_err

    def _close(self, conn):
        conn.close()

    def _ping_query(self) -> str:
        return "SELECT 1, SYS_CONTEXT('USERENV','SESSION_USER') FROM DUAL"

    def list_schemas(self) -> list[str]:
        rows = self.fetch("SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME")
        return [r[0] for r in rows]

    def list_tables(self, schema: str | None = None) -> list[str]:
        if schema:
            rows = self.fetch(
                "SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER=:1 ORDER BY TABLE_NAME",
                (schema.upper(),),
            )
        else:
            rows = self.fetch("SELECT OWNER||'.'||TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
        return [r[0] for r in rows]

    def describe_table(self, schema: str, table: str) -> TableMeta:
        # 컬럼 + 주석 (ALL_COL_COMMENTS OUTER JOIN)
        cols = self.fetch(
            "SELECT c.COLUMN_NAME, c.DATA_TYPE, c.NULLABLE, c.DATA_LENGTH, c.DATA_PRECISION, c.DATA_SCALE, "
            "       cc.COMMENTS "
            "FROM ALL_TAB_COLUMNS c "
            "LEFT JOIN ALL_COL_COMMENTS cc "
            "  ON cc.OWNER=c.OWNER AND cc.TABLE_NAME=c.TABLE_NAME AND cc.COLUMN_NAME=c.COLUMN_NAME "
            "WHERE c.OWNER=:1 AND c.TABLE_NAME=:2 "
            "ORDER BY c.COLUMN_ID",
            (schema.upper(), table.upper()),
        )
        pk = [r[0] for r in self.fetch(
            "SELECT cc.COLUMN_NAME FROM ALL_CONSTRAINTS c JOIN ALL_CONS_COLUMNS cc "
            "ON c.OWNER=cc.OWNER AND c.CONSTRAINT_NAME=cc.CONSTRAINT_NAME "
            "WHERE c.OWNER=:1 AND c.TABLE_NAME=:2 AND c.CONSTRAINT_TYPE='P' ORDER BY cc.POSITION",
            (schema.upper(), table.upper()),
        )]
        cnt = None
        try:
            cnt = self.fetch(
                "SELECT NUM_ROWS FROM ALL_TABLES WHERE OWNER=:1 AND TABLE_NAME=:2",
                (schema.upper(), table.upper()),
            )[0][0]
        except Exception:
            pass
        # 테이블 주석
        tbl_comment = None
        try:
            row = self.fetch(
                "SELECT COMMENTS FROM ALL_TAB_COMMENTS WHERE OWNER=:1 AND TABLE_NAME=:2",
                (schema.upper(), table.upper()),
            )
            tbl_comment = row[0][0] if row and row[0] else None
        except Exception:
            pass

        def _clob(v):
            if v is None:
                return None
            return v.read() if hasattr(v, "read") else str(v)

        return TableMeta(
            schema=schema, name=table,
            columns=[{
                "name": c[0], "type": c[1], "nullable": c[2] == "Y",
                "length": c[3], "precision": c[4], "scale": c[5],
                "comment": _clob(c[6]),
            } for c in cols],
            pk_columns=pk,
            row_count_estimate=cnt,
            table_comment=_clob(tbl_comment),
        )

    def row_count(self, schema: str, table: str) -> int:
        fq = self.qualify(schema, table)
        return self.fetch(f"SELECT COUNT(*) FROM {fq}")[0][0]

    def fetch(self, query: str, params=None, limit=None) -> list[tuple]:
        cur = self._conn.cursor()
        try:
            cur.execute(query, params or [])
            if cur.description is None:
                return []
            if limit:
                return cur.fetchmany(limit)
            return cur.fetchall()
        finally:
            cur.close()

    def accounts(self) -> list[dict[str, Any]]:
        rows = self.fetch(
            "SELECT USERNAME, ACCOUNT_STATUS, CREATED, DEFAULT_TABLESPACE, PROFILE "
            "FROM DBA_USERS ORDER BY USERNAME"
        )
        return [{
            "account_name": r[0], "status": r[1],
            "created": r[2].isoformat() if r[2] else None,
            "privileges": {"tablespace": r[3], "profile": r[4]},
        } for r in rows]

    # ── DDL 추출 (DB 탐색기용) — Oracle 네이티브 DBMS_METADATA ──
    # 테이블스페이스·STORAGE·SEGMENT 속성 + 테이블/컬럼 COMMENT 모두 포함
    def get_ddl(self, schema: str, table: str) -> str:
        import re
        sch = schema.upper()
        tbl = table.upper()
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', sch) or \
           not re.match(r'^[A-Z_][A-Z0-9_]*$', tbl):
            raise ValueError(f"Invalid Oracle identifier: {schema}.{table}")

        parts: list[str] = []

        def _clob(val: Any) -> str:
            if val is None:
                return ""
            return val.read() if hasattr(val, "read") else str(val)

        try:
            cur = self._conn.cursor()
            # TABLESPACE/STORAGE/SEGMENT_ATTRIBUTES 포함, PRETTY+세미콜론
            cur.execute(
                "BEGIN "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'PRETTY',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'SQLTERMINATOR',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'STORAGE',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'TABLESPACE',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'SEGMENT_ATTRIBUTES',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'CONSTRAINTS',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'REF_CONSTRAINTS',TRUE); "
                "DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'EMIT_SCHEMA',TRUE); "
                "END;"
            )
            # 테이블 DDL
            cur.execute("SELECT DBMS_METADATA.GET_DDL('TABLE', :1, :2) FROM DUAL", (tbl, sch))
            row = cur.fetchone()
            if row and row[0]:
                parts.append(_clob(row[0]).strip())

            # 테이블 + 컬럼 COMMENT 묶음 (존재하는 경우만)
            has_comments = cur.execute(
                "SELECT COUNT(*) FROM ( "
                "  SELECT 1 FROM ALL_TAB_COMMENTS WHERE OWNER=:1 AND TABLE_NAME=:2 AND COMMENTS IS NOT NULL "
                "  UNION ALL "
                "  SELECT 1 FROM ALL_COL_COMMENTS WHERE OWNER=:1 AND TABLE_NAME=:2 AND COMMENTS IS NOT NULL "
                ")", (sch, tbl)
            ).fetchone()[0]
            if has_comments:
                try:
                    cur.execute(
                        "SELECT DBMS_METADATA.GET_DEPENDENT_DDL('COMMENT', :1, :2) FROM DUAL",
                        (tbl, sch),
                    )
                    crow = cur.fetchone()
                    if crow and crow[0]:
                        comment_ddl = _clob(crow[0]).strip()
                        if comment_ddl:
                            parts.append("-- Comments")
                            parts.append(comment_ddl)
                except Exception as e:
                    # ORA-31608 (no metadata) 등은 무시
                    parts.append(f"-- ※ COMMENT DDL 수집 실패: {e}")

            # 인덱스 DDL (PK 제외 보조 인덱스)
            try:
                cur.execute(
                    "SELECT DBMS_METADATA.GET_DEPENDENT_DDL('INDEX', :1, :2) FROM DUAL",
                    (tbl, sch),
                )
                irow = cur.fetchone()
                if irow and irow[0]:
                    idx_ddl = _clob(irow[0]).strip()
                    if idx_ddl:
                        parts.append("-- Indexes")
                        parts.append(idx_ddl)
            except Exception:
                # 인덱스 없으면 ORA-31608 — 무시
                pass

            cur.close()
            if parts:
                return "\n\n".join(parts)
        except Exception as e:
            return super().get_ddl(schema, table) + f"\n\n-- ※ DBMS_METADATA.GET_DDL 실패: {e}"
        return super().get_ddl(schema, table)

    # ── 스트리밍 ETL: Oracle 은 LIMIT 미지원, FETCH NEXT N ROWS ONLY 사용 ──
    def fetch_chunks(self, schema: str, table: str, chunk_size: int = 1000,
                        columns=None, where=None):
        """Oracle cursor.arraysize + fetchmany 로 server-side streaming."""
        meta = self.describe_table(schema, table)
        cols = columns or [c["name"] for c in meta.columns]
        col_list = ", ".join(f'"{c}"' for c in cols)
        # 식별자 안전화
        sch = schema.upper()
        tbl = table.upper()
        # schema/table 은 Oracle 식별자 규칙 (대문자 영숫자/_) 만 허용
        import re
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', sch) or not re.match(r'^[A-Z_][A-Z0-9_]*$', tbl):
            raise ValueError(f"Invalid Oracle identifier: {schema}.{table}")
        where_sql = f" WHERE {where}" if where else ""
        sql = f'SELECT {col_list} FROM "{sch}"."{tbl}"{where_sql}'
        cur = self._conn.cursor()
        try:
            cur.arraysize = chunk_size  # server-side batch 크기
            cur.execute(sql)
            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break
                yield cols, rows
        finally:
            cur.close()
