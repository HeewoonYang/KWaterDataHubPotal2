"""인증 API - 로그인/로그아웃/프로필/비밀번호 변경/아이디-비밀번호 찾기"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.security import decode_token
from app.core.token_blacklist import revoke as revoke_jti
from app.database import get_db
from app.schemas.auth import (
    FindIdRequest, FindIdRequestResponse, FindIdVerifyRequest, FindIdVerifyResponse,
    LoginRequest, LoginResponse, ResetPasswordRequest, UserProfileResponse,
)
from app.schemas.common import APIResponse
from app.services import auth_service, recovery_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.authenticate_user(db, body.login_id, body.password)
    if not result:
        raise HTTPException(status_code=401, detail="로그인 ID 또는 비밀번호가 올바르지 않습니다")
    return result


@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1) DB 세션 무효화 (이력 보존용)
    await auth_service.revoke_session(db, user.id)

    # 2) 현재 요청의 access token jti 를 Redis 블랙리스트에 추가 (즉시 차단)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload:
            await revoke_jti(payload.get("jti"), payload.get("exp"))

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


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.put("/change-password", response_model=APIResponse)
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 변경 (9자 이상, 3종 이상 문자 유형)"""
    success, message = await auth_service.change_password(db, user.id, body.old_password, body.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return APIResponse(message=message)


# ── 외부사용자 아이디/비밀번호 찾기 (공개 엔드포인트) ──────────────────
def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/recovery/find-id/request", response_model=APIResponse[FindIdRequestResponse])
async def find_id_request(
    body: FindIdRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """아이디 찾기 - 이름+휴대폰으로 OTP SMS 발송.
    사용자 열거 방지를 위해 일치 여부와 무관하게 동일 응답 형태를 반환한다."""
    if not await recovery_service.check_rate_limit("findid_req", _client_ip(request)):
        raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
    result = await recovery_service.find_id_request_otp(db, body.name, body.phone)
    return APIResponse(
        message="입력하신 정보와 일치하는 계정이 있다면 SMS로 인증번호가 발송되었습니다.",
        data=FindIdRequestResponse(**result),
    )


@router.post("/recovery/find-id/verify", response_model=APIResponse[FindIdVerifyResponse])
async def find_id_verify(
    body: FindIdVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """아이디 찾기 - OTP 검증 후 마스킹된 login_id 반환."""
    if not await recovery_service.check_rate_limit("findid_ver", _client_ip(request)):
        raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
    masked = await recovery_service.find_id_verify_otp(db, body.request_id, body.code)
    if masked is None:
        raise HTTPException(status_code=400, detail="인증번호가 일치하지 않거나 만료되었습니다.")
    return APIResponse(data=FindIdVerifyResponse(login_id_masked=masked))


@router.post("/recovery/reset-password", response_model=APIResponse)
async def reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 찾기 - 아이디+이름+휴대폰 일치 시 임시 비밀번호 SMS 발송.
    열거 방지를 위해 일치/불일치 관계없이 동일 응답."""
    if not await recovery_service.check_rate_limit("resetpw_req", _client_ip(request)):
        raise HTTPException(status_code=429, detail="요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
    await recovery_service.reset_password_request(db, body.login_id, body.name, body.phone)
    return APIResponse(
        message="입력하신 정보와 일치하는 계정이 있다면 SMS로 임시 비밀번호를 발송했습니다. 로그인 후 반드시 비밀번호를 변경해주세요."
    )
