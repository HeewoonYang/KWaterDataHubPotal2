"""SA-09. 포털/UX (11개 테이블)"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class PortalDashboardTemplate(AuditMixin, Base):
    """대시보드템플릿"""
    __tablename__ = "portal_dashboard_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="템플릿ID")
    template_name = Column(String(200), nullable=False, comment="템플릿명")
    template_code = Column(String(50), unique=True, comment="템플릿코드 (DEFAULT/STATISTICS/MONITORING)")
    description = Column(Text, comment="설명")
    widget_layout = Column(JSONB, nullable=False, comment="위젯배치정보")
    is_system = Column(Boolean, default=False, comment="시스템기본여부")

    __table_args__ = (
        Index("ix_portal_dashboard_template_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "대시보드템플릿"},
    )


class PortalDashboardWidget(AuditMixin, Base):
    """위젯정의"""
    __tablename__ = "portal_dashboard_widget"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="위젯ID")
    widget_code = Column(String(50), nullable=False, unique=True, comment="위젯코드")
    widget_name = Column(String(200), nullable=False, comment="위젯명")
    widget_type = Column(String(50), comment="위젯유형 (CHART/KPI/TABLE/STATUS/SEARCH)")
    chart_type = Column(String(50), comment="차트유형 (BAR/LINE/PIE/SCATTER/MAP/GAUGE)")
    data_source_api = Column(String(500), comment="데이터소스API")
    default_config = Column(JSONB, comment="기본설정")
    min_width = Column(Integer, default=1, comment="최소너비")
    min_height = Column(Integer, default=1, comment="최소높이")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        Index("ix_portal_dashboard_widget_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "위젯정의"},
    )


class PortalUserDashboard(AuditMixin, Base):
    """사용자대시보드설정"""
    __tablename__ = "portal_user_dashboard"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="사용자대시보드ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    dashboard_name = Column(String(200), default="기본", comment="대시보드명")
    is_default = Column(Boolean, default=True, comment="기본대시보드여부")
    widget_layout = Column(JSONB, nullable=False, comment="위젯배치정보")
    widget_configs = Column(JSONB, comment="위젯별설정")

    __table_args__ = (
        Index("ix_portal_dash_user", "user_id"),
        Index("ix_portal_user_dashboard_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "사용자대시보드설정"},
    )


class PortalVisualizationChart(AuditMixin, Base):
    """시각화차트"""
    __tablename__ = "portal_visualization_chart"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="차트ID")
    chart_name = Column(String(200), nullable=False, comment="차트명")
    chart_type = Column(String(50), nullable=False, comment="차트유형 (BAR/LINE/PIE/SCATTER/MAP/HEATMAP)")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="SET NULL"), comment="데이터셋ID")
    chart_config = Column(JSONB, nullable=False, comment="차트설정")
    data_query = Column(JSONB, comment="데이터조회설정")
    thumbnail_url = Column(String(500), comment="썸네일경로")
    is_public = Column(Boolean, default=False, comment="공개여부")
    view_count = Column(Integer, default=0, comment="조회수")
    owner_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="생성자ID")

    __table_args__ = (
        Index("ix_portal_chart_owner", "owner_id"),
        Index("ix_portal_chart_type", "chart_type"),
        Index("ix_portal_visualization_chart_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "시각화차트"},
    )


class PortalChartTemplate(Base):
    """차트템플릿"""
    __tablename__ = "portal_chart_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="차트템플릿ID")
    template_name = Column(String(200), nullable=False, comment="템플릿명")
    chart_type = Column(String(50), nullable=False, comment="차트유형")
    chart_config = Column(JSONB, nullable=False, comment="차트설정")
    preview_image_url = Column(String(500), comment="미리보기이미지경로")
    category = Column(String(50), comment="카테고리")
    sort_order = Column(Integer, default=0, comment="정렬순서")
    is_active = Column(Boolean, default=True, comment="활성여부")

    __table_args__ = (
        {"comment": "차트템플릿"},
    )


class PortalBookmark(Base):
    """즐겨찾기"""
    __tablename__ = "portal_bookmark"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="즐겨찾기ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    resource_type = Column(String(50), nullable=False, comment="리소스유형 (DATASET/CHART/REPORT/API)")
    resource_id = Column(UUID(as_uuid=True), nullable=False, comment="리소스ID")
    resource_name = Column(String(300), comment="리소스명")
    bookmarked_at = Column(DateTime, default=datetime.now, comment="등록일시")

    __table_args__ = (
        Index("uq_bookmark", "user_id", "resource_type", "resource_id", unique=True),
        {"comment": "즐겨찾기"},
    )


class PortalRecentView(Base):
    """최근조회이력"""
    __tablename__ = "portal_recent_view"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="최근조회ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    resource_type = Column(String(50), comment="리소스유형")
    resource_id = Column(UUID(as_uuid=True), comment="리소스ID")
    resource_name = Column(String(300), comment="리소스명")
    viewed_at = Column(DateTime, default=datetime.now, comment="조회일시")

    __table_args__ = (
        Index("ix_recent_user", "user_id"),
        Index("ix_recent_date", "viewed_at"),
        {"comment": "최근조회이력"},
    )


class PortalSearchHistory(Base):
    """검색이력"""
    __tablename__ = "portal_search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="검색이력ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    search_keyword = Column(String(500), nullable=False, comment="검색어")
    search_type = Column(String(50), comment="검색유형 (KEYWORD/AI/FILTER)")
    result_count = Column(Integer, comment="결과수")
    searched_at = Column(DateTime, default=datetime.now, comment="검색일시")

    __table_args__ = (
        Index("ix_search_hist_user", "user_id"),
        {"comment": "검색이력"},
    )


class PortalNotification(Base):
    """알림"""
    __tablename__ = "portal_notification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="알림ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="수신자ID")
    notification_type = Column(String(50), nullable=False, comment="알림유형 (DATA_CHANGE/QUALITY/APPROVAL/SYSTEM/DOWNLOAD)")
    title = Column(String(300), nullable=False, comment="알림제목")
    message = Column(Text, comment="알림내용")
    link_url = Column(String(500), comment="이동URL")
    is_read = Column(Boolean, default=False, comment="읽음여부")
    read_at = Column(DateTime, comment="읽음일시")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")

    __table_args__ = (
        Index("ix_noti_user", "user_id"),
        Index("ix_noti_type", "notification_type"),
        Index("ix_noti_read", "user_id", "is_read"),
        {"comment": "알림"},
    )


class PortalNotificationSubscription(Base):
    """알림구독설정"""
    __tablename__ = "portal_notification_subscription"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="알림구독ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    notification_type = Column(String(50), nullable=False, comment="알림유형")
    is_enabled = Column(Boolean, default=True, comment="활성여부")
    channel = Column(String(20), default="WEB", comment="수신채널 (WEB/EMAIL/SMS)")
    filter_config = Column(JSONB, comment="필터조건")

    __table_args__ = (
        Index("uq_noti_sub", "user_id", "notification_type", "channel", unique=True),
        {"comment": "알림구독설정"},
    )


class PortalCartItem(Base):
    """데이터장바구니항목"""
    __tablename__ = "portal_cart_item"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="장바구니항목ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("catalog_dataset.id", ondelete="CASCADE"), nullable=False, comment="데이터셋ID")
    dataset_name = Column(String(300), comment="데이터셋명 (스냅샷)")
    data_format = Column(String(50), comment="데이터형식")
    grade = Column(Integer, default=3, comment="보안등급 (1=기밀/2=내부/3=공개)")
    date_from = Column(String(20), comment="요청기간시작")
    date_to = Column(String(20), comment="요청기간종료")
    max_rows = Column(String(50), comment="최대건수")
    request_format = Column(String(20), default="CSV", comment="요청포맷 (CSV/JSON/API)")
    memo = Column(Text, comment="메모")
    added_at = Column(DateTime, default=datetime.now, comment="추가일시")

    __table_args__ = (
        Index("uq_cart_user_dataset", "user_id", "dataset_id", unique=True),
        Index("ix_cart_user", "user_id"),
        {"comment": "데이터장바구니항목"},
    )


class PortalSitemapMenu(AuditMixin, Base):
    """사이트맵메뉴"""
    __tablename__ = "portal_sitemap_menu"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="메뉴ID")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("portal_sitemap_menu.id", ondelete="SET NULL"), comment="상위메뉴ID")
    menu_name = Column(String(200), nullable=False, comment="메뉴명")
    menu_code = Column(String(50), nullable=False, unique=True, comment="메뉴코드")
    menu_level = Column(Integer, nullable=False, comment="메뉴레벨 (1=대/2=중/3=소)")
    route_path = Column(String(200), comment="라우트경로")
    icon_name = Column(String(100), comment="아이콘명")
    required_roles = Column(JSONB, comment="접근역할목록")
    is_visible = Column(Boolean, default=True, comment="표시여부")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        Index("ix_sitemap_parent", "parent_id"),
        Index("ix_sitemap_code", "menu_code"),
        Index("ix_portal_sitemap_menu_not_deleted", "is_deleted", postgresql_where=text("is_deleted = false")),
        {"comment": "사이트맵메뉴"},
    )
