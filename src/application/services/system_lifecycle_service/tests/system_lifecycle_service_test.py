import unittest
from typing import Any, Dict, List

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.events.in_memory_event_bus import InMemoryEventBus

from application.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService,
    SystemShutdownApplicationService,
    StartupConfig,
    ShutdownConfig,
)
from domain.shared.events.system_events import (
    SystemReadyEvent,
    SystemStartupFailedEvent,
    SystemShuttingDownEvent,
    SystemShutdownCompleteEvent,
)


class FakeHardwareInitializer:
    """
    Simple fake object emulating the hardware initializer used by the
    SystemStartupApplicationService / SystemShutdownApplicationService.

    This keeps the test fully deterministic and independent from real hardware.
    """

    def __init__(self) -> None:
        self.initialized: bool = False
        self.verified: bool = False
        self.closed: bool = False

    def initialize_all(self) -> Dict[str, Any]:
        self.initialized = True
        return {"motion": "MockMotionController", "acquisition": "MockAcquisitionController"}

    def verify_all(self) -> bool:
        self.verified = True
        return True

    def close_all(self) -> None:
        self.closed = True


class FakeCalibrationService:
    """Simple fake calibration service used for the startup sequence."""

    def __init__(self) -> None:
        self.loaded: bool = False

    def load_last_calibration(self) -> None:
        self.loaded = True


class TestSystemLifecycleService(DiagramFriendlyTest):
    """
    Diagram‑friendly test for the system lifecycle services.

    Goal:
    - Show a complete happy‑path sequence: startup then shutdown.
    - Generate a JSON trace that can be converted to a PlantUML sequence diagram.
    """

    def setUp(self) -> None:
        super().setUp()

        # Event bus and storage for received lifecycle events
        self.event_bus = InMemoryEventBus()
        self.received_events: List[str] = []

        # Subscribe once for all lifecycle events
        def _on_system_event(event: Any) -> None:
            event_name = type(event).__name__
            self.received_events.append(event_name)
            self.log_interaction(
                actor="EventBus",
                action="RECEIVE",
                target=event_name,
                message=f"Handler received {event_name}",
                data={"event_type": event_name},
            )

        for event_type in [
            "systemready",
            "systemstartupfailed",
            "systemshuttingdown",
            "systemshutdowncomplete",
        ]:
            self.event_bus.subscribe(event_type, _on_system_event)
            self.log_interaction(
                actor="TestSystemLifecycleService",
                action="SUBSCRIBE",
                target="EventBus",
                message=f"Subscribe to '{event_type}'",
            )

        # Fakes used by the services
        self.hardware = FakeHardwareInitializer()
        self.calibration = FakeCalibrationService()

        self.startup_service = SystemStartupApplicationService(
            hardware_initializer=self.hardware,
            calibration_service=self.calibration,
            event_bus=self.event_bus,
        )
        self.shutdown_service = SystemShutdownApplicationService(
            scan_service=None,
            acquisition_service=None,
            hardware_initializer=self.hardware,
            event_bus=self.event_bus,
        )

    def test_startup_and_shutdown_happy_path(self) -> None:
        """
        Full happy‑path:
        - Startup initializes hardware, verifies, loads calibration, publishes SystemReadyEvent.
        - Shutdown publishes SystemShuttingDownEvent, closes hardware, publishes SystemShutdownCompleteEvent.
        """

        # --- Startup ---
        config = StartupConfig(verify_hardware=True, load_last_calibration=True)
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="CALL",
            target="SystemStartupApplicationService",
            message="startup_system(verify_hardware=True, load_last_calibration=True)",
            data={"verify_hardware": True, "load_last_calibration": True},
        )
        result = self.startup_service.startup_system(config)

        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="SystemStartupApplicationService",
            message="StartupResult.success should be True",
            expect=True,
            got=result.success,
        )
        self.assertTrue(result.success)

        # Check side effects on collaborators
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="FakeHardwareInitializer",
            message="Hardware should be initialized and verified",
            data={
                "initialized": self.hardware.initialized,
                "verified": self.hardware.verified,
            },
            expect={"initialized": True, "verified": True},
            got={"initialized": self.hardware.initialized, "verified": self.hardware.verified},
        )
        self.assertTrue(self.hardware.initialized)
        self.assertTrue(self.hardware.verified)

        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="FakeCalibrationService",
            message="Calibration should be loaded",
            expect=True,
            got=self.calibration.loaded,
        )
        self.assertTrue(self.calibration.loaded)

        # Ensure SystemReadyEvent has been seen on the bus
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="EventBus",
            message="SystemReadyEvent should have been published",
            expect=True,
            got=("SystemReadyEvent" in self.received_events),
        )
        self.assertIn("SystemReadyEvent", self.received_events)

        # --- Shutdown ---
        shutdown_config = ShutdownConfig(save_state=False)
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="CALL",
            target="SystemShutdownApplicationService",
            message="shutdown_system(save_state=False)",
            data={"save_state": False},
        )
        shutdown_result = self.shutdown_service.shutdown_system(shutdown_config)

        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="SystemShutdownApplicationService",
            message="ShutdownResult.success should be True",
            expect=True,
            got=shutdown_result.success,
        )
        self.assertTrue(shutdown_result.success)

        # Hardware should be closed
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="FakeHardwareInitializer",
            message="Hardware should be closed after shutdown",
            expect=True,
            got=self.hardware.closed,
        )
        self.assertTrue(self.hardware.closed)

        # Events for shutdown sequence
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="EventBus",
            message="SystemShuttingDownEvent and SystemShutdownCompleteEvent should be published",
            expect=True,
            got=(
                "SystemShuttingDownEvent" in self.received_events
                and "SystemShutdownCompleteEvent" in self.received_events
            ),
        )
        self.assertIn("SystemShuttingDownEvent", self.received_events)
        self.assertIn("SystemShutdownCompleteEvent", self.received_events)

    def test_startup_failure_when_hardware_verification_fails(self) -> None:
        """
        Failure path:
        - Hardware initialize_all succeeds but verify_all() returns False.
        - Expect StartupResult.success == False and SystemStartupFailedEvent published.
        """

        # Replace hardware initializer with a failing variant (local override)
        class FailingHardwareInitializer(FakeHardwareInitializer):
            def verify_all(self) -> bool:
                self.verified = True
                return False  # Force verification failure

        self.hardware = FailingHardwareInitializer()
        self.startup_service = SystemStartupApplicationService(
            hardware_initializer=self.hardware,
            calibration_service=self.calibration,
            event_bus=self.event_bus,
        )

        config = StartupConfig(verify_hardware=True, load_last_calibration=True)
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="CALL",
            target="SystemStartupApplicationService",
            message="startup_system() with failing verify_all()",
            data={"verify_hardware": True, "load_last_calibration": True},
        )
        result = self.startup_service.startup_system(config)

        # Startup must fail
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="SystemStartupApplicationService",
            message="StartupResult.success should be False when verification fails",
            expect=False,
            got=result.success,
        )
        self.assertFalse(result.success)

        # Hardware was initialized and verified, but not accepted
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="FailingHardwareInitializer",
            message="Hardware should be initialized and verified even on failure",
            data={
                "initialized": self.hardware.initialized,
                "verified": self.hardware.verified,
            },
            expect={"initialized": True, "verified": True},
            got={"initialized": self.hardware.initialized, "verified": self.hardware.verified},
        )
        self.assertTrue(self.hardware.initialized)
        self.assertTrue(self.hardware.verified)

        # Calibration must NOT be loaded because verification stopped the sequence
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="FakeCalibrationService",
            message="Calibration should NOT be loaded when verification fails",
            expect=False,
            got=self.calibration.loaded,
        )
        self.assertFalse(self.calibration.loaded)

        # SystemStartupFailedEvent should be published
        self.log_interaction(
            actor="TestSystemLifecycleService",
            action="ASSERT",
            target="EventBus",
            message="SystemStartupFailedEvent should have been published",
            expect=True,
            got=("SystemStartupFailedEvent" in self.received_events),
        )
        self.assertIn("SystemStartupFailedEvent", self.received_events)


if __name__ == "__main__":
    unittest.main()


