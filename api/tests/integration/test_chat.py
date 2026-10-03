"""The chat feature (SPEC.md, feature: chat): sends, the run, its stream, saving, reading back.

A run writes through its own sessions, outside any test transaction, so these tests commit: each
gets a fresh user and agent and deletes them afterwards (sessions, messages and tool calls cascade).
AgentCore is FakeAgentCore replaying tests/fixtures/agentcore/; every response and stream event is
checked against openapi.yaml.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import issue_access_token
from app.core.lifecycle import shutting_down
from app.core.settings import get_settings
from app.features.agents.models import Agent
from app.features.agents.service import AgentService
from app.features.chat import runs
from app.features.chat.jobs import interrupt_stale_replies
from app.features.chat.models import Message, Session, ToolCall
from app.features.chat.repository import ChatRepository
from app.features.chat.router import PING, get_agentcore, mirror
from app.features.chat.runs import Run, RunSettings
from app.features.chat.schemas import SendMessageRequest
from app.features.chat.service import ChatService, Started, title_of
from tests.support.agentcore import FakeAgentCore, Gate, raw, sse_response
from tests.support.agents import descriptor
from tests.support.contract import validate


@dataclass
class World:
    http: httpx.AsyncClient
    fake: FakeAgentCore
    user_id: uuid.UUID
    agent_slug: str
    headers: dict[str, str]


@pytest.fixture
async def world(
    app: object, fastapi_app: FastAPI, sessions: async_sessionmaker[AsyncSession]
) -> AsyncIterator[World]:
    slug = f"chat-{uuid.uuid4().hex[:8]}"
    async with sessions() as s:
        await AgentService(s, get_settings()).register(descriptor(slug=slug, version="1.0.0"))
        user_id = await s.scalar(
            text(
                "INSERT INTO users (google_sub, email, status) VALUES (:s, :e, 'active') RETURNING id"
            ),
            {"s": str(uuid.uuid4()), "e": f"{uuid.uuid4().hex}@example.com"},
        )
        await s.commit()
    assert isinstance(user_id, uuid.UUID)
    fake = FakeAgentCore()
    fastapi_app.dependency_overrides[get_agentcore] = lambda: fake.client
    token = issue_access_token(get_settings(), user_id)
    transport = httpx.ASGITransport(app=app)  # type: ignore[arg-type]
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield World(http, fake, user_id, slug, {"Authorization": f"Bearer {token}"})
    fastapi_app.dependency_overrides.clear()
    async with sessions() as s, s.begin():
        await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_id})
        await s.execute(delete(Agent).where(Agent.slug == slug))


def events_of(response: httpx.Response) -> list[dict[str, Any]]:
    """Parse an SSE body; check the framing and each event against the contract."""
    out: list[dict[str, Any]] = []
    for chunk in response.text.split("\n\n"):
        if not chunk.strip() or chunk.startswith(":"):
            continue
        fields = dict(line.split(": ", 1) for line in chunk.split("\n"))
        data = json.loads(fields["data"])
        assert fields["event"] == data["type"]
        assert fields["id"] == f"{data['messageId']}:{data['n']}"
        validate(data, "StreamEvent")
        out.append(data)
    assert [e["n"] for e in out] == list(range(1, len(out) + 1))
    return out


def body(text_: str = "What is example.com for?", **extra: Any) -> dict[str, Any]:
    return {"clientMessageId": str(uuid.uuid4()), "text": text_, **extra}


async def first_send(w: World, payload: dict[str, Any] | None = None) -> httpx.Response:
    return await w.http.post(
        f"/v1/agents/{w.agent_slug}/sessions", json=payload or body(), headers=w.headers
    )


async def row(sessions: async_sessionmaker[AsyncSession], message_id: str) -> Message:
    async with sessions() as s:
        found = await s.get(Message, uuid.UUID(message_id))
        assert found is not None
        return found


# ---------------------------------------------------------------- create_session_and_send


async def test_first_send_creates_the_session_and_streams_the_reply(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    sent = body("  What   is\nexample.com for?  ")
    r = await first_send(world, sent)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    events = events_of(r)
    started, *middle, last = events
    assert started["type"] == "run.started" and last["type"] == "run.completed"
    assert started["session"]["title"] == "What is example.com for?"
    assert started["session"]["isRunning"] is True and started["session"]["messageCount"] == 2
    assert started["userMessage"]["clientMessageId"] == sent["clientMessageId"]
    assert started["assistantMessage"]["status"] == "streaming"
    assert started["assistantMessage"]["agentVersion"] == "1.0.0"
    assert middle[0]["type"] == "block.started"
    assert {e["type"] for e in middle} == {"block.started", "block.delta", "block.completed"}

    final = last["message"]
    assert final["status"] == "complete" and final["usage"]["outputTokens"] > 0
    assert [b["type"] for b in final["blocks"]] == ["text"]
    deltas = "".join(e["text"] for e in middle if e["type"] == "block.delta")
    assert final["blocks"][0]["text"] == deltas

    saved = await row(sessions, final["id"])
    assert saved.status == "complete" and saved.completed_at is not None
    assert saved.blocks == final["blocks"] and saved.search_text == deltas
    payload = world.fake.payloads()[0]
    validate(payload, "AgentInvocation")
    assert payload["messages"] == [] and payload["input"] == sent["text"]
    assert payload["context"]["messageId"] == final["id"]
    request = world.fake.requests[0]
    assert (
        request.headers["x-amzn-bedrock-agentcore-runtime-session-id"] == started["session"]["id"]
    )


async def test_reload_returns_exactly_what_was_streamed(world: World) -> None:
    world.fake.reply = lambda _: sse_response("tool-call")
    events = events_of(await first_send(world))
    final = events[-1]["message"]
    session_id = events[0]["session"]["id"]

    got = await world.http.get(f"/v1/messages/{final['id']}", headers=world.headers)
    assert got.status_code == 200
    validate(got.json(), "Message")
    assert got.json() == final  # the tool block hydrated from tool_calls, identical to the stream

    page = await world.http.get(f"/v1/sessions/{session_id}/messages", headers=world.headers)
    validate(page.json(), "MessagePage")
    assert [m["role"] for m in page.json()["items"]] == ["user", "assistant"]
    assert page.json()["items"][1] == final and page.json()["nextBefore"] is None
    tool = final["blocks"][0]["toolCall"]
    assert tool["status"] == "succeeded" and tool["input"] == {"url": "https://example.com"}


async def test_tool_calls_are_rows_and_blocks_only_reference_them(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    world.fake.reply = lambda _: sse_response("tool-error")
    final = events_of(await first_send(world))[-1]["message"]
    saved = await row(sessions, final["id"])
    assert saved.blocks[0] == {
        "id": "b1",
        "type": "tool",
        "toolCallId": final["blocks"][0]["toolCall"]["id"],
    }
    async with sessions() as s:
        call = await s.scalar(select(ToolCall).where(ToolCall.message_id == saved.id))
    assert call is not None and call.status == "failed" and call.name == "fetch_url"
    assert call.output == {
        "value": final["blocks"][0]["toolCall"]["output"],
        "error": "http_error",
    }


async def test_thinking_is_saved_and_never_sent_back(world: World) -> None:
    world.fake.reply = lambda _: sse_response("thinking")
    events = events_of(await first_send(world))
    final = events[-1]["message"]
    assert [b["type"] for b in final["blocks"]] == ["thinking", "text"]
    world.fake.reply = lambda _: sse_response("plain-answer")
    session_id = events[0]["session"]["id"]
    r = await world.http.post(
        f"/v1/sessions/{session_id}/messages", json=body("And then?"), headers=world.headers
    )
    events_of(r)
    history = world.fake.payloads()[1]["messages"]
    assert history[1] == {"role": "assistant", "text": final["blocks"][1]["text"]}


# ---------------------------------------------------------------- send_message


async def test_next_message_sends_history_and_uses_the_next_seq(world: World) -> None:
    world.fake.reply = lambda _: sse_response("tool-call")
    first = events_of(await first_send(world, body("Read example.com")))
    session_id = first[0]["session"]["id"]
    world.fake.reply = lambda _: sse_response("plain-answer")
    r = await world.http.post(
        f"/v1/sessions/{session_id}/messages",
        json=body("Thanks. And Paris?"),
        headers=world.headers,
    )
    started = events_of(r)[0]
    assert "session" not in started  # only when the call created it
    assert (started["userMessage"]["seq"], started["assistantMessage"]["seq"]) == (3, 4)
    history = world.fake.payloads()[1]["messages"]
    assert history[0] == {"role": "user", "text": "Read example.com"}
    assert history[1]["role"] == "assistant"
    assert history[1]["text"].startswith("[tool fetch_url: ")
    assert world.fake.payloads()[1]["input"] == "Thanks. And Paris?"

    page = await world.http.get(
        f"/v1/sessions/{session_id}/messages?limit=3", headers=world.headers
    )
    assert [m["seq"] for m in page.json()["items"]] == [2, 3, 4]
    assert page.json()["nextBefore"] == 2
    older = await world.http.get(
        f"/v1/sessions/{session_id}/messages?before=2", headers=world.headers
    )
    assert [m["seq"] for m in older.json()["items"]] == [1] and older.json()["nextBefore"] is None


# ---------------------------------------------------------------- endings


@pytest.mark.parametrize(
    ("reply", "status", "code"),
    [
        (lambda _: sse_response("invalid-payload"), "failed", "agent_error"),
        (lambda _: sse_response("plain-answer", cut_before='"result"'), "failed", "agent_error"),
        (lambda _: sse_response("cancelled-mid-fetch"), "interrupted", "run_time_limit"),
        (lambda _: httpx.Response(429, headers={"retry-after": "9"}), "failed", "rate_limited"),
        (lambda _: httpx.Response(503, json={"message": "down"}), "failed", "agent_unavailable"),
        (lambda _: httpx.Response(403, json={"message": "denied"}), "failed", "agent_error"),
    ],
    ids=["error-frame", "no-result", "agent-time-limit", "throttled", "unavailable", "denied"],
)
async def test_failed_runs_are_saved_and_streamed(
    world: World,
    sessions: async_sessionmaker[AsyncSession],
    reply: Any,
    status: str,
    code: str,
) -> None:
    world.fake.reply = reply
    r = await first_send(world)
    last = events_of(r)[-1]
    assert last["type"] == "run.failed" and last["error"]["code"] == code
    assert last["error"]["requestId"] == r.headers["x-request-id"]
    if code == "rate_limited":
        assert last["error"]["retryAfter"] == 9
    saved = await row(sessions, last["messageId"])
    assert (saved.status, saved.error and saved.error["code"]) == (status, code)
    if code == "run_time_limit":
        assert last["message"]["blocks"][0]["toolCall"]["status"] == "cancelled"


# ---------------------------------------------------------------- idempotency


async def test_a_resend_replays_instead_of_running_again(world: World) -> None:
    sent = body()
    events = events_of(await first_send(world, sent))
    again = await first_send(world, sent)
    assert again.status_code == 200 and again.headers["content-type"] == "application/json"
    validate(again.json(), "SendReplay")
    assert again.json()["assistantMessage"] == events[-1]["message"]
    assert again.json()["session"]["id"] == events[0]["session"]["id"]
    assert len(world.fake.requests) == 1  # no second run

    session_id = events[0]["session"]["id"]
    in_session = await world.http.post(
        f"/v1/sessions/{session_id}/messages", json=sent, headers=world.headers
    )
    assert in_session.status_code == 200 and in_session.json()["userMessage"]["seq"] == 1


async def test_reusing_an_id_for_different_content_is_a_conflict(world: World) -> None:
    sent = body()
    events = events_of(await first_send(world, sent))
    changed = {**sent, "text": "Something else"}
    r = await first_send(world, changed)
    assert (r.status_code, r.json()["code"]) == (409, "idempotency_conflict")
    other = await world.http.post(
        f"/v1/sessions/{events[0]['session']['id']}/messages",
        json={**sent, "text": "Something else"},
        headers=world.headers,
    )
    assert other.json()["code"] == "idempotency_conflict"


# ---------------------------------------------------------------- refusals (nothing saved)


async def count_messages(sessions: async_sessionmaker[AsyncSession], user_id: uuid.UUID) -> int:
    async with sessions() as s:
        return int(await s.scalar(select(func.count()).where(Message.user_id == user_id)) or 0)


@pytest.mark.parametrize(
    ("payload", "status", "code"),
    [
        (body("   \n "), 422, "empty_message"),
        (body("x" * 32_001), 422, "message_too_long"),
        (body(fileIds=[str(uuid.uuid4())]), 422, "attachments_not_supported"),
        (
            body(answer={"questionRef": {"messageId": str(uuid.uuid4()), "blockId": "b1"}}),
            409,
            "question_not_open",
        ),
        ({"clientMessageId": str(uuid.uuid4()), "text": "hi", "extra": 1}, 422, "invalid_request"),
        ({"client_message_id": str(uuid.uuid4()), "text": "hi"}, 422, "invalid_request"),
        (body(fileIds=[str(uuid.uuid4())] * 2), 422, "invalid_request"),
    ],
)
async def test_refused_bodies(
    world: World,
    sessions: async_sessionmaker[AsyncSession],
    payload: dict[str, Any],
    status: int,
    code: str,
) -> None:
    r = await first_send(world, payload)
    assert (r.status_code, r.json()["code"]) == (status, code)
    assert await count_messages(sessions, world.user_id) == 0


@pytest.mark.parametrize(
    ("change", "status", "code"),
    [
        ({"status": "offline"}, 503, "agent_unavailable"),
        ({"retired_at": datetime(2026, 9, 1, tzinfo=UTC)}, 409, "agent_retired"),
        (
            {"runtime_type": "http", "runtime_arn": None, "runtime_endpoint": "https://a.example"},
            503,
            "agent_unavailable",
        ),
    ],
)
async def test_refused_agents(
    world: World,
    sessions: async_sessionmaker[AsyncSession],
    change: dict[str, Any],
    status: int,
    code: str,
) -> None:
    async with sessions() as s, s.begin():
        await s.execute(update(Agent).where(Agent.slug == world.agent_slug).values(**change))
    r = await first_send(world)
    assert (r.status_code, r.json()["code"]) == (status, code)
    assert await count_messages(sessions, world.user_id) == 0
    assert world.fake.requests == []


async def test_unknown_agent_and_others_sessions_are_not_found(world: World) -> None:
    r = await world.http.post(
        "/v1/agents/no-such-agent/sessions", json=body(), headers=world.headers
    )
    assert (r.status_code, r.json()["code"]) == (404, "agent_not_found")
    session_id = events_of(await first_send(world))[0]["session"]["id"]
    message_id = (
        await world.http.get(f"/v1/sessions/{session_id}/messages", headers=world.headers)
    ).json()["items"][0]["id"]
    stranger = {"Authorization": f"Bearer {issue_access_token(get_settings(), uuid.uuid4())}"}
    for method, path, code in [
        ("POST", f"/v1/sessions/{session_id}/messages", "session_not_found"),
        ("GET", f"/v1/sessions/{session_id}/messages", "session_not_found"),
        ("GET", f"/v1/messages/{message_id}", "message_not_found"),
    ]:
        r = await world.http.request(
            method, path, json=body() if method == "POST" else None, headers=stranger
        )
        assert (r.status_code, r.json()["code"]) == (404, code)


async def test_a_deleted_session_is_not_found(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    started = events_of(await first_send(world))[0]
    async with sessions() as s, s.begin():
        await s.execute(
            update(Session)
            .where(Session.id == uuid.UUID(started["session"]["id"]))
            .values(deleted_at=datetime.now(UTC))
        )
    r = await world.http.get(
        f"/v1/messages/{started['assistantMessage']['id']}", headers=world.headers
    )
    assert r.json()["code"] == "message_not_found"


async def test_one_open_reply_per_session(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    events = events_of(await first_send(world))
    async with sessions() as s, s.begin():  # as if the reply were still being written
        await s.execute(
            update(Message)
            .where(Message.id == uuid.UUID(events[-1]["messageId"]))
            .values(status="streaming")
        )
    r = await world.http.post(
        f"/v1/sessions/{events[0]['session']['id']}/messages", json=body(), headers=world.headers
    )
    assert (r.status_code, r.json()["code"]) == (409, "run_in_progress")


async def test_three_running_replies_per_user(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    ids = [events_of(await first_send(world))[-1]["messageId"] for _ in range(3)]
    async with sessions() as s, s.begin():
        await s.execute(
            update(Message)
            .where(Message.id.in_([uuid.UUID(i) for i in ids]))
            .values(status="streaming")
        )
    r = await first_send(world)
    assert (r.status_code, r.json()["code"], r.headers["retry-after"]) == (
        429,
        "too_many_runs",
        "10",
    )


async def test_no_new_sends_while_shutting_down(world: World) -> None:
    shutting_down.set()
    try:
        r = await first_send(world)
    finally:
        shutting_down.clear()
    assert (r.status_code, r.json()["code"], r.json()["retryable"]) == (503, "shutting_down", True)


# ---------------------------------------------------------------- the run on its own


async def started_run(
    w: World,
    sessions: async_sessionmaker[AsyncSession],
    steps: list[tuple[asyncio.Event | None, bytes]],
    settings: RunSettings | None = None,
) -> tuple[Run, asyncio.Task[None]]:
    """A send through the service, then the run with a gated body (no HTTP response)."""
    w.fake.reply = lambda _: httpx.Response(200, stream=Gate(steps))
    async with sessions() as s:
        result = await ChatService(s, get_settings()).start(
            w.user_id, w.agent_slug, SendMessageRequest.model_validate(body())
        )
    assert isinstance(result, Started)
    run = Run(
        spec=result.spec,
        client=w.fake.client,
        sessions=sessions,
        settings=settings or result.settings,
    )
    run.emit("run.started", {"assistantMessage": result.spec.assistant.model_dump(mode="json")})
    return run, runs.start(run)


def chunks(case: str) -> list[bytes]:
    return [c + b"\n\n" for c in raw(case).split(b"\n\n") if c]


async def test_a_disconnect_doesnt_stop_the_run(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    go = asyncio.Event()
    parts = chunks("plain-answer")
    run, task = await started_run(
        world, sessions, [(None, parts[0]), *((go, p) for p in parts[1:])]
    )
    stream = mirror(run)
    assert b"event: run.started" in await anext(stream)
    await stream.aclose()  # the browser went away
    assert run.listening is False
    go.set()
    await task
    saved = await row(sessions, str(run.spec.message_id))
    assert saved.status == "complete" and saved.blocks  # finished and saved with nobody reading
    polled = await world.http.get(f"/v1/messages/{run.spec.message_id}", headers=world.headers)
    assert polled.json()["status"] == "complete"


async def test_text_is_checkpointed_while_it_streams(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    go = asyncio.Event()
    parts = chunks("plain-answer")
    split = next(i for i, p in enumerate(parts) if b'"text"' in p) + 3
    settings = RunSettings(time_limit_seconds=60, drain_seconds=60, checkpoint_seconds=0.05)
    run, task = await started_run(
        world,
        sessions,
        [*((None, p) for p in parts[:split]), *((go, p) for p in parts[split:])],
        settings,
    )
    for _ in range(100):  # the 2 s checkpoint, shortened
        saved = await row(sessions, str(run.spec.message_id))
        if saved.blocks:
            break
        await asyncio.sleep(0.02)
    assert saved.status == "streaming" and saved.blocks[0]["text"]  # partial text on disk
    assert saved.heartbeat_at is not None and saved.heartbeat_at > saved.started_at  # type: ignore[operator]
    go.set()
    await task


@pytest.mark.parametrize("why", ["time-limit", "shutdown"])
async def test_runs_that_outlive_their_window_are_interrupted(
    world: World, sessions: async_sessionmaker[AsyncSession], why: str
) -> None:
    never = asyncio.Event()
    parts = chunks("tool-call")
    upto = next(i for i, p in enumerate(parts) if b'"role": "user"' in p)  # tool started, no result
    settings = RunSettings(
        time_limit_seconds=0.3 if why == "time-limit" else 60,
        drain_seconds=0.2,
    )
    run, task = await started_run(
        world, sessions, [*((None, p) for p in parts[:upto]), (never, parts[upto])], settings
    )
    if why == "shutdown":
        await asyncio.sleep(0.1)
        shutting_down.set()
    try:
        await asyncio.wait_for(task, timeout=10)
    finally:
        shutting_down.clear()
    saved = await row(sessions, str(run.spec.message_id))
    code = "run_time_limit" if why == "time-limit" else "run_interrupted"
    assert saved.status == "interrupted" and saved.error and saved.error["code"] == code
    async with sessions() as s:
        call = await s.scalar(select(ToolCall).where(ToolCall.message_id == saved.id))
    assert call is not None and call.status == "cancelled" and call.completed_at is not None


async def test_mirror_pings_while_nothing_happens() -> None:
    class Quiet:
        events: asyncio.Queue[bytes | None] = asyncio.Queue()
        listening = True

        def detach(self) -> None:
            self.listening = False

    quiet = Quiet()
    stream = mirror(quiet, keepalive=0.01)  # type: ignore[arg-type]
    assert await anext(stream) == PING
    quiet.events.put_nowait(None)
    with pytest.raises(StopAsyncIteration):
        await anext(stream)
    assert quiet.listening is False


# ---------------------------------------------------------------- the sweep


async def test_sweep_interrupts_replies_whose_task_died(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    events = events_of(await first_send(world))
    dead, alive = uuid.UUID(events[-1]["messageId"]), uuid.uuid4()
    now = datetime.now(UTC)
    async with sessions() as s, s.begin():
        await s.execute(
            update(Message)
            .where(Message.id == dead)
            .values(status="streaming", heartbeat_at=now - timedelta(minutes=5), error=None)
        )
        reply = await s.get(Message, dead)
        assert reply is not None
        await s.execute(
            text(
                "INSERT INTO tool_calls (message_id, session_id, user_id, tool_use_id, name)"
                " VALUES (:m, :s, :u, 't1', 'fetch_url')"
            ),
            {"m": dead, "s": reply.session_id, "u": world.user_id},
        )
        second = events_of(await first_send(world))  # another session, its reply fresh
        alive = uuid.UUID(second[-1]["messageId"])
        await s.execute(
            update(Message).where(Message.id == alive).values(status="streaming", heartbeat_at=now)
        )
    async with sessions() as s, s.begin():
        assert await interrupt_stale_replies(s) >= 1
    async with sessions() as s, s.begin():
        assert await interrupt_stale_replies(s) == 0  # idempotent
    swept = await row(sessions, str(dead))
    assert (
        swept.status == "interrupted" and swept.error and swept.error["code"] == "run_interrupted"
    )
    assert (await row(sessions, str(alive))).status == "streaming"
    async with sessions() as s:
        call = await s.scalar(select(ToolCall).where(ToolCall.message_id == dead))
    assert call is not None and call.status == "cancelled"


# ---------------------------------------------------------------- helpers


@pytest.mark.parametrize(
    ("given", "title"),
    [
        ("  Hello\n\n world  ", "Hello world"),
        ("word " * 30, ("word " * 12).strip()),
        ("x" * 100, "x" * 60),
    ],
)
def test_title_is_the_first_message_trimmed(given: str, title: str) -> None:
    assert title_of(given) == title


# ---------------------------------------------------------------- races and the rest


async def test_open_reply_race_is_run_in_progress_not_500(
    world: World, sessions: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    events = events_of(await first_send(world))
    async with sessions() as s, s.begin():
        await s.execute(
            update(Message)
            .where(Message.id == uuid.UUID(events[-1]["messageId"]))
            .values(status="streaming")
        )

    async def none(self: ChatRepository, session_id: uuid.UUID) -> None:
        return None  # as if the other reply started after this check

    monkeypatch.setattr(ChatRepository, "open_reply", none)
    r = await world.http.post(
        f"/v1/sessions/{events[0]['session']['id']}/messages", json=body(), headers=world.headers
    )
    assert (r.status_code, r.json()["code"]) == (409, "run_in_progress")


async def test_identical_sends_at_once_replay_the_winner(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = body()
    events = events_of(await first_send(world, sent))
    real = ChatRepository.by_client_message_id
    calls = 0

    async def miss_once(
        self: ChatRepository, user_id: uuid.UUID, client_message_id: uuid.UUID
    ) -> Message | None:
        nonlocal calls
        calls += 1
        return None if calls == 1 else await real(self, user_id, client_message_id)

    monkeypatch.setattr(ChatRepository, "by_client_message_id", miss_once)
    r = await first_send(world, sent)  # loses on the unique (user_id, client_message_id)
    assert r.status_code == 200 and r.json()["assistantMessage"]["id"] == events[-1]["messageId"]
    assert calls == 2


async def test_files_for_an_agent_that_takes_them_are_not_ready_yet(
    world: World, sessions: async_sessionmaker[AsyncSession]
) -> None:
    caps = {
        "attachments": {
            "enabled": True,
            "contentTypes": ["text/plain"],
            "maxFileBytes": 1000,
            "maxFiles": 1,
        },
        "artifacts": False,
        "approvals": False,
        "questions": False,
    }
    async with sessions() as s, s.begin():
        await s.execute(
            update(Agent).where(Agent.slug == world.agent_slug).values(capabilities=caps)
        )
    r = await first_send(world, body(fileIds=[str(uuid.uuid4())]))
    assert (r.status_code, r.json()["code"]) == (409, "file_not_ready")
