"""Process lifecycle (standard §14): SIGTERM sets `shutting_down` so streams can drain."""

import signal
from collections.abc import Iterator

import pytest
import uvicorn

from app.core.lifecycle import shutting_down
from app.serve import Server


@pytest.fixture(autouse=True)
def _reset_shutdown() -> Iterator[None]:
    shutting_down.clear()
    yield
    shutting_down.clear()


def test_sigterm_sets_shutting_down() -> None:
    server = Server(uvicorn.Config("app.main:create_app", factory=True))
    server.handle_exit(signal.SIGTERM, None)
    assert shutting_down.is_set() and server.should_exit
