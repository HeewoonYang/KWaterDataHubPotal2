"""인증 의존성 - get_current_user"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import UserAccount, UserRole, UserRoleMap

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# 역할별 접근 가능 등급
ROLE_DATA_GRADES = {
    "ADMIN": [1, 2, 3],
    "MANAGER": [1, 2, 3],
    "INTERNAL": [2, 3],
    "EXTERNAL": [3],
}


class CurrentUser:
    """인증된 사용자 정보"""
    def __init__(self, user: UserAccount, role_code: str, role_name: str):
        self.id = user.id
        self.login_id = user.login_id
        self.name = user.name
        self.email = user.email
        self.department_name = user.department_name
        self.position = user.position
        self.user_type = user.user_type
        self.role_code = role_code
        self.role_name = role_name
        self.data_grades = ROLE_DATA_GRADES.get(role_code, [3])


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰에 사용자 정보가 없습니다")

    # 사용자 조회
    result = await db.execute(select(UserAccount).where(UserAccount.id == UUID(user_id), UserAccount.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="비활성 사용자입니다")

    # 역할 조회
    role_result = await db.execute(
        select(UserRole.role_code, UserRole.role_name)
        .join(UserRoleMap, UserRoleMap.role_id == UserRole.id)
        .where(UserRoleMap.user_id == user.id, UserRoleMap.status == "ACTIVE")
    )
    role_row = role_result.first()
    role_code = role_row[0] if role_row else "EXTERNAL"
    role_name = role_row[1] if role_row else "외부사용자"

    return CurrentUser(user, role_code, role_name)


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser | None:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
