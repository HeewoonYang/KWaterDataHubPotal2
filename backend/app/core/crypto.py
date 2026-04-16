"""DB 비밀번호/API 키 등 민감정보 AES-256-GCM 암호화 모듈.

CollectionDataSource.connection_password_enc, CollectionExternalAgency.api_key_enc 등
민감정보 컬럼은 평문 저장 금지. 본 모듈의 encrypt_secret / decrypt_secret 을 통해서만 저장·복원한다.

- 알고리즘: AES-256-GCM (인증 암호화, 무결성 검증 포함)
- 키원천: 환경변수 DB_SECRET_ENCRYPTION_KEY (base64-url-safe 32바이트)
  - 운영: K8s Secret 주입, 로컬 개발: .env 로 주입
  - 미설정 시 데릭티드 키로 폴백(JWT_SECRET_KEY → HKDF)하여 부팅은 허용하되 경고 로그 기록
- 저장 포맷: "enc:v1:{base64(nonce(12B) + ciphertext + tag(16B))}"
- 하위호환: prefix 없는 문자열은 평문으로 간주 (기존 데이터 마이그레이션 중 공존 허용)
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

logger = logging.getLogger(__name__)

ENC_PREFIX = "enc:v1:"
_NONCE_LEN = 12  # GCM 권장 nonce 길이


def _load_key() -> bytes:
    """환경변수로부터 AES-256 키 로드. 미설정 시 JWT_SECRET_KEY 로부터 HKDF-SHA256 derive."""
    raw = os.environ.get("DB_SECRET_ENCRYPTION_KEY", "").strip()
    if raw:
        try:
            key = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        except Exception:
            # base64 디코드 실패 시 UTF-8 bytes 를 SHA-256 으로 축약 → 32B
            key = hashlib.sha256(raw.encode("utf-8")).digest()
        if len(key) not in (16, 24, 32):
            key = hashlib.sha256(key).digest()  # 32B 로 정규화
        return key

    # 폴백: JWT_SECRET_KEY 기반 파생 키 (운영에선 DB_SECRET_ENCRYPTION_KEY 명시 주입 권장)
    logger.warning(
        "DB_SECRET_ENCRYPTION_KEY 미설정 — JWT_SECRET_KEY 파생 키로 폴백 (운영에서는 명시 주입 필요)"
    )
    return hashlib.sha256(("datahub-db-secret/" + settings.JWT_SECRET_KEY).encode("utf-8")).digest()


_KEY_CACHE: Optional[bytes] = None


def _get_key() -> bytes:
    global _KEY_CACHE
    if _KEY_CACHE is None:
        _KEY_CACHE = _load_key()
    return _KEY_CACHE


def encrypt_secret(plaintext: str | None) -> str | None:
    """평문 비밀값 → "enc:v1:<base64>" 형식의 암호문.

    None/빈 문자열은 그대로 반환 (저장 시 NULL 유지).
    이미 ENC_PREFIX 로 시작하는 입력은 재암호화하지 않고 그대로 반환.
    """
    if plaintext is None:
        return None
    if plaintext == "":
        return ""
    if isinstance(plaintext, str) and plaintext.startswith(ENC_PREFIX):
        return plaintext  # idempotent
    aes = AESGCM(_get_key())
    nonce = secrets.token_bytes(_NONCE_LEN)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return ENC_PREFIX + base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def decrypt_secret(ciphertext: str | None) -> str | None:
    """암호문 → 평문. ENC_PREFIX 미지정(레거시 평문)은 그대로 반환."""
    if ciphertext is None:
        return None
    if ciphertext == "":
        return ""
    if not isinstance(ciphertext, str) or not ciphertext.startswith(ENC_PREFIX):
        # 레거시 평문 (마이그레이션 전 데이터) — 그대로 통과
        return ciphertext
    try:
        raw = base64.urlsafe_b64decode(ciphertext[len(ENC_PREFIX):])
        nonce, ct = raw[:_NONCE_LEN], raw[_NONCE_LEN:]
        aes = AESGCM(_get_key())
        return aes.decrypt(nonce, ct, None).decode("utf-8")
    except Exception as e:
        logger.error("민감정보 복호화 실패: %s", e)
        raise ValueError("secret decryption failed") from e


def is_encrypted(value: str | None) -> bool:
    """값이 이미 암호화되어 있는지 여부."""
    return isinstance(value, str) and value.startswith(ENC_PREFIX)


def mask_secret(value: str | None) -> str:
    """UI 노출용 마스킹. 평문/암호문 여부와 무관하게 "********" 반환."""
    if value is None or value == "":
        return ""
    return "********"
