"""Typed errors for chat. Each code is in openapi.yaml's ErrorCode enum.

Refusals are raised before anything is saved. The run errors at the bottom never reach a handler:
they end a run, and their problem object is stored in `messages.error` and sent in `run.failed`
with the status the error would have had.
"""

from app.core.errors import ApiError, Conflict, InvalidRequest, NotFound


class SessionNotFound(NotFound):
    code, title = "session_not_found", "There's no such session"


class MessageNotFound(NotFound):
    code, title = "message_not_found", "There's no such message"


class EmptyMessage(InvalidRequest):
    code, title = "empty_message", "Write a message first"


class MessageTooLong(InvalidRequest):
    code, title = "message_too_long", "The message is over 32,000 characters"


class AttachmentsNotSupported(InvalidRequest):
    code, title = "attachments_not_supported", "This agent doesn't take files"


class RunInProgress(Conflict):
    code, title = "run_in_progress", "A reply is still being written in this session"


class AgentRetired(Conflict):
    code, title = "agent_retired", "This agent was removed; its sessions are read-only"


class IdempotencyConflict(Conflict):
    code, title = "idempotency_conflict", "This message id was already used for a different message"


class FileNotReady(Conflict):
    code, title = "file_not_ready", "A file isn't uploaded yet"


class QuestionNotOpen(Conflict):
    code, title = "question_not_open", "That question isn't open"


class TooManyRuns(ApiError):
    status, code, title, retryable = 429, "too_many_runs", "Three replies are already running", True


class AgentUnavailable(ApiError):
    status, code, title, retryable = 503, "agent_unavailable", "The agent is unavailable", True


# ---------------------------------------------------------------- run endings (stored, streamed)


class AgentFailed(ApiError):
    status, code, title, retryable = 500, "agent_error", "The agent failed while replying", True


class RateLimited(ApiError):
    status, code, title, retryable = (
        429,
        "rate_limited",
        "The agent is busy; try again shortly",
        True,
    )


class RunTimeLimit(ApiError):
    status, code, title, retryable = 500, "run_time_limit", "The reply hit its time limit", True


class RunInterrupted(ApiError):
    status, code, title, retryable = 500, "run_interrupted", "The reply was interrupted", True


class InternalRunError(ApiError):
    status, code, title, retryable = 500, "internal_error", "Something went wrong", True
