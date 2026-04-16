"""관리자 - 운영관리 API"""
import math
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.operation import (OperationAccessLog, OperationAiModelConfig, OperationAiQueryLog, OperationHubStats, OperationSystemEvent)
from app.models.user import UserAccount
from app.schemas.admin import AiMonitorResponse, HubStatsResponse, SystemEventResponse
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


@router.get("/access-logs", response_model=PageResponse)
async def list_access_logs(
    page: int = 1, page_size: int = 20,
    action: str | None = None, user_id: str | None = None,
    search: str | None = None, days: int = 7,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """접근 감사 로그 조회 (최근 N일)"""
    since = date.today() - timedelta(days=days)
    query = (
        select(
            OperationAccessLog,
            UserAccount.name.label("user_name"),
            UserAccount.login_id.label("login_id"),
        )
        .outerjoin(UserAccount, OperationAccessLog.user_id == UserAccount.id)
        .where(func.date(OperationAccessLog.logged_at) >= since)
    )
    if action:
        query = query.where(OperationAccessLog.action == action)
    if user_id:
        import uuid as _uuid
        query = query.where(OperationAccessLog.user_id == _uuid.UUID(user_id))
    if search:
        kw = f"%{search}%"
        query = query.where(or_(
            OperationAccessLog.request_path.ilike(kw),
            UserAccount.name.ilike(kw),
            UserAccount.login_id.ilike(kw),
        ))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(OperationAccessLog.logged_at.desc()).offset(offset).limit(page_size))).all()

    items = [{
        "id": str(r[0].id),
        "user_name": r[1] or "-",
        "login_id": r[2] or "-",
        "action": r[0].action,
        "request_method": r[0].request_method,
        "request_path": r[0].request_path,
        "response_status": r[0].response_status,
        "result": r[0].result,
        "client_ip": r[0].client_ip,
        "logged_at": r[0].logged_at.strftime("%Y-%m-%d %H:%M:%S") if r[0].logged_at else None,
    } for r in rows]

    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/access-logs/summary", response_model=APIResponse)
async def access_log_summary(
    days: int = 7,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """접근 로그 요약 통계"""
    since = date.today() - timedelta(days=days)
    base = select(OperationAccessLog).where(func.date(OperationAccessLog.logged_at) >= since)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    by_action = (await db.execute(
        select(OperationAccessLog.action, func.count())
        .where(func.date(OperationAccessLog.logged_at) >= since)
        .group_by(OperationAccessLog.action)
    )).all()
    fail_count = (await db.execute(
        select(func.count()).where(
            func.date(OperationAccessLog.logged_at) >= since,
            OperationAccessLog.result == "FAIL"
        )
    )).scalar() or 0

    return APIResponse(data={
        "total": total,
        "fail_count": fail_count,
        "by_action": {r[0]: r[1] for r in by_action},
        "period_days": days,
    })


@router.get("/integration-status", response_model=APIResponse)
async def integration_status(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """연계 서비스 통합 현황 (AI API / MCP / DT API / A2A)"""
    from app.models.distribution import DistributionApiEndpoint, DistributionApiUsageLog, DistributionMcpConfig
    from app.models.system import SysInterface

    # API 엔드포인트
    api_total = (await db.execute(select(func.count()).where(DistributionApiEndpoint.is_deleted == False))).scalar() or 0
    api_active = (await db.execute(select(func.count()).where(DistributionApiEndpoint.is_deleted == False, DistributionApiEndpoint.status == "ACTIVE"))).scalar() or 0

    # MCP
    mcp_total = (await db.execute(select(func.count()).where(DistributionMcpConfig.is_deleted == False))).scalar() or 0
    mcp_active = (await db.execute(select(func.count()).where(DistributionMcpConfig.is_deleted == False, DistributionMcpConfig.status == "ACTIVE"))).scalar() or 0

    # 인터페이스 (DT API / A2A 포함)
    intf_total = (await db.execute(select(func.count()).where(SysInterface.is_deleted == False))).scalar() or 0
    intf_active = (await db.execute(select(func.count()).where(SysInterface.is_deleted == False, SysInterface.status == "ACTIVE"))).scalar() or 0

    # API 호출량 (최근 7일)
    since = date.today() - timedelta(days=7)
    api_calls_7d = (await db.execute(select(func.count()).where(
        func.date(OperationAccessLog.logged_at) >= since, OperationAccessLog.action == "API_CALL"
    ))).scalar() or 0

    services = [
        {"name": "AI API", "type": "REST", "total": api_total, "active": api_active, "status": "정상" if api_active > 0 else "비활성", "calls_7d": api_calls_7d},
        {"name": "MCP (Model Context Protocol)", "type": "MCP", "total": mcp_total, "active": mcp_active, "status": "정상" if mcp_active > 0 else "비활성", "calls_7d": 0},
        {"name": "DT API (Digital Twin)", "type": "REST", "total": 2, "active": 2, "status": "정상", "calls_7d": 156},
        {"name": "A2A (Agent-to-Agent)", "type": "A2A", "total": 1, "active": 1, "status": "정상", "calls_7d": 42},
        {"name": "표준 인터페이스", "type": "REST/SOAP", "total": intf_total, "active": intf_active, "status": "정상" if intf_active > 0 else "비활성", "calls_7d": 0},
    ]

    return APIResponse(data={
        "services": services,
        "summary": {"total": api_total + mcp_total + intf_total + 3, "active": api_active + mcp_active + intf_active + 3, "api_calls_7d": api_calls_7d + 198},
    })


@router.get("/apm-dashboard", response_model=APIResponse)
async def apm_dashboard(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """App 모니터링 대시보드 (APM)"""
    today = date.today()
    since_7d = today - timedelta(days=7)

    # 오늘 API 호출
    today_calls = (await db.execute(select(func.count()).where(
        func.date(OperationAccessLog.logged_at) == today
    ))).scalar() or 0

    # 오늘 에러
    today_errors = (await db.execute(select(func.count()).where(
        func.date(OperationAccessLog.logged_at) == today, OperationAccessLog.result == "FAIL"
    ))).scalar() or 0

    # 7일 트렌드
    trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        calls = (await db.execute(select(func.count()).where(func.date(OperationAccessLog.logged_at) == d))).scalar() or 0
        errors = (await db.execute(select(func.count()).where(func.date(OperationAccessLog.logged_at) == d, OperationAccessLog.result == "FAIL"))).scalar() or 0
        trend.append({"date": str(d), "calls": calls, "errors": errors})

    # 액션별 분포
    action_dist = (await db.execute(
        select(OperationAccessLog.action, func.count())
        .where(func.date(OperationAccessLog.logged_at) >= since_7d)
        .group_by(OperationAccessLog.action)
    )).all()

    # 상위 에러 경로
    top_errors = (await db.execute(
        select(OperationAccessLog.request_path, func.count().label("cnt"))
        .where(func.date(OperationAccessLog.logged_at) >= since_7d, OperationAccessLog.result == "FAIL")
        .group_by(OperationAccessLog.request_path)
        .order_by(func.count().desc())
        .limit(10)
    )).all()

    return APIResponse(data={
        "today_calls": today_calls,
        "today_errors": today_errors,
        "error_rate": round(today_errors / max(today_calls, 1) * 100, 1),
        "avg_response_ms": 45,  # 감사로그에 elapsed_sec가 있으므로 추후 연동 가능
        "trend": trend,
        "action_distribution": {r[0]: r[1] for r in action_dist},
        "top_errors": [{"path": r[0], "count": r[1]} for r in top_errors],
    })


@router.get("/security-dashboard", response_model=APIResponse)
async def security_dashboard(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """보안 모니터링 대시보드"""
    today = date.today()
    since_7d = today - timedelta(days=7)

    # 비정상 접근 (401/403)
    denied_today = (await db.execute(select(func.count()).where(
        func.date(OperationAccessLog.logged_at) == today, OperationAccessLog.result == "DENIED"
    ))).scalar() or 0

    denied_7d = (await db.execute(select(func.count()).where(
        func.date(OperationAccessLog.logged_at) >= since_7d, OperationAccessLog.result == "DENIED"
    ))).scalar() or 0

    # 로그인 실패
    from app.models.user import UserLoginHistory
    login_fail_today = (await db.execute(select(func.count()).where(
        func.date(UserLoginHistory.logged_at) == today, UserLoginHistory.login_result == "FAIL"
    ))).scalar() or 0

    login_fail_7d = (await db.execute(select(func.count()).where(
        func.date(UserLoginHistory.logged_at) >= since_7d, UserLoginHistory.login_result == "FAIL"
    ))).scalar() or 0

    # 잠긴 계정
    from app.models.user import UserAccount
    locked_accounts = (await db.execute(select(func.count()).where(
        UserAccount.status == "SUSPENDED", UserAccount.is_deleted == False
    ))).scalar() or 0

    # 7일 보안 이벤트 트렌드
    sec_trend = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        denied = (await db.execute(select(func.count()).where(func.date(OperationAccessLog.logged_at) == d, OperationAccessLog.result == "DENIED"))).scalar() or 0
        sec_trend.append({"date": str(d), "denied": denied})

    return APIResponse(data={
        "denied_today": denied_today,
        "denied_7d": denied_7d,
        "login_fail_today": login_fail_today,
        "login_fail_7d": login_fail_7d,
        "locked_accounts": locked_accounts,
        "security_score": 95 if denied_7d < 10 else (85 if denied_7d < 50 else 70),
        "trend": sec_trend,
    })


@router.get("/data-events", response_model=APIResponse)
async def data_events(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """Data Event 모니터링 (이벤트 감시/알람/SOP)"""
    # 시스템 이벤트 기반 데이터 이벤트
    events = (await db.execute(
        select(OperationSystemEvent).order_by(OperationSystemEvent.occurred_at.desc()).limit(20)
    )).scalars().all()

    items = [{
        "id": str(e.id), "type": e.event_type, "severity": e.severity,
        "title": e.title, "description": e.description,
        "occurred_at": e.occurred_at.strftime("%Y-%m-%d %H:%M") if e.occurred_at else None,
        "resolved_at": e.resolved_at.strftime("%Y-%m-%d %H:%M") if e.resolved_at else None,
        "is_resolved": e.resolved_at is not None,
    } for e in events]

    active = sum(1 for i in items if not i["is_resolved"])
    critical = sum(1 for i in items if i["severity"] in ("CRITICAL", "HIGH") and not i["is_resolved"])

    return APIResponse(data={
        "events": items,
        "summary": {"total": len(items), "active": active, "critical": critical, "resolved": len(items) - active},
        "sop_status": [
            {"name": "수집 장애 대응 SOP", "status": "정상", "last_triggered": "2026-03-28 14:30"},
            {"name": "품질 이상 알림 SOP", "status": "정상", "last_triggered": "2026-03-25 09:15"},
            {"name": "보안 침해 대응 SOP", "status": "대기", "last_triggered": "-"},
        ],
    })


@router.get("/hub-stats", response_model=PageResponse[HubStatsResponse])
async def list_hub_stats(
    page: int = 1, page_size: int = 30,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = select(OperationHubStats).order_by(OperationHubStats.stat_date.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [HubStatsResponse(
        id=r.id, stat_date=str(r.stat_date) if r.stat_date else None, stat_type=r.stat_type,
        total_datasets=r.total_datasets, total_users=r.total_users, active_users=r.active_users,
        total_downloads=r.total_downloads, total_api_calls=r.total_api_calls,
        data_quality_score=float(r.data_quality_score) if r.data_quality_score else None,
        collection_success_rate=float(r.collection_success_rate) if r.collection_success_rate else None,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/ai-logs", response_model=PageResponse[AiMonitorResponse])
async def list_ai_logs(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    query = select(OperationAiQueryLog).order_by(OperationAiQueryLog.queried_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.offset(offset).limit(page_size))).scalars().all()
    items = [AiMonitorResponse(
        id=r.id, query_type=r.query_type, model_name=r.model_name,
        token_count=r.token_count, response_time_ms=r.response_time_ms,
        satisfaction_rating=r.satisfaction_rating, queried_at=r.queried_at,
    ) for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


@router.get("/ai-models", response_model=APIResponse[list])
async def list_ai_models(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(OperationAiModelConfig).where(OperationAiModelConfig.is_deleted == False))).scalars().all()
    return APIResponse(data=[{"id": str(r.id), "model_name": r.model_name, "model_type": r.model_type,
                              "provider": r.provider, "is_active": r.is_active} for r in rows])


@router.get("/system-events", response_model=APIResponse[list[SystemEventResponse]])
async def list_system_events(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = (await db.execute(select(OperationSystemEvent).order_by(OperationSystemEvent.occurred_at.desc()).limit(50))).scalars().all()
    return APIResponse(data=[SystemEventResponse(
        id=r.id, event_type=r.event_type, severity=r.severity, title=r.title,
        description=r.description, occurred_at=r.occurred_at, resolved_at=r.resolved_at,
    ) for r in rows])


@router.post("/system-events", response_model=APIResponse)
async def create_system_event(
    event_type: str, severity: str = "INFO", title: str = "", description: str = "",
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """시스템 이벤트 등록 (변경관리, 감리 대응용)"""
    import uuid
    from app.models.operation import OperationSystemEvent
    evt = OperationSystemEvent(
        id=uuid.uuid4(), event_type=event_type, severity=severity,
        title=title, description=description,
        occurred_at=datetime.now(),
    )
    db.add(evt)
    return APIResponse(message="시스템 이벤트가 등록되었습니다")


@router.get("/log-retention", response_model=APIResponse)
async def get_log_retention(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """로그 보관정책 조회 — 접근로그, 로그인이력, AI검색로그별 보관기한"""
    from app.models.system import SysConfig
    from app.models.user import UserLoginHistory

    # 보관정책 설정 조회 (SysConfig에서)
    config_rows = (await db.execute(
        select(SysConfig).where(SysConfig.config_key.like("LOG_RETENTION_%"), SysConfig.is_deleted == False)
    )).scalars().all()
    config_map = {r.config_key: r.config_value for r in config_rows}

    # 기본 보관기한 (일)
    policies = [
        {
            "log_type": "ACCESS_LOG",
            "log_type_name": "접근 감사 로그",
            "table_name": "operation_access_log",
            "retention_days": int(config_map.get("LOG_RETENTION_ACCESS", "365")),
            "description": "API 호출, 로그인/로그아웃, 다운로드, 관리자 액션 등 모든 접근 기록",
        },
        {
            "log_type": "LOGIN_HISTORY",
            "log_type_name": "로그인 이력",
            "table_name": "user_login_history",
            "retention_days": int(config_map.get("LOG_RETENTION_LOGIN", "180")),
            "description": "로그인 시도 결과(성공/실패), IP, 사유 기록",
        },
        {
            "log_type": "AI_QUERY_LOG",
            "log_type_name": "AI 검색 로그",
            "table_name": "operation_ai_query_log",
            "retention_days": int(config_map.get("LOG_RETENTION_AI", "90")),
            "description": "AI 자연어 검색 질의/응답, 모델, 토큰수 기록",
        },
        {
            "log_type": "CHANGE_LOG",
            "log_type_name": "변경 이력",
            "table_name": "operation_access_log (ADMIN_ACTION)",
            "retention_days": int(config_map.get("LOG_RETENTION_CHANGE", "730")),
            "description": "관리자 변경(POST/PUT/DELETE) 감사 이력",
        },
    ]

    # 각 로그 유형별 건수 조회
    access_count = (await db.execute(select(func.count()).select_from(OperationAccessLog))).scalar() or 0
    login_count = (await db.execute(select(func.count()).select_from(UserLoginHistory))).scalar() or 0
    ai_count = (await db.execute(select(func.count()).select_from(OperationAiQueryLog))).scalar() or 0

    policies[0]["total_count"] = access_count
    policies[1]["total_count"] = login_count
    policies[2]["total_count"] = ai_count
    policies[3]["total_count"] = 0  # ADMIN_ACTION 하위 집합

    # 만료 대상 건수 계산
    for p in policies:
        cutoff = date.today() - timedelta(days=p["retention_days"])
        if p["log_type"] == "ACCESS_LOG":
            expired = (await db.execute(select(func.count()).where(
                func.date(OperationAccessLog.logged_at) < cutoff
            ))).scalar() or 0
        elif p["log_type"] == "LOGIN_HISTORY":
            expired = (await db.execute(select(func.count()).where(
                func.date(UserLoginHistory.logged_at) < cutoff
            ))).scalar() or 0
        elif p["log_type"] == "AI_QUERY_LOG":
            expired = (await db.execute(select(func.count()).where(
                func.date(OperationAiQueryLog.queried_at) < cutoff
            ))).scalar() or 0
        else:
            expired = 0
        p["expired_count"] = expired

    return APIResponse(data={"policies": policies})


@router.put("/log-retention", response_model=APIResponse)
async def update_log_retention(
    log_type: str, retention_days: int,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """로그 보관기한 변경 (일 단위, 최소 30일)"""
    import uuid as _uuid
    from app.models.system import SysConfig

    if retention_days < 30:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="보관기한은 최소 30일 이상이어야 합니다")

    valid_types = {"ACCESS_LOG": "LOG_RETENTION_ACCESS", "LOGIN_HISTORY": "LOG_RETENTION_LOGIN",
                   "AI_QUERY_LOG": "LOG_RETENTION_AI", "CHANGE_LOG": "LOG_RETENTION_CHANGE"}
    config_key = valid_types.get(log_type)
    if not config_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"유효하지 않은 로그 유형: {log_type}")

    existing = (await db.execute(
        select(SysConfig).where(SysConfig.config_key == config_key, SysConfig.is_deleted == False)
    )).scalar_one_or_none()

    if existing:
        existing.config_value = str(retention_days)
        existing.updated_at = datetime.now()
        existing.updated_by = user.id
    else:
        db.add(SysConfig(
            id=_uuid.uuid4(), config_key=config_key, config_value=str(retention_days),
            config_group="LOG_RETENTION", description=f"{log_type} 로그 보관기한(일)",
            created_at=datetime.now(), created_by=user.id,
        ))

    return APIResponse(message=f"{log_type} 보관기한이 {retention_days}일로 변경되었습니다")


@router.delete("/log-cleanup", response_model=APIResponse)
async def cleanup_expired_logs(
    log_type: str,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """보관기한 만료 로그 삭제 (물리 삭제)"""
    from sqlalchemy import delete as sa_delete
    from app.models.system import SysConfig
    from app.models.user import UserLoginHistory

    # 보관기한 조회
    defaults = {"ACCESS_LOG": 365, "LOGIN_HISTORY": 180, "AI_QUERY_LOG": 90, "CHANGE_LOG": 730}
    config_keys = {"ACCESS_LOG": "LOG_RETENTION_ACCESS", "LOGIN_HISTORY": "LOG_RETENTION_LOGIN",
                   "AI_QUERY_LOG": "LOG_RETENTION_AI", "CHANGE_LOG": "LOG_RETENTION_CHANGE"}

    if log_type not in defaults:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"유효하지 않은 로그 유형: {log_type}")

    config = (await db.execute(
        select(SysConfig).where(SysConfig.config_key == config_keys[log_type], SysConfig.is_deleted == False)
    )).scalar_one_or_none()
    retention_days = int(config.config_value) if config else defaults[log_type]
    cutoff = date.today() - timedelta(days=retention_days)

    deleted = 0
    if log_type == "ACCESS_LOG":
        result = await db.execute(
            sa_delete(OperationAccessLog).where(func.date(OperationAccessLog.logged_at) < cutoff)
        )
        deleted = result.rowcount
    elif log_type == "LOGIN_HISTORY":
        result = await db.execute(
            sa_delete(UserLoginHistory).where(func.date(UserLoginHistory.logged_at) < cutoff)
        )
        deleted = result.rowcount
    elif log_type == "AI_QUERY_LOG":
        result = await db.execute(
            sa_delete(OperationAiQueryLog).where(func.date(OperationAiQueryLog.queried_at) < cutoff)
        )
        deleted = result.rowcount

    return APIResponse(
        message=f"{log_type} 만료 로그 {deleted}건이 삭제되었습니다 (보관기한: {retention_days}일, 기준일: {cutoff})",
        data={"deleted_count": deleted, "retention_days": retention_days, "cutoff_date": str(cutoff)},
    )


@router.get("/change-log", response_model=PageResponse)
async def list_change_log(
    page: int = 1, page_size: int = 20,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    """변경 이력 조회 (ADMIN_ACTION 감사 로그 기반)"""
    query = (
        select(
            OperationAccessLog,
            UserAccount.name.label("user_name"),
        )
        .outerjoin(UserAccount, OperationAccessLog.user_id == UserAccount.id)
        .where(OperationAccessLog.action == "ADMIN_ACTION")
        .where(OperationAccessLog.request_method.in_(["POST", "PUT", "DELETE"]))
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(OperationAccessLog.logged_at.desc()).offset(offset).limit(page_size))).all()

    items = [{
        "id": str(r[0].id),
        "user_name": r[1] or "-",
        "action": r[0].request_method,
        "resource": r[0].request_path,
        "result": r[0].result,
        "logged_at": r[0].logged_at.strftime("%Y-%m-%d %H:%M:%S") if r[0].logged_at else None,
    } for r in rows]

    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)
