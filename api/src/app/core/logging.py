"""Logs (standard §17): one JSON object per line in deployed environments, readable text locally.

A filter adds request_id, user_id and trace_id to every record, including library records.
"""

import json
import logging
import sys
from typing import Any

from opentelemetry import trace

from app.core.context import request_id_var, user_id_var

_STANDARD = set(logging.makeLogRecord({}).__dict__) | {
    "message",
    "asctime",
    "taskName",
    "color_message",
}


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        ctx = trace.get_current_span().get_span_context()
        record.trace_id = trace.format_trace_id(ctx.trace_id) if ctx.is_valid else "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD:
                out[key] = value
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out, default=str)


class TextFormatter(logging.Formatter):
    """Readable local lines, with the request id and any extra fields as key=value."""

    def format(self, record: logging.LogRecord) -> str:
        line = (
            f"{self.formatTime(record, '%H:%M:%S')} {record.levelname} {record.name} "
            f"[req={getattr(record, 'request_id', '-')}] {record.getMessage()}"
        )
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _STANDARD and k not in {"request_id", "user_id", "trace_id"}
        }
        if extras:
            line += " " + " ".join(f"{k}={v}" for k, v in extras.items())
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def configure_logging(level: str, *, json_output: bool) -> None:
    """Install one stdout handler on the root logger (replacing Uvicorn's), once per process."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True  # the request middleware logs instead
