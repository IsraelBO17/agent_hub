"""The agent descriptor (D6, F02): the repository's descriptors are valid, and mistakes fail at
`hub agents add`, not in the catalog."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.features.agents.descriptor import AgentDescriptor, load_descriptor
from tests.support.agents import descriptor_data as minimal

AGENTS = Path(__file__).resolve().parents[3] / "agents"


@pytest.mark.parametrize("path", sorted(AGENTS.glob("*.yaml")), ids=lambda p: p.name)
def test_repository_descriptors_are_valid(path: Path) -> None:
    descriptor = load_descriptor(path)
    assert path.stem == descriptor.slug


def test_minimal_descriptor_has_defaults() -> None:
    d = AgentDescriptor.model_validate(minimal())
    assert (d.stage, d.visibility, d.sort_order, d.tools, d.starters) == (
        "stable",
        "listed",
        0,
        [],
        [],
    )


@pytest.mark.parametrize(
    ("changes", "where"),
    [
        ({"colour": "blue"}, "colour"),  # unknown key: a typo must not pass silently
        ({"runtime_type": "agentcore"}, "runtime_type"),  # snake_case isn't the descriptor's name
        ({"color": "pink"}, "color"),
        ({"slug": "Research_Analyst"}, "slug"),
        ({"runtimeArn": "arn:aws:lambda:us-east-1:123456789012:function:x"}, "runtimeArn"),
        ({"runtimeArn": None}, ""),  # agentcore needs an ARN
        ({"runtimeType": "http"}, ""),  # http needs an endpoint, and no ARN
        ({"starters": [{"title": "t", "prompt": "p"}] * 7}, "starters"),
    ],
)
def test_invalid_descriptors_are_rejected(changes: dict[str, Any], where: str) -> None:
    with pytest.raises(ValidationError) as exc:
        AgentDescriptor.model_validate(minimal(**changes))
    assert any(".".join(map(str, e["loc"])).startswith(where) for e in exc.value.errors())


def test_approval_tools_need_the_approvals_capability() -> None:
    tool = {"name": "send_email", "description": "Sends it", "requiresApproval": True}
    with pytest.raises(ValidationError, match=r"capabilities\.approvals"):
        AgentDescriptor.model_validate(minimal(tools=[tool]))


def test_attachment_limits_are_capped() -> None:
    caps = minimal()["capabilities"]
    caps["attachments"] = {
        "enabled": True,
        "contentTypes": ["application/zip"],
        "maxFileBytes": 50 * 1024 * 1024,
        "maxFiles": 11,
    }
    with pytest.raises(ValidationError) as exc:
        AgentDescriptor.model_validate(minimal(capabilities=caps))
    assert len(exc.value.errors()) == 3


def test_nested_objects_are_stored_in_their_wire_shape() -> None:
    d = AgentDescriptor.model_validate(
        minimal(
            details={"model": "m"},
            starters=[{"title": "t", "prompt": "p"}],
            tools=[{"name": "x", "description": "y", "requiresApproval": False}],
        )
    )
    assert d.details.model_dump() == {"model": "m"}  # optional properties are left out, not null
    assert d.starters[0].model_dump() == {"title": "t", "prompt": "p"}
    assert d.tools[0].model_dump() == {"name": "x", "description": "y", "requiresApproval": False}
    assert "maxFileBytes" in d.capabilities.model_dump()["attachments"]
