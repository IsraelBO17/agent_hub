"""HTTP middleware (standard §8, §14, §15, §17). Pure ASGI only: BaseHTTPMiddleware blocks
context-var changes from propagating and gets in the way of streaming responses.

Order in create_app() (the last added is the outermost):
    RequestId -> SecurityHeaders -> CORS -> BodySizeLimit -> app
"""

import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.context import request_id_var
from app.core.errors import problem

log = logging.getLogger("app.access")
_VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestIdMiddleware:
    """Sets the request id (a well-formed inbound X-Request-Id, or a new one), echoes it on the
    response, and writes one access line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        inbound = dict(scope["headers"]).get(b"x-request-id", b"").decode("latin-1")
        rid = inbound if _VALID_ID.match(inbound) else f"req_{uuid.uuid4().hex}"
        token = request_id_var.set(rid)
        started, status = time.perf_counter(), 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message).append("X-Request-Id", rid)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            route = scope.get("route")
            level = (
                logging.ERROR
                if status >= 500
                else logging.WARNING
                if status >= 400
                else logging.INFO
            )
            log.log(
                level,
                "request",
                extra={
                    "method": scope["method"],
                    "route": getattr(route, "path", scope["path"]),
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "no-referrer")
                headers.setdefault("Cache-Control", "no-store")
                if self.hsts:
                    headers.setdefault("Strict-Transport-Security", "max-age=63072000")
            await send(message)

        await self.app(scope, receive, send_wrapper)


class _BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """Rejects bodies over the limit before the app buffers them (OWASP API4): a declared
    Content-Length over the limit is refused at once; a chunked body is counted as it arrives."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(scope, receive, send)
            return
        seen = 0
        started = False

        async def limited_receive() -> Message:
            nonlocal seen
            message = await receive()
            if message["type"] == "http.request":
                seen += len(message.get("body", b""))
                if seen > self.max_bytes:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not started:
                await self._reject(scope, receive, send)

    async def _reject(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = problem(413, "payload_too_large", "Request body too large")
        await response(scope, receive, send)
