from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

from domain.shared_kernel.operation_result import OperationResult


@dataclass(frozen=True)
class StoredEventLogSession:
    name: str
    started_at: datetime  # UTC, from the session's name
    size_bytes: int
    is_live: bool  # the session the running app is writing to


@dataclass(frozen=True)
class EventLogSessionNotDeleted:
    session_name: str
    reason: str


class IEventLogStoragePort(ABC):
    """
    Responsibility:
    - List the event audit log's sessions and delete one of them.

    Rationale:
    - Keeps the session file naming and the filesystem out of the
      maintenance service, so its retention rule is testable on a Fake.

    Design:
    - Outbound port. Expected failures (file in use, live session) come back
      as OperationResult, never raised.
    """

    @abstractmethod
    def location(self) -> str:
        """Where the sessions are stored, for the user to open."""

    @abstractmethod
    def list_sessions(self) -> List[StoredEventLogSession]: ...

    @abstractmethod
    def delete_session(self, name: str) -> OperationResult[None, EventLogSessionNotDeleted]: ...
