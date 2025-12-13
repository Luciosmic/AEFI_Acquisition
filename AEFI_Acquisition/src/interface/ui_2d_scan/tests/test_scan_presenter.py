import unittest
from unittest.mock import MagicMock, ANY
from typing import Any, Optional
import threading

from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed
from domain.value_objects.scan.step_scan_config import StepScanConfig, ScanPattern
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from datetime import datetime
from uuid import uuid4

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
        if name.startswith('_'):
             return getattr(self.mock, name)
             
        def wrapper(*args, **kwargs):
            self.test_case.log_interaction(
                actor=self.actor_name,
                action="CALL",
                target=self.target_name,
                message=f"Call {name}",
                data={"args": [str(a) for a in args], "kwargs": kwargs}
            )
            result = getattr(self.mock, name)(*args, **kwargs)
            self.test_case.log_interaction(
                actor=self.target_name,
                action="RETURN",
                target=self.actor_name,
                message=f"Return from {name}",
                data={"result": str(result)}
            )
            return result
        return wrapper

class TracingSignal:
    """
    Replaces a pyqtSignal to log emissions.
    """
    def __init__(self, test_case: DiagramFriendlyTest, name: str):
        self.test_case = test_case
        self.name = name
        
    def emit(self, *args):
        self.test_case.log_interaction(
            actor="ScanPresenter",
            action="EMIT",
            target="UI",
            message=f"Signal {self.name}",
            data={"args": [str(a) for a in args]}
        )

class TestScanPresenter(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        
        # 1. Mock the Service
        self.service_mock = TracingMock(self, "ScanPresenter", "ScanApplicationService")
        
        # 2. Create Presenter
        self.log_interaction("Test", "CREATE", "ScanPresenter", "Initialize Presenter")
        self.presenter = ScanPresenter(self.service_mock) # type: ignore
        
        # 3. Replace Signals with TracingSignals
        # We need to do this AFTER init because init might use them (though usually not)
        # But ScanPresenter defines them as class attributes (descriptors).
        # We need to replace the INSTANCE attributes.
        self.presenter.scan_started = TracingSignal(self, "scan_started") # type: ignore
        self.presenter.scan_point_acquired = TracingSignal(self, "scan_point_acquired") # type: ignore
        self.presenter.scan_completed = TracingSignal(self, "scan_completed") # type: ignore
        self.presenter.scan_failed = TracingSignal(self, "scan_failed") # type: ignore
        self.presenter.scan_progress = TracingSignal(self, "scan_progress") # type: ignore

    def test_start_scan_flow(self):
        self.log_interaction("Test", "START", "ScanPresenter", "Start scan flow test")
        
        # 1. User clicks Start (simulated call to start_scan)
        params = {
            'x_min': 0, 'x_max': 1, 'x_nb_points': 2,
            'y_min': 0, 'y_max': 1, 'y_nb_points': 2,
            'scan_pattern': 'RASTER'
        }
        
        # Mock threading to run synchronously for the test
        # We patch threading.Thread to just call the target immediately
        with unittest.mock.patch('threading.Thread') as mock_thread:
            def side_effect(target, args):
                target(*args)
                return MagicMock()
            mock_thread.side_effect = side_effect
            
            self.log_interaction("UI", "CALL", "ScanPresenter", "start_scan", data=params)
            self.presenter.start_scan(params)
            
        # 2. Service emits ScanStarted (simulated)
        scan_id = uuid4()
        scan_zone = ScanZone(0, 1, 0, 1)
        uncertainty = MeasurementUncertainty(1e-6)
        config = StepScanConfig(
            scan_zone=scan_zone,
            x_nb_points=2, y_nb_points=2,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=0,
            averaging_per_position=1,
            measurement_uncertainty=uncertainty
        )
        
        event_started = ScanStarted(scan_id=scan_id, config=config)
        
        self.log_interaction("ScanApplicationService", "PUBLISH", "ScanPresenter", "ScanStarted Event")
        # Manually invoke the handler as if the service called the callback
        self.presenter._on_domain_event(event_started)
        
        # 3. Service emits ScanPointAcquired
        event_point = ScanPointAcquired(
            scan_id=scan_id,
            point_index=0,
            position=Position2D(0, 0),
            measurement=VoltageMeasurement(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        )
        
        self.log_interaction("ScanApplicationService", "PUBLISH", "ScanPresenter", "ScanPointAcquired Event")
        self.presenter._on_domain_event(event_point)
        
        # 4. Service emits ScanCompleted
        event_completed = ScanCompleted(scan_id=scan_id, total_points=4)
        
        self.log_interaction("ScanApplicationService", "PUBLISH", "ScanPresenter", "ScanCompleted Event")
        self.presenter._on_domain_event(event_completed)

if __name__ == '__main__':
    unittest.main()
