"""SSO 공통 서비스 — 사용자 매칭/자동생성 + JWT 토큰 발급"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import ROLE_DATA_GRADES
from app.core.security import create_access_token, create_refresh_token, generate_jti
from app.models.user import UserAccount, UserLoginHistory, UserRole, UserRoleMap, UserScreenPermission, UserSession
from app.schemas.auth import LoginResponse, UserProfileResponse


async def find_or_provision_user(
    db: AsyncSession,
    sso_identifier: str,
    provider_name: str,
    attributes: dict,
    default_role: str = "EMPLOYEE",
    default_user_type: str = "INTERNAL",
) -> UserAccount:
    """SSO 인증 후 사용자 매칭 또는 자동 생성 (JIT Provisioning)"""
    # 1) sso_identifier로 검색
    user = (await db.execute(
        select(UserAccount).where(
            UserAccount.sso_identifier == sso_identifier,
            UserAccount.is_deleted == False,
        )
    )).scalar_one_or_none()

    if user:
        # 정보 업데이트
        if attributes.get("name"):
            user.name = attributes["name"]
        if attributes.get("department_code"):
            user.department_code = attributes["department_code"]
            user.department_name = attributes.get("department_name", "")
        if attributes.get("position"):
            user.position = attributes["position"]
        if attributes.get("email"):
            user.email = attributes["email"]
        user.sso_provider = provider_name
        user.updated_at = datetime.now()
        return user

    # 2) employee_no 또는 email로 기존 사용자 검색
    emp_no = attributes.get("employee_no")
    email = attributes.get("email")
    if emp_no:
        user = (await db.execute(
            select(UserAccount).where(UserAccount.employee_no == emp_no, UserAccount.is_deleted == False)
        )).scalar_one_or_none()
    if not user and email:
        user = (await db.execute(
            select(UserAccount).where(UserAccount.email == email, UserAccount.is_deleted == False)
        )).scalar_one_or_none()

    if user:
        # SSO 연결
        user.sso_identifier = sso_identifier
        user.sso_provider = provider_name
        user.updated_at = datetime.now()
        return user

    # 3) 자동 생성 (JIT Provisioning)
    login_id = emp_no or email or sso_identifier
    new_user = UserAccount(
        id=uuid.uuid4(),
        login_id=login_id,
        name=attributes.get("name", login_id),
        email=email,
        employee_no=emp_no,
        department_code=attributes.get("department_code"),
        department_name=attributes.get("department_name"),
        position=attributes.get("position"),
        user_type=default_user_type,
        sso_identifier=sso_identifier,
        sso_provider=provider_name,
        status="ACTIVE",
        created_at=datetime.now(),
    )
    db.add(new_user)
    await db.flush()

    # 기본 역할 부여
    role = (await db.execute(
        select(UserRole).where(UserRole.role_code == default_role)
    )).scalar_one_or_none()
    if role:
        db.add(UserRoleMap(
            id=uuid.uuid4(), user_id=new_user.id, role_id=role.id,
            granted_at=datetime.now(), status="ACTIVE",
        ))

    return new_user


async def build_login_response(db: AsyncSession, user: UserAccount, login_type: str = "PASSWORD") -> LoginResponse:
    """JWT 토큰 생성 + 세션 저장 + 로그인 이력 기록 → LoginResponse 반환 (공통 헬퍼)"""
    # 역할 조회
    role_result = await db.execute(
        select(UserRole.role_code, UserRole.role_name, UserRole.role_group, UserRole.id)
        .join(UserRoleMap, UserRoleMap.role_id == UserRole.id)
        .where(UserRoleMap.user_id == user.id, UserRoleMap.status == "ACTIVE")
    )
    role_row = role_result.first()
    role_code = role_row[0] if role_row else "EXTERNAL"
    role_name = role_row[1] if role_row else "외부사용자"
    role_group = role_row[2] if role_row else "EXTERNAL"
    role_id = role_row[3] if role_row else None

    # 화면별 권한
    screen_permissions = {}
    if role_id:
        sp_result = await db.execute(
            select(UserScreenPermission).where(UserScreenPermission.role_id == role_id)
        )
        for sp in sp_result.scalars().all():
            screen_permissions[sp.screen_code] = {
                "create": sp.can_create, "update": sp.can_update, "delete": sp.can_delete,
            }

    # 토큰 생성
    access_jti = generate_jti()
    refresh_jti = generate_jti()
    token_data = {"sub": str(user.id), "role": role_code, "jti": access_jti}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({**token_data, "jti": refresh_jti})

    # 세션 저장
    db.add(UserSession(
        id=uuid.uuid4(), user_id=user.id,
        access_token_jti=access_jti, refresh_token_jti=refresh_jti,
        issued_at=datetime.now(), expires_at=datetime.now() + timedelta(minutes=60),
        is_revoked=False,
    ))

    # 로그인 성공 기록
    user.last_login_at = datetime.now()
    user.login_fail_count = 0
    db.add(UserLoginHistory(
        id=uuid.uuid4(), user_id=user.id,
        login_type=login_type, login_result="SUCCESS", logged_at=datetime.now(),
    ))

    profile = UserProfileResponse(
        id=user.id, login_id=user.login_id, name=user.name,
        email=user.email, department_name=user.department_name,
        position=user.position, user_type=user.user_type,
        role_code=role_code, role_name=role_name, role_group=role_group or "",
        data_grades=ROLE_DATA_GRADES.get(role_code, [3]),
        screen_permissions=screen_permissions,
    )

    return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=profile)
