"""The Bedrock AgentCore Runtime client: `InvokeAgentRuntime`, streamed (standard §16, recipe 7).

Plain HTTPS through one `httpx.AsyncClient`, signed with SigV4 by botocore (the same signer boto3
uses), so the reply streams without a thread and tests replay the recorded bodies through
`httpx.MockTransport`. Credentials come from botocore's chain: the ECS task role when deployed,
`AWS_PROFILE` locally. Only runtimes in the task role's policy can be called (D27).

The response is SSE of `data: <json>` frames (tests/fixtures/agentcore/README.md). Failures are this
module's own errors, never httpx's or botocore's.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import ReadOnlyCredentials
from botocore.session import get_session

SERVICE = "bedrock-agentcore"
ERROR_BODY_BYTES = 4096


class AgentCoreError(Exception):
    """Base. `aws_code` is AWS's error type when there is one (logged, never shown)."""

    def __init__(self, message: str, *, aws_code: str | None = None) -> None:
        super().__init__(message)
        self.aws_code = aws_code


class AgentCoreUnavailable(AgentCoreError):
    """Unreachable, timed out connecting, a 5xx, or no credentials."""


class AgentCoreThrottled(AgentCoreError):
    def __init__(self, message: str, *, retry_after: int, aws_code: str | None = None) -> None:
        super().__init__(message, aws_code=aws_code)
        self.retry_after = retry_after


class AgentCoreRejected(AgentCoreError):
    """A 4xx other than throttling: access denied, unknown runtime, invalid request."""

    def __init__(self, message: str, *, status: int, aws_code: str | None = None) -> None:
        super().__init__(message, aws_code=aws_code)
        self.status = status


class AgentCoreStreamLost(AgentCoreError):
    """The connection broke after the reply had started."""


class Credentials:
    """botocore's credential chain. Refreshing may make an HTTP call (the container's credential
    endpoint), so it runs in a thread."""

    def __init__(self) -> None:
        self._source = get_session().get_credentials()

    async def frozen(self) -> ReadOnlyCredentials:
        if self._source is None:
            raise AgentCoreUnavailable("no AWS credentials")
        return await asyncio.to_thread(self._source.get_frozen_credentials)


class AgentCoreClient:
    def __init__(self, http: httpx.AsyncClient, *, region: str, credentials: Credentials) -> None:
        self.http = http
        self.region = region
        self.credentials = credentials

    def url(self, runtime_arn: str, qualifier: str) -> str:
        return (
            f"https://{SERVICE}.{self.region}.amazonaws.com/runtimes/"
            f"{quote(runtime_arn, safe='')}/invocations?qualifier={quote(qualifier, safe='')}"
        )

    async def _signed_headers(
        self, url: str, body: bytes, headers: dict[str, str]
    ) -> dict[str, str]:
        request = AWSRequest(method="POST", url=url, data=body, headers=headers)
        SigV4Auth(await self.credentials.frozen(), SERVICE, self.region).add_auth(request)
        return dict(request.headers.items())

    async def invoke(
        self, *, runtime_arn: str, qualifier: str, session_id: str, payload: dict[str, Any]
    ) -> AsyncIterator[Any]:
        """Yields each decoded `data:` frame (a JSON value; a non-JSON line as its string). Ends when
        the body ends. Raises the errors above."""
        url = self.url(runtime_arn, qualifier)
        body = json.dumps(payload, ensure_ascii=False).encode()
        headers = await self._signed_headers(
            url,
            body,
            {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                # AgentCore routes a runtime session to one microVM: Stop reaches the same process.
                "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
            },
        )
        try:
            async with self.http.stream("POST", url, content=body, headers=headers) as response:
                if response.status_code != 200:
                    raise await _http_error(response)
                started = False
                try:
                    async for frame in _frames(response.aiter_lines()):
                        started = True
                        yield frame
                except (httpx.ReadError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
                    if started:
                        raise AgentCoreStreamLost(f"stream broke: {type(exc).__name__}") from exc
                    raise AgentCoreUnavailable(f"no reply: {type(exc).__name__}") from exc
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
            raise AgentCoreUnavailable(f"can't reach AgentCore: {type(exc).__name__}") from exc


async def _frames(lines: AsyncIterator[str]) -> AsyncIterator[Any]:
    """SSE: `data:` lines up to a blank line make one frame; comments and other fields ignored."""
    data: list[str] = []
    async for line in lines:
        if line == "":
            if data:
                yield _decode("\n".join(data))
                data = []
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))
    if data:
        yield _decode("\n".join(data))


def _decode(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        return text


async def _http_error(response: httpx.Response) -> AgentCoreError:
    raw = b""
    async for chunk in response.aiter_bytes():
        raw += chunk
        if len(raw) >= ERROR_BODY_BYTES:
            break
    try:
        body = json.loads(raw)
    except ValueError:
        body = {}
    aws_code = (response.headers.get("x-amzn-errortype") or "").split(":")[0] or (
        body.get("__type") if isinstance(body, dict) else None
    )
    message = (body.get("message") or body.get("Message")) if isinstance(body, dict) else None
    text = f"AgentCore {response.status_code}" + (f": {message}" if message else "")
    status = response.status_code
    if status == 429 or aws_code == "ThrottlingException":
        retry_after = response.headers.get("retry-after", "")
        return AgentCoreThrottled(
            text, retry_after=int(retry_after) if retry_after.isdigit() else 5, aws_code=aws_code
        )
    if status >= 500:
        return AgentCoreUnavailable(text, aws_code=aws_code)
    return AgentCoreRejected(text, status=status, aws_code=aws_code)
