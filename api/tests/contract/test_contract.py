"""The running app against openapi.yaml (standard §18): Schemathesis generates requests for every
operation and checks status codes, content types, headers and response schemas.
Exceptions, each with a reason, are in schemathesis.toml."""

import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
import schemathesis
from fastapi import FastAPI
from hypothesis import HealthCheck, settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_access_token
from app.core.db import get_session
from app.core.settings import get_settings
from tests.contract_routes import implemented, labels


@pytest.fixture
def api_schema(app: object, fastapi_app: FastAPI, session: AsyncSession) -> Iterator[object]:
    """In process, on the rolled-back session, so generated writes don't outlive the test."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield session

    fastapi_app.dependency_overrides[get_session] = _session
    schema = schemathesis.openapi.from_path("openapi.yaml")
    schema.app = app  # the path prefix comes from servers[0].url
    yield schema
    fastapi_app.dependency_overrides.clear()


schema = schemathesis.pytest.from_fixture("api_schema")


@schema.parametrize()
@settings(
    max_examples=25,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
def test_app_matches_contract(case: schemathesis.Case[Any], fastapi_app: FastAPI) -> None:
    if case.operation.label not in labels(implemented(fastapi_app)):
        # Documented but not built yet: the contract is written first (standard §4).
        pytest.skip(f"{case.operation.label} is not implemented yet")
    token = issue_access_token(get_settings(), uuid.uuid4())
    case.call_and_validate(headers={"Authorization": f"Bearer {token}"})
