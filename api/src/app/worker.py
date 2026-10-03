"""Run the job worker and sweeps: `python -m app.worker` (a second role of the same image).

Stops claiming on SIGTERM and finishes the batch it holds (standard §13).
"""

import asyncio
import signal

from app.core.db import init_db
from app.core.jobs.runner import configure_retention, work_loop
from app.core.logging import configure_logging
from app.core.settings import get_settings


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.log_json)
    configure_retention(settings.job_retention_days)
    db = init_db(settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        await work_loop(db.sessions, settings, stop)
    finally:
        await db.engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
