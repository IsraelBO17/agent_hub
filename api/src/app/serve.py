"""Start the API: `python -m app.serve` (the container's command).

Uvicorn tells the app nothing about shutdown until open requests have finished, so this sets
`shutting_down` the moment SIGTERM arrives; streams then finish or checkpoint (standard §14).
"""

from types import FrameType

import uvicorn

from app.core.lifecycle import shutting_down
from app.core.settings import get_settings


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        shutting_down.set()
        super().handle_exit(sig, frame)


def main() -> None:
    settings = get_settings()
    config = uvicorn.Config(
        "app.main:create_app",
        factory=True,
        host="0.0.0.0",  # noqa: S104  (inside a container)
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        timeout_graceful_shutdown=settings.shutdown_grace_seconds,
        log_config=None,  # logging is configured by create_app()
    )
    Server(config).run()


if __name__ == "__main__":
    main()
