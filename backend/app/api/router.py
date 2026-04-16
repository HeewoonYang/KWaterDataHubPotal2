from fastapi import APIRouter

from app.api.v1 import (
    standard, classification, quality, meta_model,
    auth, sso, portal_dashboard, portal_catalog, portal_distribution,
    portal_visualization, portal_user, portal_ai, portal_board, portal_widget,
    portal_measurement, portal_cart,
    admin_system, admin_user, admin_collection, admin_cleansing,
    admin_storage, admin_distribution, admin_operation,
    admin_dr,
)

api_router = APIRouter()

# 기존
api_router.include_router(standard.router, prefix="/standards", tags=["표준사전"])
api_router.include_router(classification.router, prefix="/classifications", tags=["분류체계"])
api_router.include_router(quality.router, prefix="/quality", tags=["품질검증"])
api_router.include_router(meta_model.router, prefix="/models", tags=["메타모델"])

# 인증
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(sso.router, prefix="/sso", tags=["SSO"])

# 포털
api_router.include_router(portal_dashboard.router, prefix="/portal/dashboard", tags=["포털-대시보드"])
api_router.include_router(portal_catalog.router, prefix="/portal/catalog", tags=["포털-카탈로그"])
api_router.include_router(portal_distribution.router, prefix="/portal/distribution", tags=["포털-유통"])
api_router.include_router(portal_visualization.router, prefix="/portal/visualization", tags=["포털-시각화"])
api_router.include_router(portal_user.router, prefix="/portal/user", tags=["포털-사용자"])
api_router.include_router(portal_ai.router, prefix="/portal/ai", tags=["포털-AI검색"])
api_router.include_router(portal_board.router, prefix="/portal/board", tags=["포털-게시판"])
api_router.include_router(portal_widget.router, prefix="/portal/widget", tags=["포털-위젯/갤러리"])
api_router.include_router(portal_measurement.router, prefix="/portal/measurement", tags=["포털-실시간계측DB"])
api_router.include_router(portal_cart.router, prefix="/portal/cart", tags=["포털-장바구니"])

# 관리자
api_router.include_router(admin_system.router, prefix="/admin/system", tags=["관리-시스템"])
api_router.include_router(admin_user.router, prefix="/admin/user", tags=["관리-사용자"])
api_router.include_router(admin_collection.router, prefix="/admin/collection", tags=["관리-수집"])
api_router.include_router(admin_cleansing.router, prefix="/admin/cleansing", tags=["관리-정제"])
api_router.include_router(admin_storage.router, prefix="/admin/storage", tags=["관리-저장"])
api_router.include_router(admin_distribution.router, prefix="/admin/distribution", tags=["관리-유통"])
api_router.include_router(admin_operation.router, prefix="/admin/operation", tags=["관리-운영"])
# REQ-DHUB-005-003: DR/PIT/이관감사/OpenMetadata
api_router.include_router(admin_dr.router, prefix="/admin/dr", tags=["관리-재해복구/이관/OM"])
