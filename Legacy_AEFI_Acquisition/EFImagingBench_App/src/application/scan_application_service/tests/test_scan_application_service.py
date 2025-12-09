import unittest
from typing import List
from application.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort
from domain.events.domain_event import DomainEvent
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.tests.diagram_friendly_test import DiagramFriendlyTest

class TestScanApplicationService(DiagramFriendlyTest):
    def setUp(self):
        super().setUp()
        self.log_interaction("Test", "CREATE", "ScanApplicationService", "Setup service and ports")
        
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        self.event_bus = InMemoryEventBus()
        self.events: List[DomainEvent] = []
        
        # Subscribe to relevant events via EventBus
        self.log_interaction("Test", "SUBSCRIBE", "EventBus", "Subscribe to scan events")
        self.event_bus.subscribe('scanstarted', self.on_event)
        self.event_bus.subscribe('scanpointacquired', self.on_event)
        self.event_bus.subscribe('scancompleted', self.on_event)
        
        self.service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus
        )
        
    def on_event(self, event: DomainEvent):
        event_name = type(event).__name__
        self.log_interaction("EventBus", "RECEIVE", "Test", f"Received {event_name}", {"event": event_name})
        self.events.append(event)
        
    def test_full_scan_execution(self):
        self.log_interaction("Test", "START", "ScanApplicationService", "Start full scan execution test")
        
        # Config
        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        self.log_interaction("Test", "CREATE", "Scan2DConfigDTO", "Create scan config", {"pattern": scan_dto.scan_pattern})
        
        # Execute
        self.log_interaction("Test", "COMMAND", "ScanApplicationService", "Execute scan")
        success = self.service.execute_scan(scan_dto)
        
        # Verify Success
        self.log_interaction("Test", "ASSERT", "ScanApplicationService", "Verify execution success", expect=True, got=success)
        self.assertTrue(success)
        
        # Verify Events
        self.log_interaction("Test", "ASSERT", "EventBus", "Verify ScanStarted event")
        self.assertTrue(any(isinstance(e, ScanStarted) for e in self.events))
        
        self.log_interaction("Test", "ASSERT", "EventBus", "Verify ScanCompleted event")
        self.assertTrue(any(isinstance(e, ScanCompleted) for e in self.events))
        
        points_acquired = [e for e in self.events if isinstance(e, ScanPointAcquired)]
        self.log_interaction("Test", "ASSERT", "EventBus", "Verify points acquired", expect=4, got=len(points_acquired))
        self.assertEqual(len(points_acquired), 4) # 2x2 grid
        
        # Verify Ports
        self.log_interaction("Test", "ASSERT", "MotionPort", "Verify move history", expect=4, got=len(self.motion_port.move_history))
        self.assertEqual(len(self.motion_port.move_history), 4)

if __name__ == '__main__':
    unittest.main()
