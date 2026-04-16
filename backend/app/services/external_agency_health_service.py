"""외부기관 연계포인트 점검 서비스 (REQ-DHUB-005-005-001).

지원 유형:
- API: httpx 기반 HEAD/GET 호출 → 상태코드·응답시간·인증
- DB : SQLAlchemy sync create_engine + SELECT 1
- MQ : Kafka bootstrap.servers TCP 연결 확인(선택: Redis PING)

결과는 collection_external_agency_health_log 에 적재하고,
agency.last_health_* 필드를 업데이트한다. 연속실패 임계치 초과 시:
 - alert_enabled=True → 알림 디스패치
 - failover_endpoint 존재 + 활성화 → 핫스왑
"""
from __future__ import annotations

import logging
import socket
import time
import uuid
from contextlib import closing
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret
from app.models.collection import (
    CollectionExternalAgency,
    CollectionExternalAgencyHealthLog,
)

logger = logging.getLogger(__name__)


STATUS_HEALTHY = "HEALTHY"
STATUS_DEGRADED = "DEGRADED"
STATUS_UNHEALTHY = "UNHEALTHY"
STATUS_UNKNOWN = "UNKNOWN"


# ── 유형별 점검 ──────────────────────────────────────────────────────────
def _check_api(endpoint: str, timeout: int, cfg: dict, auth_method: str,
               auth_config: dict | None, api_key: str | None) -> dict:
    cfg = cfg or {}
    method = (cfg.get("method") or "GET").upper()
    verify_tls = cfg.get("verify_tls", True)
    headers: dict[str, str] = dict(cfg.get("headers") or {})

    if auth_method == "API_KEY" and api_key:
        key_header = (auth_config or {}).get("header", "X-API-Key")
        headers[key_header] = api_key
    elif auth_method == "BASIC" and auth_config:
        auth = (auth_config.get("user", ""), auth_config.get("password", ""))
    else:
        auth = None

    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=timeout, verify=verify_tls) as client:
            resp = client.request(method, endpoint, headers=headers, auth=auth)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        http_status = resp.status_code
        if 200 <= http_status < 400:
            status = STATUS_HEALTHY if latency_ms < (cfg.get("slow_ms") or 2000) else STATUS_DEGRADED
            msg = f"HTTP {http_status} ({latency_ms}ms)"
            return {"status": status, "latency_ms": latency_ms, "http_status": http_status,
                    "error_code": None, "message": msg}
        else:
            return {"status": STATUS_UNHEALTHY, "latency_ms": latency_ms, "http_status": http_status,
                    "error_code": f"HTTP_{http_status}", "message": f"HTTP {http_status}"}
    except httpx.TimeoutException as e:
        return {"status": STATUS_UNHEALTHY, "latency_ms": int((time.perf_counter() - t0) * 1000),
                "http_status": None, "error_code": "TIMEOUT", "message": f"Timeout: {e}"}
    except httpx.ConnectError as e:
        return {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                "error_code": "CONNECT_ERROR", "message": f"Connection failed: {e}"}
    except Exception as e:
        return {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                "error_code": "ERROR", "message": str(e)[:500]}


def _check_db(cfg: dict, timeout: int) -> dict:
    """DB 연계포인트 점검 — SQLAlchemy 경량 연결 + SELECT 1."""
    cfg = cfg or {}
    driver = (cfg.get("driver") or "postgresql").lower()
    host = cfg.get("host", "localhost")
    port = cfg.get("port", 5432)
    database = cfg.get("database", "")
    user = cfg.get("user", "")
    pwd = decrypt_secret(cfg.get("password_enc")) or cfg.get("password", "")

    url_map = {
        "postgresql": f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{database}",
        "mysql": f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{database}",
        "mssql": f"mssql+pyodbc://{user}:{pwd}@{host}:{port}/{database}",
        "oracle": f"oracle+oracledb://{user}:{pwd}@{host}:{port}/{database}",
    }
    url = url_map.get(driver)
    if not url:
        return {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                "error_code": "UNSUPPORTED_DRIVER", "message": f"지원하지 않는 driver: {driver}"}

    t0 = time.perf_counter()
    try:
        eng = create_engine(url, connect_args={"connect_timeout": timeout} if driver == "postgresql" else {},
                            pool_pre_ping=True, pool_size=1, max_overflow=0)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        latency_ms = int((time.perf_counter() - t0) * 1000)
        slow = cfg.get("slow_ms") or 1000
        status = STATUS_HEALTHY if latency_ms < slow else STATUS_DEGRADED
        return {"status": status, "latency_ms": latency_ms, "http_status": None,
                "error_code": None, "message": f"DB OK ({latency_ms}ms)"}
    except Exception as e:
        msg = str(e)[:500]
        code = "AUTH" if ("password" in msg.lower() or "authent" in msg.lower()) else "CONNECT_ERROR"
        return {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                "error_code": code, "message": msg}


def _check_mq(cfg: dict, timeout: int) -> dict:
    """MQ 연계포인트 점검 — Kafka bootstrap servers TCP 연결/Redis PING 등."""
    cfg = cfg or {}
    mq_type = (cfg.get("mq_type") or "KAFKA").upper()
    brokers = cfg.get("brokers") or cfg.get("host") or ""
    if isinstance(brokers, str):
        broker_list = [b.strip() for b in brokers.split(",") if b.strip()]
    else:
        broker_list = list(brokers or [])
    if not broker_list:
        return {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                "error_code": "NO_BROKER", "message": "브로커 미지정"}

    failures = []
    total_t0 = time.perf_counter()
    for b in broker_list:
        try:
            host, _, port = b.partition(":")
            port = int(port or (9092 if mq_type == "KAFKA" else 6379))
            with closing(socket.create_connection((host, port), timeout=timeout)):
                pass
        except Exception as e:
            failures.append(f"{b}: {e}")
    latency_ms = int((time.perf_counter() - total_t0) * 1000)

    if not failures:
        return {"status": STATUS_HEALTHY, "latency_ms": latency_ms, "http_status": None,
                "error_code": None, "message": f"{mq_type} OK ({len(broker_list)} brokers, {latency_ms}ms)"}
    if len(failures) < len(broker_list):
        return {"status": STATUS_DEGRADED, "latency_ms": latency_ms, "http_status": None,
                "error_code": "PARTIAL_BROKER_DOWN", "message": "; ".join(failures)[:500]}
    return {"status": STATUS_UNHEALTHY, "latency_ms": latency_ms, "http_status": None,
            "error_code": "ALL_BROKER_DOWN", "message": "; ".join(failures)[:500]}


# ── 메인 진입점 ──────────────────────────────────────────────────────────
def perform_health_check(
    db: Session,
    agency: CollectionExternalAgency,
    check_type: str = "MANUAL",
    commit: bool = True,
) -> CollectionExternalAgencyHealthLog:
    """연계포인트 유형별 점검 실행 → 로그 적재 + 기관 상태 업데이트.

    failover_endpoint 가 있고 primary 점검이 실패하면 failover 엔드포인트로 재시도한다.
    """
    endpoint_type = (agency.endpoint_type or "API").upper()
    timeout = agency.health_timeout_sec or 10
    cfg = agency.endpoint_config or {}
    api_key = decrypt_secret(agency.api_key_enc) if agency.api_key_enc else None
    failover_used = False

    # 1차: primary 엔드포인트
    if endpoint_type == "API":
        endpoint = agency.api_endpoint or cfg.get("url") or ""
        result = _check_api(endpoint, timeout, cfg, agency.auth_method or "NONE",
                            agency.auth_config, api_key) if endpoint else \
                 {"status": STATUS_UNHEALTHY, "latency_ms": None, "http_status": None,
                  "error_code": "NO_ENDPOINT", "message": "엔드포인트 미지정"}
    elif endpoint_type == "DB":
        result = _check_db(cfg, timeout)
    elif endpoint_type == "MQ":
        result = _check_mq(cfg, timeout)
    else:
        result = {"status": STATUS_UNKNOWN, "latency_ms": None, "http_status": None,
                  "error_code": "UNSUPPORTED", "message": f"지원하지 않는 유형: {endpoint_type}"}

    # 2차: failover (primary 가 UNHEALTHY + failover_endpoint 보유)
    if result["status"] == STATUS_UNHEALTHY and agency.failover_endpoint and endpoint_type == "API":
        fallback = _check_api(agency.failover_endpoint, timeout, cfg, agency.auth_method or "NONE",
                              agency.auth_config, api_key)
        if fallback["status"] in (STATUS_HEALTHY, STATUS_DEGRADED):
            fallback["message"] = "[FAILOVER] " + (fallback.get("message") or "")
            result = fallback
            failover_used = True

    log = CollectionExternalAgencyHealthLog(
        id=uuid.uuid4(),
        agency_id=agency.id,
        checked_at=datetime.now(),
        check_type=check_type,
        endpoint_type=endpoint_type,
        status=result["status"],
        latency_ms=result.get("latency_ms"),
        http_status=result.get("http_status"),
        error_code=result.get("error_code"),
        message=result.get("message"),
        detail=result,
        failover_used=failover_used,
    )
    db.add(log)

    # agency 집계 업데이트
    agency.last_health_check_at = log.checked_at
    agency.last_health_status = log.status
    agency.last_health_latency_ms = log.latency_ms
    agency.last_health_message = log.message
    if log.status == STATUS_HEALTHY:
        agency.consecutive_failures = 0
    elif log.status in (STATUS_UNHEALTHY, STATUS_DEGRADED):
        agency.consecutive_failures = (agency.consecutive_failures or 0) + 1

    # 연속 실패 임계 도달 → 알림 + 핫스왑 자동 전환
    if (agency.consecutive_failures or 0) >= (agency.alert_threshold_failures or 3):
        if log.status == STATUS_UNHEALTHY:
            # status 를 FAILED 로 변경
            if agency.status == "ACTIVE":
                agency.status = "FAILED"
            # 핫스왑 자동 활성화
            if agency.failover_endpoint and not agency.failover_active:
                agency.failover_active = True
                agency.failover_activated_at = datetime.now()

    if commit:
        db.commit()
    return log


def dispatch_health_alert(db: Session, agency: CollectionExternalAgency, log: CollectionExternalAgencyHealthLog) -> None:
    """장애 알림 발송 (EMAIL/SMS/WEBHOOK).

    alert_channels: [{"type": "WEBHOOK", "url": "..."}, {"type": "EMAIL", "to": "..."}]
    최소 구현: 웹훅 POST + 로그. 실제 메일/SMS 는 별도 게이트웨이 연동 시 확장.
    """
    if not agency.alert_enabled:
        return
    channels = agency.alert_channels or []
    if isinstance(channels, dict):
        channels = [channels]

    payload = {
        "agency_id": str(agency.id),
        "agency_name": agency.agency_name,
        "endpoint_type": agency.endpoint_type,
        "status": log.status,
        "error_code": log.error_code,
        "message": log.message,
        "consecutive_failures": agency.consecutive_failures,
        "checked_at": log.checked_at.isoformat() if log.checked_at else None,
    }

    sent = False
    for ch in channels:
        try:
            if ch.get("type") == "WEBHOOK" and ch.get("url"):
                with httpx.Client(timeout=5) as cli:
                    cli.post(ch["url"], json=payload)
                sent = True
            else:
                logger.info("[external-agency alert] (ch=%s) %s", ch.get("type"), payload)
                sent = True
        except Exception as e:
            logger.warning("external-agency alert 실패: ch=%s err=%s", ch, e)

    if sent:
        agency.alert_last_sent_at = datetime.now()


def sync_to_openmetadata(db: Session, agency: CollectionExternalAgency) -> None:
    """OpenMetadata 로 연계 현황/이력 동기화 (경량 스텁).

    실제 상세 스펙은 app.services.openmetadata_client 확장에서 다룬다.
    여기서는 om_last_sync_at / om_last_sync_status 만 업데이트하여 추적 가능하게 한다.
    """
    if not agency.om_service_name:
        return
    try:
        # TODO: 실제 openmetadata_client.upsert_custom_service(agency) 호출
        agency.om_last_sync_at = datetime.now()
        agency.om_last_sync_status = "SUCCESS"
    except Exception as e:
        agency.om_last_sync_at = datetime.now()
        agency.om_last_sync_status = "FAIL"
        logger.warning("OpenMetadata 동기화 실패 (agency=%s): %s", agency.id, e)


def compute_availability(db: Session, agency_id: uuid.UUID, days: int = 7) -> Optional[float]:
    """최근 N일 availability (%) = HEALTHY 비율."""
    since = datetime.now() - timedelta(days=days)
    q = select(
        CollectionExternalAgencyHealthLog.status
    ).where(
        CollectionExternalAgencyHealthLog.agency_id == agency_id,
        CollectionExternalAgencyHealthLog.checked_at >= since,
    )
    rows = db.execute(q).scalars().all()
    if not rows:
        return None
    total = len(rows)
    healthy = sum(1 for s in rows if s == STATUS_HEALTHY)
    return round(healthy * 100.0 / total, 2)
