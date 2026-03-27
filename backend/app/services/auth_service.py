"""인증 서비스"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import ROLE_DATA_GRADES
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import UserAccount, UserLoginHistory, UserRole, UserRoleMap, UserSession
from app.schemas.auth import LoginResponse, UserProfileResponse


async def authenticate_user(db: AsyncSession, login_id: str, password: str) -> LoginResponse | None:
    # 사용자 조회
    result = await db.execute(
        select(UserAccount).where(UserAccount.login_id == login_id, UserAccount.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    # 비밀번호 검증
    if not verify_password(password, user.password_hash):
        user.login_fail_count = (user.login_fail_count or 0) + 1
        await _log_login(db, user.id, "FAIL", "비밀번호 불일치")
        return None

    if user.status != "ACTIVE":
        await _log_login(db, user.id, "FAIL", f"비활성 계정: {user.status}")
        return None

    # 역할 조회
    role_result = await db.execute(
        select(UserRole.role_code, UserRole.role_name)
        .join(UserRoleMap, UserRoleMap.role_id == UserRole.id)
        .where(UserRoleMap.user_id == user.id, UserRoleMap.status == "ACTIVE")
    )
    role_row = role_result.first()
    role_code = role_row[0] if role_row else "EXTERNAL"
    role_name = role_row[1] if role_row else "외부사용자"

    # 토큰 생성
    token_data = {"sub": str(user.id), "role": role_code}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # 로그인 성공 처리
    user.last_login_at = datetime.now()
    user.login_fail_count = 0
    await _log_login(db, user.id, "SUCCESS")

    profile = UserProfileResponse(
        id=user.id, login_id=user.login_id, name=user.name,
        email=user.email, department_name=user.department_name,
        position=user.position, user_type=user.user_type,
        role_code=role_code, role_name=role_name,
        data_grades=ROLE_DATA_GRADES.get(role_code, [3]),
    )

    return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=profile)


async def get_user_profile(db: AsyncSession, user_id) -> UserProfileResponse | None:
    result = await db.execute(select(UserAccount).where(UserAccount.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    role_result = await db.execute(
        select(UserRole.role_code, UserRole.role_name)
        .join(UserRoleMap, UserRoleMap.role_id == UserRole.id)
        .where(UserRoleMap.user_id == user.id, UserRoleMap.status == "ACTIVE")
    )
    role_row = role_result.first()
    role_code = role_row[0] if role_row else "EXTERNAL"
    role_name = role_row[1] if role_row else "외부사용자"

    return UserProfileResponse(
        id=user.id, login_id=user.login_id, name=user.name,
        email=user.email, department_name=user.department_name,
        position=user.position, user_type=user.user_type,
        role_code=role_code, role_name=role_name,
        data_grades=ROLE_DATA_GRADES.get(role_code, [3]),
    )


async def _log_login(db: AsyncSession, user_id, result: str, reason: str | None = None):
    import uuid
    log = UserLoginHistory(
        id=uuid.uuid4(), user_id=user_id,
        login_type="PASSWORD", login_result=result,
        fail_reason=reason, logged_at=datetime.now(),
    )
    db.add(log)
