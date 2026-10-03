"""Typed errors for agents. Each code is in openapi.yaml's ErrorCode enum."""

from app.core.errors import NotFound


class AgentNotFound(NotFound):
    code, title = "agent_not_found", "There's no agent with this slug"
