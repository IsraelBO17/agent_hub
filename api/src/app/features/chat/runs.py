"""A reply's run: the agent call, translated, saved as it goes, mirrored to whoever is listening.

The run is its own asyncio task, not the request's (D11, SEND_MESSAGE rule 5): the SSE response
reads `events` while it is connected, and a disconnect only stops the reading. Its durable record
is its `messages` row (standard §13): blocks saved when a block completes and at least every 2 s
while text streams, `heartbeat_at` on every save and a 15 s tick (P1). Ending rules: SPEC.md,
feature chat.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.errors import ApiError, problem_body
from app.core.lifecycle import shutting_down
from app.core.service import BaseService
from app.features.chat.agentcore import (
    AgentCoreClient,
    AgentCoreRejected,
    AgentCoreStreamLost,
    AgentCoreThrottled,
    AgentCoreUnavailable,
)
from app.features.chat.exceptions import (
    AgentFailed,
    AgentUnavailable,
    InternalRunError,
    RateLimited,
    RunInterrupted,
    RunTimeLimit,
)
from app.features.chat.models import ToolCall
from app.features.chat.repository import ChatRepository
from app.features.chat.schemas import MessageOut
from app.features.chat.translator import (
    BlockCompleted,
    BlockDelta,
    BlockStarted,
    Output,
    RunError,
    RunResult,
    Translator,
)

log = logging.getLogger("app.chat.run")

_END = object()  # the agent's body ended
_TICK = object()  # a second passed with no frame


@dataclass(frozen=True)
class RunSettings:
    time_limit_seconds: float  # the run cap (D11), per agent
    drain_seconds: float  # after SIGTERM, how long a run may continue (P2)
    checkpoint_seconds: float = 2.0
    heartbeat_seconds: float = 15.0


@dataclass(frozen=True)
class RunSpec:
    """Everything the run needs, fixed when the send commits."""

    message_id: uuid.UUID
    session_id: uuid.UUID
    user_id: uuid.UUID
    request_id: str
    runtime_arn: str
    qualifier: str
    payload: dict[str, Any]
    assistant: MessageOut  # the row as inserted; the run updates a copy


def stored_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Blocks as saved: a tool block keeps only a reference to its `tool_calls` row (P6)."""
    return [
        {"id": b["id"], "type": "tool", "toolCallId": b["toolCall"]["id"]}
        if b["type"] == "tool"
        else b
        for b in blocks
    ]


def _when(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def tool_row_values(call: dict[str, Any]) -> dict[str, Any]:
    """A wire ToolCall as `tool_calls` columns. JSONB holds any value, so input and output are
    wrapped; the error text is stored inside `output` (contract: ToolCall.error)."""
    done = call["status"] != "running"
    return {
        "status": call["status"],
        "summary": call["summary"],
        "input": {"value": call["input"]},
        "output": {"value": call["output"], "error": call["error"]} if done else None,
        "completed_at": _when(call["completedAt"]),
    }


def sse(event_type: str, message_id: uuid.UUID, n: int, data: dict[str, Any]) -> bytes:
    payload = {"type": event_type, "messageId": str(message_id), "n": n, **data}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
    return f"id: {message_id}:{n}\nevent: {event_type}\ndata: {body}\n\n".encode()


class RunStore(BaseService):
    """The run's writes, each its own small transaction."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.repo = ChatRepository(session)

    async def save(
        self,
        spec: RunSpec,
        blocks: list[dict[str, Any]],
        tools: list[tuple[str, dict[str, Any]]],
        final: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now(UTC)
        async with self.transaction():
            for action, call in tools:
                if action == "insert":
                    await self.repo.add(
                        ToolCall(
                            id=uuid.UUID(call["id"]),
                            message_id=spec.message_id,
                            session_id=spec.session_id,
                            user_id=spec.user_id,
                            tool_use_id=call["toolUseId"],
                            name=call["name"],
                            started_at=_when(call["startedAt"]),
                            **tool_row_values(call),
                        )
                    )
                else:
                    await self.repo.update_tool_call(uuid.UUID(call["id"]), **tool_row_values(call))
            values: dict[str, Any] = {"blocks": stored_blocks(blocks), "heartbeat_at": now}
            if final is not None:
                values.update(final)
                await self.repo.touch_session(spec.session_id, now)
            await self.repo.update_message(spec.message_id, **values)

    async def beat(self, spec: RunSpec) -> None:
        async with self.transaction():
            await self.repo.update_message(spec.message_id, heartbeat_at=datetime.now(UTC))


@dataclass
class Run:
    spec: RunSpec
    client: AgentCoreClient
    sessions: async_sessionmaker[AsyncSession]
    settings: RunSettings
    events: asyncio.Queue[bytes | None] = field(default_factory=asyncio.Queue)
    listening: bool = True
    n: int = 0
    message: MessageOut | None = None  # the final state, once ended

    def emit(self, event_type: str, data: dict[str, Any]) -> None:
        self.n += 1
        if self.listening:
            self.events.put_nowait(sse(event_type, self.spec.message_id, self.n, data))

    def detach(self) -> None:
        """The client went away: keep running and saving, stop queueing events (D11)."""
        self.listening = False

    async def _save(
        self,
        blocks: list[dict[str, Any]],
        tools: list[tuple[str, dict[str, Any]]],
        final: dict[str, Any] | None = None,
    ) -> None:
        async with self.sessions() as session:
            await RunStore(session).save(self.spec, blocks, tools, final)

    async def _beat(self) -> None:
        async with self.sessions() as session:
            await RunStore(session).beat(self.spec)

    async def _read(self, frames: asyncio.Queue[Any]) -> None:
        try:
            async for frame in self.client.invoke(
                runtime_arn=self.spec.runtime_arn,
                qualifier=self.spec.qualifier,
                session_id=str(self.spec.session_id),
                payload=self.spec.payload,
            ):
                await frames.put(frame)
            await frames.put(_END)
        except Exception as exc:  # handed to the run loop, which decides the ending
            await frames.put(exc)

    async def main(self) -> None:
        translator = Translator()
        tools: list[tuple[str, dict[str, Any]]] = []
        frames: asyncio.Queue[Any] = asyncio.Queue()
        reader = asyncio.create_task(self._read(frames))
        start = time.monotonic()
        last_save = last_beat = start
        drain_deadline: float | None = None
        dirty = False
        ending: tuple[str, ApiError | None, dict[str, int] | None] | None = None

        def handle(outputs: list[Output]) -> bool:
            """Forward block outputs as events; True when a block completed (save now)."""
            nonlocal dirty
            completed = False
            for out in outputs:
                if isinstance(out, BlockStarted):
                    self.emit("block.started", {"index": out.index, "block": out.block})
                    if out.block["type"] == "tool":
                        tools.append(("insert", out.block["toolCall"]))
                elif isinstance(out, BlockDelta):
                    self.emit("block.delta", {"blockId": out.block_id, "text": out.text})
                elif isinstance(out, BlockCompleted):
                    self.emit("block.completed", {"block": out.block})
                    if out.block["type"] == "tool":
                        tools.append(("update", out.block["toolCall"]))
                    completed = True
                dirty = True
            return completed

        try:
            while ending is None:
                now = time.monotonic()
                if shutting_down.is_set() and drain_deadline is None:
                    drain_deadline = now + self.settings.drain_seconds
                if now - start >= self.settings.time_limit_seconds:
                    ending = ("interrupted", RunTimeLimit(), None)
                    break
                if drain_deadline is not None and now >= drain_deadline:
                    ending = (
                        "interrupted",
                        RunInterrupted("The service restarted while the reply was being written."),
                        None,
                    )
                    break
                try:
                    item = await asyncio.wait_for(frames.get(), timeout=1.0)
                except TimeoutError:
                    item = _TICK
                save_now = False
                if item is _END:
                    ending = _ending_of(translator.ended)
                elif isinstance(item, Exception):
                    ending = _ending_of_error(item)
                elif item is not _TICK:
                    save_now = handle(translator.feed(item, datetime.now(UTC)))
                    if translator.ended is not None:
                        ending = _ending_of(translator.ended)
                if ending is not None:
                    break
                now = time.monotonic()
                if save_now or (dirty and now - last_save >= self.settings.checkpoint_seconds):
                    blocks, pending = list(translator.blocks), tools[:]
                    tools.clear()
                    await self._save(blocks, pending)
                    last_save = last_beat = time.monotonic()
                    dirty = False
                elif now - last_beat >= self.settings.heartbeat_seconds:
                    await self._beat()
                    last_beat = time.monotonic()
        except Exception:
            log.exception("run_failed", extra={"message_id": str(self.spec.message_id)})
            ending = ("failed", InternalRunError(), None)
        finally:
            reader.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await reader
        await self._finish(
            translator, tools, ending or ("failed", InternalRunError(), None), handle
        )

    async def _finish(
        self,
        translator: Translator,
        tools: list[tuple[str, dict[str, Any]]],
        ending: tuple[str, ApiError | None, dict[str, int] | None],
        handle: Callable[[list[Output]], bool],
    ) -> None:
        status, error, usage = ending
        handle(translator.close(datetime.now(UTC)))
        problem = problem_body(error, request_id=self.spec.request_id) if error else None
        completed_at = datetime.now(UTC)
        final = {
            "status": status,
            "error": problem,
            "usage": usage,
            "completed_at": completed_at,
            "search_text": translator.search_text() or None,
        }
        try:
            await self._save(translator.blocks, tools, final)
        except Exception:  # the sweep marks it interrupted once the heartbeat goes stale
            log.exception("run_final_save_failed", extra={"message_id": str(self.spec.message_id)})
        self.message = self.spec.assistant.model_copy(
            update={
                "status": status,
                "blocks": translator.blocks,
                "error": problem,
                "usage": usage,
                "completed_at": completed_at,
            }
        )
        log.info(
            "run_ended",
            extra={
                "message_id": str(self.spec.message_id),
                "status": status,
                "code": problem["code"] if problem else None,
                "blocks": len(translator.blocks),
            },
        )
        wire = self.message.model_dump(mode="json")
        if status == "complete":
            self.emit("run.completed", {"message": wire})
        else:
            self.emit("run.failed", {"error": problem, "message": wire})
        if self.listening:
            self.events.put_nowait(None)


def _usage(result: RunResult) -> dict[str, int]:
    return {k: result.usage[k] for k in ("inputTokens", "outputTokens") if k in result.usage}


def _ending_of(
    ended: RunResult | RunError | None,
) -> tuple[str, ApiError | None, dict[str, int] | None]:
    if isinstance(ended, RunResult):
        if ended.stop_reason == "cancelled":  # the agent's own time limit; Stop (#9) is ours
            detail = "The agent's own time limit ended the reply."
            return ("interrupted", RunTimeLimit(detail), _usage(ended))
        return ("complete", None, _usage(ended))
    if isinstance(ended, RunError):
        log.warning(
            "agent_error_frame", extra={"error_type": ended.error_type, "detail": ended.message}
        )
        return ("failed", AgentFailed(), None)
    return ("failed", AgentFailed("The agent's reply ended without a result."), None)


def _ending_of_error(exc: Exception) -> tuple[str, ApiError | None, dict[str, int] | None]:
    if isinstance(exc, AgentCoreThrottled):
        return ("failed", RateLimited(retry_after=exc.retry_after), None)
    if isinstance(exc, AgentCoreUnavailable):
        log.warning("agentcore_unavailable", extra={"detail": str(exc), "aws_code": exc.aws_code})
        return ("failed", AgentUnavailable("The agent couldn't be reached."), None)
    if isinstance(exc, AgentCoreStreamLost):
        return ("failed", AgentFailed("The connection to the agent was lost."), None)
    if isinstance(exc, AgentCoreRejected):
        log.error("agentcore_rejected", extra={"detail": str(exc), "aws_code": exc.aws_code})
        return ("failed", AgentFailed(), None)
    log.error("agent_call_failed", exc_info=exc)
    return ("failed", InternalRunError(), None)


# ---------------------------------------------------------------------- the running set

_running: set[asyncio.Task[None]] = set()


def start(run: Run) -> asyncio.Task[None]:
    """Run it as its own task, kept referenced until it ends."""
    task = asyncio.create_task(run.main(), name=f"run:{run.spec.message_id}")
    _running.add(task)
    task.add_done_callback(_running.discard)
    return task


async def wait_for_runs(grace_seconds: float) -> None:
    """Lifespan shutdown: runs end themselves within their drain window (P2); this waits for them
    to save. Anything left after `grace_seconds` is cancelled, and the sweep finds it by its heartbeat."""
    if not _running:
        return
    _done, pending = await asyncio.wait(set(_running), timeout=grace_seconds)
    for task in pending:
        task.cancel()
    if pending:
        log.warning("runs_cancelled_at_shutdown", extra={"count": len(pending)})
