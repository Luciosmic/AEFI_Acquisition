from abc import ABC, abstractmethod


class ISystemSessionGuard(ABC):
    """Hold the operating system's session end and sleep while an acquisition export is open.

    Responsibility:
        - `hold(reason)`: hold the session end and sleep, with a reason the operator can read.
          An empty reason is refused with ValueError: the system would have nothing to show.
        - `release()`: give them back. Without a previous `hold`, does nothing.

    Rationale:
        A system shutdown or restart during an export loses the measurement as surely as an operator
        closing the window. What a system lets an application ask depends on the system; the closing
        guard must stay the same everywhere.

    Design:
        - Implementations: NullSystemSessionGuard (systems not supported) and its Fake; later Windows.
        - Contract suite: closing_guard_service/_tests/system_session_guard_contract_test.py.
        - Called from the thread that publishes the export opening or closing.
    """

    @abstractmethod
    def hold(self, reason: str) -> None:
        """Hold the session end and sleep. Raises ValueError on an empty reason."""

    @abstractmethod
    def release(self) -> None:
        """Give the session end and sleep back. No-op without a previous hold."""
