"""SAP HANA 커넥터 (hdbcli)."""
from __future__ import annotations

from typing import Any

try:
    from hdbcli import dbapi
    _AVAILABLE = True
except ImportError:
    dbapi = None
    _AVAILABLE = False

from app.services.db_connectors.base import BaseConnector, ConnectionError, TableMeta, UnsupportedError


class HanaConnector(BaseConnector):
    driver_name = "sap_hana"
    driver_version = "hdbcli" if _AVAILABLE else "n/a"
    native_available = _AVAILABLE

    def _open(self):
        if not _AVAILABLE:
            raise UnsupportedError("hdbcli 미설치")
        try:
            return dbapi.connect(
                address=self.config.host, port=self.config.port,
                user=self.config.user, password=self.config.password,
                currentSchema=self.config.schema or None,
                encrypt=self.config.ssl,
            )
        except Exception as e:
            raise ConnectionError(f"SAP HANA connection failed: {e}") from e

    def _close(self, conn):
        conn.close()

    def _ping_query(self) -> str:
        return "SELECT 1 AS ping, CURRENT_USER, CURRENT_SCHEMA FROM DUMMY"

    def list_schemas(self) -> list[str]:
        rows = self.fetch("SELECT SCHEMA_NAME FROM SCHEMAS ORDER BY SCHEMA_NAME")
        return [r[0] for r in rows]

    def list_tables(self, schema: str | None = None) -> list[str]:
        if schema:
            rows = self.fetch(
                "SELECT TABLE_NAME FROM TABLES WHERE SCHEMA_NAME=? ORDER BY TABLE_NAME",
                (schema.upper(),),
            )
        else:
            rows = self.fetch(
                "SELECT SCHEMA_NAME || '.' || TABLE_NAME FROM TABLES ORDER BY SCHEMA_NAME, TABLE_NAME"
            )
        return [r[0] for r in rows]

    def describe_table(self, schema: str, table: str) -> TableMeta:
        cols = self.fetch(
            "SELECT COLUMN_NAME, DATA_TYPE_NAME, IS_NULLABLE, LENGTH, SCALE "
            "FROM TABLE_COLUMNS WHERE SCHEMA_NAME=? AND TABLE_NAME=? ORDER BY POSITION",
            (schema.upper(), table.upper()),
        )
        pk = [r[0] for r in self.fetch(
            "SELECT COLUMN_NAME FROM CONSTRAINTS WHERE SCHEMA_NAME=? AND TABLE_NAME=? AND IS_PRIMARY_KEY='TRUE' ORDER BY POSITION",
            (schema.upper(), table.upper()),
        )]
        return TableMeta(
            schema=schema, name=table,
            columns=[{
                "name": c[0], "type": c[1], "nullable": c[2] == "TRUE",
                "length": c[3], "scale": c[4],
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
                "SELECT USER_NAME, USER_MODE, CREATE_TIME, VALID_FROM, VALID_UNTIL "
                "FROM USERS ORDER BY USER_NAME"
            )
            return [{
                "account_name": r[0], "status": r[1],
                "created": r[2].isoformat() if r[2] else None,
                "privileges": {"valid_from": r[3].isoformat() if r[3] else None,
                                "valid_until": r[4].isoformat() if r[4] else None},
            } for r in rows]
        except Exception:
            return []
