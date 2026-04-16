"""이기종 DB 커넥터 추상 인터페이스."""
from __future__ import annotations

import abc
import hashlib
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """커넥터 연결 실패."""
    pass


class UnsupportedError(Exception):
    """해당 DB 유형이 실환경에서 지원되지 않음 (드라이버 미설치 등)."""
    pass


@dataclass
class ConnectionConfig:
    """커넥터 공통 구성 (CollectionDataSource 에서 생성)."""
    db_type: str                # ORACLE / SAP_HANA / POSTGRESQL / TIBERO / MSSQL
    host: str
    port: int
    database: str | None = None
    schema: str | None = None
    user: str | None = None
    password: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    timeout_sec: int = 15
    ssl: bool = False


@dataclass
class TableMeta:
    """테이블 메타정보."""
    schema: str
    name: str
    columns: list[dict[str, Any]]
    pk_columns: list[str]
    row_count_estimate: int | None = None
    table_comment: str | None = None  # 테이블 자체의 한글 주석 (ALL_TAB_COMMENTS / pg_description)


class BaseConnector(abc.ABC):
    """이기종 DB 커넥터 추상 클래스.

    실제 연결은 ``connect()`` 컨텍스트 매니저 내부에서만 유효.
    """

    driver_name: str = "abstract"
    driver_version: str = "n/a"
    native_available: bool = False

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._conn = None

    # ── 연결 라이프사이클 ──
    @contextmanager
    def connect(self):
        try:
            self._conn = self._open()
            yield self
        finally:
            if self._conn is not None:
                try:
                    self._close(self._conn)
                except Exception:
                    logger.exception("커넥터 종료 실패 (%s)", self.driver_name)
            self._conn = None

    @abc.abstractmethod
    def _open(self) -> Any: ...

    @abc.abstractmethod
    def _close(self, conn: Any) -> None: ...

    # ── 기능 인터페이스 ──
    def test(self) -> dict[str, Any]:
        """단순 SELECT 1 (또는 유사) 로 연결 테스트."""
        try:
            rows = self.fetch(self._ping_query(), limit=1)
            return {"ok": True, "driver": self.driver_name, "result": rows[:1]}
        except Exception as e:
            return {"ok": False, "driver": self.driver_name, "error": str(e)[:500]}

    @abc.abstractmethod
    def _ping_query(self) -> str: ...

    @abc.abstractmethod
    def list_schemas(self) -> list[str]: ...

    @abc.abstractmethod
    def list_tables(self, schema: str | None = None) -> list[str]: ...

    @abc.abstractmethod
    def describe_table(self, schema: str, table: str) -> TableMeta: ...

    @abc.abstractmethod
    def row_count(self, schema: str, table: str) -> int: ...

    def checksum(self, schema: str, table: str, pk_columns: list[str] | None = None,
                    limit: int | None = None) -> str:
        """MD5 기반 테이블 체크섬 (python 측 row hashing 기본 구현).

        대용량 테이블은 서브클래스에서 DB 측 MD5_AGG 로 오버라이드 권장.
        """
        pk = pk_columns or self.describe_table(schema, table).pk_columns
        if not pk:
            raise ValueError(f"{schema}.{table}: PK 없음 — 체크섬 불가")
        pk_list = ", ".join(pk)
        fq = self.qualify(schema, table)
        sql = f"SELECT {pk_list} FROM {fq} ORDER BY {pk_list}"
        if limit:
            sql += f" LIMIT {int(limit)}"
        h = hashlib.md5()
        for row in self.fetch(sql):
            h.update(("|".join(str(v) for v in row)).encode("utf-8"))
        return h.hexdigest()

    @abc.abstractmethod
    def fetch(self, query: str, params: dict | tuple | None = None,
                limit: int | None = None) -> list[tuple]: ...

    # ── 스트리밍 ETL (REQ-DHUB-005-004-007) ──
    def fetch_chunks(self, schema: str, table: str,
                        chunk_size: int = 1000, columns: list[str] | None = None,
                        where: str | None = None) -> Iterator[tuple[list[str], list[tuple]]]:
        """테이블을 chunk_size 행씩 스트리밍. (cols, rows) 튜플 제너레이터.

        기본 구현: fetch() 를 offset/limit 으로 반복 호출 (정렬 보장을 위해 PK 기준).
        서브클래스는 server-side cursor 로 오버라이드 권장.
        """
        meta = self.describe_table(schema, table)
        cols = columns or [c["name"] for c in meta.columns]
        col_list = ", ".join(cols)
        pk = meta.pk_columns or cols[:1]
        order = ", ".join(pk)
        fq = self.qualify(schema, table)
        where_sql = f" WHERE {where}" if where else ""
        offset = 0
        while True:
            sql = f"SELECT {col_list} FROM {fq}{where_sql} ORDER BY {order} LIMIT {int(chunk_size)} OFFSET {int(offset)}"
            rows = self.fetch(sql)
            if not rows:
                break
            yield cols, rows
            if len(rows) < chunk_size:
                break
            offset += chunk_size

    def bulk_insert(self, schema: str, table: str, columns: list[str],
                      rows: list[tuple]) -> int:
        """bulk insert. 반환값은 성공 삽입 건수. 서브클래스에서 DB별 최적화 권장."""
        if not rows:
            return 0
        # 기본 구현: executemany (폴백) — 서브클래스에서 COPY/bulk API 로 오버라이드
        col_list = ", ".join(self._safe_ident(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        fq = self.qualify(schema, table)
        sql = f"INSERT INTO {fq} ({col_list}) VALUES ({placeholders})"
        with self._conn.cursor() as cur:
            cur.executemany(sql, rows)
        self._conn.commit()
        return len(rows)

    def create_schema_if_not_exists(self, schema: str) -> None:
        """target schema 자동 생성. 미지원 DB 는 ValueError."""
        sch = self._safe_ident(schema)
        with self._conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {sch}")
        self._conn.commit()

    def truncate_table(self, schema: str, table: str) -> None:
        """대상 테이블 초기화 (TRUNCATE). 실패시 DELETE 폴백."""
        fq = self.qualify(self._safe_ident(schema), self._safe_ident(table))
        try:
            with self._conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {fq}")
            self._conn.commit()
        except Exception:
            with self._conn.cursor() as cur:
                cur.execute(f"DELETE FROM {fq}")
            self._conn.commit()

    def create_table_from_meta(self, target_schema: str, target_table: str,
                                    source_meta: TableMeta) -> None:
        """source TableMeta 로부터 target DDL 을 만들어 CREATE TABLE. 미지원 DB 는 ValueError."""
        raise UnsupportedError(f"{self.driver_name}: create_table_from_meta 미지원")

    # ── DDL 추출 / 리드온리 쿼리 (DB 탐색기용) ──
    def get_ddl(self, schema: str, table: str) -> str:
        """테이블의 CREATE TABLE DDL 반환. 서브클래스에서 DB 네이티브 기능으로 구현 권장.

        기본 구현: describe_table 결과를 이용해 표준 SQL 로 재구성 (근사치).
        """
        meta = self.describe_table(schema, table)
        lines = [f'-- {self.driver_name.upper()} 추정 DDL (describe_table 기반 재구성)']
        lines.append(f'CREATE TABLE "{schema}"."{table}" (')
        col_defs = []
        for c in meta.columns:
            t = (c.get("type") or "").upper()
            length = c.get("length")
            precision = c.get("precision")
            scale = c.get("scale")
            nullable = c.get("nullable", True)
            type_str = t
            if length and t in ("VARCHAR", "VARCHAR2", "CHAR", "NCHAR", "NVARCHAR", "NVARCHAR2"):
                type_str = f"{t}({length})"
            elif precision is not None and t in ("NUMERIC", "NUMBER", "DECIMAL"):
                type_str = f"{t}({precision}" + (f",{scale}" if scale is not None else "") + ")"
            null_str = "" if nullable else " NOT NULL"
            col_defs.append(f'  "{c["name"]}" {type_str}{null_str}')
        lines.append(",\n".join(col_defs))
        if meta.pk_columns:
            pk_cols = ', '.join(f'"{c}"' for c in meta.pk_columns)
            lines[-1] += ","
            lines.append(f'  PRIMARY KEY ({pk_cols})')
        lines.append(");")
        return "\n".join(lines)

    # 쿼리 안전 검증 — 서브클래스 공통으로 사용
    _QUERY_READONLY_PREFIXES: tuple[str, ...] = (
        "SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN",
    )
    _QUERY_BLOCKED_TOKENS: tuple[str, ...] = (
        " INTO ", ";DROP", ";TRUNCATE", ";DELETE", ";UPDATE", ";INSERT",
        ";ALTER", ";CREATE", ";GRANT", ";REVOKE", "EXECUTE IMMEDIATE",
    )

    @classmethod
    def validate_readonly_query(cls, sql: str) -> str:
        """읽기 전용 쿼리만 허용. 위반 시 ValueError."""
        if not sql or not isinstance(sql, str):
            raise ValueError("빈 쿼리")
        stripped = sql.strip().rstrip(";")
        up = stripped.upper().lstrip()
        if not any(up.startswith(p) for p in cls._QUERY_READONLY_PREFIXES):
            raise ValueError("읽기 전용(SELECT/WITH/SHOW/DESC/EXPLAIN)만 허용됩니다")
        # 세미콜론으로 다중 문장 방지
        if ";" in stripped:
            raise ValueError("다중 문장은 허용되지 않습니다 (세미콜론 제거)")
        up_nocase = (" " + up + " ").replace("\n", " ").replace("\t", " ")
        for bad in cls._QUERY_BLOCKED_TOKENS:
            if bad in up_nocase:
                raise ValueError(f"금지 키워드 포함: {bad.strip()}")
        return stripped

    def run_readonly_query(self, sql: str, limit: int = 500) -> dict[str, Any]:
        """읽기 전용 쿼리 실행 + 행수 제한. {columns, rows, row_count, elapsed_ms} 반환.

        값은 JSON-직렬화 가능하도록 _json_safe 로 변환 (LOB, 공간데이터, datetime, Decimal, bytes 등).
        """
        import time
        safe_sql = self.validate_readonly_query(sql)
        t0 = time.time()
        with self._conn.cursor() as cur:
            cur.execute(safe_sql)
            if cur.description is None:
                return {"columns": [], "rows": [], "row_count": 0,
                        "elapsed_ms": int((time.time() - t0) * 1000)}
            cols = [d[0] for d in cur.description]
            raw_rows = cur.fetchmany(int(limit) if limit else 500)
        safe_rows = [[_json_safe(v) for v in r] for r in raw_rows]
        return {
            "columns": cols,
            "rows": safe_rows,
            "row_count": len(safe_rows),
            "elapsed_ms": int((time.time() - t0) * 1000),
            "truncated": len(safe_rows) >= (int(limit) if limit else 500),
        }


def _json_safe(v: Any) -> Any:
    """DB 반환값 → JSON 직렬화 가능한 파이썬 원시값으로 변환.

    - datetime/date → ISO8601 문자열
    - Decimal → float (정밀 손실 가능하나 UI 표시용)
    - bytes/bytearray → b64 문자열 (선두 "b64:" 프리픽스)
    - Oracle LOB(Object with read()) → 문자열 (최대 10KB)
    - Oracle SDO_GEOMETRY 등 DbObject → dict 요약 또는 "<타입명>"
    - 기타 객체 → str()
    """
    if v is None:
        return None
    # 기본 직렬화 가능 타입
    if isinstance(v, (str, bool, int, float)):
        return v
    # datetime / date / time
    import datetime as _dt
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        return v.isoformat()
    # Decimal
    try:
        from decimal import Decimal as _Decimal
        if isinstance(v, _Decimal):
            return float(v)
    except Exception:
        pass
    # bytes
    if isinstance(v, (bytes, bytearray, memoryview)):
        try:
            import base64
            return "b64:" + base64.b64encode(bytes(v)).decode("ascii")
        except Exception:
            return f"<bytes {len(v)}>"
    # Oracle LOB (CLOB/BLOB/NCLOB) — .read() 보유
    if hasattr(v, "read") and callable(getattr(v, "read", None)):
        try:
            data = v.read()
            if isinstance(data, bytes):
                return _json_safe(data)
            s = str(data)
            return s if len(s) <= 10240 else s[:10240] + f"... (truncated, total {len(s)} chars)"
        except Exception as e:
            return f"<LOB read error: {e}>"
    # Oracle DbObject (SDO_GEOMETRY 등 사용자 정의 객체)
    # Object(scalar attribute 조합) vs Collection(Varray/Nested Table) 구분
    if hasattr(v, "type") and (hasattr(v, "aslist") or hasattr(v, "asdict")):
        type_name = "OBJECT"
        try:
            type_name = f"{getattr(v.type, 'schema', '')}.{getattr(v.type, 'name', '')}".strip(".")
        except Exception:
            pass
        # 1) Object 라면 attribute 를 개별 조회 (DbObjectType.attributes 순회)
        try:
            attrs = getattr(v.type, "attributes", None)
            if attrs:
                d: dict[str, Any] = {}
                for a in attrs:
                    aname = getattr(a, "name", None)
                    if not aname:
                        continue
                    try:
                        aval = getattr(v, aname)
                        d[aname] = _json_safe(aval)
                    except Exception as ae:
                        d[aname] = f"<attr {aname} error: {ae}>"
                return {"__type__": type_name, "value": d}
        except Exception:
            pass
        # 2) Collection 이면 aslist
        try:
            if hasattr(v, "aslist"):
                return {"__type__": type_name, "value": [_json_safe(x) for x in v.aslist()]}
        except Exception:
            pass
        # 3) 폴백
        return f"<{type_name}>"
    # 그 외
    try:
        return str(v)
    except Exception:
        return repr(v)

    def qualify(self, schema: str, table: str) -> str:
        """스키마.테이블 안전한 식별자로 반환 (기본: 따옴표 없음)."""
        if schema:
            return f"{schema}.{table}"
        return table

    # 기본 호환성 — 서브클래스에서 오버라이드
    def accounts(self) -> list[dict[str, Any]]:
        """DB 계정 목록 조회 (미지원 커넥터는 빈 리스트 반환)."""
        return []

    # ── DB 계정·권한 관리 (REQ-DHUB-005-004-002) ──
    # 각 커넥터는 아래 메서드를 DB별 DDL/DCL 로 구현한다.
    # 공통 시그니처로 API 레이어에서 일관되게 호출·감사로그 기록 가능.
    def create_account(self, account_name: str, password: str) -> dict[str, Any]:
        """새 DB 계정 생성. 미지원 커넥터는 UnsupportedError."""
        raise UnsupportedError(f"{self.driver_name}: create_account 미지원")

    def drop_account(self, account_name: str) -> dict[str, Any]:
        """계정 제거. 미지원 커넥터는 UnsupportedError."""
        raise UnsupportedError(f"{self.driver_name}: drop_account 미지원")

    def change_password(self, account_name: str, new_password: str) -> dict[str, Any]:
        """계정 비밀번호 변경."""
        raise UnsupportedError(f"{self.driver_name}: change_password 미지원")

    def grant(self, account_name: str, privileges: list[str],
                 schema: str | None = None, table: str | None = None) -> dict[str, Any]:
        """권한 부여. privileges: ["SELECT","INSERT","UPDATE","DELETE","ALL"] 등."""
        raise UnsupportedError(f"{self.driver_name}: grant 미지원")

    def revoke(self, account_name: str, privileges: list[str],
                 schema: str | None = None, table: str | None = None) -> dict[str, Any]:
        """권한 회수."""
        raise UnsupportedError(f"{self.driver_name}: revoke 미지원")

    # 식별자 안전화 (SQL 주입 방지) — 서브클래스에서 DB별 인용 규칙으로 오버라이드 권장
    @staticmethod
    def _safe_ident(name: str) -> str:
        """식별자(계정/스키마/테이블) 안전화. 영숫자/언더스코어만 허용."""
        import re
        if not name or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            raise ValueError(f"Invalid identifier: {name!r}")
        return name

    _ALLOWED_PRIVS: set[str] = {
        "SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE",
        "REFERENCES", "TRIGGER", "EXECUTE", "USAGE", "CONNECT", "TEMP",
        "ALL", "ALL PRIVILEGES",
    }

    @classmethod
    def _safe_privs(cls, privileges: list[str]) -> list[str]:
        out = []
        for p in privileges or []:
            pu = (p or "").strip().upper()
            if pu not in cls._ALLOWED_PRIVS:
                raise ValueError(f"Unsupported privilege: {p!r}")
            out.append(pu)
        if not out:
            raise ValueError("privileges 비어 있음")
        return out
