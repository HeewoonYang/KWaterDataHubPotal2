"""계정 복구 서비스 - 아이디 찾기 / 비밀번호 초기화 / 초기 비밀번호 SMS 발송

외부사용자 셀프서비스 + 관리자 수동 재발송을 모두 담당한다.
Redis 에 OTP 및 레이트리밋 카운터를 저장 (K8s 멀티 레플리카 친화).

보안 원칙:
- 사용자 열거(enumeration) 공격 방지: 일치 여부와 무관하게 동일 형태의 성공 응답을 돌려준다.
- 임시/초기 비밀번호는 DB/응답/로그에 평문으로 남기지 않고 오직 SMS 페이로드에만 담는다.
- 비밀번호 초기화 시 기존 세션을 즉시 모두 무효화한다.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import string
import uuid
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import hash_password
from app.models.user import UserAccount, UserLoginHistory
from app.services import auth_service, sms_service

logger = logging.getLogger(__name__)

# ── Redis 싱글톤 ──────────────────────────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None

OTP_TTL_SECONDS = 300  # 5분
OTP_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 600  # 10분
RATE_LIMIT_MAX = 5  # IP 당 10분 5회


def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


# ── 유틸 ───────────────────────────────────────────────────────────────
def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _generate_temp_password(length: int = 12) -> str:
    """정책(9자+3종)을 항상 만족하는 임시 비밀번호 생성."""
    upper = secrets.choice(string.ascii_uppercase)
    lower = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    remaining_pool = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = [secrets.choice(remaining_pool) for _ in range(length - 4)]
    chars = [upper, lower, digit, special, *remaining]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _mask_login_id(login_id: str) -> str:
    if not login_id:
        return ""
    n = len(login_id)
    if n <= 3:
        return login_id[0] + "*" * (n - 1) if n > 1 else login_id
    if n <= 5:
        return login_id[:2] + "*" * (n - 3) + login_id[-1]
    return login_id[:3] + "*" * (n - 4) + login_id[-1]


def _normalize_phone(phone: str) -> str:
    """비교/저장용 정규화 - 하이픈 제거"""
    return re.sub(r"\D", "", phone or "")


# ── 레이트 리밋 ────────────────────────────────────────────────────────
async def check_rate_limit(scope: str, identifier: str) -> bool:
    """해당 scope+identifier 의 최근 호출 수가 한도를 넘지 않았는지 확인.
    True=허용, False=차단."""
    key = f"ratelimit:recovery:{scope}:{identifier}"
    try:
        r = _get_redis()
        cnt = await r.incr(key)
        if cnt == 1:
            await r.expire(key, RATE_LIMIT_WINDOW_SECONDS)
        return cnt <= RATE_LIMIT_MAX
    except Exception as e:
        logger.warning("recovery.rate_limit failed (fail-open): %s", e)
        return True


# ── 아이디 찾기 ────────────────────────────────────────────────────────
async def find_id_request_otp(db: AsyncSession, name: str, phone: str) -> dict:
    """이름+휴대폰 일치 외부사용자에게 OTP SMS 발송.
    일치하지 않더라도 동일 응답 구조로 돌려준다 (열거 방지)."""
    normalized_phone = _normalize_phone(phone)
    request_id = str(uuid.uuid4())

    user = await _find_external_user_by_name_phone(db, name, normalized_phone)

    if user is not None:
        code = _generate_otp()
        key = f"otp:findid:{request_id}"
        payload = json.dumps({
            "user_id": str(user.id),
            "code": code,
            "attempts": 0,
        })
        try:
            await _get_redis().set(key, payload, ex=OTP_TTL_SECONDS)
        except Exception as e:
            logger.error("find_id_request_otp: redis set failed: %s", e)
            # fail-closed: OTP 저장 실패 시 SMS 보내지 않음. 응답은 동일 형태 유지.
            return {"request_id": request_id, "masked_phone": sms_service.mask_phone(phone)}

        await sms_service.send_sms(
            db,
            phone=phone,
            purpose="FIND_ID_OTP",
            template_key="FIND_ID_OTP",
            params={"code": code},
            target_user_id=user.id,
        )
        await _log_event(db, user.id, "ID_LOOKUP_OTP", "SUCCESS", "OTP 발송")
    else:
        # 열거 방지: 실제 사용자가 없어도 시간 지연을 유사하게 맞춤
        await asyncio.sleep(0.2)

    return {"request_id": request_id, "masked_phone": sms_service.mask_phone(phone)}


async def find_id_verify_otp(db: AsyncSession, request_id: str, code: str) -> Optional[str]:
    """OTP 검증 성공 시 마스킹된 login_id 반환, 실패 시 None."""
    key = f"otp:findid:{request_id}"
    try:
        r = _get_redis()
        raw = await r.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        attempts = int(data.get("attempts", 0)) + 1
        if attempts > OTP_MAX_ATTEMPTS:
            await r.delete(key)
            return None
        if str(data.get("code")) != str(code):
            data["attempts"] = attempts
            await r.set(key, json.dumps(data), ex=OTP_TTL_SECONDS)
            return None
        # 성공
        user_id_str = data.get("user_id")
        await r.delete(key)
    except Exception as e:
        logger.error("find_id_verify_otp: redis error: %s", e)
        return None

    user = (await db.execute(
        select(UserAccount).where(UserAccount.id == uuid.UUID(user_id_str))
    )).scalar_one_or_none()
    if not user:
        return None
    return _mask_login_id(user.login_id)


# ── 비밀번호 초기화 ────────────────────────────────────────────────────
async def reset_password_request(db: AsyncSession, login_id: str, name: str, phone: str) -> None:
    """login_id + 이름 + 휴대폰 일치하는 외부사용자에 대해 임시 비밀번호 발송.
    일치하지 않더라도 성공 응답으로 끝낸다 (열거 방지). """
    normalized_phone = _normalize_phone(phone)

    user = (await db.execute(
        select(UserAccount).where(
            UserAccount.login_id == login_id,
            UserAccount.is_deleted == False,
            UserAccount.user_type == "EXTERNAL",
        )
    )).scalar_one_or_none()

    if user is None or user.name != name or _normalize_phone(user.phone or "") != normalized_phone:
        await asyncio.sleep(0.2)
        return

    temp_password = _generate_temp_password()
    user.password_hash = hash_password(temp_password)
    user.password_changed_at = datetime.now()
    user.must_change_password = True
    user.login_fail_count = 0
    if user.status == "SUSPENDED":
        user.status = "ACTIVE"

    await auth_service.revoke_session(db, user.id)

    await sms_service.send_sms(
        db,
        phone=phone,
        purpose="RESET_PWD",
        template_key="RESET_PWD",
        params={"password": temp_password},
        target_user_id=user.id,
    )
    await _log_event(db, user.id, "PWD_RESET_ISSUED", "SUCCESS", "임시 비밀번호 발송")


# ── 초기 비밀번호 SMS ─────────────────────────────────────────────────
async def send_initial_password(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    issued_by: Optional[uuid.UUID] = None,
) -> tuple[bool, str]:
    """관리자 트리거 - 외부사용자에게 초기/재발급 비밀번호 SMS."""
    user = (await db.execute(
        select(UserAccount).where(UserAccount.id == user_id, UserAccount.is_deleted == False)
    )).scalar_one_or_none()
    if not user:
        return False, "사용자를 찾을 수 없습니다"
    if user.user_type != "EXTERNAL":
        return False, "외부사용자만 초기 비밀번호 SMS 발송 대상입니다"
    if not user.phone:
        return False, "대상 사용자의 휴대폰번호가 등록되어 있지 않습니다"

    temp_password = _generate_temp_password()
    user.password_hash = hash_password(temp_password)
    user.password_changed_at = datetime.now()
    user.must_change_password = True
    user.login_fail_count = 0
    if user.status in ("SUSPENDED", "PENDING"):
        user.status = "ACTIVE"
    if issued_by is not None:
        user.updated_by = issued_by
        user.updated_at = datetime.now()

    await auth_service.revoke_session(db, user.id)

    await sms_service.send_sms(
        db,
        phone=user.phone,
        purpose="INITIAL_PWD",
        template_key="INITIAL_PWD",
        params={"name": user.name, "password": temp_password},
        target_user_id=user.id,
    )
    await _log_event(db, user.id, "INITIAL_PWD_SENT", "SUCCESS", "초기 비밀번호 SMS 발송")
    return True, "초기 비밀번호 SMS를 발송했습니다"


# ── 내부 헬퍼 ──────────────────────────────────────────────────────────
async def _find_external_user_by_name_phone(
    db: AsyncSession, name: str, normalized_phone: str
) -> Optional[UserAccount]:
    """외부사용자 중 이름이 일치하고 휴대폰번호(정규화)가 일치하는 첫 번째 사용자를 반환."""
    candidates = (await db.execute(
        select(UserAccount).where(
            UserAccount.user_type == "EXTERNAL",
            UserAccount.name == name,
            UserAccount.is_deleted == False,
        )
    )).scalars().all()
    for u in candidates:
        if _normalize_phone(u.phone or "") == normalized_phone and normalized_phone:
            return u
    return None


async def _log_event(db: AsyncSession, user_id, login_type: str, result: str, reason: str) -> None:
    db.add(UserLoginHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        login_type=login_type,
        login_result=result,
        fail_reason=reason,
        logged_at=datetime.now(),
    ))
