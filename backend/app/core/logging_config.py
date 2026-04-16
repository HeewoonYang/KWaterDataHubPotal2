"""
구조화 로깅 설정 (structlog + stdout JSON)

K8s 환경에서는 파일 로그 대신 stdout JSON 으로 출력해야 Fluent Bit/Loki 등이 수집 가능하다.
correlation_id (X-Request-ID) 를 contextvar 로 바인딩해 같은 요청의 모든 로그에 자동 포함한다.
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# 요청 단위 컨텍스트 (미들웨어에서 세팅)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def _add_request_id(logger, method_name, event_dict):
    """structlog processor: context var 의 request_id 를 모든 로그에 주입."""
    event_dict["request_id"] = request_id_ctx.get()
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """앱 부팅 시 1회 호출."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 표준 logging: stdout 으로만 출력 (파일 로거 금지)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
