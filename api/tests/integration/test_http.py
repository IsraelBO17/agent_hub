"""Cross-cutting HTTP behaviour: health, request ids, errors, headers, limits, auth."""

import httpx

from app.core.settings import get_settings
from tests.conftest import AuthHeaders


async def test_health_needs_no_auth_and_echoes_request_id(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/health", headers={"X-Request-Id": "trace-abc-123"})
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert r.headers["x-request-id"] == "trace-abc-123"


async def test_malformed_request_id_is_replaced(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/health", headers={"X-Request-Id": "bad id with spaces"})
    assert r.headers["x-request-id"].startswith("req_")


async def test_security_headers(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"


async def test_unknown_route_and_method_are_problems(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/nope")
    assert r.status_code == 404 and r.json()["code"] == "not_found"
    assert r.headers["content-type"] == "application/problem+json"
    r = await client.put("/v1/health")
    assert r.status_code == 405 and "GET" in r.headers["allow"]


ECHO = "/v1/_test/echo"  # test-only route from conftest.py
INVALID = get_settings().validation_status  # 400, or 422 if the profile chose it


async def test_missing_or_bad_token_is_401(client: httpx.AsyncClient) -> None:
    r = await client.post(ECHO, json={"text": "x"})
    assert r.status_code == 401 and r.json()["code"] == "token_invalid"
    r = await client.post(ECHO, json={"text": "x"}, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401 and r.json()["code"] == "token_invalid"


async def test_inputs_accept_only_contract_names(
    client: httpx.AsyncClient, auth: AuthHeaders
) -> None:
    r = await client.post(ECHO, json={"text": "x", "extra": 1}, headers=auth(None))
    assert r.status_code == INVALID and r.json()["errors"][0]["path"] == "/extra"
    # The Python name isn't a contract name either.
    r = await client.post(ECHO, json={"text": "x", "max_words": 1}, headers=auth(None))
    assert r.status_code == INVALID
    r = await client.post(ECHO, json={"text": "x", "maxWords": 1}, headers=auth(None))
    assert r.status_code == 200


async def test_unparseable_body_is_a_validation_error(
    client: httpx.AsyncClient, auth: AuthHeaders
) -> None:
    headers = {**auth(None), "Content-Type": "application/json"}
    r = await client.post(ECHO, content=b"{not json", headers=headers)
    assert r.status_code == INVALID and r.json()["code"] == "invalid_request"


async def test_nul_in_a_string_is_rejected_not_500(
    client: httpx.AsyncClient, auth: AuthHeaders
) -> None:
    r = await client.post(ECHO, json={"text": "a\u0000b"}, headers=auth(None))
    assert r.status_code == INVALID and r.json()["code"] == "invalid_request"


async def test_body_over_the_limit_is_413(client: httpx.AsyncClient, auth: AuthHeaders) -> None:
    r = await client.post(ECHO, content=b"x" * 1_000_001, headers=auth(None))
    assert r.status_code == 413 and r.json()["code"] == "payload_too_large"
    assert r.headers["x-request-id"]


async def test_cors_allows_only_listed_origins(client: httpx.AsyncClient) -> None:
    r = await client.get("/v1/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers
