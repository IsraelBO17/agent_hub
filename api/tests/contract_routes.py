"""Which contract operations the app implements. Shared by the contract tests (standard §18).

A contract can be ahead of the code: it is written first, then built in stages. Every implemented
operation must be in the contract; documented operations not built yet are pending, reported but
not failures. Schemathesis runs against the implemented ones only.
"""

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
SPEC: dict[str, Any] = yaml.safe_load((ROOT / "openapi.yaml").read_text())
# The first server's path is the prefix of every operation ("/v1" for `url: /v1`; "" for a full
# URL such as https://api.example.com whose paths already start with /v1).
BASE = urlparse(SPEC["servers"][0]["url"]).path.rstrip("/")
METHODS = {"get", "put", "post", "patch", "delete"}

Operation = tuple[str, str]  # ("GET", "/v1/notes/{noteId}")


def documented() -> set[Operation]:
    return {
        (method.upper(), BASE + path)
        for path, ops in SPEC["paths"].items()
        for method in ops
        if method in METHODS
    }


def implemented(app: FastAPI) -> set[Operation]:
    """From FastAPI's own schema (built even though it isn't served), path parameters in camelCase."""
    generated: dict[str, Any] = app.openapi()
    return {
        (method.upper(), re.sub(r"\{(\w+?)\}", lambda m: "{" + _camel(m.group(1)) + "}", path))
        for path, ops in generated["paths"].items()
        for method in ops
        if method in METHODS
    }


def labels(operations: set[Operation]) -> list[str]:
    """Schemathesis operation labels ("GET /notes/{noteId}"), relative to the server path."""
    return sorted(f"{method} {path.removeprefix(BASE)}" for method, path in operations)


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(w.title() for w in rest)
