import sys
from pathlib import Path

import unittest
from unittest.mock import MagicMock, ANY
from typing import Dict, Any

from tool.diagram_friendly_test import DiagramFriendlyTest
from src.application.services.scan_application_service.scan_application_service import ScanApplicationService
from interface.interactive.scan_interactive_port import IScanOutputPort
from application.dtos.scan_dtos import Scan2DConfigDTO
from domain.models.scan.events.scan_events import ScanStarted, ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from domain.models.scan.value_objects.scan_pattern import ScanPattern

sys.path.append(str(Path(__file__).parent.parent.parent))

class TestScanHybridArchitecture(DiagramFriendlyTest):
    """
    Test suite to verify the Hybrid Output Architecture of ScanApplicationService.
    Generates a sequence diagram of the interaction flow.
    """

    def test_scan_execution_hybrid_flow(self):
        # 1. SETUP
        self.log_divider("Setup Phase")
        self.log_interaction("TestAgent", "CREATE", "Infrastructure", "Setup EventBus & Mocks")
        
        event_bus = InMemoryEventBus()
        
        # Mocks
        motion_port = MagicMock()
        acquisition_port = MagicMock()
        scan_executor = MagicMock()
        
        # Output Port Mock (The "Contract" side)
        # We use a real class mock to ensure interface compliance conceptually
        output_port = MagicMock(spec=IScanOutputPort)
        
        # 2. CREATE SERVICE
        self.log_interaction("TestAgent", "CREATE", "ScanApplicationService", "Initialize Service")
        service = ScanApplicationService(motion_port, acquisition_port, event_bus, scan_executor)
        
        # 3. WIRE OUTPUT PORT
        self.log_interaction("TestAgent", "CALL", "ScanApplicationService", "set_output_port", data={"port": "MockOutputPort"})
        service.set_output_port(output_port)

        # 4. PREPARE EXECUTION
        config_dto = Scan2DConfigDTO(
            x_min=0, x_max=10, x_nb_points=5,
            y_min=0, y_max=10, y_nb_points=5,
            scan_pattern="RASTER",
            stabilization_delay_ms=10,
            averaging_per_position=1,
            uncertainty_volts=0.001
        )
        
        # Configure Executor to allow success
        scan_executor.execute.return_value = True

        # 5. EXECUTE SCAN
        self.log_divider("Execution Phase")
        self.log_interaction("TestAgent", "COMMAND", "ScanApplicationService", "execute_scan", data={"pattern": "RASTER"})
        
        # We need to simulate the Executor actually DOING something (publishing events)
        # because the Service relies on the EventBus to trigger the OutputPort.
        # So we use a side_effect on the executorMock.
        def executor_side_effect(scan, trajectory, config):
            self.log_interaction("ScanApplicationService", "CALL", "ScanExecutor", "execute", data={"points": len(trajectory)})
            
            # Simulate Event: Scan Completed (or Point Acquired)
            # We don't simulate ScanStarted here because the Service already did it
            
            # Simulate Event: Scan Completed
            complete_event = ScanCompleted(scan.id, len(trajectory))
            self.log_interaction("ScanExecutor", "PUBLISH", "EventBus", "ScanCompleted")
            event_bus.publish("scancompleted", complete_event)
            return True

        scan_executor.execute.side_effect = executor_side_effect

        # RUN
        success = service.execute_scan(config_dto)

        # 6. VERIFY (The core logic mapping Event -> OutputPort)
        self.log_divider("Verification Phase")
        
        # Check output_port calls
        self.log_interaction("TestAgent", "ASSERT", "MockOutputPort", "Verify present_scan_started called")
        output_port.present_scan_started.assert_called_once()
        
        self.log_interaction("TestAgent", "ASSERT", "MockOutputPort", "Verify present_scan_completed called")
        output_port.present_scan_completed.assert_called_once()

        self.log_interaction("TestAgent", "ASSERT", "ScanApplicationService", "Verify return value", expect=True, got=success)
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
