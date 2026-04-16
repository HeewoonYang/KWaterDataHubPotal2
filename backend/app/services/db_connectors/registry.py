"""커넥터 팩토리 — CollectionDataSource 또는 직접 구성에서 커넥터 획득."""
from __future__ import annotations

from typing import Any

from app.core.crypto import decrypt_secret
from app.services.db_connectors.base import BaseConnector, ConnectionConfig, UnsupportedError
from app.services.db_connectors.hana import HanaConnector
from app.services.db_connectors.mssql import MssqlConnector
from app.services.db_connectors.oracle import OracleConnector
from app.services.db_connectors.postgres import PostgresConnector
from app.services.db_connectors.tibero import TiberoConnector


_REGISTRY: dict[str, type[BaseConnector]] = {
    "POSTGRESQL": PostgresConnector,
    "POSTGRES": PostgresConnector,
    "PG": PostgresConnector,
    "ORACLE": OracleConnector,
    "SAP_HANA": HanaConnector,
    "HANA": HanaConnector,
    "MSSQL": MssqlConnector,
    "SQLSERVER": MssqlConnector,
    "TIBERO": TiberoConnector,
}


def _norm(t: str) -> str:
    return (t or "").upper().replace("-", "_").strip()


def get_connector(data_source: Any) -> BaseConnector:
    """CollectionDataSource 인스턴스 또는 dict 로부터 커넥터 생성."""
    if hasattr(data_source, "db_type"):
        db_type = _norm(data_source.db_type)
        # 저장된 암호문을 복호화해 실제 연결에 사용 (레거시 평문은 그대로 통과)
        raw_pw = data_source.connection_password_enc
        try:
            pw = decrypt_secret(raw_pw) if raw_pw else None
        except Exception:
            pw = raw_pw  # 복호화 실패 시 원문으로 시도 (레거시 데이터 호환)
        config = ConnectionConfig(
            db_type=db_type,
            host=data_source.connection_host or "",
            port=int(data_source.connection_port or 0),
            database=data_source.connection_db,
            schema=data_source.connection_schema,
            user=data_source.connection_user,
            password=pw,
            options=data_source.connection_options or {},
        )
    elif isinstance(data_source, dict):
        db_type = _norm(data_source.get("db_type"))
        config = ConnectionConfig(
            db_type=db_type,
            host=data_source.get("host", ""),
            port=int(data_source.get("port", 0)),
            database=data_source.get("database"),
            schema=data_source.get("schema"),
            user=data_source.get("user"),
            password=data_source.get("password"),
            options=data_source.get("options") or {},
        )
    else:
        raise ValueError("data_source must be CollectionDataSource or dict")

    cls = _REGISTRY.get(db_type)
    if cls is None:
        raise UnsupportedError(f"지원하지 않는 DB유형: {db_type}")
    return cls(config)


def available_drivers() -> list[dict[str, Any]]:
    """현재 설치되어 있는 드라이버 목록 (status=OK/MISSING)."""
    seen: dict[str, type[BaseConnector]] = {}
    for key, cls in _REGISTRY.items():
        if cls not in seen.values():
            seen[cls.driver_name] = cls
    result = []
    for name, cls in seen.items():
        result.append({
            "driver": name,
            "version": cls.driver_version,
            "available": cls.native_available,
            "status": "OK" if cls.native_available else "MISSING",
        })
    return result
