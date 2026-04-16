"""OAuth 2.0 서비스 — authlib 래핑"""
import json
import secrets
from app.config import settings


def get_oauth_providers() -> list[dict]:
    """설정에서 OAuth 제공자 목록 조회"""
    try:
        providers = json.loads(settings.OAUTH_PROVIDERS_JSON)
        return [p for p in providers if p.get("enabled", True)]
    except (json.JSONDecodeError, TypeError):
        return []


def get_provider_config(provider_name: str) -> dict | None:
    """특정 OAuth 제공자 설정 조회"""
    for p in get_oauth_providers():
        if p.get("name") == provider_name:
            return p
    return None


def generate_state() -> str:
    """CSRF 방지 state 파라미터 생성"""
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """PKCE code_verifier 생성"""
    return secrets.token_urlsafe(64)


async def exchange_code_for_token(provider_name: str, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict:
    """인가 코드 → 액세스 토큰 교환"""
    config = get_provider_config(provider_name)
    if not config:
        raise ValueError(f"OAuth provider not found: {provider_name}")

    import httpx
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": config["client_id"],
        "client_secret": config.get("client_secret", ""),
    }
    if code_verifier:
        data["code_verifier"] = code_verifier

    async with httpx.AsyncClient() as client:
        resp = await client.post(config["token_url"], data=data, timeout=10)
        resp.raise_for_status()
        return resp.json()


async def fetch_user_info(provider_name: str, access_token: str) -> dict:
    """OAuth userinfo 엔드포인트에서 사용자 정보 조회"""
    config = get_provider_config(provider_name)
    if not config or not config.get("userinfo_url"):
        return {}

    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            config["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        info = resp.json()

    # 표준화된 속성으로 변환
    return {
        "sub": info.get("sub") or info.get("id", ""),
        "email": info.get("email", ""),
        "name": info.get("name") or info.get("display_name", ""),
        "employee_no": info.get("employee_no") or info.get("employeeNumber", ""),
        "department_code": info.get("department_code") or info.get("dept_code", ""),
        "department_name": info.get("department_name") or info.get("dept_name", ""),
        "position": info.get("position") or info.get("title", ""),
    }
