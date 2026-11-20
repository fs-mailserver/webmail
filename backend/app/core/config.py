"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    app_name: str = "Webmail API"
    environment: Literal["development", "test", "production"] = Field(
        default="production", validation_alias=AliasChoices("WEBMAIL_ENVIRONMENT", "ENVIRONMENT")
    )

    database_url: str = Field(validation_alias=AliasChoices("WEBMAIL_DATABASE_URL", "DATABASE_URL"))
    database_pool_size: int = Field(default=10, validation_alias="WEBMAIL_DATABASE_POOL_SIZE")
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias=AliasChoices("WEBMAIL_REDIS_URL", "REDIS_URL"))

    jwt_secret: SecretStr = Field(validation_alias="WEBMAIL_JWT_SECRET")
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = Field(default="HS256", validation_alias="WEBMAIL_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=720, ge=5, le=60 * 24 * 30, validation_alias="WEBMAIL_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Comma-separated list of Fernet keys; the first one encrypts, all of them decrypt (rotation).
    mailbox_credential_encryption_key: SecretStr = Field(validation_alias="MAILBOX_CREDENTIAL_ENCRYPTION_KEY")

    # Comma-separated list of allowed browser origins (frontend lives on its own subdomain).
    cors_origins_raw: str = Field(default="", validation_alias="WEBMAIL_CORS_ORIGINS")

    storage_root: Path = Field(default=Path("/app/storage"), validation_alias="WEBMAIL_STORAGE_ROOT")

    mail_imap_host: str = Field(default="mailserver", validation_alias="MAIL_IMAP_HOST")
    mail_imap_port: int = Field(default=993, validation_alias="MAIL_IMAP_PORT")
    mail_smtp_host: str = Field(default="mailserver", validation_alias="MAIL_SMTP_HOST")
    mail_smtp_port: int = Field(default=587, validation_alias="MAIL_SMTP_PORT")

    @field_validator("database_url")
    @classmethod
    def _force_asyncpg_driver(cls, value: str) -> str:
        value = value.strip()
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix):]
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL (postgresql+asyncpg://...).")
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_strength(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"WEBMAIL_JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters long.")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def attachments_dir(self) -> Path:
        return self.storage_root / "attachments"

    @property
    def eml_dir(self) -> Path:
        return self.storage_root / "eml"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

