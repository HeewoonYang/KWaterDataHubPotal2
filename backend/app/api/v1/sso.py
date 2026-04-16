"""SSO 인증 API — SAML 2.0 / OAuth 2.0 / 1회용 코드 교환"""
import json
import secrets
import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.sso import SsoProviderConfig
from app.services import sso_service, oauth_service, saml_service

router = APIRouter()

# ── 인메모리 1회용 코드 저장소 (프로덕션에서는 Redis 사용) ──
_one_time_codes: dict[str, dict] = {}


def _store_code(login_response_dict: dict, ttl: int = 120) -> str:
    code = secrets.token_urlsafe(32)
    _one_time_codes[code] = login_response_dict
    return code


def _consume_code(code: str) -> dict | None:
    return _one_time_codes.pop(code, None)


# ── SAML 2.0 ──

@router.get("/saml/login")
async def saml_login(request: Request, return_url: str = "/portal/sso-callback"):
    """SAML AuthnRequest 생성 → IdP 리다이렉트"""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
        req_data = saml_service.build_request_data(request)
        auth = OneLogin_Saml2_Auth(req_data, saml_service.get_saml_settings())
        sso_url = auth.login(return_to=return_url)
        return RedirectResponse(url=sso_url, status_code=302)
    except ImportError:
        # python3-saml 미설치 시 IdP URL로 직접 리다이렉트 (개발용)
        params = urlencode({"SAMLRequest": "dev_mode", "RelayState": return_url})
        return RedirectResponse(url=f"{settings.SAML_IDP_SSO_URL}?{params}", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAML 요청 생성 실패: {str(e)}")


@router.post("/saml/acs")
async def saml_acs(request: Request, db: AsyncSession = Depends(get_db)):
    """SAML ACS — IdP 응답 검증 → 사용자 매칭 → 1회용 코드 발급 → 프론트 리다이렉트"""
    try:
        from onelogin.saml2.auth import OneLogin_Saml2_Auth
        req_data = await saml_service.build_request_data_with_post(request)
        auth = OneLogin_Saml2_Auth(req_data, saml_service.get_saml_settings())
        auth.process_response()
        errors = auth.get_errors()
        if errors:
            raise HTTPException(status_code=400, detail=f"SAML 응답 검증 실패: {errors}")

        name_id = auth.get_nameid()
        attrs = auth.get_attributes()
        attributes = {
            "email": attrs.get("email", [name_id])[0] if attrs.get("email") else name_id,
            "name": attrs.get("name", [""])[0] if attrs.get("name") else "",
            "employee_no": attrs.get("employeeNumber", [""])[0] if attrs.get("employeeNumber") else "",
            "department_code": attrs.get("department", [""])[0] if attrs.get("department") else "",
            "department_name": attrs.get("departmentName", [""])[0] if attrs.get("departmentName") else "",
            "position": attrs.get("position", [""])[0] if attrs.get("position") else "",
        }
    except ImportError:
        # python3-saml 미설치 시 개발용 mock
        form = await request.form()
        name_id = form.get("NameID", "dev_user@kwater.or.kr")
        attributes = {
            "email": str(name_id), "name": "SSO 테스트 사용자",
            "employee_no": "99999", "department_code": "DEV",
            "department_name": "개발팀", "position": "연구원",
        }

    # 사용자 매칭/자동생성
    user = await sso_service.find_or_provision_user(
        db, sso_identifier=str(name_id), provider_name="OASIS_SAML",
        attributes=attributes, default_role="EMPLOYEE", default_user_type="INTERNAL",
    )

    # JWT 토큰 발급
    login_response = await sso_service.build_login_response(db, user, login_type="SSO_SAML")
    await db.commit()

    # 1회용 코드 발급 → 프론트 리다이렉트
    code = _store_code(login_response.model_dump(mode="json"))
    relay_state = (await request.form()).get("RelayState", "/portal/sso-callback") if hasattr(request, '_form') else "/portal/sso-callback"
    return RedirectResponse(url=f"/portal/sso-callback?code={code}", status_code=302)


@router.get("/saml/metadata")
async def saml_metadata():
    """SP 메타데이터 XML"""
    xml = saml_service.generate_sp_metadata()
    return Response(content=xml, media_type="application/xml")


# ── OAuth 2.0 ──

@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """OAuth 인가 요청 → IdP 리다이렉트"""
    config = oauth_service.get_provider_config(provider)
    if not config:
        raise HTTPException(status_code=404, detail=f"OAuth 제공자를 찾을 수 없습니다: {provider}")

    state = oauth_service.generate_state()
    code_verifier = oauth_service.generate_code_verifier()

    # state에 code_verifier 저장 (인메모리, 프로덕션에서는 Redis)
    _one_time_codes[f"oauth_state_{state}"] = {"code_verifier": code_verifier, "provider": provider}

    # PKCE challenge
    import hashlib, base64
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    callback_url = str(request.base_url).rstrip("/") + f"/api/v1/sso/oauth/{provider}/callback"
    params = {
        "response_type": "code",
        "client_id": config["client_id"],
        "redirect_uri": callback_url,
        "scope": " ".join(config.get("scopes", ["openid", "profile", "email"])),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = config["authorize_url"] + "?" + urlencode(params)
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, request: Request, db: AsyncSession = Depends(get_db)):
    """OAuth 콜백 → 코드 교환 → userinfo → 사용자 매칭"""
    state_data = _one_time_codes.pop(f"oauth_state_{state}", None)
    if not state_data:
        raise HTTPException(status_code=400, detail="유효하지 않은 state 파라미터")

    callback_url = str(request.base_url).rstrip("/") + f"/api/v1/sso/oauth/{provider}/callback"

    # 코드 → 토큰 교환
    token_resp = await oauth_service.exchange_code_for_token(
        provider, code, callback_url, code_verifier=state_data.get("code_verifier"),
    )

    # userinfo 조회
    access_token = token_resp.get("access_token", "")
    user_info = await oauth_service.fetch_user_info(provider, access_token)

    sso_id = user_info.get("sub") or user_info.get("email", "")
    if not sso_id:
        raise HTTPException(status_code=400, detail="사용자 식별 정보를 가져올 수 없습니다")

    # 제공자 설정에서 기본 역할/유형 조회
    config = oauth_service.get_provider_config(provider)
    default_role = config.get("default_role", "EXTERNAL") if config else "EXTERNAL"
    default_type = config.get("default_user_type", "EXTERNAL") if config else "EXTERNAL"

    user = await sso_service.find_or_provision_user(
        db, sso_identifier=sso_id, provider_name=provider,
        attributes=user_info, default_role=default_role, default_user_type=default_type,
    )

    login_response = await sso_service.build_login_response(db, user, login_type="SSO_OAUTH")
    await db.commit()

    one_time_code = _store_code(login_response.model_dump(mode="json"))
    return RedirectResponse(url=f"/portal/sso-callback?code={one_time_code}", status_code=302)


# ── 1회용 코드 → JWT 교환 ──

class ExchangeRequest(BaseModel):
    code: str

@router.post("/exchange")
async def exchange_code(body: ExchangeRequest):
    """1회용 코드 → JWT 토큰 교환 (프론트엔드 호출)"""
    data = _consume_code(body.code)
    if not data:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 코드입니다")
    return data


# ── SSO 제공자 목록 (로그인 페이지용) ──

@router.get("/providers")
async def list_providers(db: AsyncSession = Depends(get_db)):
    """활성 SSO 제공자 목록 (인증 불필요)"""
    rows = (await db.execute(
        select(SsoProviderConfig).where(SsoProviderConfig.is_enabled == True, SsoProviderConfig.is_deleted == False)
        .order_by(SsoProviderConfig.sort_order)
    )).scalars().all()

    providers = [{
        "provider_type": r.provider_type,
        "provider_name": r.provider_name,
        "display_name": r.display_name,
    } for r in rows]

    # SAML(오아시스)은 설정이 있으면 항상 포함
    if settings.SAML_IDP_SSO_URL and not any(p["provider_name"] == "OASIS_SAML" for p in providers):
        providers.insert(0, {
            "provider_type": "SAML",
            "provider_name": "OASIS_SAML",
            "display_name": "오아시스 SSO",
        })

    return {"success": True, "data": providers}
