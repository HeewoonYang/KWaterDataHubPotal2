"""이기종 DB 커넥터 프레임워크 (REQ-DHUB-005-003).

지원 DB 유형:
- POSTGRESQL : psycopg (built-in)
- ORACLE     : oracledb (Thin/Thick)
- SAP_HANA   : hdbcli
- MSSQL      : pymssql
- TIBERO     : JDBC 기반 (실환경 Tibero 드라이버 필요, 기본 stub)

사용법:
    from app.services.db_connectors import get_connector
    conn = get_connector(data_source)  # CollectionDataSource 인스턴스
    with conn.connect() as c:
        c.test()                       # 연결 테스트
        c.list_schemas()               # 스키마 목록
        c.list_tables(schema)          # 테이블 목록
        c.describe_table(schema, tbl)  # 컬럼 메타
        c.row_count(schema, tbl)       # 행수
        c.checksum(schema, tbl, pk)    # MD5 체크섬
        c.fetch(query, params, limit)  # 쿼리 실행
"""
from app.services.db_connectors.base import BaseConnector, ConnectionError, UnsupportedError
from app.services.db_connectors.registry import get_connector, available_drivers

__all__ = ["BaseConnector", "ConnectionError", "UnsupportedError", "get_connector", "available_drivers"]
