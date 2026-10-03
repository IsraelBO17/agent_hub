"""AgentCore (Strands) frames → the app's message blocks and stream events (D10).

Written against the recorded output in tests/fixtures/agentcore/ (README.md there describes every
frame). Pure: no I/O, the clock is passed in. The run (runs.py) feeds it frames, forwards what it
returns as events, and saves `blocks`.

Blocks are kept in their wire shape (camelCase dicts, as openapi.yaml's Block), so an event's block
is exactly what a reload returns. A tool block carries its whole `toolCall`; the run stores that in
`tool_calls` and keeps only a reference in `messages.blocks` (P6).
"""

import copy
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

MAX_TOOL_JSON_BYTES = 16 * 1024  # tool input and output are truncated to 16 KB (contract)
SUMMARY_CHARS = 120


def iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class BlockStarted:
    index: int
    block: dict[str, Any]


@dataclass(frozen=True)
class BlockDelta:
    block_id: str
    text: str


@dataclass(frozen=True)
class BlockCompleted:
    block: dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    """The agent's last frame of a finished run."""

    stop_reason: str
    usage: dict[str, int]


@dataclass(frozen=True)
class RunError:
    """The agent's `error` frame: the run failed inside the agent."""

    error_type: str | None
    message: str | None


Output = BlockStarted | BlockDelta | BlockCompleted | RunResult | RunError


@dataclass
class _Call:
    """One model call (messageStart … message): its content-block indexes and timing."""

    started_at: datetime | None
    open_blocks: dict[int, dict[str, Any]] = field(default_factory=dict)  # text and thinking
    pending_tools: dict[int, dict[str, Any]] = field(default_factory=dict)  # input still streaming
    has_blocks: bool = False


class Translator:
    def __init__(self) -> None:
        self.blocks: list[dict[str, Any]] = []
        self.ended: RunResult | RunError | None = None
        self._call = _Call(started_at=None)
        self._tools: dict[str, dict[str, Any]] = {}  # toolUseId → its block
        self._force_stop_reason: str | None = None

    # ------------------------------------------------------------------ feeding

    def feed(self, frame: Any, now: datetime) -> list[Output]:
        """One decoded `data:` frame. Unknown frames are ignored (agents may add more)."""
        if not isinstance(frame, dict) or self.ended is not None:
            return []
        if "start_event_loop" in frame or "start" in frame:
            if self._call.started_at is None or self._call.has_blocks:
                self._call = _Call(started_at=now)
            return []
        if "event" in frame and isinstance(frame["event"], dict):
            return self._event(frame["event"], now)
        if "message" in frame and isinstance(frame["message"], dict):
            return self._message(frame["message"], now)
        if "result" in frame and isinstance(frame["result"], dict):
            result = frame["result"]
            raw_usage = result.get("usage")
            usage: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
            self.ended = RunResult(
                stop_reason=str(result.get("stopReason") or "end_turn"),
                usage={k: v for k, v in usage.items() if isinstance(v, int)},
            )
            return [self.ended]
        if "error" in frame:
            message = frame.get("error")
            self.ended = RunError(
                error_type=_str_or_none(frame.get("error_type")),
                message=_str_or_none(message) or self._force_stop_reason,
            )
            return [self.ended]
        if frame.get("force_stop"):
            self._force_stop_reason = _str_or_none(frame.get("force_stop_reason"))
        return []

    def _event(self, event: dict[str, Any], now: datetime) -> list[Output]:
        if "messageStart" in event:
            started = self._call.started_at if not self._call.has_blocks else None
            self._call = _Call(started_at=started or now)
            return []
        if "contentBlockStart" in event:
            start = event["contentBlockStart"]
            tool = (start.get("start") or {}).get("toolUse")
            if isinstance(tool, dict) and tool.get("toolUseId"):
                index = int(start.get("contentBlockIndex", 0))
                self._call.pending_tools[index] = {
                    "toolUseId": str(tool["toolUseId"]),
                    "name": str(tool.get("name") or "tool"),
                    "input": "",
                }
            return []
        if "contentBlockDelta" in event:
            body = event["contentBlockDelta"]
            index = int(body.get("contentBlockIndex", 0))
            delta = body.get("delta") or {}
            if isinstance(delta.get("text"), str):
                return self._append(index, "text", delta["text"], now)
            reasoning = delta.get("reasoningContent")
            if isinstance(reasoning, dict) and isinstance(reasoning.get("text"), str):
                return self._append(index, "thinking", reasoning["text"], now)
            tool_input = delta.get("toolUse")
            if isinstance(tool_input, dict) and index in self._call.pending_tools:
                self._call.pending_tools[index]["input"] += str(tool_input.get("input") or "")
            return []  # signatures, redacted reasoning, citations: not shown
        if "contentBlockStop" in event:
            index = int(event["contentBlockStop"].get("contentBlockIndex", 0))
            if index in self._call.open_blocks:
                return [self._complete(self._call.open_blocks.pop(index), now)]
            if index in self._call.pending_tools:
                pending = self._call.pending_tools.pop(index)
                return self._start_tool(
                    pending["toolUseId"], pending["name"], _parse_json(pending["input"]), now
                )
        return []  # messageStop, metadata: usage arrives totalled in `result`

    def _message(self, message: dict[str, Any], now: datetime) -> list[Output]:
        raw_content = message.get("content")
        content: list[Any] = raw_content if isinstance(raw_content, list) else []
        out: list[Output] = []
        if message.get("role") == "assistant":
            # The finished model call. Anything it holds that wasn't streamed is added now: a tool
            # call without a contentBlockStart, or text from an agent that doesn't stream.
            streamed = self._call.has_blocks
            for item in content:
                if not isinstance(item, dict):
                    continue
                tool = item.get("toolUse")
                if isinstance(tool, dict) and str(tool.get("toolUseId")) not in self._tools:
                    out += self._start_tool(
                        str(tool.get("toolUseId") or uuid.uuid4()),
                        str(tool.get("name") or "tool"),
                        tool.get("input"),
                        now,
                    )
                elif not streamed and isinstance(item.get("text"), str) and item["text"]:
                    out += self._append(-1, "text", item["text"], now)
                    out.append(self._complete(self._call.open_blocks.pop(-1), now))
            for index in list(self._call.open_blocks):  # a block whose stop never came
                out.append(self._complete(self._call.open_blocks.pop(index), now))
        elif message.get("role") == "user":
            for item in content:
                result = item.get("toolResult") if isinstance(item, dict) else None
                if isinstance(result, dict):
                    out += self._finish_tool(result, now)
        return out

    # ------------------------------------------------------------------ blocks

    def _new_block(self, kind: str, now: datetime) -> dict[str, Any]:
        block: dict[str, Any] = {"id": f"b{len(self.blocks) + 1}", "type": kind}
        if kind in ("text", "thinking"):
            block["text"] = ""
        if kind == "thinking":
            # Strands sends the summary in one burst after the model has thought in silence, so
            # the thinking began when its model call did (fixture `thinking`: 4.1 s earlier).
            first = not self._call.has_blocks and self._call.started_at is not None
            block["startedAt"] = iso(
                self._call.started_at if first and self._call.started_at else now
            )
            block["endedAt"] = None
        self._call.has_blocks = True
        self.blocks.append(block)
        return block

    def _append(self, index: int, kind: str, text: str, now: datetime) -> list[Output]:
        out: list[Output] = []
        block = self._call.open_blocks.get(index)
        if block is None or block["type"] != kind:
            if block is not None:
                out.append(self._complete(self._call.open_blocks.pop(index), now))
            block = self._new_block(kind, now)
            self._call.open_blocks[index] = block
            out.append(BlockStarted(len(self.blocks) - 1, copy.deepcopy(block)))
        if text:
            block["text"] += text
            out.append(BlockDelta(block["id"], text))
        return out

    def _complete(self, block: dict[str, Any], now: datetime) -> BlockCompleted:
        if block["type"] == "thinking":
            block["endedAt"] = iso(now)
        return BlockCompleted(copy.deepcopy(block))

    def _start_tool(
        self, tool_use_id: str, name: str, tool_input: Any, now: datetime
    ) -> list[Output]:
        block = self._new_block("tool", now)
        block["toolCall"] = {
            "id": str(uuid.uuid4()),
            "toolUseId": tool_use_id,
            "name": name,
            "status": "running",
            "summary": None,
            "input": truncate(tool_input),
            "output": None,
            "outputFile": None,
            "error": None,
            "startedAt": iso(now),
            "completedAt": None,
        }
        self._tools[tool_use_id] = block
        return [BlockStarted(len(self.blocks) - 1, copy.deepcopy(block))]

    def _finish_tool(self, result: dict[str, Any], now: datetime) -> list[Output]:
        block = self._tools.get(str(result.get("toolUseId")))
        if block is None or block["toolCall"]["status"] != "running":
            return []
        output = _tool_output(result.get("content"))
        failed = result.get("status") == "error"
        error = _error_text(output) if failed else None
        call = block["toolCall"]
        call["status"] = (
            "cancelled"
            if failed and error == "cancelled"
            else ("failed" if failed else "succeeded")
        )
        call["output"] = truncate(output)
        call["error"] = error
        call["summary"] = _summary(output, error)
        call["completedAt"] = iso(now)
        return [BlockCompleted(copy.deepcopy(block))]

    # ------------------------------------------------------------------ ending

    def close(self, now: datetime) -> list[Output]:
        """End every open block: text and thinking complete as they are, and running tools become
        `cancelled` (the run ended without their result). Call when the run ends any way."""
        out: list[Output] = []
        for index in list(self._call.open_blocks):
            out.append(self._complete(self._call.open_blocks.pop(index), now))
        self._call.pending_tools.clear()
        for block in self._tools.values():
            call = block["toolCall"]
            if call["status"] == "running":
                call["status"] = "cancelled"
                call["completedAt"] = iso(now)
                out.append(BlockCompleted(copy.deepcopy(block)))
        return out

    def search_text(self) -> str:
        return "\n\n".join(b["text"] for b in self.blocks if b["type"] == "text" and b["text"])


# ---------------------------------------------------------------------- helpers


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _parse_json(raw: str) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {"raw": raw}  # partial or invalid JSON from the model: kept, never guessed at


def truncate(value: Any) -> Any:
    """Values over 16 KB of JSON are replaced by a preview (contract: ToolCall input/output)."""
    if value is None:
        return None
    encoded = json.dumps(value, ensure_ascii=False, default=str)
    if len(encoded.encode()) <= MAX_TOOL_JSON_BYTES:
        return value
    return {"truncated": True, "preview": encoded[: MAX_TOOL_JSON_BYTES // 2]}


def _tool_output(content: Any) -> Any:
    """Strands' toolResult content: [{"json": …} | {"text": …}, …]. One item is returned bare."""
    items: list[Any] = []
    for item in content if isinstance(content, list) else []:
        if isinstance(item, dict) and "json" in item:
            items.append(item["json"])
        elif isinstance(item, dict) and "text" in item:
            items.append(item["text"])
    if not items:
        return None
    return items[0] if len(items) == 1 else items


def _error_text(output: Any) -> str:
    if isinstance(output, dict):
        for key in ("error", "detail", "message"):
            if isinstance(output.get(key), str) and output[key]:
                return str(output[key])
    if isinstance(output, str) and output:
        return output[:500]
    return "failed"


def _summary(output: Any, error: str | None) -> str | None:
    """The chip's one line: the result's own `summary`, else the error, else its start."""
    if isinstance(output, dict) and isinstance(output.get("summary"), str):
        return str(output["summary"])[:SUMMARY_CHARS]
    if error is not None:
        detail = output.get("detail") if isinstance(output, dict) else None
        text = detail if isinstance(detail, str) and detail else error
        return text[:SUMMARY_CHARS]
    if output is None:
        return None
    text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
    return text[:SUMMARY_CHARS] + ("…" if len(text) > SUMMARY_CHARS else "")
