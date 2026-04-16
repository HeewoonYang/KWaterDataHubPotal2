"""SA-02. 사용자/권한 (10개 테이블)"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base
from app.models.base import AuditMixin, new_uuid


class UserAccount(AuditMixin, Base):
    """사용자계정"""
    __tablename__ = "user_account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="사용자ID")
    user_type = Column(String(20), nullable=False, comment="사용자유형 (INTERNAL/EXTERNAL)")
    login_id = Column(String(100), nullable=False, unique=True, comment="로그인ID")
    password_hash = Column(String(255), comment="비밀번호해시")
    employee_no = Column(String(20), unique=True, comment="사번")
    sso_identifier = Column(String(200), comment="SSO식별자")
    sso_provider = Column(String(100), comment="SSO제공자명 (OASIS_SAML/provider_name)")
    name = Column(String(100), nullable=False, comment="사용자명")
    email = Column(String(200), comment="이메일")
    phone = Column(String(20), comment="전화번호")
    department_code = Column(String(50), comment="부서코드")
    department_name = Column(String(200), comment="부서명")
    position = Column(String(100), comment="직급")
    status = Column(String(20), default="PENDING", comment="계정상태 (PENDING/ACTIVE/SUSPENDED/WITHDRAWN)")
    last_login_at = Column(DateTime, comment="최근로그인일시")
    password_changed_at = Column(DateTime, comment="비밀번호변경일시")
    login_fail_count = Column(Integer, default=0, comment="로그인실패횟수")
    must_change_password = Column(Boolean, default=False, comment="최초로그인비밀번호강제변경여부")
    agreed_terms_at = Column(DateTime, comment="약관동의일시")

    __table_args__ = (
        Index("ix_user_login_id", "login_id"),
        Index("ix_user_employee_no", "employee_no"),
        Index("ix_user_type", "user_type"),
        Index("ix_user_dept", "department_code"),
        {"comment": "사용자계정"},
    )


class UserRole(AuditMixin, Base):
    """역할정의"""
    __tablename__ = "user_role"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="역할ID")
    role_code = Column(String(50), nullable=False, unique=True, comment="역할코드 (SUPER_ADMIN/OPERATOR/ENGINEER/STEWARD/EXECUTIVE/KW_MANAGER/EMPLOYEE/EXTERNAL)")
    role_name = Column(String(100), nullable=False, comment="역할명")
    role_group = Column(String(20), comment="역할그룹 (GENERAL/DATA_ADMIN/SYS_ADMIN/EXTERNAL)")
    description = Column(Text, comment="설명")
    is_system_role = Column(Boolean, default=False, comment="시스템역할여부")
    default_route = Column(String(200), comment="기본라우트경로")
    can_access_admin = Column(Boolean, default=False, comment="관리자접근가능여부")
    admin_menu_access = Column(JSONB, comment="관리자메뉴접근범위")
    sort_order = Column(Integer, default=0, comment="정렬순서")

    __table_args__ = (
        {"comment": "역할정의"},
    )


class UserPermission(AuditMixin, Base):
    """권한정의"""
    __tablename__ = "user_permission"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="권한ID")
    permission_code = Column(String(100), nullable=False, unique=True, comment="권한코드")
    permission_name = Column(String(200), nullable=False, comment="권한명")
    permission_type = Column(String(50), comment="권한유형 (MENU/DATA/API/FUNCTION)")
    resource = Column(String(200), comment="대상리소스")
    action = Column(String(50), comment="수행작업 (READ/WRITE/DELETE/DOWNLOAD/MANAGE)")
    description = Column(Text, comment="설명")

    __table_args__ = (
        {"comment": "권한정의"},
    )


class UserRolePermission(AuditMixin, Base):
    """역할권한매핑"""
    __tablename__ = "user_role_permission"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="역할권한매핑ID")
    role_id = Column(UUID(as_uuid=True), ForeignKey("user_role.id", ondelete="CASCADE"), nullable=False, comment="역할ID")
    permission_id = Column(UUID(as_uuid=True), ForeignKey("user_permission.id", ondelete="CASCADE"), nullable=False, comment="권한ID")

    __table_args__ = (
        Index("uq_role_perm", "role_id", "permission_id", unique=True),
        {"comment": "역할권한매핑"},
    )


class UserScreenPermission(AuditMixin, Base):
    """화면별권한"""
    __tablename__ = "user_screen_permission"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="화면권한ID")
    role_id = Column(UUID(as_uuid=True), ForeignKey("user_role.id", ondelete="CASCADE"), nullable=False, comment="역할ID")
    screen_code = Column(String(50), nullable=False, comment="화면코드")
    screen_name = Column(String(200), comment="화면명")
    screen_group = Column(String(50), comment="화면그룹 (시스템관리/사용자관리/데이터표준 등)")
    can_create = Column(Boolean, default=False, comment="등록권한")
    can_update = Column(Boolean, default=False, comment="수정권한")
    can_delete = Column(Boolean, default=False, comment="삭제권한")

    __table_args__ = (
        Index("uq_role_screen", "role_id", "screen_code", unique=True),
        Index("ix_screen_perm_role", "role_id"),
        {"comment": "화면별권한"},
    )


class UserRoleMap(Base):
    """사용자역할매핑"""
    __tablename__ = "user_role_map"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="사용자역할매핑ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    role_id = Column(UUID(as_uuid=True), ForeignKey("user_role.id", ondelete="CASCADE"), nullable=False, comment="역할ID")
    granted_by = Column(UUID(as_uuid=True), comment="부여자ID")
    granted_at = Column(DateTime, default=datetime.now, comment="부여일시")
    valid_until = Column(DateTime, comment="유효기한일시")
    status = Column(String(20), default="ACTIVE", comment="상태 (ACTIVE/EXPIRED/REVOKED)")

    __table_args__ = (
        Index("uq_user_role", "user_id", "role_id", unique=True),
        {"comment": "사용자역할매핑"},
    )


class UserDataAccessPolicy(AuditMixin, Base):
    """데이터접근정책"""
    __tablename__ = "user_data_access_policy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="접근정책ID")
    policy_name = Column(String(200), nullable=False, comment="정책명")
    role_id = Column(UUID(as_uuid=True), ForeignKey("user_role.id", ondelete="SET NULL"), comment="역할ID")
    data_grade_id = Column(Integer, ForeignKey("data_grade.id", ondelete="SET NULL"), comment="데이터등급ID")
    allowed_actions = Column(JSONB, comment="허용작업목록")
    condition_expression = Column(Text, comment="ABAC조건표현식")
    requires_approval = Column(Boolean, default=False, comment="결재필요여부")
    description = Column(Text, comment="설명")

    __table_args__ = (
        {"comment": "데이터접근정책"},
    )


class UserAccessRequest(AuditMixin, Base):
    """데이터접근신청"""
    __tablename__ = "user_access_request"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="접근신청ID")
    requester_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="신청자ID")
    target_resource_type = Column(String(50), comment="대상리소스유형 (DATASET/API/REPORT)")
    target_resource_id = Column(UUID(as_uuid=True), comment="대상리소스ID")
    data_grade_code = Column(String(10), comment="데이터등급코드 (L1/L2/L3)")
    requested_actions = Column(JSONB, comment="요청작업목록")
    reason = Column(Text, comment="신청사유")
    valid_until = Column(DateTime, comment="요청유효기한")
    status = Column(String(20), default="REQUESTED", comment="신청상태 (REQUESTED/REVIEWING/APPROVED/REJECTED)")
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), comment="검토자ID")
    reviewed_at = Column(DateTime, comment="검토일시")
    review_comment = Column(Text, comment="검토의견")

    __table_args__ = (
        Index("ix_access_req_requester", "requester_id"),
        Index("ix_access_req_status", "status"),
        {"comment": "데이터접근신청"},
    )


class UserLoginHistory(Base):
    """로그인이력"""
    __tablename__ = "user_login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="로그인이력ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    login_type = Column(String(20), comment="로그인유형 (SSO/PASSWORD/TOKEN_REFRESH)")
    client_ip = Column(String(45), comment="클라이언트IP")
    user_agent = Column(String(500), comment="사용자에이전트")
    login_result = Column(String(20), comment="로그인결과 (SUCCESS/FAIL)")
    fail_reason = Column(String(200), comment="실패사유")
    logged_at = Column(DateTime, default=datetime.now, comment="로그인일시")

    __table_args__ = (
        Index("ix_login_hist_user", "user_id"),
        Index("ix_login_hist_date", "logged_at"),
        {"comment": "로그인이력"},
    )


class UserSession(Base):
    """세션관리"""
    __tablename__ = "user_session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid, comment="세션ID")
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False, comment="사용자ID")
    access_token_jti = Column(String(200), unique=True, comment="액세스토큰JTI")
    refresh_token_jti = Column(String(200), unique=True, comment="리프레시토큰JTI")
    client_ip = Column(String(45), comment="클라이언트IP")
    issued_at = Column(DateTime, comment="발급일시")
    expires_at = Column(DateTime, comment="만료일시")
    is_revoked = Column(Boolean, default=False, comment="폐기여부")

    __table_args__ = (
        Index("ix_session_user", "user_id"),
        {"comment": "세션관리"},
    )
