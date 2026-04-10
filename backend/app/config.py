from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    app_name: str = Field(default='RefurbOps API', alias='APP_NAME')
    app_env: str = Field(default='local', alias='APP_ENV')
    app_debug: bool = Field(default=True, alias='APP_DEBUG')
    app_host: str = Field(default='127.0.0.1', alias='APP_HOST')
    app_port: int = Field(default=8000, alias='APP_PORT')
    app_public_url: str = Field(default='https://app.refurbops.local', alias='APP_PUBLIC_URL')
    api_public_url: str = Field(default='https://api.refurbops.local', alias='API_PUBLIC_URL')
    frontend_origin: str = Field(default='https://app.refurbops.local', alias='FRONTEND_ORIGIN')

    mongo_uri: str = Field(default='mongodb://localhost:27017', alias='MONGO_URI')
    mongo_db_name: str = Field(default='refurbops', alias='MONGO_DB_NAME')
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')

    access_cookie_name: str = Field(default='refurbops_access', alias='ACCESS_COOKIE_NAME')
    refresh_cookie_name: str = Field(default='refurbops_refresh', alias='REFRESH_COOKIE_NAME')
    access_token_ttl_minutes: int = Field(default=10, alias='ACCESS_TOKEN_TTL_MINUTES')
    session_idle_timeout_minutes: int = Field(default=15, alias='SESSION_IDLE_TIMEOUT_MINUTES')
    session_absolute_timeout_hours: int = Field(default=12, alias='SESSION_ABSOLUTE_TIMEOUT_HOURS')
    sensitive_reauth_window_minutes: int = Field(default=5, alias='SENSITIVE_REAUTH_WINDOW_MINUTES')
    jwt_active_kid: str = Field(default='local-dev-key-1', alias='JWT_ACTIVE_KID')
    jwt_issuer: str = Field(default='refurbops-api', alias='JWT_ISSUER')
    jwt_audience: str = Field(default='refurbops-web', alias='JWT_AUDIENCE')
    jwt_private_key_pem: str = Field(default='', alias='JWT_PRIVATE_KEY_PEM')
    jwt_public_key_pem: str = Field(default='', alias='JWT_PUBLIC_KEY_PEM')
    jwt_private_key_path: str = Field(default='', alias='JWT_PRIVATE_KEY_PATH')
    jwt_public_key_path: str = Field(default='', alias='JWT_PUBLIC_KEY_PATH')

    platform_owner_email: str = Field(default='info@repairedtech.co.uk', alias='PLATFORM_OWNER_EMAIL')
    platform_owner_initial_password: str = Field(default='', alias='PLATFORM_OWNER_INITIAL_PASSWORD')
    platform_owner_require_mfa: bool = Field(default=True, alias='PLATFORM_OWNER_REQUIRE_MFA')
    mfa_issuer: str = Field(default='RefurbOps', alias='MFA_ISSUER')

    email_provider: str = Field(default='postmark', alias='EMAIL_PROVIDER')
    email_from_name: str = Field(default='RefurbOps', alias='EMAIL_FROM_NAME')
    email_from_address: str = Field(default='noreply@repairedtech.co.uk', alias='EMAIL_FROM_ADDRESS')
    email_reply_to: str = Field(default='info@repairedtech.co.uk', alias='EMAIL_REPLY_TO')

    email_token_ttl_invite_hours: int = Field(default=72, alias='EMAIL_TOKEN_TTL_INVITE_HOURS')
    postmark_server_token: str = Field(default='', alias='POSTMARK_SERVER_TOKEN')
    postmark_webhook_secret: str = Field(default='', alias='POSTMARK_WEBHOOK_SECRET')

    stripe_secret_key: str = Field(default='', alias='STRIPE_SECRET_KEY')
    stripe_webhook_secret: str = Field(default='', alias='STRIPE_WEBHOOK_SECRET')
    stripe_use_tax: bool = Field(default=True, alias='STRIPE_USE_TAX')

    aws_region: str = Field(default='eu-west-2', alias='AWS_REGION')
    aws_secrets_manager_prefix: str = Field(default='refurbops/local', alias='AWS_SECRETS_MANAGER_PREFIX')
    aws_kms_key_id: str = Field(default='', alias='AWS_KMS_KEY_ID')
    aws_s3_bucket: str = Field(default='', alias='AWS_S3_BUCKET')
    aws_sqs_queue_url: str = Field(default='', alias='AWS_SQS_QUEUE_URL')

    otel_enabled: bool = Field(default=False, alias='OTEL_ENABLED')
    otel_service_name: str = Field(default='refurbops-backend', alias='OTEL_SERVICE_NAME')
    otel_exporter_otlp_endpoint: str = Field(default='', alias='OTEL_EXPORTER_OTLP_ENDPOINT')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
