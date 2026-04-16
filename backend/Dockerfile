# syntax=docker/dockerfile:1

# ───────── 1) Builder: 의존성 컴파일만 담당 ─────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libxmlsec1-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ───────── 2) Runtime: 최소 실행 이미지 ─────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    WEB_CONCURRENCY=4

# 폐쇄망 빌드 대응: vendor/ 에 오프라인 파일이 있으면 미리 복사
# 인터넷망에서는 vendor/ 가 비어있어도 .gitkeep만 복사 → curl 다운로드 fallback
COPY vendor/ /tmp/vendor/

# 런타임 전용 shared library + healthcheck용 curl + Oracle 구버전 지원용 Instant Client
# Oracle 11g 이하는 python-oracledb Thin 모드 미지원 → Thick 모드 필수 (Instant Client 필요)
# Instant Client basic-lite(약 45MB) + libaio 로 최소 구성
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libxmlsec1-openssl \
        unzip \
        curl \
        ca-certificates && \
    # libaio: Debian bookworm(libaio1t64) / bullseye(libaio1) 양쪽 호환 처리
    (apt-get install -y --no-install-recommends libaio1t64 || apt-get install -y --no-install-recommends libaio1) && \
    # libaio.so.1 심볼릭 링크: bookworm 의 T64 전환(libaio.so.1t64) 을 Oracle Client 가 찾는 이름으로 매핑
    (test -e /usr/lib/x86_64-linux-gnu/libaio.so.1 || \
      (test -e /usr/lib/x86_64-linux-gnu/libaio.so.1t64 && ln -sf libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1) || true) && \
    # Oracle Instant Client: vendor/ 로컬 파일 우선, 없으면 원격 다운로드 (폐쇄망 대응)
    # 인터넷망: 자동 다운로드  /  폐쇄망: backend/vendor/instantclient-basiclite-linux.zip 에 미리 복사
    (cp /tmp/vendor/instantclient-basiclite-linux*.zip /tmp/ic.zip 2>/dev/null || \
      curl -fsSLo /tmp/ic.zip \
        https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basiclite-linux.x64-21.15.0.0.0dbru.zip) && \
    rm -rf /tmp/vendor && \
    mkdir -p /opt/oracle && \
    unzip -q /tmp/ic.zip -d /opt/oracle && \
    mv /opt/oracle/instantclient_* /opt/oracle/instantclient && \
    rm -f /tmp/ic.zip && \
    echo "/opt/oracle/instantclient" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig && \
    apt-get purge -y --auto-remove unzip && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system --gid 1001 appuser && \
    useradd  --system --uid 1001 --gid appuser --home-dir /app --create-home appuser

ENV ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient \
    LD_LIBRARY_PATH=/opt/oracle/instantclient

WORKDIR /app

# 빌더에서 설치된 파이썬 패키지만 복사
COPY --from=builder /install /usr/local

# 애플리케이션 코드
COPY --chown=appuser:appuser . /app

# non-root 로 실행
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/livez || exit 1

# 프로덕션 기본 커맨드 (--reload 제거, multi-worker)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-4} --proxy-headers --forwarded-allow-ips='*'"]
