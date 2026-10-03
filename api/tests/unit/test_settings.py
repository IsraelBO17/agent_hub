from typing import Any

import pytest
from pydantic import ValidationError

from app.core.settings import Settings

BASE = {
    "database_url": "postgresql+psycopg://u:p@h/db",
    "google_client_id": "client.apps.googleusercontent.com",
    "files_bucket": "bucket",
}


def build(**values: Any) -> Settings:
    """Settings from these values and the environment, ignoring any .env file."""
    return Settings(_env_file=None, **values)


@pytest.mark.parametrize("missing", ["session_signing_key", "APP_ENV", "google_client_id"])
def test_missing_required_value_stops_the_boot(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing.upper(), raising=False)
    values = {**BASE, "APP_ENV": "local", "session_signing_key": "x" * 40}
    values.pop(missing)
    with pytest.raises(ValidationError):
        build(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"cors_origins": ["*"]},
        {"session_signing_key": "short"},
        {"session_signing_key": "local-only-signing-key-change-me-0123456789"},
        {"docs_enabled": True, "APP_ENV": "prod"},
        {"google_client_id": "local-placeholder.apps.googleusercontent.com"},
        {"app_origin": "*"},
    ],
)
def test_unsafe_values_refused_outside_local(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        build(**{**BASE, "APP_ENV": "dev", "session_signing_key": "x" * 40, **overrides})


def test_validation_status_is_400_or_422() -> None:
    with pytest.raises(ValidationError):
        build(**BASE, APP_ENV="local", session_signing_key="x" * 40, validation_status=418)


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://", "postgresql+psycopg://"])
def test_database_urls_use_psycopg(scheme: str) -> None:
    s = build(
        google_client_id="client.apps.googleusercontent.com",
        files_bucket="bucket",
        APP_ENV="local",
        session_signing_key="x" * 40,
        database_url=f"{scheme}u:p@h/db",
        database_url_direct=f"{scheme}u:p@h-direct/db",
    )
    assert s.database_url == "postgresql+psycopg://u:p@h/db"
    assert s.migrations_url == "postgresql+psycopg://u:p@h-direct/db"
