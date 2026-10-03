"""The running app against openapi.yaml (standard §18): Schemathesis generates requests for every
operation and checks status codes, content types, headers and response schemas.
Exceptions, each with a reason, are in schemathesis.toml."""

import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
import schemathesis
from fastapi import FastAPI
from hypothesis import HealthCheck, settings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import issue_access_token
from app.core.db import get_session
from app.core.settings import get_settings
from app.features.agents.descriptor import load_descriptor
from app.features.agents.service import AgentService
from tests.contract_routes import implemented, labels

AGENTS = Path(__file__).resolve().parents[3] / "agents"


@pytest.fixture
async def registered_agents(session: AsyncSession) -> None:
    """The repository's agent descriptors, so agent responses are checked with real data (the
    slug parameter's example is one of them). On the rolled-back session."""
    for path in sorted(AGENTS.glob("*.yaml")):
        await AgentService(session, get_settings()).register(load_descriptor(path))


@pytest.fixture
def api_schema(
    app: object, fastapi_app: FastAPI, session: AsyncSession, registered_agents: None
) -> Iterator[object]:
    """In process, on the rolled-back session, so generated writes don't outlive the test."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield session

    fastapi_app.dependency_overrides[get_session] = _session
    schema = schemathesis.openapi.from_path("openapi.yaml")
    schema.app = _requests_only(app)  # the path prefix comes from servers[0].url
    yield schema
    fastapi_app.dependency_overrides.clear()


def _requests_only(app: Any) -> Any:
    """The `app` fixture already runs the lifespan. Schemathesis would start a second one on its
    own event loop: a second job worker on the shared `shutting_down` event, a re-pointed database
    and, when it stops, `shutting_down` set for every later test (a flaky "bound to a different
    event loop"). Refusing the lifespan scope before receiving is how an app says it has none."""

    async def asgi(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            raise RuntimeError("the lifespan is run by the app fixture")
        await app(scope, receive, send)

    return asgi


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
