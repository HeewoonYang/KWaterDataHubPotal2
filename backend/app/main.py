import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.api.router import api_router
from app.core import token_blacklist
from app.core.logging_config import configure_logging, get_logger, request_id_ctx
from app.database import async_session, engine

# 부팅 시 구조화 로깅 설정 (stdout JSON)
configure_logging("DEBUG" if settings.DEBUG else "INFO")
logger = get_logger(__name__)


# ── Lifespan: 애플리케이션 수명주기 리소스 관리 ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("startup", component="redis", url=settings.REDIS_URL)
    except Exception as e:
        logger.warning("startup.redis_failed", error=str(e))
        app.state.redis = None

    yield

    logger.info("shutdown.begin")
    try:
        if app.state.redis is not None:
            await app.state.redis.close()
    except Exception as e:
        logger.warning("shutdown.redis_close_failed", error=str(e))
    try:
        await token_blacklist.close()
    except Exception as e:
        logger.warning("shutdown.blacklist_close_failed", error=str(e))
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning("shutdown.engine_dispose_failed", error=str(e))
    logger.info("shutdown.done")


app = FastAPI(
    title=settings.APP_NAME,
    docs_url=None if not settings.DEBUG else "/docs",
    redoc_url=None if not settings.DEBUG else "/redoc",
    lifespan=lifespan,
)

# ── 오프라인 Swagger UI (폐쇄망 대응) ──
# DEBUG=false(운영)에서는 CDN 의존 없는 로컬 번들 Swagger 제공
if not settings.DEBUG:
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{settings.APP_NAME} - Swagger UI",
            swagger_js_url="/api/v1/static/swagger-ui-bundle.js",
            swagger_css_url="/api/v1/static/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc():
        return get_redoc_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{settings.APP_NAME} - ReDoc",
            redoc_js_url="/api/v1/static/redoc.standalone.js",
        )

# Prometheus 메트릭 자동 계측 (/metrics 노출)
Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/metrics", "/livez", "/readyz", "/health"],
).instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Correlation ID 미들웨어 (X-Request-ID) ──
class RequestIDMiddleware(BaseHTTPMiddleware):
    """모든 요청에 X-Request-ID 부여. 하위 로그에 자동 전파."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)


# ── 감사 로그 미들웨어 ──
class AuditLogMiddleware(BaseHTTPMiddleware):
    """모든 API 요청을 OperationAccessLog에 자동 기록"""

    SKIP_PATHS = {"/health", "/livez", "/readyz", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def _extract_user_id(self, request: Request) -> str | None:
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return None
        try:
            payload = jwt.decode(auth[7:], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload.get("sub")
        except Exception:
            return None

    def _derive_action(self, method: str, path: str) -> str:
        if "/auth/login" in path:
            return "LOGIN"
        if "/auth/logout" in path:
            return "LOGOUT"
        if "/download" in path:
            return "DOWNLOAD"
        if path.startswith("/api/v1/admin"):
            return "ADMIN_ACTION"
        if method == "GET":
            return "READ"
        return "API_CALL"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in self.SKIP_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        start = datetime.now()
        response = await call_next(request)
        elapsed = (datetime.now() - start).total_seconds()

        try:
            user_id = self._extract_user_id(request)
            action = self._derive_action(request.method, path)
            client_ip = request.client.host if request.client else None

            from app.models.operation import OperationAccessLog

            async with async_session() as session:
                log = OperationAccessLog(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id) if user_id else None,
                    action=action,
                    resource_type="API",
                    request_method=request.method,
                    request_path=path[:500],
                    client_ip=client_ip,
                    user_agent=str(request.headers.get("user-agent", ""))[:500],
                    response_status=response.status_code,
                    result="SUCCESS" if response.status_code < 400 else ("DENIED" if response.status_code in (401, 403) else "FAIL"),
                    detail={"elapsed_sec": round(elapsed, 3), "request_id": request_id_ctx.get()},
                    logged_at=datetime.now(),
                )
                session.add(log)
                await session.commit()
        except Exception:
            pass

        return response


app.add_middleware(AuditLogMiddleware)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# ── 정적 파일 (Swagger UI 오프라인 번들 등) ──
import pathlib
_static_dir = pathlib.Path(__file__).parent / "static"
if _static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount(f"{settings.API_V1_PREFIX}/static", StaticFiles(directory=str(_static_dir)), name="api-static")


# ── Health / Readiness / Liveness ──
@app.get("/livez")
async def livez():
    """Liveness: 프로세스가 살아있기만 하면 OK. 의존성 체크 금지."""
    return {"status": "alive"}


@app.get("/readyz")
async def readyz(request: Request):
    """Readiness: DB·Redis 등 필수 의존성이 정상일 때만 200."""
    checks: dict[str, str] = {}

    try:
        async with async_session() as s:
            await s.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"fail: {e.__class__.__name__}"

    try:
        if getattr(request.app.state, "redis", None) is not None:
            await request.app.state.redis.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "uninitialized"
    except Exception as e:
        checks["redis"] = f"fail: {e.__class__.__name__}"

    if any(v != "ok" for v in checks.values()):
        raise HTTPException(status_code=503, detail={"ready": False, "checks": checks})
    return {"ready": True, "checks": checks}


@app.get("/health")
async def health_check():
    """레거시 호환용. 신규 Probe 는 /livez, /readyz 사용 권장."""
    return {"status": "ok"}
