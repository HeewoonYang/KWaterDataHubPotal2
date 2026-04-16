"""PostgreSQL 커넥터 (psycopg 기반)."""
from __future__ import annotations

import hashlib
from typing import Any

try:
    import psycopg
    _AVAILABLE = True
except ImportError:
    psycopg = None
    _AVAILABLE = False

from app.services.db_connectors.base import BaseConnector, ConnectionError, TableMeta, UnsupportedError


class PostgresConnector(BaseConnector):
    driver_name = "postgres"
    driver_version = psycopg.__version__ if _AVAILABLE else "n/a"
    native_available = _AVAILABLE

    def _open(self):
        if not _AVAILABLE:
            raise UnsupportedError("psycopg 미설치")
        try:
            return psycopg.connect(
                host=self.config.host, port=self.config.port, dbname=self.config.database,
                user=self.config.user, password=self.config.password,
                connect_timeout=self.config.timeout_sec,
                sslmode="require" if self.config.ssl else "prefer",
            )
        except Exception as e:
            raise ConnectionError(f"PG connection failed: {e}") from e

    def _close(self, conn):
        conn.close()

    def _ping_query(self) -> str:
        return "SELECT 1 AS ping, current_database(), current_user, version()"

    def list_schemas(self) -> list[str]:
        rows = self.fetch(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('information_schema','pg_catalog','pg_toast') "
            "ORDER BY schema_name"
        )
        return [r[0] for r in rows]

    def list_tables(self, schema: str | None = None) -> list[str]:
        if schema:
            rows = self.fetch(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name",
                (schema,),
            )
        else:
            rows = self.fetch(
                "SELECT table_schema||'.'||table_name FROM information_schema.tables "
                "WHERE table_type='BASE TABLE' ORDER BY table_schema, table_name"
            )
        return [r[0] for r in rows]

    def describe_table(self, schema: str, table: str) -> TableMeta:
        # 컬럼 + 주석 한 번에 조회 (pg_description)
        cols = self.fetch(
            "SELECT c.column_name, c.data_type, c.is_nullable, c.character_maximum_length, "
            "  c.numeric_precision, c.numeric_scale, pd.description "
            "FROM information_schema.columns c "
            "LEFT JOIN pg_class pc ON pc.relname=c.table_name "
            "LEFT JOIN pg_namespace pn ON pn.oid=pc.relnamespace AND pn.nspname=c.table_schema "
            "LEFT JOIN pg_description pd ON pd.objoid=pc.oid AND pd.objsubid=c.ordinal_position "
            "WHERE c.table_schema=%s AND c.table_name=%s "
            "ORDER BY c.ordinal_position",
            (schema, table),
        )
        pk = [r[0] for r in self.fetch(
            "SELECT a.attname FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = (%s || '.' || %s)::regclass AND i.indisprimary",
            (schema, table),
        )]
        cnt = None
        try:
            cnt = self.fetch(
                "SELECT reltuples::bigint FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname=%s AND c.relname=%s",
                (schema, table),
            )[0][0]
        except Exception:
            pass
        # 테이블 주석
        tbl_comment = None
        try:
            row = self.fetch(
                "SELECT obj_description((%s||'.'||%s)::regclass::oid, 'pg_class')",
                (schema, table),
            )
            tbl_comment = row[0][0] if row else None
        except Exception:
            pass
        return TableMeta(
            schema=schema, name=table,
            columns=[{
                "name": c[0], "type": c[1], "nullable": c[2] == "YES",
                "length": c[3], "precision": c[4], "scale": c[5],
                "comment": c[6],
            } for c in cols],
            pk_columns=pk,
            row_count_estimate=cnt,
            table_comment=tbl_comment,
        )

    def row_count(self, schema: str, table: str) -> int:
        fq = self.qualify(schema, table)
        return self.fetch(f"SELECT COUNT(*) FROM {fq}")[0][0]

    def checksum(self, schema: str, table: str, pk_columns=None, limit=None) -> str:
        """PG MD5 집계로 체크섬 (대용량에 효율적)."""
        meta = self.describe_table(schema, table)
        pk = pk_columns or meta.pk_columns
        if not pk:
            raise ValueError(f"{schema}.{table}: PK 없음 — 체크섬 불가")
        pk_list = ", ".join(pk)
        row_expr = " || '|' || ".join(f"COALESCE({c}::text,'')" for c in pk)
        fq = self.qualify(schema, table)
        inner = f"SELECT {row_expr} AS _row FROM {fq} ORDER BY {pk_list}"
        if limit:
            inner += f" LIMIT {int(limit)}"
        sql = f"SELECT md5(string_agg(_row, '|')) FROM ({inner}) _t"
        row = self.fetch(sql)
        return row[0][0] if row and row[0][0] else hashlib.md5(b"").hexdigest()

    def fetch(self, query: str, params=None, limit=None) -> list[tuple]:
        with self._conn.cursor() as cur:
            cur.execute(query, params or ())
            if cur.description is None:
                return []
            if limit:
                return cur.fetchmany(limit)
            return cur.fetchall()

    def accounts(self) -> list[dict[str, Any]]:
        rows = self.fetch(
            "SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolcanlogin, rolvaliduntil "
            "FROM pg_roles WHERE rolcanlogin = true ORDER BY rolname"
        )
        return [{
            "account_name": r[0], "is_super": r[1],
            "privileges": {"createdb": r[2], "createrole": r[3]},
            "valid_until": r[5].isoformat() if r[5] else None,
        } for r in rows]

    # ── 권한 관리 (REQ-DHUB-005-004-002) ──
    def _exec(self, sql: str) -> None:
        """DDL/DCL 실행. 식별자는 사전에 _safe_ident 로 검증 후 호출한다."""
        with self._conn.cursor() as cur:
            cur.execute(sql)
        self._conn.commit()

    def create_account(self, account_name: str, password: str) -> dict[str, Any]:
        acct = self._safe_ident(account_name)
        if not password or len(password) < 8:
            raise ValueError("password: 최소 8자 이상 필요")
        # 비밀번호는 파라미터 바인딩이 DCL 에 지원되지 않으므로 '' 이스케이프만 수행
        pw_esc = password.replace("'", "''")
        self._exec(f"CREATE ROLE {acct} LOGIN PASSWORD '{pw_esc}'")
        return {"account": acct, "action": "CREATE", "driver": self.driver_name}

    def drop_account(self, account_name: str) -> dict[str, Any]:
        acct = self._safe_ident(account_name)
        self._exec(f"DROP ROLE IF EXISTS {acct}")
        return {"account": acct, "action": "DROP", "driver": self.driver_name}

    def change_password(self, account_name: str, new_password: str) -> dict[str, Any]:
        acct = self._safe_ident(account_name)
        if not new_password or len(new_password) < 8:
            raise ValueError("password: 최소 8자 이상 필요")
        pw_esc = new_password.replace("'", "''")
        self._exec(f"ALTER ROLE {acct} WITH PASSWORD '{pw_esc}'")
        return {"account": acct, "action": "PASSWORD_CHANGE", "driver": self.driver_name}

    def _grant_target(self, schema: str | None, table: str | None) -> tuple[str, str]:
        """GRANT/REVOKE 대상 표현 생성."""
        if table:
            sch = self._safe_ident(schema) if schema else None
            tbl = self._safe_ident(table)
            fq = f"{sch}.{tbl}" if sch else tbl
            return "TABLE", fq
        if schema:
            return "SCHEMA", self._safe_ident(schema)
        return "DATABASE", self._safe_ident(self.config.database or "postgres")

    def grant(self, account_name: str, privileges: list[str],
                 schema: str | None = None, table: str | None = None) -> dict[str, Any]:
        acct = self._safe_ident(account_name)
        privs = ", ".join(self._safe_privs(privileges))
        scope, target = self._grant_target(schema, table)
        # SCHEMA 에는 USAGE/CREATE 만 의미가 있지만 요구사항 단순화를 위해 그대로 전달
        self._exec(f"GRANT {privs} ON {scope} {target} TO {acct}")
        return {"account": acct, "action": "GRANT", "privileges": privs,
                "scope": scope, "target": target, "driver": self.driver_name}

    def revoke(self, account_name: str, privileges: list[str],
                 schema: str | None = None, table: str | None = None) -> dict[str, Any]:
        acct = self._safe_ident(account_name)
        privs = ", ".join(self._safe_privs(privileges))
        scope, target = self._grant_target(schema, table)
        self._exec(f"REVOKE {privs} ON {scope} {target} FROM {acct}")
        return {"account": acct, "action": "REVOKE", "privileges": privs,
                "scope": scope, "target": target, "driver": self.driver_name}

    # ── 스트리밍 ETL 오버라이드 (REQ-DHUB-005-004-007) ──
    def fetch_chunks(self, schema: str, table: str, chunk_size: int = 1000,
                        columns: list[str] | None = None, where: str | None = None):
        """psycopg named (server-side) cursor 로 메모리 효율적 스트리밍."""
        from app.services.db_connectors.base import UnsupportedError  # noqa
        meta = self.describe_table(schema, table)
        cols = columns or [c["name"] for c in meta.columns]
        # 식별자 안전화
        sch = self._safe_ident(schema)
        tbl = self._safe_ident(table)
        col_list = ", ".join(self._safe_ident(c) for c in cols)
        where_sql = f" WHERE {where}" if where else ""
        sql = f"SELECT {col_list} FROM {sch}.{tbl}{where_sql}"
        # named cursor = server-side cursor (chunk 단위 fetch, FROM/backpressure)
        cursor_name = f"dh_stream_{id(self)}"
        with self._conn.cursor(name=cursor_name) as cur:
            cur.itersize = chunk_size
            cur.execute(sql)
            while True:
                rows = cur.fetchmany(chunk_size)
                if not rows:
                    break
                yield cols, rows

    def bulk_insert(self, schema: str, table: str, columns: list[str],
                       rows: list[tuple]) -> int:
        """PG COPY 를 사용한 고속 bulk insert (executemany 대비 10~50배)."""
        if not rows:
            return 0
        sch = self._safe_ident(schema)
        tbl = self._safe_ident(table)
        col_list = ", ".join(self._safe_ident(c) for c in columns)
        fq = f"{sch}.{tbl}"
        copy_sql = f"COPY {fq} ({col_list}) FROM STDIN"
        with self._conn.cursor() as cur:
            with cur.copy(copy_sql) as copy:
                for r in rows:
                    copy.write_row(r)
        self._conn.commit()
        return len(rows)

    def create_table_from_meta(self, target_schema: str, target_table: str, source_meta) -> None:
        """source TableMeta 기반 PG DDL 생성. 이미 존재하면 skip."""
        sch = self._safe_ident(target_schema)
        tbl = self._safe_ident(target_table)
        # 존재 여부 확인
        exists = self.fetch(
            "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
            (target_schema, target_table),
        )
        if exists:
            return
        # 타입 매핑 (이기종 → PG)
        defs = []
        for c in source_meta.columns:
            name = self._safe_ident(c["name"])
            pg_type = _map_to_pg_type(c.get("type"), c.get("length"), c.get("precision"), c.get("scale"))
            nullable = "" if c.get("nullable", True) else " NOT NULL"
            defs.append(f"{name} {pg_type}{nullable}")
        pk = source_meta.pk_columns or []
        if pk:
            defs.append(f"PRIMARY KEY ({', '.join(self._safe_ident(c) for c in pk)})")
        ddl = f"CREATE TABLE IF NOT EXISTS {sch}.{tbl} (\n  " + ",\n  ".join(defs) + "\n)"
        with self._conn.cursor() as cur:
            cur.execute(ddl)
        self._conn.commit()


    # ── DDL 추출 (DB 탐색기용) ── 테이블스페이스 + 테이블/컬럼 COMMENT 포함
    def get_ddl(self, schema: str, table: str) -> str:
        """PostgreSQL: information_schema + pg_indexes + pg_description 로 CREATE TABLE 재구성."""
        import re
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', schema) or \
           not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table):
            raise ValueError(f"Invalid identifier: {schema}.{table}")
        cols = self.fetch(
            "SELECT column_name, data_type, character_maximum_length, "
            "numeric_precision, numeric_scale, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
            (schema, table),
        )
        if not cols:
            raise ValueError(f"{schema}.{table}: 테이블을 찾을 수 없습니다")
        # PK
        pk = [r[0] for r in self.fetch(
            "SELECT a.attname FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
            "WHERE i.indrelid = (%s || '.' || %s)::regclass AND i.indisprimary",
            (schema, table),
        )]
        # 인덱스 (PK 제외 — pg_indexes 는 PK 인덱스도 포함하므로 필터)
        idxs = self.fetch(
            "SELECT pi.indexname, pi.indexdef "
            "FROM pg_indexes pi "
            "LEFT JOIN pg_index px ON px.indexrelid = (pi.schemaname||'.'||pi.indexname)::regclass "
            "WHERE pi.schemaname=%s AND pi.tablename=%s AND COALESCE(px.indisprimary,false)=false",
            (schema, table),
        )
        # 테이블스페이스 (NULL = 데이터베이스 기본값)
        tbs_row = self.fetch(
            "SELECT COALESCE(t.spcname, pg_catalog.current_database() || ' default') "
            "FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "LEFT JOIN pg_tablespace t ON t.oid=c.reltablespace "
            "WHERE n.nspname=%s AND c.relname=%s",
            (schema, table),
        )
        tablespace = tbs_row[0][0] if tbs_row else None
        # 테이블 COMMENT
        tbl_cmt_row = self.fetch(
            "SELECT obj_description((%s||'.'||%s)::regclass::oid, 'pg_class')",
            (schema, table),
        )
        tbl_comment = tbl_cmt_row[0][0] if tbl_cmt_row and tbl_cmt_row[0][0] else None
        # 컬럼 COMMENT
        col_comments = dict(self.fetch(
            "SELECT a.attname, pd.description "
            "FROM pg_attribute a "
            "JOIN pg_class c ON c.oid=a.attrelid "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "LEFT JOIN pg_description pd ON pd.objoid=a.attrelid AND pd.objsubid=a.attnum "
            "WHERE n.nspname=%s AND c.relname=%s AND a.attnum>0 AND NOT a.attisdropped "
            "AND pd.description IS NOT NULL",
            (schema, table),
        ))

        lines = [f'-- PostgreSQL DDL for "{schema}"."{table}"']
        lines.append(f'CREATE TABLE "{schema}"."{table}" (')
        col_defs = []
        for c in cols:
            name, dtype, maxlen, prec, scale, nullable, default = c
            t = (dtype or "").upper()
            if t in ("CHARACTER VARYING",) and maxlen:
                type_str = f"VARCHAR({maxlen})"
            elif t == "CHARACTER" and maxlen:
                type_str = f"CHAR({maxlen})"
            elif t == "NUMERIC" and prec is not None:
                type_str = f"NUMERIC({prec}" + (f",{scale}" if scale is not None else "") + ")"
            else:
                type_str = t
            null_str = "" if nullable == "YES" else " NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            col_defs.append(f'  "{name}" {type_str}{default_str}{null_str}')
        if pk:
            col_defs.append(f'  PRIMARY KEY ({", ".join(chr(34) + c + chr(34) for c in pk)})')
        lines.append(",\n".join(col_defs))
        # 테이블스페이스 (기본값이면 주석만 표기)
        if tablespace and "default" not in (tablespace or "").lower():
            lines.append(f') TABLESPACE "{tablespace}";')
        else:
            lines.append(f");  -- tablespace: {tablespace or "default"}")

        # 인덱스 DDL
        if idxs:
            lines.append("")
            lines.append("-- Indexes")
            for name, defsql in idxs:
                lines.append(f"{defsql};")

        # 테이블/컬럼 COMMENT
        if tbl_comment or col_comments:
            lines.append("")
            lines.append("-- Comments")
        if tbl_comment:
            esc = tbl_comment.replace("'", "''")
            lines.append(f"COMMENT ON TABLE \"{schema}\".\"{table}\" IS '{esc}';")
        for col_name, cmt in col_comments.items():
            esc = cmt.replace("'", "''")
            lines.append(f"COMMENT ON COLUMN \"{schema}\".\"{table}\".\"{col_name}\" IS '{esc}';")
        return "\n".join(lines)


def _map_to_pg_type(src_type: str | None, length=None, precision=None, scale=None) -> str:
    """이기종 DB 타입 → PostgreSQL 타입 매핑 (마이그레이션 자동 DDL 생성용)."""
    if not src_type:
        return "TEXT"
    t = src_type.upper().split("(")[0].strip()
    # 문자열
    if t in ("VARCHAR", "VARCHAR2", "NVARCHAR", "NVARCHAR2", "CHAR", "NCHAR"):
        return f"VARCHAR({length})" if length and length < 10485760 else "TEXT"
    if t in ("TEXT", "CLOB", "NCLOB", "LONGTEXT"):
        return "TEXT"
    # 숫자
    if t in ("INT", "INTEGER", "INT4"):
        return "INTEGER"
    if t in ("BIGINT", "INT8", "NUMBER") and not scale:
        # Oracle NUMBER without scale → BIGINT 추정
        return "BIGINT"
    if t in ("SMALLINT", "INT2", "TINYINT"):
        return "SMALLINT"
    if t in ("DECIMAL", "NUMERIC", "NUMBER"):
        if precision and scale is not None:
            return f"NUMERIC({precision},{scale})"
        return "NUMERIC"
    if t in ("FLOAT", "DOUBLE", "DOUBLE PRECISION", "REAL"):
        return "DOUBLE PRECISION"
    # 날짜/시간
    if t in ("DATE",):
        return "DATE"
    if t in ("TIMESTAMP", "DATETIME", "TIMESTAMP WITHOUT TIME ZONE"):
        return "TIMESTAMP"
    if t in ("TIMESTAMPTZ", "TIMESTAMP WITH TIME ZONE"):
        return "TIMESTAMPTZ"
    if t in ("TIME",):
        return "TIME"
    # 불리언
    if t in ("BOOLEAN", "BOOL"):
        return "BOOLEAN"
    # 바이너리
    if t in ("BLOB", "BYTEA", "VARBINARY", "BINARY", "RAW"):
        return "BYTEA"
    # JSON
    if t in ("JSON", "JSONB"):
        return "JSONB"
    # 기본값
    return "TEXT"
