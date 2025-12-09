"""
System lifecycle application services.

Responsibility:
- Orchestrate high‑level startup and shutdown sequences.
- Delegate hardware / calibration / scan logic to injected collaborators.
- Publish system lifecycle events via the domain event bus.

Important:
- These services are intentionally thin and stateless.
- They do NOT know hardware details; they just call well‑named methods
  on the injected components if those methods exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.system_events import (
    SystemReadyEvent,
    SystemStartupFailedEvent,
    SystemShuttingDownEvent,
    SystemShutdownCompleteEvent,
)


@dataclass
class StartupConfig:
    """
    Configuration for system startup.

    - verify_hardware: if True, call an optional verification step
      on the hardware initializer (advanced but optional).
    - load_last_calibration: if True, ask the calibration service
      to restore the last known calibration.
    """

    verify_hardware: bool = True
    load_last_calibration: bool = True


@dataclass
class StartupResult:
    """
    Result of the startup sequence.

    - success: global success flag
    - initialized_resources: anything returned by the hardware initializer
      (typically controllers or ports)
    - errors: list of human‑readable error messages
    """

    success: bool
    initialized_resources: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class ShutdownConfig:
    """
    Configuration for system shutdown.

    - save_state: if True, call optional persistence methods on services.
    """

    save_state: bool = True


@dataclass
class ShutdownResult:
    """
    Result of the shutdown sequence.

    - success: global success flag
    - cleanup_status: per‑subsystem status (scan, acquisition, hardware, …)
    - errors: list of human‑readable error messages
    """

    success: bool
    cleanup_status: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class SystemStartupApplicationService:
    """
    Orchestrates system initialization sequence: hardware → calibration → ready state.

    Rationale:
    - Centralize startup logic so UI, tests and CLI use the same choreography.
    - Keep hardware details in infrastructure; here we only call collaborators.
    """

    def __init__(
        self,
        hardware_initializer: Any,
        calibration_service: Optional[Any],
        event_bus: IDomainEventBus,
    ) -> None:
        self._hardware_initializer = hardware_initializer
        self._calibration_service = calibration_service
        self._event_bus = event_bus

    def startup_system(self, config: StartupConfig) -> StartupResult:
        """
        Execute the startup sequence.

        Steps:
        1. Initialize hardware (infrastructure layer)
        2. Optionally verify hardware connectivity
        3. Optionally load last calibration
        4. Publish SystemReadyEvent or SystemStartupFailedEvent
        """

        errors: List[str] = []
        resources: Dict[str, Any] = {}

        # 1. Initialize hardware
        try:
            if hasattr(self._hardware_initializer, "initialize_all"):
                # expected API: returns a dict of initialized controllers/ports
                resources = self._hardware_initializer.initialize_all()
            else:
                errors.append("hardware_initializer has no 'initialize_all' method")
        except Exception as exc:  # advanced: we capture and continue to build a clear error
            errors.append(f"hardware initialization failed: {exc!r}")

        # 2. Verify connectivity (optional)
        if not errors and config.verify_hardware:
            try:
                if hasattr(self._hardware_initializer, "verify_all"):
                    ok = bool(self._hardware_initializer.verify_all())
                    if not ok:
                        errors.append("hardware verification failed")
                # if no verify_all: silently skip, to keep API flexible
            except Exception as exc:
                errors.append(f"hardware verification failed: {exc!r}")

        # 3. Load calibration (optional)
        if not errors and config.load_last_calibration and self._calibration_service is not None:
            try:
                # expected API name kept very generic on purpose
                if hasattr(self._calibration_service, "load_last_calibration"):
                    self._calibration_service.load_last_calibration()
                elif hasattr(self._calibration_service, "load_last"):
                    self._calibration_service.load_last()
                # else: silently skip, calibration is optional
            except Exception as exc:
                errors.append(f"calibration load failed: {exc!r}")

        success = not errors

        if success:
            # We only publish a lightweight event (no heavy infra objects inside)
            self._event_bus.publish("systemready", SystemReadyEvent())
        else:
            reason = "; ".join(errors)
            self._event_bus.publish("systemstartupfailed", SystemStartupFailedEvent(reason=reason))

        return StartupResult(success=success, initialized_resources=resources, errors=errors)


class SystemShutdownApplicationService:
    """
    Orchestrates graceful system shutdown: stop acquisitions → save state → close hardware.

    Rationale:
    - Avoid data loss (flush before closing).
    - Avoid hardware damage (stop motion before power‑off).
    """

    def __init__(
        self,
        scan_service: Optional[Any],
        acquisition_service: Optional[Any],
        hardware_initializer: Any,
        event_bus: IDomainEventBus,
    ) -> None:
        self._scan_service = scan_service
        self._acquisition_service = acquisition_service
        self._hardware_initializer = hardware_initializer
        self._event_bus = event_bus

    def shutdown_system(self, config: ShutdownConfig) -> ShutdownResult:
        """
        Execute the shutdown sequence.

        Steps:
        1. Publish SystemShuttingDownEvent
        2. Stop active operations (scan, acquisition) if services are provided
        3. Optionally flush/save state
        4. Close hardware connections
        5. Publish SystemShutdownCompleteEvent
        """

        cleanup_status: Dict[str, bool] = {}
        errors: List[str] = []

        # 1. Notify start of shutdown
        self._event_bus.publish("systemshuttingdown", SystemShuttingDownEvent())

        # 2. Stop scan operations
        if self._scan_service is not None:
            try:
                # We use the existing API from ScanApplicationService (cancel_scan).
                if hasattr(self._scan_service, "cancel_scan"):
                    self._scan_service.cancel_scan()
                elif hasattr(self._scan_service, "stop"):
                    self._scan_service.stop()
                cleanup_status["scan"] = True
            except Exception as exc:
                cleanup_status["scan"] = False
                errors.append(f"scan stop failed: {exc!r}")

            # 2.b Optional persistence
            if config.save_state:
                try:
                    if hasattr(self._scan_service, "save_state"):
                        self._scan_service.save_state()
                except Exception as exc:
                    errors.append(f"scan save_state failed: {exc!r}")

        # 3. Stop acquisition operations (if a dedicated service exists)
        if self._acquisition_service is not None:
            try:
                if hasattr(self._acquisition_service, "stop"):
                    self._acquisition_service.stop()
                cleanup_status["acquisition"] = True
            except Exception as exc:
                cleanup_status["acquisition"] = False
                errors.append(f"acquisition stop failed: {exc!r}")

            if config.save_state:
                try:
                    if hasattr(self._acquisition_service, "save_state"):
                        self._acquisition_service.save_state()
                except Exception as exc:
                    errors.append(f"acquisition save_state failed: {exc!r}")

        # 4. Close hardware connections
        try:
            if hasattr(self._hardware_initializer, "close_all"):
                self._hardware_initializer.close_all()
            elif hasattr(self._hardware_initializer, "shutdown_all"):
                self._hardware_initializer.shutdown_all()
            cleanup_status["hardware"] = True
        except Exception as exc:
            cleanup_status["hardware"] = False
            errors.append(f"hardware shutdown failed: {exc!r}")

        success = not errors and all(cleanup_status.values()) if cleanup_status else not errors

        self._event_bus.publish(
            "systemshutdowncomplete",
            SystemShutdownCompleteEvent(success=success, details="; ".join(errors)),
        )

        return ShutdownResult(success=success, cleanup_status=cleanup_status, errors=errors)


