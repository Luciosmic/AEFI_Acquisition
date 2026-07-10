"""
Fake Thread Pool Task Runner

Responsibility:
- Implement IAsyncTaskRunner for tests by executing the callable synchronously
  in the calling thread, making test assertions deterministic.

Rationale:
- The real ThreadPoolTaskRunner spawns a daemon thread, introducing timing
  non-determinism that forces tests to use waits/sleeps and makes failures
  hard to reproduce.
- Running the callable synchronously in setUp / test body removes all
  threading: the callable returns before submit() returns, so assertions
  can follow immediately.

Design:
- submit() calls the callable directly, then returns a completed FakeTaskHandle.
- FakeTaskHandle.is_running() always returns False (task is done by the time
  submit() returns). wait() is a no-op.
- No thread is created. No daemon flag. No join.
"""

from __future__ import annotations

from typing import Callable, Optional

from application._shared.ports.i_async_task_runner import IAsyncTaskRunner, TaskHandle


class _CompletedTaskHandle(TaskHandle):
    def is_running(self) -> bool:
        return False

    def wait(self, timeout: Optional[float] = None) -> None:
        pass


class FakeThreadPoolTaskRunner(IAsyncTaskRunner):
    """Executes submitted callables synchronously — designed for deterministic tests."""

    def submit(self, task: Callable[[], None]) -> TaskHandle:
        task()
        return _CompletedTaskHandle()
