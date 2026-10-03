"""The AgentCore client over httpx.MockTransport: signing, the URL, frames, and each failure."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.features.chat.agentcore import (
    AgentCoreClient,
    AgentCoreRejected,
    AgentCoreStreamLost,
    AgentCoreThrottled,
    AgentCoreUnavailable,
    Credentials,
)
from tests.support.agentcore import FakeCredentials, frames, raw
from tests.support.agents import ARN

SESSION = "dc167109-812c-4dff-b6ac-babc7128aab9"


def client(handler: Callable[[httpx.Request], httpx.Response]) -> AgentCoreClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    creds: Credentials = FakeCredentials()  # type: ignore[assignment]
    return AgentCoreClient(http, region="us-east-1", credentials=creds)


async def collect(c: AgentCoreClient, payload: dict[str, Any] | None = None) -> list[Any]:
    return [
        f
        async for f in c.invoke(
            runtime_arn=ARN, qualifier="DEFAULT", session_id=SESSION, payload=payload or {}
        )
    ]


async def test_replays_a_recorded_stream_with_a_signed_request() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, content=raw("tool-call"), headers={"content-type": "text/event-stream"}
        )

    got = await collect(client(handler), {"input": "hi"})
    assert got == [f for _, f in frames("tool-call")]
    request = seen[0]
    assert request.url.host == "bedrock-agentcore.us-east-1.amazonaws.com"
    assert request.url.raw_path.decode().startswith(
        "/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A123456789012%3Aruntime%2F"
    )
    assert request.url.params["qualifier"] == "DEFAULT"
    assert request.headers["x-amzn-bedrock-agentcore-runtime-session-id"] == SESSION
    auth = request.headers["authorization"]
    assert auth.startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")
    assert "/us-east-1/bedrock-agentcore/aws4_request" in auth
    assert "x-amzn-bedrock-agentcore-runtime-session-id" in auth  # the session header is signed
    assert json.loads(request.content) == {"input": "hi"}


async def test_comments_multiline_data_and_non_json_frames() -> None:
    body = b': ping\n\ndata: {"a": 1}\n\ndata: {"b":\ndata: 2}\n\ndata: not json\n\ndata: {"c": 3}'
    got = await collect(client(lambda _: httpx.Response(200, content=body)))
    assert got == [{"a": 1}, {"b": 2}, "not json", {"c": 3}]


@pytest.mark.parametrize(
    ("status", "headers", "body", "error"),
    [
        (429, {"retry-after": "7"}, {"message": "slow down"}, AgentCoreThrottled),
        (400, {"x-amzn-errortype": "ThrottlingException:http://x"}, {}, AgentCoreThrottled),
        (503, {}, {"message": "unavailable"}, AgentCoreUnavailable),
        (403, {"x-amzn-errortype": "AccessDeniedException"}, {"message": "no"}, AgentCoreRejected),
        (404, {}, {"__type": "ResourceNotFoundException"}, AgentCoreRejected),
    ],
)
async def test_http_errors_map_to_typed_errors(
    status: int, headers: dict[str, str], body: dict[str, str], error: type[Exception]
) -> None:
    c = client(lambda _: httpx.Response(status, json=body, headers=headers))
    with pytest.raises(error) as exc:
        await collect(c)
    if isinstance(exc.value, AgentCoreThrottled):
        assert exc.value.retry_after == (7 if status == 429 else 5)
    if isinstance(exc.value, AgentCoreRejected):
        assert exc.value.aws_code in ("AccessDeniedException", "ResourceNotFoundException")


async def test_unreachable_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(AgentCoreUnavailable):
        await collect(client(handler))


async def test_a_break_after_the_first_frame_is_a_lost_stream() -> None:
    class Broken(httpx.AsyncByteStream):
        async def __aiter__(self):  # type: ignore[no-untyped-def]
            yield b'data: {"init_event_loop": true}\n\n'
            raise httpx.ReadError("reset")

    c = client(lambda _: httpx.Response(200, stream=Broken()))
    got: list[Any] = []
    with pytest.raises(AgentCoreStreamLost):
        async for f in c.invoke(
            runtime_arn=ARN, qualifier="DEFAULT", session_id=SESSION, payload={}
        ):
            got.append(f)
    assert got == [{"init_event_loop": True}]
