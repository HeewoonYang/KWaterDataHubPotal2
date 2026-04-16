"""인증 스키마"""
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    login_id: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfileResponse"


class UserProfileResponse(BaseModel):
    id: UUID
    login_id: str
    name: str
    email: str | None = None
    department_name: str | None = None
    position: str | None = None
    user_type: str
    role_code: str
    role_name: str
    role_group: str = ""
    data_grades: list[int]
    screen_permissions: dict[str, dict[str, bool]] = {}
    must_change_password: bool = False

    model_config = {"from_attributes": True}


# ── 아이디/비밀번호 찾기 ───────────────────────────────────────────────
class FindIdRequest(BaseModel):
    name: str
    phone: str


class FindIdRequestResponse(BaseModel):
    request_id: str
    masked_phone: str
    # 주의: 보안상 실제 매칭 여부는 응답에 노출하지 않는다 (열거 공격 방지)


class FindIdVerifyRequest(BaseModel):
    request_id: str
    code: str


class FindIdVerifyResponse(BaseModel):
    login_id_masked: str


class ResetPasswordRequest(BaseModel):
    login_id: str
    name: str
    phone: str
