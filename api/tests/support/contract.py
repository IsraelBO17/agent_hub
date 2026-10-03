"""Validate a value against a schema in openapi.yaml (OpenAPI 3.1 schemas are JSON Schema 2020-12).

For what Schemathesis can't check: stream events, stored blocks, and responses it never reaches."""

from functools import cache
from typing import Any

from jsonschema import Draft202012Validator

from tests.contract_routes import SPEC


@cache
def _validator(name: str) -> Draft202012Validator:
    schema = {"$ref": f"#/components/schemas/{name}", "components": SPEC["components"]}
    return Draft202012Validator(schema)


def validate(instance: Any, schema: str) -> None:
    errors = sorted(_validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        raise AssertionError(
            f"not a valid {schema}:\n"
            + "\n".join(f"  {list(e.path)}: {e.message}" for e in errors[:10])
        )
