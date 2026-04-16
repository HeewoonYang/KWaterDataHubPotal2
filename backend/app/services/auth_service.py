"""인증 서비스 - 로그인/프로필/비밀번호 관리"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import ROLE_DATA_GRADES
from app.core.security import (
    MAX_LOGIN_FAILURES, PASSWORD_EXPIRY_DAYS,
    create_access_token, create_refresh_token, generate_jti,
    hash_password, validate_password, verify_password,
)
from app.models.user import UserAccount, UserLoginHistory, UserRole, UserRoleMap, UserScreenPermission, UserSession
from app.schemas.auth import LoginResponse, UserProfileResponse


async def authenticate_user(db: AsyncSession, login_id: str, password: str) -> LoginResponse | None:
    # 사용자 조회
    result = await db.execute(
        select(UserAccount).where(UserAccount.login_id == login_id, UserAccount.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    # 계정 잠금 체크 (5회 연속 실패)
    if (user.login_fail_count or 0) >= MAX_LOGIN_FAILURES:
        await _log_login(db, user.id, "FAIL", "계정 잠금 (연속 실패 초과)")
        return None

    # 비밀번호 검증
    if not verify_password(password, user.password_hash):
        user.login_fail_count = (user.login_fail_count or 0) + 1
        # 잠금 임계치 도달 시 상태 변경
        if user.login_fail_count >= MAX_LOGIN_FAILURES:
            user.status = "SUSPENDED"
        await _log_login(db, user.id, "FAIL", "비밀번호 불일치")
        return None

    if user.status != "ACTIVE":
        await _log_login(db, user.id, "FAIL", f"비활성 계정: {user.status}")
        return None

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

    # 화면별 권한 조회
    screen_permissions = {}
    if role_id:
        sp_result = await db.execute(
            select(UserScreenPermission).where(UserScreenPermission.role_id == role_id)
        )
        for sp in sp_result.scalars().all():
            screen_permissions[sp.screen_code] = {
                "create": sp.can_create,
                "update": sp.can_update,
                "delete": sp.can_delete,
            }

    # 토큰 생성 (JTI 포함으로 세션 추적)
    access_jti = generate_jti()
    refresh_jti = generate_jti()
    token_data = {"sub": str(user.id), "role": role_code, "jti": access_jti}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({**token_data, "jti": refresh_jti})

    # 세션 저장
    db.add(UserSession(
        id=uuid.uuid4(), user_id=user.id,
        access_token_jti=access_jti, refresh_token_jti=refresh_jti,
        issued_at=datetime.now(),
        expires_at=datetime.now() + timedelta(minutes=60),
        is_revoked=False,
    ))

    # 로그인 성공 처리
    user.last_login_at = datetime.now()
    user.login_fail_count = 0
    await _log_login(db, user.id, "SUCCESS")

    # 비밀번호 만료 경고 (응답에 포함)
    pw_expired = False
    if user.password_changed_at:
        days_since = (datetime.now() - user.password_changed_at).days
        pw_expired = days_since >= PASSWORD_EXPIRY_DAYS

    profile = UserProfileResponse(
        id=user.id, login_id=user.login_id, name=user.name,
        email=user.email, department_name=user.department_name,
        position=user.position, user_type=user.user_type,
        role_code=role_code, role_name=role_name, role_group=role_group or "",
        data_grades=ROLE_DATA_GRADES.get(role_code, [3]),
        screen_permissions=screen_permissions,
        must_change_password=bool(user.must_change_password),
    )

    return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=profile)


async def revoke_session(db: AsyncSession, user_id) -> None:
    """사용자의 모든 활성 세션 무효화"""
    sessions = (await db.execute(
        select(UserSession).where(UserSession.user_id == user_id, UserSession.is_revoked == False)
    )).scalars().all()
    for s in sessions:
        s.is_revoked = True


async def change_password(db: AsyncSession, user_id, old_password: str, new_password: str) -> tuple[bool, str]:
    """비밀번호 변경"""
    user = (await db.execute(select(UserAccount).where(UserAccount.id == user_id))).scalar_one_or_none()
    if not user:
        return False, "사용자를 찾을 수 없습니다"

    if not verify_password(old_password, user.password_hash):
        return False, "현재 비밀번호가 일치하지 않습니다"

    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg

    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.now()
    user.must_change_password = False  # 강제 변경 해제

    # 기존 세션 모두 무효화 (재로그인 유도)
    await revoke_session(db, user_id)

    return True, "비밀번호가 변경되었습니다"


async def get_user_profile(db: AsyncSession, user_id) -> UserProfileResponse | None:
    result = await db.execute(select(UserAccount).where(UserAccount.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

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

    # 화면별 권한 조회
    screen_permissions = {}
    if role_id:
        sp_result = await db.execute(
            select(UserScreenPermission).where(UserScreenPermission.role_id == role_id)
        )
        for sp in sp_result.scalars().all():
            screen_permissions[sp.screen_code] = {
                "create": sp.can_create,
                "update": sp.can_update,
                "delete": sp.can_delete,
            }

    return UserProfileResponse(
        id=user.id, login_id=user.login_id, name=user.name,
        email=user.email, department_name=user.department_name,
        position=user.position, user_type=user.user_type,
        role_code=role_code, role_name=role_name, role_group=role_group or "",
        data_grades=ROLE_DATA_GRADES.get(role_code, [3]),
        screen_permissions=screen_permissions,
    )


async def _log_login(db: AsyncSession, user_id, result: str, reason: str | None = None):
    log = UserLoginHistory(
        id=uuid.uuid4(), user_id=user_id,
        login_type="PASSWORD", login_result=result,
        fail_reason=reason, logged_at=datetime.now(),
    )
    db.add(log)
