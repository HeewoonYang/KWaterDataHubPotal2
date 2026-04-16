from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "K-water DataHub Portal API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database (환경변수 주입 필수 - K8s ConfigMap/Secret)
    DATABASE_URL: str = "postgresql+asyncpg://datahub:datahub@postgres:5432/datahub"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://datahub:datahub@postgres:5432/datahub"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # OpenMetadata
    OPENMETADATA_URL: str = "http://openmetadata:8585/api"
    OPENMETADATA_JWT_TOKEN: str = ""

    # JWT (보안 크리티컬 - 기본값 없음, 미주입 시 부팅 실패)
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=16,
        description="JWT 서명 키. K8s Secret 또는 .env 로만 주입 (코드·이미지 하드코딩 금지)",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # DB 비밀번호 등 민감정보 AES-256-GCM 암호화 키 (base64-url 32바이트)
    # 미설정 시 JWT_SECRET_KEY 에서 파생되며 경고 로그 기록 — 운영에서는 반드시 명시 주입
    # 생성: python -c "import os,base64;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
    DB_SECRET_ENCRYPTION_KEY: str = ""

    # SAML 2.0 (오아시스 SSO)
    SAML_SP_ENTITY_ID: str = "https://datahub.kwater.or.kr"
    SAML_SP_ACS_URL: str = "https://datahub.kwater.or.kr/api/v1/sso/saml/acs"
    SAML_IDP_ENTITY_ID: str = "https://oasis.kwater.or.kr/idp"
    SAML_IDP_SSO_URL: str = "https://oasis.kwater.or.kr/idp/sso"
    SAML_IDP_SLO_URL: str = ""
    SAML_IDP_CERT: str = ""
    SAML_SP_CERT_FILE: str = ""
    SAML_SP_KEY_FILE: str = ""

    # OAuth 2.0 (외부 사용자)
    OAUTH_PROVIDERS_JSON: str = "[]"

    # 유통 API (API 키 발급 시 사용자에게 제공하는 엔드포인트)
    DISTRIBUTION_API_ENDPOINT: str = "https://api.kwater.or.kr/data/v1/query"

    # ERP 연계
    ERP_API_URL: str = "https://erp.kwater.or.kr/api/hr"
    ERP_API_KEY: str = ""
    ERP_SYNC_CRON: str = "0 6 * * *"
    ERP_DEFAULT_ROLE: str = "EMPLOYEE"
    ERP_CONFLICT_POLICY: str = "ERP_FIRST"

    # CORS (운영에서는 명시적 allowlist 필수. "*"은 DEBUG=true 일 때만 허용)
    CORS_ORIGINS: list[str] = Field(default_factory=list)

    # 품질 AI 학습 피드백
    # STUB: stdout JSON + OperationAiQueryLog 에 synthetic 학습 질의로 기록 (기본값, 개발/테스트)
    # HTTP: OperationAiModelConfig.endpoint_url 로 실제 전송
    QUALITY_AI_FEEDBACK_DISPATCH: str = "STUB"
    QUALITY_AI_FEEDBACK_THRESHOLD: float = 80.0  # 이 점수 미만 결과를 피드백 대상으로 삼음
    QUALITY_AI_FEEDBACK_BATCH: int = 50  # 1회 dispatch 배치 크기

    # SMS (아이디/비밀번호 찾기·초기 비밀번호 발송)
    # STUB: 개발용 - DB 로그 + 인앱 알림 + stdout JSON 으로만 기록
    # DMZ_PROXY: 운영 - 내부망 DMZ 프록시 연동 (별도 어댑터 구현 필요)
    SMS_PROVIDER: str = "STUB"
    SMS_SENDER_NAME: str = "K-water 데이터허브"
    SMS_DMZ_PROXY_URL: str = ""

    # Object Storage (MinIO / S3 호환) - 업로드 파일은 파드 로컬이 아닌 오브젝트 스토리지로
    OBJECT_STORAGE_ENDPOINT: str = "minio:9000"
    OBJECT_STORAGE_ACCESS_KEY: str = ""
    OBJECT_STORAGE_SECRET_KEY: str = ""
    OBJECT_STORAGE_BUCKET: str = "datahub"
    OBJECT_STORAGE_SECURE: bool = False
    OBJECT_STORAGE_REGION: str = "us-east-1"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _validate_cors(cls, v: list[str]) -> list[str]:
        # 와일드카드는 DEBUG 환경에서만 허용 (운영 배포 시 반드시 도메인 목록으로 지정)
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
