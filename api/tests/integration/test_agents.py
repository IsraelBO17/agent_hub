"""The agents feature (SPEC.md, feature: agents): registering from a descriptor, the catalog, one
agent, and the caller's stats."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import cli
from app.core.errors import Conflict
from app.core.settings import get_settings
from app.features.agents.descriptor import AgentDescriptor, load_descriptor
from app.features.agents.models import Agent
from app.features.agents.repository import AgentRepository
from app.features.agents.service import AgentService
from tests.conftest import AuthHeaders
from tests.support.agents import descriptor, descriptor_data

RESEARCH_ANALYST = Path(__file__).resolve().parents[3] / "agents" / "research-analyst.yaml"


async def register(session: AsyncSession, d: AgentDescriptor) -> Any:
    return await AgentService(session, get_settings()).register(d)


async def add_user(session: AsyncSession) -> uuid.UUID:
    user_id: uuid.UUID = await session.scalar(
        text(
            "INSERT INTO users (google_sub, email, status) VALUES (:s, :e, 'active') RETURNING id"
        ),
        {"s": str(uuid.uuid4()), "e": f"{uuid.uuid4().hex}@example.com"},
    )
    return user_id


async def add_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_id: uuid.UUID,
    last: datetime,
    *,
    deleted: bool = False,
    archived: bool = False,
) -> None:
    await session.execute(
        text(
            "INSERT INTO sessions (user_id, agent_id, last_message_at, deleted_at, archived_at)"
            " VALUES (:u, :a, :t, :d, :r)"
        ),
        {
            "u": user_id,
            "a": agent_id,
            "t": last,
            "d": last if deleted else None,
            "r": last if archived else None,
        },
    )


# ---------------------------------------------------------------- register_agent


async def test_register_adds_then_reports_unchanged(session: AsyncSession) -> None:
    first = await register(session, descriptor(version="1.0.0"))
    assert first.action == "added"
    assert first.agent.status == "online" and first.agent.deployed_at is not None
    again = await register(session, descriptor(version="1.0.0"))
    assert again.action == "unchanged"


async def test_register_updates_to_match_the_descriptor(session: AsyncSession) -> None:
    added = (await register(session, descriptor(version="1.0.0"))).agent
    deployed_at = added.deployed_at
    await session.execute(
        update(Agent)
        .where(Agent.id == added.id)
        .values(status="offline", deployed_at=deployed_at - timedelta(days=1))
    )
    await session.commit()

    same_version = await register(session, descriptor(version="1.0.0", name="Demo 2"))
    assert same_version.action == "updated"
    assert same_version.agent.name == "Demo 2"
    assert same_version.agent.deployed_at == deployed_at - timedelta(days=1)  # version unchanged
    assert same_version.agent.status == "offline"  # health isn't a descriptor field

    new_version = await register(session, descriptor(version="1.1.0", name="Demo 2"))
    assert (new_version.action, new_version.previous_version) == ("updated", "1.0.0")
    assert new_version.agent.deployed_at > deployed_at - timedelta(days=1)


async def test_register_stores_nested_objects_in_wire_shape(session: AsyncSession) -> None:
    agent = (await register(session, load_descriptor(RESEARCH_ANALYST))).agent
    assert agent.capabilities["attachments"]["maxFileBytes"] == 0
    assert agent.tools[0]["requiresApproval"] is False
    assert agent.runtime_arn is not None and agent.runtime_arn.startswith(
        "arn:aws:bedrock-agentcore"
    )


async def test_register_race_on_the_slug_is_a_conflict(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    await register(session, descriptor())

    async def not_found(self: AgentRepository, slug: str, *, for_update: bool = False) -> None:
        return None  # as if another `hub agents add` inserted it after our lookup

    monkeypatch.setattr(AgentRepository, "by_slug", not_found)
    with pytest.raises(Conflict):
        await register(session, descriptor())


# ---------------------------------------------------------------- list_agents


async def test_catalog_lists_live_agents_in_order(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    await session.execute(delete(Agent))  # rolled back after the test
    await register(session, descriptor(slug="zeta", name="Zeta"))
    await register(session, descriptor(slug="alpha", name="Alpha"))
    await register(session, descriptor(slug="first", name="Zz First", sortOrder=-1))
    await register(session, descriptor(slug="hidden", name="Hidden", visibility="hidden"))
    await register(session, descriptor(slug="gone", name="Gone"))
    await session.execute(
        update(Agent).where(Agent.slug == "gone").values(retired_at=datetime.now(UTC))
    )
    await session.commit()

    r = await client.get("/v1/agents", headers=auth(None))
    assert r.status_code == 200
    assert [a["slug"] for a in r.json()["items"]] == ["first", "alpha", "hidden", "zeta"]


async def test_hidden_agents_are_not_listed_in_production(
    client: httpx.AsyncClient,
    session: AsyncSession,
    auth: AuthHeaders,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await session.execute(delete(Agent))
    await register(session, descriptor(slug="shown"))
    await register(session, descriptor(slug="hidden", visibility="hidden"))
    monkeypatch.setattr(get_settings(), "env", "prod")
    r = await client.get("/v1/agents", headers=auth(None))
    assert [a["slug"] for a in r.json()["items"]] == ["shown"]


async def test_catalog_is_empty_with_no_agents(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    await session.execute(delete(Agent))  # rolled back after the test
    r = await client.get("/v1/agents", headers=auth(None))
    assert r.status_code == 200 and r.json() == {"items": []}


async def test_my_stats_count_only_my_live_sessions(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    agent = (await register(session, descriptor())).agent
    me, other = await add_user(session), await add_user(session)
    t = datetime(2026, 10, 1, 12, tzinfo=UTC)
    await add_session(session, me, agent.id, t)
    await add_session(session, me, agent.id, t + timedelta(hours=2), archived=True)
    await add_session(session, me, agent.id, t + timedelta(hours=5), deleted=True)
    await add_session(session, other, agent.id, t + timedelta(hours=9))
    await session.commit()

    for path in ("/v1/agents", "/v1/agents/demo"):
        r = await client.get(path, headers=auth(me))
        body = r.json()
        found = body["items"][0] if "items" in body else body
        assert found["myStats"] == {"sessionCount": 2, "lastActiveAt": "2026-10-01T14:00:00Z"}

    r = await client.get("/v1/agents/demo", headers=auth(None))
    assert r.json()["myStats"] == {"sessionCount": 0, "lastActiveAt": None}


async def test_catalog_needs_a_token(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/agents")
    assert (r.status_code, r.json()["code"]) == (401, "token_invalid")


# ---------------------------------------------------------------- get_agent


async def test_get_agent_returns_the_descriptor_without_the_runtime_arn(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    d = load_descriptor(RESEARCH_ANALYST)
    await register(session, d)
    account_id = (d.runtime_arn or "").split(":")[4]
    r = await client.get("/v1/agents/research-analyst", headers=auth(None))
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Research Analyst" and body["stage"] == "beta"
    assert body["runtimeType"] == "agentcore" and body["status"] == "online"
    assert "runtimeArn" not in body and account_id not in r.text  # never the account id
    assert body["details"]["runtimeLabel"].startswith("arn:…:runtime/fleet_dev_research_analyst")
    assert body["details"]["model"] == "Claude Sonnet 5"
    assert len(body["starters"]) == 4 and body["starters"][0]["prompt"]
    assert body["tools"] == [
        {"name": "fetch_url", "description": "Reads a web page you link", "requiresApproval": False}
    ]


async def test_optional_properties_are_left_out_not_null(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    await register(
        session,
        descriptor(
            runtimeType="http",
            runtimeArn=None,
            runtimeEndpoint="https://agent.example.com/invoke",
            starters=[{"title": "Hi", "prompt": "Hello"}],
        ),
    )
    body = (await client.get("/v1/agents/demo", headers=auth(None))).json()
    assert body["starters"] == [{"title": "Hi", "prompt": "Hello"}]
    assert body["details"] == {"runtimeLabel": "agent.example.com"}
    assert body["tagline"] is None  # nullable and required: present as null


async def test_get_agent_includes_retired_and_hidden(
    client: httpx.AsyncClient, session: AsyncSession, auth: AuthHeaders
) -> None:
    await register(session, descriptor(slug="old", visibility="hidden"))
    retired = datetime(2026, 9, 1, tzinfo=UTC)
    await session.execute(update(Agent).where(Agent.slug == "old").values(retired_at=retired))
    await session.commit()
    r = await client.get("/v1/agents/old", headers=auth(None))
    assert r.status_code == 200 and r.json()["retiredAt"] == "2026-09-01T00:00:00Z"


async def test_unknown_slug_is_agent_not_found(
    client: httpx.AsyncClient, auth: AuthHeaders
) -> None:
    r = await client.get("/v1/agents/no-such-agent", headers=auth(None))
    assert (r.status_code, r.json()["code"]) == (404, "agent_not_found")


async def test_malformed_slug_is_invalid(client: httpx.AsyncClient, auth: AuthHeaders) -> None:
    r = await client.get("/v1/agents/Not_A_Slug", headers=auth(None))
    assert (r.status_code, r.json()["code"]) == (422, "invalid_request")


# ---------------------------------------------------------------- the CLI (hub)


def test_cli_rejects_an_invalid_descriptor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("slug: Bad Slug\ncolour: blue\n")
    assert cli.main(["agents", "add", str(bad)]) == 1
    err = capsys.readouterr().err
    assert "slug:" in err and "colour:" in err and "name:" in err


def test_cli_rejects_invalid_yaml(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("slug: [unclosed\n")
    assert cli.main(["agents", "add", str(bad)]) == 1
    assert "isn't valid YAML" in capsys.readouterr().err


def test_cli_reports_a_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["agents", "add", str(tmp_path / "nope.yaml")]) == 1
    assert "can't read" in capsys.readouterr().err


async def run(*args: str) -> int:
    """The CLI in a thread: it runs its own event loop, as it does from a shell."""
    return await asyncio.to_thread(cli.main, list(args))


async def test_cli_adds_lists_and_is_idempotent(
    tmp_path: Path,
    sessions: async_sessionmaker[AsyncSession],
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = f"cli-{uuid.uuid4().hex[:8]}"
    path = tmp_path / f"{slug}.yaml"
    path.write_text(yaml.safe_dump(descriptor_data(slug=slug, version="0.1.0")))
    try:
        assert await run("agents", "add", str(path)) == 0
        assert f"added {slug} (0.1.0, local)" in capsys.readouterr().out
        assert await run("agents", "add", str(path)) == 0
        assert f"{slug} unchanged" in capsys.readouterr().out
        path.write_text(yaml.safe_dump(descriptor_data(slug=slug, version="0.2.0")))
        assert await run("agents", "add", str(path)) == 0
        assert f"updated {slug}: 0.1.0 → 0.2.0" in capsys.readouterr().out
        assert await run("agents", "list") == 0
        listing = capsys.readouterr().out
        assert listing.startswith("SLUG") and slug in listing and "0.2.0" in listing
    finally:
        async with sessions() as s, s.begin():
            await s.execute(delete(Agent).where(Agent.slug == slug))
        async with sessions() as s:
            assert await s.scalar(select(Agent.id).where(Agent.slug == slug)) is None
