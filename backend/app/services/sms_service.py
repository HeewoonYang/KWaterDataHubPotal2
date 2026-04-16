"""SMS 발송 서비스

현재 SMS 게이트웨이 인프라가 없으므로 추상화 + Stub 구현을 제공한다.
- Stub: `sys_sms_log` 테이블에 기록 + 식별된 사용자에게 포털 인앱 알림 생성 + stdout JSON 로그
- 향후 DMZ 프록시 어댑터를 추가할 때 `get_sms_provider()` 팩토리를 확장한다.

K8s 멀티 레플리카 전제를 지키기 위해 상태는 DB/Redis 에만 둔다.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Protocol, Optional
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.base import new_uuid
from app.models.portal import PortalNotification
from app.models.system import SysSmsLog

logger = logging.getLogger(__name__)


# ── 템플릿 ─────────────────────────────────────────────────────────────
SMS_TEMPLATES: dict[str, str] = {
    "INITIAL_PWD": "[K-water 데이터허브] {name}님, 초기 비밀번호는 {password} 입니다. 최초 로그인 후 반드시 변경해주세요.",
    "RESET_PWD": "[K-water 데이터허브] 임시 비밀번호 {password}. 로그인 후 반드시 변경하세요.",
    "FIND_ID_OTP": "[K-water 데이터허브] 아이디찾기 인증번호 {code} (5분 유효).",
}


# ── 유틸 ───────────────────────────────────────────────────────────────
def mask_phone(phone: str) -> str:
    """010-1234-5678 → 010-****-5678, 01012345678 → 010-****-5678"""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11:
        return f"{digits[:3]}-****-{digits[7:]}"
    if len(digits) == 10:
        return f"{digits[:3]}-***-{digits[6:]}"
    # 폴백: 마지막 4자리만 노출
    return "****" + digits[-4:] if digits else phone


def render_template(template_key: str, params: dict) -> str:
    tmpl = SMS_TEMPLATES.get(template_key)
    if not tmpl:
        raise ValueError(f"Unknown SMS template: {template_key}")
    return tmpl.format(**params)


# ── Provider 인터페이스 ────────────────────────────────────────────────
class SmsProvider(Protocol):
    name: str

    async def send(self, *, to: str, text: str) -> tuple[bool, Optional[str]]:
        """발송 시도. (성공여부, 에러메시지) 반환"""
        ...


class StubSmsProvider:
    """실제 SMS 를 보내지 않고 stdout JSON 으로만 로그하는 개발용 Provider."""
    name = "STUB"

    async def send(self, *, to: str, text: str) -> tuple[bool, Optional[str]]:
        logger.info(
            "SMS_STUB_SEND %s",
            json.dumps({"to": to, "text": text, "ts": datetime.utcnow().isoformat()}, ensure_ascii=False),
        )
        return True, None


_provider_singleton: Optional[SmsProvider] = None


def get_sms_provider() -> SmsProvider:
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton
    choice = (settings.SMS_PROVIDER or "STUB").upper()
    if choice == "STUB":
        _provider_singleton = StubSmsProvider()
    else:
        # 향후 DMZ_PROXY 등 추가 시 여기서 분기. 현재는 Stub 으로 폴백.
        logger.warning("Unknown SMS_PROVIDER=%s, falling back to STUB", choice)
        _provider_singleton = StubSmsProvider()
    return _provider_singleton


# ── 공개 API ───────────────────────────────────────────────────────────
async def send_sms(
    db: AsyncSession,
    *,
    phone: str,
    purpose: str,
    template_key: str,
    params: dict,
    target_user_id: Optional[UUID] = None,
    inapp_title: Optional[str] = None,
    inapp_message: Optional[str] = None,
) -> bool:
    """SMS 발송 + 이력 기록 + (선택) 인앱 알림 생성.

    Args:
        phone: 수신 휴대폰번호 (원본). DB 에는 마스킹된 값만 저장.
        purpose: INITIAL_PWD / RESET_PWD / FIND_ID_OTP
        template_key: SMS_TEMPLATES 의 키
        params: 템플릿 치환 값
        target_user_id: 식별된 대상 사용자 (있으면 인앱 알림도 생성)
        inapp_title/inapp_message: 인앱 알림 문구. 미지정 시 템플릿 기반 요약.
    """
    provider = get_sms_provider()
    text = render_template(template_key, params)
    ok, err = await provider.send(to=phone, text=text)

    # 이력 기록
    await db.execute(
        insert(SysSmsLog).values(
            id=new_uuid(),
            target_user_id=target_user_id,
            recipient_phone_masked=mask_phone(phone),
            purpose=purpose,
            payload_template=template_key,
            status="SENT" if ok else "FAIL",
            provider=provider.name,
            error_message=err,
            sent_at=datetime.now(),
        )
    )

    # 식별된 사용자면 인앱 알림도 남김 (Stub 환경에서 테스트 편의)
    if ok and target_user_id is not None:
        title = inapp_title or _default_inapp_title(purpose)
        message = inapp_message or _default_inapp_message(purpose)
        db.add(PortalNotification(
            id=new_uuid(),
            user_id=target_user_id,
            notification_type="SYSTEM",
            title=title,
            message=message,
            is_read=False,
            created_at=datetime.now(),
        ))

    return ok


def _default_inapp_title(purpose: str) -> str:
    return {
        "INITIAL_PWD": "[계정] 초기 비밀번호 SMS 발송",
        "RESET_PWD": "[계정] 비밀번호 초기화 SMS 발송",
        "FIND_ID_OTP": "[계정] 아이디찾기 인증번호 SMS 발송",
    }.get(purpose, "[계정] SMS 발송")


def _default_inapp_message(purpose: str) -> str:
    return {
        "INITIAL_PWD": "가입하신 휴대폰번호로 초기 비밀번호가 발송되었습니다. 최초 로그인 후 반드시 비밀번호를 변경해주세요.",
        "RESET_PWD": "가입하신 휴대폰번호로 임시 비밀번호가 발송되었습니다. 로그인 후 비밀번호를 변경해주세요.",
        "FIND_ID_OTP": "인증번호가 발송되었습니다. 5분 이내 입력해주세요.",
    }.get(purpose, "SMS가 발송되었습니다.")
