"""
Thread Pool Task Runner

Responsibility:
- Implement IAsyncTaskRunner using a daemon threading.Thread per submitted task.

Rationale:
- Satisfies the Application layer's need to run a callable in the background
  without coupling any business logic to threading primitives.
- Single cause of change: the concurrency mechanism (thread per task, pool,
  asyncio event loop). No knowledge of StepScan, EF probe, or any domain
  concept belongs here.

Design:
- Each submit() call spawns a new daemon thread.
- The thread is daemon so it does not prevent process exit.
- Exceptions raised by the callable propagate to stderr (daemon thread
  behaviour) — programmer errors stay visible; the runner does not swallow them.
- ThreadTaskHandle wraps the Thread to expose is_running/wait without
  leaking threading internals to the Application layer.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

from application._shared.ports.i_async_task_runner import IAsyncTaskRunner, TaskHandle


class _ThreadTaskHandle(TaskHandle):
    def __init__(self, thread: threading.Thread) -> None:
        self._thread = thread

    def is_running(self) -> bool:
        return self._thread.is_alive()

    def wait(self, timeout: Optional[float] = None) -> None:
        self._thread.join(timeout=timeout)


class ThreadPoolTaskRunner(IAsyncTaskRunner):
    """Runs each submitted callable in its own daemon thread."""

    def submit(self, task: Callable[[], None]) -> TaskHandle:
        thread = threading.Thread(target=task, daemon=True)
        thread.start()
        return _ThreadTaskHandle(thread)
