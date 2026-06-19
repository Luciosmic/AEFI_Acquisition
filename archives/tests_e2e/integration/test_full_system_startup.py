"""
E2E Test: Full System Startup

Integration test: Complete system initialization and readiness.
Validates: startup → hardware initialization → services ready.
"""

import unittest
from tests_e2e.base import DiagramFriendlyTest, create_event_bus
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService,
    StartupConfig
)
from infrastructure.fake.hardware.fake_hardware_initialization_port import FakeHardwareInitializationPort


class MockCalibrationService:
    """Simple mock calibration service for testing."""
    def load_last_calibration(self):
        return True


class TestFullSystemStartup(DiagramFriendlyTest):
    """
    Test full system startup sequence.
    """
    
    def setUp(self):
        super().setUp()
        self.log_divider("Setup")
        
        self.event_bus = create_event_bus()
        self.init_port = FakeHardwareInitializationPort()
        self.calibration_service = MockCalibrationService()
        self.startup_service = SystemStartupApplicationService(
            self.init_port,
            self.calibration_service,
            self.event_bus
        )
    
    def test_system_startup_nominal(self):
        """
        Test nominal system startup.
        """
        self.log_divider("System Startup")
        
        config = StartupConfig(
            verify_hardware=True,
            load_last_calibration=True
        )
        
        self.log_interaction("Test", "CALL", "StartupService", "startup_system(config)")
        result = self.startup_service.startup_system(config)
        
        self.log_interaction("Test", "ASSERT", "StartupService", "Startup succeeded",
                           {"result": result.success}, expect=True, got=result.success)
        self.assertTrue(result.success, f"Startup should succeed: {result.errors}")
        
        # Verify hardware was initialized
        self.log_interaction("Test", "ASSERT", "InitPort", "Hardware initialized",
                           {"initialized": self.init_port.initialized}, expect=True,
                           got=self.init_port.initialized)
        self.assertTrue(self.init_port.initialized, "Hardware should be initialized")
    
    def test_system_startup_without_verification(self):
        """
        Test startup without hardware verification.
        """
        self.log_divider("Startup Without Verification")
        
        config = StartupConfig(
            verify_hardware=False,
            load_last_calibration=True
        )
        
        self.log_interaction("Test", "CALL", "StartupService", "startup_system(config)")
        result = self.startup_service.startup_system(config)
        
        self.assertTrue(result.is_success)
        self.assertTrue(self.init_port.initialized)


if __name__ == '__main__':
    unittest.main()

