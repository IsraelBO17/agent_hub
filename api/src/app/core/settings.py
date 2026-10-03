"""Typed settings from the environment (standard §10). Loaded once; missing or unsafe values stop the boot.

Agent Hub values follow docs/API_PROFILE.md. ECS injects APP_ENV, PORT, APP_ORIGIN, FILES_BUCKET,
GOOGLE_CLIENT_ID and AWS_REGION, and from Secrets Manager DATABASE_URL, DATABASE_URL_DIRECT and
SESSION_SIGNING_KEY (D15).
"""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Local defaults come from the committed .env.example, overridden by a local .env, overridden by
    # real environment variables. The image contains neither file, so in a deployed environment a
    # missing required value still stops the boot. pydantic-settings forbids unknown variables by
    # default; shared env files need "ignore".
    model_config = SettingsConfigDict(env_file=(".env.example", ".env"), extra="ignore")

    # Required: a deployment that forgot it must not run with the local-only guards off.
    env: str = Field(validation_alias="APP_ENV")  # local | dev | prod (ECS sets APP_ENV)
    service_name: str = "agent-hub-api"

    # Database (§11). Required: no default, so a missing value stops the boot.
    database_url: str
    database_url_direct: str | None = None  # migrations; never through a transaction-mode pooler
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_statement_timeout_ms: int = 30_000
    db_prepared_statements: bool = False  # true only after a test through the real pooler

    # Auth (§12)
    session_signing_key: SecretStr
    access_token_ttl_seconds: int = 900
    token_issuer: str = "https://api.fleet.qucoon.com"  # noqa: S105  (a name, not a secret)
    token_audience: str = "https://api.fleet.qucoon.com"  # noqa: S105
    google_client_id: str  # D8; not secret (also ships to the web app)

    # HTTP (§8, §15)
    app_origin: str | None = None  # the web app (APP_ORIGIN); always an allowed CORS origin
    cors_origins: list[str] = []  # extra origins, JSON in the environment (local dev only)
    max_body_bytes: int = 1_000_000  # files go straight to S3 (D7); bodies are small
    errors_base_url: str = "https://fleet.qucoon.com/errors/"
    validation_status: int = 422  # the contract's choice (D23)
    docs_enabled: bool = False  # serves openapi.yaml at /openapi.yaml when true

    # Process (§14, §19)
    port: int = 8000
    # The task's security group admits only the ALB, so its forwarded headers are trusted.
    forwarded_allow_ips: str = "*"
    shutdown_grace_seconds: int = 110  # below the ECS stop timeout of 120 s (P2)
    stream_time_limit_seconds: int = 900
    log_level: str = "INFO"
    log_json: bool = True

    # Jobs (§13)
    run_worker_in_api: bool = True  # one API task, no separate worker (P7)
    worker_poll_seconds: float = 1.0
    worker_batch_size: int = 10
    job_lease_seconds: int = 300
    job_retention_days: int = 14

    # AWS (D7, D12)
    aws_region: str = "us-east-1"
    files_bucket: str

    @field_validator("database_url", "database_url_direct", mode="before")
    @classmethod
    def _psycopg_scheme(cls, url: object) -> object:
        """Hosts hand out postgres:// or postgresql:// URLs; the app and migrations use psycopg 3."""
        if isinstance(url, str):
            for prefix in ("postgres://", "postgresql://"):
                if url.startswith(prefix):
                    return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    @model_validator(mode="after")
    def _refuse_unsafe(self) -> "Settings":
        if self.env != "local":
            if "*" in self.allowed_origins:
                raise ValueError("CORS_ORIGINS must list explicit origins outside local")
            if len(self.session_signing_key.get_secret_value()) < 32:
                raise ValueError("SESSION_SIGNING_KEY must be at least 32 characters")
            if "local-only" in self.session_signing_key.get_secret_value():
                raise ValueError("SESSION_SIGNING_KEY is the local placeholder")
            if self.google_client_id.startswith("local-placeholder"):
                raise ValueError("GOOGLE_CLIENT_ID is the local placeholder")
            if self.docs_enabled and self.env == "prod":
                raise ValueError("DOCS_ENABLED must be false in prod")
        if self.validation_status not in (400, 422):
            raise ValueError("VALIDATION_STATUS must be 400 or 422")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        """CORS origins: the app origin plus any extra local ones."""
        return [o for o in [self.app_origin, *self.cors_origins] if o]

    @property
    def migrations_url(self) -> str:
        return self.database_url_direct or self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
