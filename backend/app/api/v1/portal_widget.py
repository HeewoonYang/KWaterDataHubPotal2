"""포털 위젯/갤러리 관리 API"""
import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.portal import (PortalDashboardTemplate, PortalDashboardWidget, PortalUserDashboard,
                                PortalVisualizationChart, PortalChartTemplate)
from app.models.user import UserAccount
from app.schemas.common import APIResponse, PageResponse

router = APIRouter()


# ── 위젯 설정 (사용자별 대시보드) ──
@router.get("/user-dashboard")
async def get_user_dashboard(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    dash = (await db.execute(
        select(PortalUserDashboard).where(PortalUserDashboard.user_id == user.id, PortalUserDashboard.is_default == True)
    )).scalar_one_or_none()
    if dash:
        return APIResponse(data={"id": str(dash.id), "widget_layout": dash.widget_layout, "widget_configs": dash.widget_configs})
    return APIResponse(data=None)


@router.put("/user-dashboard")
async def save_user_dashboard(
    body: dict,
    db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(get_current_user),
):
    dash = (await db.execute(
        select(PortalUserDashboard).where(PortalUserDashboard.user_id == user.id, PortalUserDashboard.is_default == True)
    )).scalar_one_or_none()
    if dash:
        dash.widget_layout = body.get("widget_layout", dash.widget_layout)
        dash.widget_configs = body.get("widget_configs", dash.widget_configs)
        dash.updated_at = datetime.now()
    else:
        db.add(PortalUserDashboard(
            id=uuid.uuid4(), user_id=user.id, dashboard_name="기본",
            is_default=True, widget_layout=body.get("widget_layout", {}),
            widget_configs=body.get("widget_configs"), created_at=datetime.now(),
        ))
    return APIResponse(message="대시보드 설정이 저장되었습니다")


# ── 위젯 목록 (전체 사용 가능 위젯) ──
@router.get("/widgets")
async def list_widgets(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PortalDashboardWidget).where(PortalDashboardWidget.is_deleted == False, PortalDashboardWidget.is_active == True)
        .order_by(PortalDashboardWidget.widget_type, PortalDashboardWidget.widget_name)
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "widget_code": r.widget_code, "widget_name": r.widget_name,
        "widget_type": r.widget_type, "chart_type": r.chart_type,
        "data_source_api": r.data_source_api, "default_config": r.default_config,
        "min_width": r.min_width, "min_height": r.min_height,
    } for r in rows])


# ── 위젯 템플릿 관리 (관리자) ──
@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PortalDashboardTemplate).where(PortalDashboardTemplate.is_deleted == False)
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "template_name": r.template_name, "template_code": r.template_code,
        "description": r.description, "widget_layout": r.widget_layout, "is_system": r.is_system,
    } for r in rows])


# ── 시각화 갤러리 차트 목록 ──
@router.get("/gallery-charts")
async def list_gallery_charts(
    page: int = 1, page_size: int = 20, chart_type: str | None = None, search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(PortalVisualizationChart, UserAccount.name.label("owner_name"))
        .outerjoin(UserAccount, PortalVisualizationChart.owner_id == UserAccount.id)
        .where(PortalVisualizationChart.is_deleted == False)
    )
    if chart_type:
        query = query.where(PortalVisualizationChart.chart_type == chart_type)
    if search:
        query = query.where(PortalVisualizationChart.chart_name.ilike(f"%{search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    offset = (page - 1) * page_size
    rows = (await db.execute(query.order_by(PortalVisualizationChart.created_at.desc()).offset(offset).limit(page_size))).all()

    items = [{
        "id": str(r[0].id), "chart_name": r[0].chart_name, "chart_type": r[0].chart_type,
        "chart_config": r[0].chart_config, "is_public": r[0].is_public,
        "view_count": r[0].view_count or 0, "owner_name": r[1],
        "created_at": r[0].created_at.strftime("%Y-%m-%d") if r[0].created_at else None,
    } for r in rows]
    return PageResponse(items=items, total=total, page=page, page_size=page_size,
                        total_pages=math.ceil(total / page_size) if page_size else 0)


# ── 차트 템플릿 목록 ──
@router.get("/chart-templates")
async def list_chart_templates(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PortalChartTemplate).where(PortalChartTemplate.is_active == True)
        .order_by(PortalChartTemplate.sort_order)
    )).scalars().all()
    return APIResponse(data=[{
        "id": str(r.id), "template_name": r.template_name, "chart_type": r.chart_type,
        "chart_config": r.chart_config, "category": r.category,
    } for r in rows])
