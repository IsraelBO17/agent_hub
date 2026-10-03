"""openapi.yaml is valid, lists every error code the code can raise, and matches the app's routes
(standard §8, §9; OWASP API9)."""

from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate

import app.core.errors as core_errors
import app.features
from app.core.errors import ApiError
from app.main import create_app
from tests.contract_routes import documented, implemented

ROOT = Path(__file__).resolve().parents[2]
SPEC: dict[str, Any] = yaml.safe_load((ROOT / "openapi.yaml").read_text())


def _all_error_classes() -> set[type[ApiError]]:
    for path in Path(app.features.__path__[0]).glob("*/exceptions.py"):
        __import__(f"app.features.{path.parent.name}.exceptions")
    seen: set[type[ApiError]] = set()
    todo: list[type[ApiError]] = [ApiError]
    while todo:
        cls = todo.pop()
        if cls.__module__.startswith("app."):  # not classes a test defines
            seen.add(cls)
        todo += cls.__subclasses__()
    return seen


def test_contract_is_valid_openapi() -> None:
    validate(SPEC)


def test_every_error_code_is_in_the_contract() -> None:
    documented = set(SPEC["components"]["schemas"]["ErrorCode"]["enum"])
    raised = {cls.code for cls in _all_error_classes()}
    raised |= set(core_errors._HTTP_CODES.values()) | {"payload_too_large"}
    missing = raised - documented
    assert not missing, f"add these codes to ErrorCode in openapi.yaml: {sorted(missing)}"


def test_routes_match_the_contract() -> None:
    """Everything the app serves is in the contract. Documented operations not built yet are
    pending: listed in the test output, not a failure (the contract is written first)."""
    app_ops, contract_ops = implemented(create_app()), documented()
    assert app_ops - contract_ops == set(), "routes missing from openapi.yaml"
    pending = sorted(contract_ops - app_ops)
    if pending:
        print(f"\n{len(pending)} contract operations not implemented yet: {pending}")
