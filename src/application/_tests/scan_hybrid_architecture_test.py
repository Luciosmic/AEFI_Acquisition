import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import unittest
from domain.shared_kernel.operation_result import OperationResult
from tool.diagram_friendly_test import DiagramFriendlyTest
from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.ports.i_scan_output_port import IScanOutputPort
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.execution.fake.fake_event_bus_motion_synchronizer import FakeEventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import MockAcquisitionPort
from unittest.mock import MagicMock


class TestScanHybridArchitecture(DiagramFriendlyTest):
    """
    Test suite to verify the Hybrid Output Architecture of ScanApplicationService.
    Uses FakeThreadPoolTaskRunner (synchronous) + FakeEventBusMotionSynchronizer
    so no thread coordination is needed in assertions.
    """

    def test_scan_execution_hybrid_flow(self):
        # 1. SETUP
        self.log_divider("Setup Phase")
        self.log_interaction("TestAgent", "CREATE", "Infrastructure", "Setup EventBus & Mocks")

        event_bus = InMemoryEventBus()
        motion_port = MockMotionPort(event_bus=event_bus, motion_delay_ms=0)
        acquisition_port = MockAcquisitionPort()

        # 5×5 = 25 points — pre-program 25 successful motion results
        motion_sync = FakeEventBusMotionSynchronizer(
            [OperationResult.ok(None)] * 25
        )
        task_runner = FakeThreadPoolTaskRunner()

        # Output Port Mock (The "Contract" side)
        output_port = MagicMock(spec=IScanOutputPort)

        # 2. CREATE SERVICE
        self.log_interaction("TestAgent", "CREATE", "ScanApplicationService", "Initialize Service")
        service = ScanApplicationService(
            motion_port, acquisition_port, event_bus,
            task_runner=task_runner,
            motion_sync=motion_sync,
        )

        # 3. WIRE OUTPUT PORT
        self.log_interaction("TestAgent", "CALL", "ScanApplicationService", "set_output_port", data={"port": "MockOutputPort"})
        service.set_output_port(output_port)

        # 4. PREPARE EXECUTION
        config_dto = Scan2DConfigDTO(
            x_min=0, x_max=10, x_nb_points=5,
            y_min=0, y_max=10, y_nb_points=5,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=0.001,
        )

        # 5. EXECUTE SCAN (synchronous via FakeThreadPoolTaskRunner)
        self.log_divider("Execution Phase")
        self.log_interaction("TestAgent", "COMMAND", "ScanApplicationService", "execute_scan", data={"pattern": "RASTER"})

        success = service.execute_scan(config_dto)

        # 6. VERIFY
        self.log_divider("Verification Phase")

        self.log_interaction("TestAgent", "ASSERT", "MockOutputPort", "Verify present_scan_started called")
        output_port.present_scan_started.assert_called_once()

        self.log_interaction("TestAgent", "ASSERT", "MockOutputPort", "Verify present_scan_completed called")
        output_port.present_scan_completed.assert_called_once()

        self.log_interaction("TestAgent", "ASSERT", "ScanApplicationService", "Verify return value", expect=True, got=success)
        self.assertTrue(success)


if __name__ == '__main__':
    unittest.main()
