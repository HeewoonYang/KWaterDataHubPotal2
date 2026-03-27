"""인증 API - 로그인/로그아웃/프로필"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, UserProfileResponse
from app.schemas.common import APIResponse
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.authenticate_user(db, body.login_id, body.password)
    if not result:
        raise HTTPException(status_code=401, detail="로그인 ID 또는 비밀번호가 올바르지 않습니다")
    return result


@router.post("/logout", response_model=APIResponse)
async def logout(user: CurrentUser = Depends(get_current_user)):
    return APIResponse(message="로그아웃 완료")


@router.get("/me", response_model=APIResponse[UserProfileResponse])
async def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await auth_service.get_user_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return APIResponse(data=profile)
