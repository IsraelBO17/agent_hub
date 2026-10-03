"""Swagger UI over the hand-written contract, for local testing only (`make docs`).

Served only when DOCS_ENABLED is true, which settings refuse in prod; the profile keeps it off on
deployed environments. The contract is served with its `servers` replaced by the URL it was fetched
from, so "Try it out" calls this API, not a deployed one.
"""

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, Response


def install_docs(app: FastAPI, contract: Path, title: str) -> None:
    base: dict[str, Any] = yaml.safe_load(contract.read_text())  # once, at startup

    @app.get("/openapi.yaml", include_in_schema=False)
    async def served_contract(request: Request) -> Response:
        spec = dict(base)
        spec["servers"] = [{"url": str(request.base_url).rstrip("/"), "description": "This API"}]
        return Response(yaml.safe_dump(spec, sort_keys=False), media_type="application/yaml")

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/openapi.yaml",
            title=f"{title}: contract",
            swagger_ui_parameters={"persistAuthorization": True, "tryItOutEnabled": True},
        )
