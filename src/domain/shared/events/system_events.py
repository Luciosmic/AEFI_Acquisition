"""
System Lifecycle Domain Events

Responsibility:
- Define events related to system startup / shutdown lifecycle.
- Used by application services to notify the rest of the system
  (UI, logging, exporters, etc.) in a decoupled way.
"""

from dataclasses import dataclass

from domain.shared.events.domain_event import DomainEvent


@dataclass(frozen=True)
class SystemReadyEvent(DomainEvent):
    """Event emitted when the system startup sequence completes successfully."""
    message: str = "System is ready"


@dataclass(frozen=True)
class SystemStartupFailedEvent(DomainEvent):
    """Event emitted when the system fails to start."""
    reason: str


@dataclass(frozen=True)
class SystemShuttingDownEvent(DomainEvent):
    """Event emitted when the system shutdown sequence begins."""
    message: str = "System shutting down"


@dataclass(frozen=True)
class SystemShutdownCompleteEvent(DomainEvent):
    """Event emitted when the system shutdown sequence completes."""
    success: bool
    details: str = ""


