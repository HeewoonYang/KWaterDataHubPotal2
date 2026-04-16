"""Tibero 커넥터 (Oracle 프로토콜 호환 stub).

Tibero는 Python 네이티브 드라이버가 PyPI에 공식 제공되지 않으므로, 실환경에서는 다음 중 택1:
1. JDBC + JayDeBeApi (jaydebeapi + Tibero JDBC jar)
2. Tibero ODBC + pyodbc (Tibero ODBC 드라이버 설치)
3. Tibero가 Oracle 호환 모드로 구성된 경우 oracledb Thick 모드로 대체 가능

본 스텁은 실제 연결을 시도하지 않고 ``UnsupportedError`` 를 발생시켜
운영 환경에서 설치를 명시적으로 요구한다.
"""
from __future__ import annotations

from typing import Any

from app.services.db_connectors.base import BaseConnector, TableMeta, UnsupportedError


class TiberoConnector(BaseConnector):
    driver_name = "tibero"
    driver_version = "stub"
    native_available = False   # 실환경 JDBC/ODBC 드라이버 설치 시 True 로 변경

    def _open(self):
        raise UnsupportedError(
            "Tibero 드라이버 미설치. 실환경에서는 jaydebeapi + Tibero JDBC jar 또는 "
            "Tibero ODBC 드라이버 + pyodbc 를 설치 후 TiberoConnector 를 재구현하세요."
        )

    def _close(self, conn):
        return

    def _ping_query(self) -> str:
        return "SELECT 1 FROM DUAL"

    def list_schemas(self) -> list[str]:
        return []

    def list_tables(self, schema: str | None = None) -> list[str]:
        return []

    def describe_table(self, schema: str, table: str) -> TableMeta:
        return TableMeta(schema=schema, name=table, columns=[], pk_columns=[])

    def row_count(self, schema: str, table: str) -> int:
        return 0

    def fetch(self, query: str, params=None, limit=None) -> list[tuple]:
        return []
