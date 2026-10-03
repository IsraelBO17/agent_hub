"""Errors as RFC 9457 problems (standard §9).

Services raise `ApiError` subclasses; one handler renders every error as `application/problem+json`
with a stable `code`, the request id and `retryable`. Routers never build error bodies.
A shipped `code` is never renamed or removed.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

from app.core.context import request_id_var

log = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"


class _Config:
    errors_base_url = "https://errors.example.com/"
    validation_status = 400


class ApiError(Exception):
    """Base for every error the API returns. One subclass per code, in the feature's exceptions.py."""

    status: int = 500
    code: str = "internal_error"
    title: str = "Something went wrong"
    retryable: bool = False
    is_validation: bool = False  # rendered with the profile's validation status (400 or 422)

    def __init__(
        self, detail: str | None = None, *, retry_after: int | None = None, **extra: Any
    ) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
        self.retry_after = retry_after
        self.extra = extra


class InvalidRequest(ApiError):
    status, code, title, is_validation = 400, "invalid_request", "Invalid request", True


class InvalidCursor(InvalidRequest):
    title = "Invalid cursor"


class Unauthenticated(ApiError):
    status, code, title = 401, "token_invalid", "Missing or invalid access token"


class TokenExpired(Unauthenticated):
    """The access token was valid but has expired: the client refreshes, then repeats the request."""

    code, title, retryable = "token_expired", "Access token expired", True


class Forbidden(ApiError):
    status, code, title = 403, "forbidden", "Not allowed"


class NotFound(ApiError):
    status, code, title = 404, "not_found", "Not found"


class Conflict(ApiError):
    status, code, title = 409, "conflict", "Conflict"


class ShuttingDown(ApiError):
    status, code, title, retryable = 503, "shutting_down", "Restarting, try again shortly", True


def problem(
    status: int,
    code: str,
    title: str,
    *,
    detail: str | None = None,
    retryable: bool = False,
    retry_after: int | None = None,
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": _Config.errors_base_url + code,
        "title": title,
        "status": status,
        "code": code,
        "requestId": request_id_var.get(),
        "retryable": retryable,
    }
    if detail:
        body["detail"] = detail
    out_headers = dict(headers or {})
    if retry_after is not None:
        body["retryAfter"] = retry_after
        out_headers["Retry-After"] = str(retry_after)
    body.update(extra)
    return JSONResponse(body, status_code=status, headers=out_headers, media_type=PROBLEM_JSON)


def problem_body(exc: ApiError, *, request_id: str | None = None) -> dict[str, Any]:
    """The problem object for an error that isn't an HTTP response: one stored on a row or sent in
    a stream event (it keeps the status it would have had). `request_id` defaults to the current
    request's."""
    body: dict[str, Any] = {
        "type": _Config.errors_base_url + exc.code,
        "title": exc.title,
        "status": _Config.validation_status if exc.is_validation else exc.status,
        "code": exc.code,
        "requestId": request_id or request_id_var.get(),
        "retryable": exc.retryable,
    }
    if exc.detail:
        body["detail"] = exc.detail
    if exc.retry_after is not None:
        body["retryAfter"] = exc.retry_after
    body.update(exc.extra)
    return body


def render(exc: ApiError) -> JSONResponse:
    status = _Config.validation_status if exc.is_validation else exc.status
    return problem(
        status,
        exc.code,
        exc.title,
        detail=exc.detail,
        retryable=exc.retryable,
        retry_after=exc.retry_after,
        **exc.extra,
    )


_HTTP_CODES = {
    400: "invalid_request",
    401: "token_invalid",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
}


def _allowed_methods(request: Request) -> str:
    allowed = []
    for method in ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"):
        scope = {**request.scope, "method": method}
        if any(route.matches(scope)[0] == Match.FULL for route in request.app.router.routes):
            allowed.append(method)
    return ", ".join(allowed)


def install_error_handlers(app: FastAPI, *, errors_base_url: str, validation_status: int) -> None:
    _Config.errors_base_url = errors_base_url
    _Config.validation_status = validation_status

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return render(exc)

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"path": "/" + "/".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return problem(validation_status, "invalid_request", "Invalid request", errors=errors)

    @app.exception_handler(StarletteHTTPException)  # also catches router 404 and 405
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = dict(exc.headers or {})
        if exc.status_code == 405:
            # RFC 9110: Allow lists every method the resource supports. Starlette lists only the
            # first route that matched the path, so collect them from all routes.
            headers["Allow"] = _allowed_methods(request)
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        # The framework's own 400 (an unparseable body) is a validation error: same status as one.
        status = _Config.validation_status if exc.status_code == 400 else exc.status_code
        return problem(status, code, str(exc.detail), headers=headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_error", exc_info=exc)
        return problem(500, "internal_error", "Something went wrong")
