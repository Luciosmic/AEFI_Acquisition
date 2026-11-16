from abc import ABC, abstractmethod

from application.closing_guard_service.dtos.close_decision_dto import CloseDecisionDTO


class IApiClosingGuardService(ABC):
    """Inbound contract of the closing guard: may the application close now?

    Responsibility:
        - `can_close()`: allowed when no acquisition export is open; otherwise refused, with the open acquisitions.

    Rationale:
        The interface receives the close requests (main window, session end) and must decide without
        knowing anything about the exports.

    Design:
        - A query without arguments, hence no request DTO; it logs its decision.
    """

    @abstractmethod
    def can_close(self) -> CloseDecisionDTO:
        """Allowed when no acquisition export is open; otherwise refused, naming each open acquisition."""
