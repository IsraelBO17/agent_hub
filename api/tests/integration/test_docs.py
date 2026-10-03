"""Local Swagger UI (make docs): off by default; when on, it serves the contract pointed at itself."""

import httpx
import pytest
import yaml
from asgi_lifespan import LifespanManager

from app.core.settings import get_settings
from app.main import create_app


async def test_docs_are_off_by_default(client: httpx.AsyncClient) -> None:
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/openapi.yaml")).status_code == 404


async def test_docs_serve_the_contract_pointed_at_this_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "docs_enabled", True)
    app = create_app()
    async with LifespanManager(app) as manager:
        transport = httpx.ASGITransport(app=manager.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://localhost:8000") as c:
            page = await c.get("/docs")
            assert page.status_code == 200 and "swagger-ui" in page.text
            spec = yaml.safe_load((await c.get("/openapi.yaml")).text)
    assert spec["servers"] == [{"url": "http://localhost:8000", "description": "This API"}]
    assert "/v1/auth/google" in spec["paths"]
