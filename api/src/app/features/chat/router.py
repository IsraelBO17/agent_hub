"""HTTP endpoints for sending and reading messages. Thin: parse, call the service, then either
replay as JSON or start the run and mirror it as SSE (D5)."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import CurrentUser
from app.core.db import SessionDep, get_db
from app.core.settings import Settings, get_settings
from app.features.agents.public import SLUG
from app.features.chat import runs
from app.features.chat.agentcore import AgentCoreClient
from app.features.chat.schemas import (
    MessageOut,
    MessagePage,
    MessagePageQuery,
    SendMessageRequest,
    SendReplay,
)
from app.features.chat.service import ChatService, Started

KEEPALIVE_SECONDS = 15.0  # D5: a `: ping` comment after 15 s without an event
PING = b": ping\n\n"

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_service(session: SessionDep, settings: SettingsDep) -> ChatService:
    return ChatService(session, settings)


def get_agentcore(request: Request) -> AgentCoreClient:
    """Created in the lifespan; tests replace it with one on httpx.MockTransport."""
    client: AgentCoreClient = request.app.state.agentcore
    return client


def get_run_sessions() -> async_sessionmaker[AsyncSession]:
    """Runs outlive the request, so they write through their own sessions."""
    return get_db().sessions


Service = Annotated[ChatService, Depends(get_service)]
AgentCore = Annotated[AgentCoreClient, Depends(get_agentcore)]
RunSessions = Annotated[async_sessionmaker[AsyncSession], Depends(get_run_sessions)]

router = APIRouter(prefix="/v1", tags=["chat"])


async def mirror(run: runs.Run, keepalive: float = KEEPALIVE_SECONDS) -> AsyncGenerator[bytes]:
    """The run's events while the client is connected. Leaving (a closed tab, a dropped network)
    only detaches: the run carries on and saves (D11)."""
    try:
        while True:
            try:
                chunk = await asyncio.wait_for(run.events.get(), timeout=keepalive)
            except TimeoutError:
                yield PING
                continue
            if chunk is None:
                return
            yield chunk
    finally:
        run.detach()


def respond(
    result: Started | SendReplay, client: AgentCoreClient, sessions: RunSessions
) -> Response:
    if isinstance(result, SendReplay):  # a resend: no new run (Idempotency, rule 4)
        return JSONResponse(result.model_dump(mode="json"))
    run = runs.Run(spec=result.spec, client=client, sessions=sessions, settings=result.settings)
    started: dict[str, object] = {
        "userMessage": result.user_message.model_dump(mode="json"),
        "assistantMessage": result.spec.assistant.model_dump(mode="json"),
    }
    if result.session is not None:
        started["session"] = result.session.model_dump(mode="json")
    run.emit("run.started", started)
    runs.start(run)
    return EventSourceResponse(
        mirror(run), headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.post("/agents/{slug}/sessions")
async def create_session_and_send(
    slug: Annotated[str, Path(pattern=SLUG)],
    body: SendMessageRequest,
    user: CurrentUser,
    svc: Service,
    client: AgentCore,
    sessions: RunSessions,
) -> Response:
    return respond(await svc.start(user.user_id, slug, body), client, sessions)


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    user: CurrentUser,
    svc: Service,
    client: AgentCore,
    sessions: RunSessions,
) -> Response:
    return respond(await svc.send(user.user_id, session_id, body), client, sessions)


@router.get("/sessions/{session_id}/messages")
async def list_messages(
    session_id: uuid.UUID,
    params: Annotated[MessagePageQuery, Query()],
    user: CurrentUser,
    svc: Service,
) -> MessagePage:
    return await svc.list_messages(
        user.user_id, session_id, before=params.before, limit=params.limit
    )


@router.get("/messages/{message_id}")
async def get_message(message_id: uuid.UUID, user: CurrentUser, svc: Service) -> MessageOut:
    return await svc.get_message(user.user_id, message_id)
