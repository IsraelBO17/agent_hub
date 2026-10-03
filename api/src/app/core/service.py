"""BaseService: the transaction boundary (standard §11.2).

Only services commit. Repositories and `public.py` doors flush; they never commit, roll back or
open a session. Irreversible work (email, HTTP calls, payments) is never done inside the
transaction: enqueue a job instead (core/jobs), which commits with the work.
"""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


class BaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._after_commit: list[Callable[[], Awaitable[None]]] = []

    def after_commit(self, fn: Callable[[], Awaitable[None]]) -> None:
        """Run fn only if the transaction commits (cache busts, best-effort notices). Anything that
        must happen is a job, not an after-commit hook."""
        self._after_commit.append(fn)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        try:
            yield
            await self.session.commit()
        except BaseException:
            self._after_commit.clear()
            await self.session.rollback()
            raise
        hooks, self._after_commit = self._after_commit, []
        for fn in hooks:
            try:
                await fn()
            except Exception:
                log.exception("after_commit_failed")
