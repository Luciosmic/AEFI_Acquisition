"""
Asynchronous Task Runner Port

Responsibility:
- Provide the Application layer with a way to run a callable in the background
  without knowing anything about the underlying concurrency mechanism.

Rationale:
- Hexagonal architecture / outbound port.
- Decouples application use-case loops (scan step loop, EF probe streaming loop)
  from the infrastructure choice of threading, asyncio, multiprocessing, or
  a remote task queue.
- Shared across multiple application services (scan, EF probe) because the
  cause of change (how we run background work) is orthogonal to any given
  service's business rules.

Design:
- Fire-and-forget submit returning a lightweight TaskHandle for optional wait.
- Cancellation is out of scope: the callable itself must observe a cooperative
  stop signal owned by the application service. This keeps the port free of
  cancellation semantics that would leak infra concerns (thread interrupt,
  future.cancel, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional


class TaskHandle(ABC):
    """
    Opaque handle representing a task submitted to an IAsyncTaskRunner.

    Only exposes the operations the Application layer legitimately needs:
    ask whether the task is still running, and block until it completes.
    """

    @abstractmethod
    def is_running(self) -> bool:
        """Return True as long as the submitted callable has not returned."""

    @abstractmethod
    def wait(self, timeout: Optional[float] = None) -> None:
        """
        Block until the submitted callable returns, or until timeout elapses.

        A timeout of None means wait forever.
        """


class IAsyncTaskRunner(ABC):
    """
    Port for running a callable in the background.

    The callable is expected to be self-contained: it captures its own
    dependencies via closure and reports its own outcome through side effects
    (domain event bus, application state, aggregate mutations).

    The runner MUST NOT wrap the callable in any error-handling logic that
    would swallow exceptions — programmer errors must remain visible.
    """

    @abstractmethod
    def submit(self, task: Callable[[], None]) -> TaskHandle:
        """
        Submit the callable for background execution and return immediately.

        The returned TaskHandle can be used to observe or await completion.
        """
