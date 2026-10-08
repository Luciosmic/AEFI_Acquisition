from abc import ABC, abstractmethod

from application.services.event_log_maintenance_service.dtos.event_log_dto import (
    EventLogPurgeResultDTO,
    EventLogSummaryDTO,
)


class IApiEventLogMaintenanceService(ABC):
    """
    Responsibility:
    - Inbound API contract for EventLogMaintenanceService.

    Rationale:
    - Lets the presenter depend on a contract, and be tested against a stub.

    Design:
    - Pure ABC, DTOs only.
    """

    @abstractmethod
    def get_summary(self) -> EventLogSummaryDTO:
        """Size of the event log, and what delete_expired_sessions() would remove."""

    @abstractmethod
    def delete_expired_sessions(self) -> EventLogPurgeResultDTO:
        """Delete sessions older than the retention period, never the live one."""
