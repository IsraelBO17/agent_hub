"""The recorded AgentCore streams in tests/fixtures/agentcore/ (README.md there), for replaying."""

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.features.chat.agentcore import AgentCoreClient

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "agentcore"
T0 = datetime(2026, 9, 30, 11, 0, tzinfo=UTC)
CASES = [
    "plain-answer",
    "thinking",
    "tool-call",
    "tool-error",
    "invalid-payload",
    "cancelled-mid-fetch",
]


def raw(case: str) -> bytes:
    """The response body exactly as AgentCore sent it."""
    return (FIXTURES / f"{case}.sse").read_bytes()


def frames(case: str) -> list[tuple[datetime, Any]]:
    """Each `data:` frame, decoded, with the moment it arrived (from the recording's timing)."""
    timing = json.loads((FIXTURES / f"{case}.json").read_text())["timing"]["frames"]
    data = [
        json.loads(chunk.removeprefix("data: "))
        for chunk in raw(case).decode().split("\n\n")
        if chunk.startswith("data: ")
    ]
    assert len(data) == len(timing), case
    return [
        (T0 + timedelta(seconds=t["at_s"]), frame) for t, frame in zip(timing, data, strict=True)
    ]


def request(case: str) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads((FIXTURES / f"{case}.json").read_text())["request"]
    return payload


class FakeCredentials:
    """Stands in for botocore's chain: fixed, obviously fake keys."""

    async def frozen(self) -> Any:
        from botocore.credentials import ReadOnlyCredentials

        return ReadOnlyCredentials("AKIDEXAMPLE", "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", None)


class Gate(httpx.AsyncByteStream):
    """A response body sent in steps: each chunk waits for its event, so a test can look at the
    database between frames (checkpoints) or hold the stream open (time limits, disconnects)."""

    def __init__(self, steps: list[tuple[asyncio.Event | None, bytes]]) -> None:
        self.steps = steps

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for gate, chunk in self.steps:
            if gate is not None:
                await gate.wait()
            yield chunk


class FakeAgentCore:
    """An AgentCoreClient on httpx.MockTransport. `reply` decides each response (default: the
    recorded plain answer); `requests` keeps what was sent."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.reply: Callable[[httpx.Request], httpx.Response] = lambda _: sse_response(
            "plain-answer"
        )
        http = httpx.AsyncClient(transport=httpx.MockTransport(self._handle))
        self.client = AgentCoreClient(http, region="us-east-1", credentials=FakeCredentials())  # type: ignore[arg-type]

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.reply(request)

    def payloads(self) -> list[dict[str, Any]]:
        return [json.loads(r.content) for r in self.requests]


def sse_response(case: str, *, cut_before: str | None = None) -> httpx.Response:
    """A recorded body; `cut_before` drops everything from the first frame containing it."""
    body = raw(case)
    if cut_before is not None:
        body = body[: body.index(cut_before.encode())].rsplit(b"\n\n", 1)[0] + b"\n\n"
    return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})
