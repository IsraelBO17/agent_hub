"""HTTP endpoints for the catalog. Read only: agents are registered by the operator (`hub`)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.core.auth import CurrentUser
from app.core.db import SessionDep
from app.core.settings import Settings, get_settings
from app.features.agents.descriptor import SLUG
from app.features.agents.schemas import AgentList, AgentOut
from app.features.agents.service import AgentService


def get_service(
    session: SessionDep, settings: Annotated[Settings, Depends(get_settings)]
) -> AgentService:
    return AgentService(session, settings)


Service = Annotated[AgentService, Depends(get_service)]
Slug = Annotated[str, Path(pattern=SLUG)]

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.get("")
async def list_agents(user: CurrentUser, svc: Service) -> AgentList:
    return await svc.list_agents(user.user_id)


@router.get("/{slug}")
async def get_agent(slug: Slug, user: CurrentUser, svc: Service) -> AgentOut:
    return await svc.get_agent(user.user_id, slug)
