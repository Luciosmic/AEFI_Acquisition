import unittest
from unittest.mock import MagicMock, ANY
from typing import Any, Optional

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from infrastructure.execution.step_scan_executor import StepScanExecutor
from domain.models.scan.aggregates.step_scan import StepScan
from domain.models.scan.value_objects.scan_trajectory import ScanTrajectory
from domain.models.scan.value_objects.step_scan_config import StepScanConfig, ScanPattern
from domain.shared.value_objects.position_2d import Position2D
from domain.models.aefi_device.value_objects.acquisition.acquisition_sample import AcquisitionSample

class TracingMock:
    """
    Wrapper around a mock that logs interactions to the DiagramFriendlyTest.
    """
    def __init__(self, test_case: DiagramFriendlyTest, actor_name: str, target_name: str):
        self.test_case = test_case
        self.actor_name = actor_name
        self.target_name = target_name
        self.mock = MagicMock()
        
    def __getattr__(self, name):
        # Return a callable that logs the call and delegates to the mock
        if name.startswith('_'):
             return getattr(self.mock, name)
             
        def wrapper(*args, **kwargs):
            # Log the CALL
            self.test_case.log_interaction(
                actor=self.actor_name,
                action="CALL",
                target=self.target_name,
                message=f"Call {name}",
                data={"args": [str(a) for a in args], "kwargs": kwargs}
            )
            
            # Execute mock
            result = getattr(self.mock, name)(*args, **kwargs)
            
            # Log the RETURN (optional, but good for completeness)
            self.test_case.log_interaction(
                actor=self.target_name,
                action="RETURN",
                target=self.actor_name,
                message=f"Return from {name}",
                data={"result": str(result)}
            )
            return result
        return wrapper

class TestStepScanExecutor(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        
        # Setup Tracing Mocks
        # We want to see StepScanExecutor calling these ports
        self.motion_port = TracingMock(self, "StepScanExecutor", "MotionPort")
        self.acquisition_port = TracingMock(self, "StepScanExecutor", "AcquisitionPort")
        self.event_bus = TracingMock(self, "StepScanExecutor", "EventBus")
        
        # Configure Mock Returns
        self.acquisition_port.mock.acquire_sample.return_value = AcquisitionSample(
            voltage_x_in_phase=1.0, voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0, voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
            timestamp=0.0
        )
        
        # Create Executor
        self.log_interaction("Test", "CREATE", "StepScanExecutor", "Initialize Executor")
        self.executor = StepScanExecutor(
            motion_port=self.motion_port, # type: ignore
            acquisition_port=self.acquisition_port, # type: ignore
            event_bus=self.event_bus # type: ignore
        )

    def test_execute_nominal_case(self):
        self.log_interaction("Test", "START", "StepScanExecutor", "Start nominal execution test")
        
        # Prepare Data
        # Prepare Data
        from domain.models.scan.value_objects.scan_zone import ScanZone
        from domain.models.scan.value_objects.measurement_uncertainty import MeasurementUncertainty
        
        scan_zone = ScanZone(x_min=0, x_max=1, y_min=0, y_max=1)
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=1e-6)
        
        config = StepScanConfig(
            scan_zone=scan_zone,
            x_nb_points=2,
            y_nb_points=1,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=0,
            averaging_per_position=1,
            measurement_uncertainty=uncertainty
        )
        trajectory = ScanTrajectory([
            Position2D(0, 0),
            Position2D(1, 0)
        ])
        scan = StepScan()
        # Manually set ID if needed for assertions, or just let it be random
        # scan.id = ...
        scan.start(config)
        
        # Execute
        self.log_interaction("Test", "CALL", "StepScanExecutor", "execute")
        success = self.executor.execute(scan, trajectory, config)
        
        # Assert
        self.log_interaction("Test", "ASSERT", "StepScanExecutor", "Check success", expect="True", got=str(success))
        self.assertTrue(success)
        
        # Verify Interactions (via TracingMock logs)
        # We expect 2 moves, 2 acquisitions, and event publications
        
        # Verify Event Bus calls specifically (using the underlying mock for assertion convenience)
        self.log_interaction("Test", "ASSERT", "EventBus", "Check publish calls")
        # We expect at least ScanStarted, 2 ScanPointAcquired, ScanCompleted
        self.assertTrue(self.event_bus.mock.publish.call_count >= 4)

if __name__ == '__main__':
    unittest.main()
