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
    data_grades: list[int]

    model_config = {"from_attributes": True}
