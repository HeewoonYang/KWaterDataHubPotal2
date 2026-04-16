"""MS SQL Server 커넥터 (pymssql)."""
from __future__ import annotations

from typing import Any

try:
    import pymssql
    _AVAILABLE = True
except ImportError:
    pymssql = None
    _AVAILABLE = False

from app.services.db_connectors.base import BaseConnector, ConnectionError, TableMeta, UnsupportedError


class MssqlConnector(BaseConnector):
    driver_name = "mssql"
    driver_version = pymssql.__version__ if _AVAILABLE else "n/a"
    native_available = _AVAILABLE

    def _open(self):
        if not _AVAILABLE:
            raise UnsupportedError("pymssql 미설치")
        try:
            return pymssql.connect(
                server=self.config.host, port=self.config.port,
                user=self.config.user, password=self.config.password,
                database=self.config.database,
                timeout=self.config.timeout_sec,
            )
        except Exception as e:
            raise ConnectionError(f"MSSQL connection failed: {e}") from e

    def _close(self, conn):
        conn.close()

    def _ping_query(self) -> str:
        return "SELECT 1 AS ping, SUSER_NAME(), DB_NAME()"

    def list_schemas(self) -> list[str]:
        rows = self.fetch("SELECT name FROM sys.schemas ORDER BY name")
        return [r[0] for r in rows]

    def list_tables(self, schema: str | None = None) -> list[str]:
        if schema:
            rows = self.fetch(
                "SELECT t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id "
                "WHERE s.name=%s ORDER BY t.name", (schema,),
            )
        else:
            rows = self.fetch(
                "SELECT s.name + '.' + t.name FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id "
                "ORDER BY s.name, t.name"
            )
        return [r[0] for r in rows]

    def describe_table(self, schema: str, table: str) -> TableMeta:
        cols = self.fetch(
            "SELECT c.name, ty.name, c.is_nullable, c.max_length, c.precision, c.scale "
            "FROM sys.columns c JOIN sys.types ty ON c.user_type_id=ty.user_type_id "
            "JOIN sys.tables t ON c.object_id=t.object_id JOIN sys.schemas s ON t.schema_id=s.schema_id "
            "WHERE s.name=%s AND t.name=%s ORDER BY c.column_id",
            (schema, table),
        )
        pk = [r[0] for r in self.fetch(
            "SELECT c.name FROM sys.indexes i JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id "
            "JOIN sys.columns c ON ic.object_id=c.object_id AND ic.column_id=c.column_id "
            "JOIN sys.tables t ON i.object_id=t.object_id JOIN sys.schemas s ON t.schema_id=s.schema_id "
            "WHERE s.name=%s AND t.name=%s AND i.is_primary_key=1 ORDER BY ic.key_ordinal",
            (schema, table),
        )]
        return TableMeta(
            schema=schema, name=table,
            columns=[{
                "name": c[0], "type": c[1], "nullable": bool(c[2]),
                "length": c[3], "precision": c[4], "scale": c[5],
            } for c in cols],
            pk_columns=pk,
        )

    def row_count(self, schema: str, table: str) -> int:
        fq = self.qualify(schema, table)
        return self.fetch(f"SELECT COUNT(*) FROM {fq}")[0][0]

    def fetch(self, query: str, params=None, limit=None) -> list[tuple]:
        cur = self._conn.cursor()
        try:
            cur.execute(query, params or ())
            if cur.description is None:
                return []
            if limit:
                return cur.fetchmany(limit)
            return cur.fetchall()
        finally:
            cur.close()

    def accounts(self) -> list[dict[str, Any]]:
        try:
            rows = self.fetch(
                "SELECT name, type_desc, create_date, is_disabled FROM sys.server_principals "
                "WHERE type IN ('S','U','G') ORDER BY name"
            )
            return [{
                "account_name": r[0], "status": r[1],
                "created": r[2].isoformat() if r[2] else None,
                "privileges": {"disabled": bool(r[3])},
            } for r in rows]
        except Exception:
            return []
