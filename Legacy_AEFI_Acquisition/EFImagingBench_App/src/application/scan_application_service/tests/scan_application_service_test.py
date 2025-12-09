import unittest
from typing import List
import datetime
import sys
from pathlib import Path
from application.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort
from domain.events.domain_event import DomainEvent
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted
from application.event_bus import EventBus

class TestScanApplicationService(unittest.TestCase):
    def setUp(self):
        # Setup log file for this test
        test_name = self._testMethodName
        test_file_path = Path(__file__)
        log_file_path = test_file_path.parent / f"{test_file_path.stem}_log.txt"
        
        self.log_file = open(log_file_path, 'a', encoding='utf-8')
        self._original_stdout = sys.stdout
        
        # Tee output to both console and file
        class TeeOutput:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
                    f.flush()
            def flush(self):
                for f in self.files:
                    f.flush()
        
        sys.stdout = TeeOutput(sys.stdout, self.log_file)
        
        ts = datetime.datetime.now().isoformat()
        print(f"\n{'='*80}")
        print(f"[{ts}] [TestScanApplicationService] SETUP | init service and ports")
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        self.event_bus = EventBus()
        self.events: List[DomainEvent] = []
        
        # Subscribe to relevant events via EventBus
        print(f"[{ts}] [TestScanApplicationService] SUBSCRIBE -> [EventBus] : on 'scanstarted', 'scanpointacquired', 'scancompleted' | expect registered")
        self.event_bus.subscribe('scanstarted', self.on_event)
        self.event_bus.subscribe('scanpointacquired', self.on_event)
        self.event_bus.subscribe('scancompleted', self.on_event)
        
        self.service = ScanApplicationService(
            self.motion_port,
            self.acquisition_port,
            self.event_bus
        )
        self.events: List[DomainEvent] = []
    
    def tearDown(self):
        """Restore stdout and close log file."""
        sys.stdout = self._original_stdout
        if hasattr(self, 'log_file'):
            self.log_file.close()
        
    def on_event(self, event: DomainEvent):
        ts = datetime.datetime.now().isoformat()
        self.events.append(event)
        print(f"[{ts}] [TestScanApplicationService] RECEIVE from [EventBus] : event={type(event).__name__}")
        
    def test_full_scan_execution(self):
        ts = lambda: datetime.datetime.now().isoformat()
        print(f"\n[{ts()}] [TestScanApplicationService] START test_full_scan_execution | Full scan 2x2 RASTER")
        
        # Config
        print(f"[{ts()}] [TestScanApplicationService] CREATE -> [Scan2DConfigDTO] | pattern=RASTER grid=2x2")
        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        
        # Execute
        print(f"[{ts()}] [TestScanApplicationService] CALL -> [ScanApplicationService] : execute_scan | data={scan_dto.scan_pattern} | expect success=True")
        success = self.service.execute_scan(scan_dto)
        
        # Verify Success
        print(f"[{ts()}] [TestScanApplicationService] ASSERT success | expect=True | got={success}")
        self.assertTrue(success)
        
        # Verify Events
        has_started = any(isinstance(e, ScanStarted) for e in self.events)
        has_completed = any(isinstance(e, ScanCompleted) for e in self.events)
        print(f"[{ts()}] [TestScanApplicationService] ASSERT events | expect=ScanStarted | got={has_started}")
        print(f"[{ts()}] [TestScanApplicationService] ASSERT events | expect=ScanCompleted | got={has_completed}")
        self.assertTrue(has_started)
        self.assertTrue(has_completed)
        
        points_acquired = [e for e in self.events if isinstance(e, ScanPointAcquired)]
        expected_points = 4
        print(f"[{ts()}] [TestScanApplicationService] ASSERT points_acquired | expect={expected_points} | got={len(points_acquired)}")
        self.assertEqual(len(points_acquired), expected_points)
        
        # Verify Ports
        expected_moves = 4
        print(f"[{ts()}] [TestScanApplicationService] ASSERT motion_history | expect={expected_moves} moves | got={len(self.motion_port.move_history)}")
        self.assertEqual(len(self.motion_port.move_history), expected_moves)
        
        print(f"[{ts()}] [TestScanApplicationService] PASSED test_full_scan_execution ✓ | Summary: {expected_points} points, {expected_moves} moves")

if __name__ == '__main__':
    unittest.main()
