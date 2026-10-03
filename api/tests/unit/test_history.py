"""D18: which earlier turns go to the agent, within the turns and characters budget."""

from app.features.chat.service import TRUNCATED, pick_history


def turns(*texts: str) -> list[tuple[str, str]]:
    """Newest first, as the repository reads them; roles alternate from the newest reply back."""
    return [("assistant" if i % 2 == 0 else "user", t) for i, t in enumerate(texts)]


def test_one_oversize_reply_is_cut_to_the_budget_not_dropped() -> None:
    report = "Report. " + "x" * 38_000
    history = pick_history(turns(report, "Write me a report"), 20, 32_000)
    assert history == [{"role": "assistant", "text": report[: 32_000 - len(TRUNCATED)] + TRUNCATED}]
    assert len(history[0]["text"]) == 32_000
    assert history[0]["text"].startswith("Report. ")


def test_the_turn_that_crosses_the_budget_is_cut_and_ends_the_history() -> None:
    history = pick_history(turns("a" * 400, "b" * 400, "c" * 400, "d" * 400), 20, 1_000)
    assert history == [
        {"role": "assistant", "text": "c" * (200 - len(TRUNCATED)) + TRUNCATED},
        {"role": "user", "text": "b" * 400},
        {"role": "assistant", "text": "a" * 400},
    ]
    assert sum(len(t["text"]) for t in history) == 1_000


def test_whole_turns_that_fit_go_in_oldest_first() -> None:
    history = pick_history(turns("third", "second", "first"), 20, 32_000)
    assert [t["text"] for t in history] == ["first", "second", "third"]
    assert [t["role"] for t in history] == ["assistant", "user", "assistant"]


def test_a_turn_with_no_room_left_for_any_text_is_left_out() -> None:
    history = pick_history(turns("a" * 995, "b" * 400), 20, 1_000)
    assert history == [{"role": "assistant", "text": "a" * 995}]


def test_the_turn_limit_keeps_the_newest() -> None:
    many = [f"turn {n}" for n in range(40, 0, -1)]  # newest first
    history = pick_history(turns(*many), 20, 32_000)
    assert [t["text"] for t in history] == [f"turn {n}" for n in range(21, 41)]


def test_empty_turns_are_skipped_and_not_counted() -> None:
    history = pick_history(turns("reply", "", "question"), 2, 32_000)
    assert [t["text"] for t in history] == ["question", "reply"]


def test_no_earlier_turns() -> None:
    assert pick_history([], 20, 32_000) == []
