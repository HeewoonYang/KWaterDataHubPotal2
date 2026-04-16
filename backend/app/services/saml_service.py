"""SAML 2.0 서비스 — python3-saml 래핑"""
import os
from fastapi import Request
from app.config import settings


def get_saml_settings() -> dict:
    """python3-saml 설정 딕셔너리 생성"""
    sp_cert = ""
    sp_key = ""
    if settings.SAML_SP_CERT_FILE and os.path.exists(settings.SAML_SP_CERT_FILE):
        with open(settings.SAML_SP_CERT_FILE) as f:
            sp_cert = f.read()
    if settings.SAML_SP_KEY_FILE and os.path.exists(settings.SAML_SP_KEY_FILE):
        with open(settings.SAML_SP_KEY_FILE) as f:
            sp_key = f.read()

    return {
        "strict": True,
        "debug": settings.DEBUG,
        "sp": {
            "entityId": settings.SAML_SP_ENTITY_ID,
            "assertionConsumerService": {
                "url": settings.SAML_SP_ACS_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "x509cert": sp_cert,
            "privateKey": sp_key,
        },
        "idp": {
            "entityId": settings.SAML_IDP_ENTITY_ID,
            "singleSignOnService": {
                "url": settings.SAML_IDP_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "singleLogoutService": {
                "url": settings.SAML_IDP_SLO_URL or settings.SAML_IDP_SSO_URL,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": settings.SAML_IDP_CERT,
        },
        "security": {
            "authnRequestsSigned": bool(sp_key),
            "wantAssertionsSigned": True,
            "wantNameIdEncrypted": False,
        },
    }


def build_request_data(request: Request) -> dict:
    """FastAPI Request → python3-saml 호환 딕셔너리 변환"""
    scheme = request.url.scheme
    host = request.headers.get("host", request.url.hostname)
    return {
        "https": "on" if scheme == "https" else "off",
        "http_host": host,
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": {},
    }


async def build_request_data_with_post(request: Request) -> dict:
    """POST 요청용 — form 데이터 포함"""
    data = build_request_data(request)
    form = await request.form()
    data["post_data"] = dict(form)
    return data


def generate_sp_metadata() -> str:
    """SP 메타데이터 XML 생성"""
    try:
        from onelogin.saml2.settings import OneLogin_Saml2_Settings
        saml_settings = OneLogin_Saml2_Settings(get_saml_settings(), sp_validation_only=True)
        metadata = saml_settings.get_sp_metadata()
        errors = saml_settings.validate_metadata(metadata)
        if errors:
            return f"<!-- Metadata validation errors: {errors} -->\n{metadata.decode('utf-8') if isinstance(metadata, bytes) else metadata}"
        return metadata.decode("utf-8") if isinstance(metadata, bytes) else metadata
    except ImportError:
        # python3-saml이 설치되지 않은 경우 기본 메타데이터 반환
        return f"""<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="{settings.SAML_SP_ENTITY_ID}">
  <md:SPSSODescriptor AuthnRequestsSigned="false"
      protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService
        Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        Location="{settings.SAML_SP_ACS_URL}" index="1"/>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""
