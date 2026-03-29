from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    secret_key: str = Field(validation_alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cors_origins: str = Field(
        default="http://127.0.0.1:3000,http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )
    database_url: str = Field(default="sqlite:///./banklens.db", validation_alias="DATABASE_URL")
    allow_registration: bool = Field(default=False, validation_alias="ALLOW_REGISTRATION")
    seed_demo_user: bool = Field(default=False, validation_alias="SEED_DEMO_USER")
    demo_user_email: str = Field(default="demo@example.com", validation_alias="DEMO_USER_EMAIL")
    demo_user_password: str = Field(default="", validation_alias="DEMO_USER_PASSWORD")
    trusted_hosts: str = Field(default="localhost,127.0.0.1", validation_alias="TRUSTED_HOSTS")
    rule_pack_version: str = Field(default="RULEPACK_V1", validation_alias="RULE_PACK_VERSION")
    seed_banklens_demo: bool = Field(default=True, validation_alias="SEED_BANKLENS_DEMO")
    default_enterprise_slug: str = Field(default="demo", validation_alias="DEFAULT_ENTERPRISE_SLUG")

    # Generative layer (OpenAI-compatible API). Rules engine remains source of truth for signals.
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    gen_ai_after_bsi: bool = Field(default=True, validation_alias="GEN_AI_AFTER_BSI")
    openai_timeout_seconds: float = Field(default=60.0, ge=5.0, le=120.0, validation_alias="OPENAI_TIMEOUT_SECONDS")

    smtp_host: str = Field(default="", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65535, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="", validation_alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")

    whatsapp_access_token: str = Field(default="", validation_alias="WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_number_id: str = Field(default="", validation_alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_api_version: str = Field(default="v21.0", validation_alias="WHATSAPP_API_VERSION")

    @field_validator("secret_key")
    @classmethod
    def secret_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def reject_wildcard_cors_in_production(self):
        if self.is_production and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS must not use '*' in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [x.strip() for x in self.trusted_hosts.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")


def get_settings() -> Settings:
    return Settings()
