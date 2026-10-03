"""Agent descriptors for tests. The ARN's account id is the AWS documentation example."""

from typing import Any

from app.features.agents.descriptor import AgentDescriptor

ARN = "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/demo_runtime-AbC123"


def descriptor_data(**changes: Any) -> dict[str, Any]:
    """A minimal valid descriptor as YAML would load it; `key=None` removes a key."""
    d: dict[str, Any] = {
        "slug": "demo",
        "name": "Demo",
        "description": "A demo agent.",
        "icon": "bot",
        "color": "green",
        "runtimeType": "agentcore",
        "runtimeArn": ARN,
        "capabilities": {
            "attachments": {"enabled": False, "contentTypes": [], "maxFileBytes": 0, "maxFiles": 0},
            "artifacts": False,
            "approvals": False,
            "questions": False,
        },
    }
    d.update(changes)
    return {k: v for k, v in d.items() if v is not None}


def descriptor(**changes: Any) -> AgentDescriptor:
    return AgentDescriptor.model_validate(descriptor_data(**changes))
