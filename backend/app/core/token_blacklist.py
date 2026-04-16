"""
JWT 토큰 블랙리스트 (Redis 캐시)

K8s 멀티 레플리카 환경에서 로그아웃/세션 무효화를 stateless 하게 처리하려면
DB 조회 대신 Redis 를 사용해야 한다. jti 를 키로 저장하고 토큰 만료 시각까지 TTL 을 준다.

키 포맷:  jwt:blacklist:{jti}
값       :  "1"  (존재 자체가 revoked 를 의미)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "jwt:blacklist:"
_redis_client: Optional[aioredis.Redis] = None


def _get_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def revoke(jti: str, exp_timestamp: Optional[int] = None) -> None:
    """jti 를 블랙리스트에 추가. exp_timestamp (unix) 가 주어지면 해당 시각까지 TTL."""
    if not jti:
        return
    key = _KEY_PREFIX + jti
    try:
        if exp_timestamp is not None:
            ttl = max(int(exp_timestamp - datetime.utcnow().timestamp()), 1)
            await _get_client().set(key, "1", ex=ttl)
        else:
            # fallback: access token 최대 수명 + 1분 여유
            ttl = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 60
            await _get_client().set(key, "1", ex=ttl)
    except Exception as e:
        logger.warning("token_blacklist.revoke failed: %s", e)


async def is_revoked(jti: str) -> bool:
    """블랙리스트 조회. Redis 장애 시 fail-open (False 반환)."""
    if not jti:
        return False
    try:
        return bool(await _get_client().exists(_KEY_PREFIX + jti))
    except Exception as e:
        logger.warning("token_blacklist.is_revoked failed (fail-open): %s", e)
        return False


async def close() -> None:
    """lifespan shutdown 시 호출."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
