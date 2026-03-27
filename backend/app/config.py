from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "K-water DataHub Portal API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://datahub:datahub@postgres:5432/datahub"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://datahub:datahub@postgres:5432/datahub"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # OpenMetadata
    OPENMETADATA_URL: str = "http://openmetadata:8585/api"
    OPENMETADATA_JWT_TOKEN: str = ""

    # JWT
    JWT_SECRET_KEY: str = "kwater-datahub-portal-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:8088", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
