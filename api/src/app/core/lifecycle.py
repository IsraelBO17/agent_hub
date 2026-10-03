"""Process lifecycle. `shutting_down` is set by serve.py on SIGTERM/SIGINT (standard §14).

Uvicorn tells the app nothing until open requests have finished, so long streams and the in-process
worker watch this event to drain.
"""

import asyncio

shutting_down = asyncio.Event()
