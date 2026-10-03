"""Background work (standard §13): a Postgres job table, a worker, and sweeps.

enqueue(session, "billing.send_receipt", {...})   inside the producing transaction (the outbox)
@job("billing.send_receipt", SendReceipt)        a handler, in the feature that owns the work
@sweep("jobs.purge_finished", every=...)          periodic, bounded, idempotent work
"""

from app.core.jobs.queue import enqueue
from app.core.jobs.registry import job, sweep

__all__ = ["enqueue", "job", "sweep"]
