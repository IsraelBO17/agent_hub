"""The translator against every recorded AgentCore stream (D10; tests/fixtures/agentcore/)."""

import json
from datetime import datetime, timedelta
from typing import Any

import pytest

from app.features.chat.translator import (
    BlockCompleted,
    BlockDelta,
    BlockStarted,
    Output,
    RunError,
    RunResult,
    Translator,
    truncate,
)
from tests.support.agentcore import CASES, T0, frames
from tests.support.contract import validate


def replay(case: str) -> tuple[Translator, list[Output]]:
    t = Translator()
    out: list[Output] = []
    for at, frame in frames(case):
        out += t.feed(frame, at)
    return t, out


def final_message_texts(case: str) -> list[str]:
    """The text of the agent's own finished assistant messages, to compare with the deltas."""
    return [
        item["text"]
        for _, f in frames(case)
        if isinstance(f.get("message"), dict) and f["message"]["role"] == "assistant"
        for item in f["message"]["content"]
        if "text" in item
    ]


@pytest.mark.parametrize("case", CASES)
def test_every_block_starts_once_and_completes_once(case: str) -> None:
    t, out = replay(case)
    started = [o.block["id"] for o in out if isinstance(o, BlockStarted)]
    completed = [o.block["id"] for o in out if isinstance(o, BlockCompleted)]
    assert started == [b["id"] for b in t.blocks] == [f"b{i + 1}" for i in range(len(t.blocks))]
    assert sorted(completed) == sorted(started)
    for o in out:
        if isinstance(o, BlockStarted | BlockCompleted):
            validate(o.block, "Block")
    assert [o.index for o in out if isinstance(o, BlockStarted)] == list(range(len(t.blocks)))


@pytest.mark.parametrize("case", CASES)
def test_deltas_rebuild_the_agents_own_text(case: str) -> None:
    t, out = replay(case)
    rebuilt: dict[str, str] = {}
    for o in out:
        if isinstance(o, BlockDelta):
            rebuilt[o.block_id] = rebuilt.get(o.block_id, "") + o.text
    texts = [b["text"] for b in t.blocks if b["type"] == "text"]
    assert texts == final_message_texts(case)
    assert all(rebuilt[b["id"]] == b["text"] for b in t.blocks if b["type"] in ("text", "thinking"))


def test_plain_answer() -> None:
    t, out = replay("plain-answer")
    assert [b["type"] for b in t.blocks] == ["text"]
    assert out[-1] == t.ended and isinstance(t.ended, RunResult)
    assert t.ended.stop_reason == "end_turn" and t.ended.usage["outputTokens"] > 0
    assert t.search_text() == t.blocks[0]["text"]


def test_thinking_is_timed_from_the_start_of_its_model_call() -> None:
    t, _ = replay("thinking")
    thinking, text = t.blocks
    assert (thinking["type"], text["type"]) == ("thinking", "text")
    assert thinking["text"] and thinking["endedAt"] is not None
    start_loop = next(at for at, f in frames("thinking") if "start" in f)  # the model call begins
    first_delta = next(at for at, f in frames("thinking") if "reasoningContent" in json.dumps(f))
    assert first_delta - start_loop > timedelta(seconds=3)  # the silence the README describes
    assert thinking["startedAt"] == start_loop.isoformat().replace("+00:00", "Z")
    ended = datetime.fromisoformat(thinking["endedAt"])
    assert ended - start_loop > timedelta(seconds=3)  # "Thought for 4s", not 0.3 s


def test_tool_call_succeeds_with_input_and_output() -> None:
    t, out = replay("tool-call")
    assert [b["type"] for b in t.blocks] == ["tool", "text"]
    call = t.blocks[0]["toolCall"]
    assert call["name"] == "fetch_url" and call["status"] == "succeeded"
    assert call["input"] == {"url": "https://example.com"}
    assert call["output"]["title"] == "Example Domain" and call["error"] is None
    assert call["summary"] and call["completedAt"] > call["startedAt"]
    started = next(o for o in out if isinstance(o, BlockStarted) and o.block["type"] == "tool")
    assert started.block["toolCall"]["status"] == "running"  # the chip shows it running first
    assert started.block["toolCall"]["input"] == {"url": "https://example.com"}


def test_tool_error_is_a_failed_call_with_its_detail() -> None:
    t, _ = replay("tool-error")
    call = t.blocks[0]["toolCall"]
    assert (call["status"], call["error"]) == ("failed", "http_error")
    assert call["summary"] == "The server answered 404 Not Found."
    assert isinstance(t.ended, RunResult) and t.ended.stop_reason == "end_turn"


def test_cancelled_tool_and_run() -> None:
    t, _ = replay("cancelled-mid-fetch")
    assert t.blocks[0]["toolCall"]["status"] == "cancelled"
    assert isinstance(t.ended, RunResult) and t.ended.stop_reason == "cancelled"


def test_agent_error_frame_ends_the_run() -> None:
    t, out = replay("invalid-payload")
    assert t.blocks == [] and out == [t.ended]
    assert isinstance(t.ended, RunError) and t.ended.message == "messages is required"
    assert t.ended.error_type == "ValueError"


def test_nothing_is_translated_after_the_end() -> None:
    t, _ = replay("plain-answer")
    assert t.feed({"event": {"contentBlockDelta": {"delta": {"text": "late"}}}}, T0) == []


def test_close_completes_open_text_and_cancels_running_tools() -> None:
    t = Translator()
    cut = [f for _, f in frames("tool-call")]
    i = next(i for i, f in enumerate(cut) if f.get("message", {}).get("role") == "user")
    for frame in cut[:i]:  # the tool has started; its result never arrives
        t.feed(frame, T0)
    t.feed({"start": True}, T0)
    t.feed({"event": {"messageStart": {"role": "assistant"}}}, T0)
    t.feed({"event": {"contentBlockDelta": {"delta": {"text": "Partial"}}}}, T0)
    out = t.close(T0 + timedelta(seconds=1))
    assert {o.block["type"] for o in out if isinstance(o, BlockCompleted)} == {"text", "tool"}
    assert t.blocks[0]["toolCall"]["status"] == "cancelled"
    assert t.blocks[1]["text"] == "Partial"
    assert t.close(T0) == []


def test_unknown_and_malformed_frames_are_ignored() -> None:
    t = Translator()
    for frame in ["a string", 42, {"unknown": 1}, {"event": "x"}, {"message": []}]:
        assert t.feed(frame, T0) == []


def test_unstreamed_text_in_a_finished_message_is_kept() -> None:
    t = Translator()
    t.feed({"start_event_loop": True}, T0)
    out = t.feed({"message": {"role": "assistant", "content": [{"text": "Whole answer"}]}}, T0)
    assert [type(o) for o in out] == [BlockStarted, BlockDelta, BlockCompleted]
    assert t.blocks == [{"id": "b1", "type": "text", "text": "Whole answer"}]


def test_partial_tool_json_is_kept_raw() -> None:
    t = Translator()
    events: list[dict[str, Any]] = [
        {"event": {"messageStart": {"role": "assistant"}}},
        {"event": {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "t1", "name": "x"}}}}},
        {"event": {"contentBlockDelta": {"delta": {"toolUse": {"input": '{"a": '}}}}},
        {"event": {"contentBlockStop": {"contentBlockIndex": 0}}},
    ]
    for e in events:
        t.feed(e, T0)
    assert t.blocks[0]["toolCall"]["input"] == {"raw": '{"a": '}


def test_large_values_are_truncated() -> None:
    big = {"text": "x" * 40_000}
    small = truncate(big)
    assert small["truncated"] is True and len(json.dumps(small)) < 16 * 1024
    assert truncate({"a": 1}) == {"a": 1} and truncate(None) is None
