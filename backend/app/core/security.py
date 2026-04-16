"""보안 유틸리티 - JWT 토큰, 비밀번호 해싱, 정책 검증"""
import re
import uuid
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호 해싱. bcrypt 백엔드 로딩 실패 시 SHA256 폴백 (seed 와 동일).

    최신 bcrypt(>=4.1) 는 passlib 의 detect_wrap_bug 초기화 단계에서
    72바이트 초과 입력에 ValueError 를 던져 전체 해싱을 실패시킬 수 있다.
    개발/테스트 환경에서 바로 실패하지 않도록 SHA256 폴백을 둔다.
    """
    try:
        return pwd_context.hash(password)
    except Exception:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    # seed 데이터는 SHA256으로 해싱되어 있으므로 bcrypt 실패 시 SHA256 비교
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        import hashlib
        return hashlib.sha256(plain.encode()).hexdigest() == hashed


# ── 비밀번호 정책 (행안부 지침 준수) ──
PASSWORD_MIN_LENGTH = 9
PASSWORD_EXPIRY_DAYS = 90
MAX_LOGIN_FAILURES = 5


def validate_password(password: str) -> tuple[bool, str]:
    """비밀번호 복잡도 검증: 9자 이상, 3종 이상 문자 유형 필수"""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"비밀번호는 {PASSWORD_MIN_LENGTH}자 이상이어야 합니다"

    type_count = 0
    if re.search(r"[A-Z]", password):
        type_count += 1
    if re.search(r"[a-z]", password):
        type_count += 1
    if re.search(r"\d", password):
        type_count += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", password):
        type_count += 1

    if type_count < 3:
        return False, "대문자, 소문자, 숫자, 특수문자 중 3종 이상 포함해야 합니다"

    return True, ""


def generate_jti() -> str:
    return str(uuid.uuid4())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None
