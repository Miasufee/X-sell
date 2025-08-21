from pydantic_settings import BaseSettings
from pydantic import field_validator, EmailStr
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application Configuration
    APP_ENV: str
    APP_SECRET_KEY: str
    APP_DEBUG: bool = False

    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    DB_POOL_MIN: int = 2
    DB_POOL_MAX: int = 20
    DB_POOL_TIMEOUT: int = 30

    # API Superuser Configuration
    API_SUPERUSER_USERNAME: str
    API_SUPERUSER_PASSWORD: str
    API_SUPERUSER_EMAIL: EmailStr
    API_SUPERUSER_SECRET_KEY: str

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str
    CORS_ALLOWED_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_ALLOWED_HEADERS: str = "Authorization,Content-Type"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_EXPOSE_HEADERS: Optional[str] = None

    @property
    def database_url(self) -> str:
        """PostgreSQL URL for synchronous connections."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """PostgreSQL URL for asynchronous connections."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def cors_methods(self) -> List[str]:
        """Parse CORS methods from comma-separated string."""
        return [method.strip() for method in self.CORS_ALLOWED_METHODS.split(",") if method.strip()]

    @property
    def cors_headers(self) -> List[str]:
        """Parse CORS headers from comma-separated string."""
        return [header.strip() for header in self.CORS_ALLOWED_HEADERS.split(",") if header.strip()]

    @property
    def cors_expose_headers(self) -> List[str]:
        """Parse CORS expose headers from comma-separated string."""
        if not self.CORS_EXPOSE_HEADERS:
            return []
        return [header.strip() for header in self.CORS_EXPOSE_HEADERS.split(",") if header.strip()]

    @field_validator('APP_SECRET_KEY', 'JWT_SECRET_KEY', 'API_SUPERUSER_SECRET_KEY')
    def validate_secret_keys(cls, v: str) -> str:
        """Ensure secret keys are not empty and have minimum length."""
        if not v or len(v) < 32:
            raise ValueError(
                "Secret keys must be at least 32 characters long. "
                "Use 'python -c \"import secrets; print(secrets.token_urlsafe(32))\"' to generate one."
            )
        return v

    @field_validator('POSTGRES_PORT')
    def validate_postgres_port(cls, v: int) -> int:
        """Validate PostgreSQL port range."""
        if not 1 <= v <= 65535:
            raise ValueError("PostgreSQL port must be between 1 and 65535")
        return v

    @field_validator('APP_ENV')
    def validate_environment(cls, v: str) -> str:
        """Validate and warn about production settings."""
        if v == "production":
            logger.warning(
                "Running in PRODUCTION mode. Ensure all secret keys are properly configured!"
            )
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True
        use_enum_values = True


def get_settings() -> Settings:
    """Get application settings with proper error handling."""
    try:
        app_settings = Settings()
        if app_settings.APP_ENV == "production":
            logger.info("Running in production mode with configured environment variables.")
        else:
            logger.info(f"Running in {app_settings.APP_ENV} mode.")
        return app_settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise


settings = get_settings()
