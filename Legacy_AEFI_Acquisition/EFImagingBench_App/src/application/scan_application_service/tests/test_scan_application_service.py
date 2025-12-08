import unittest
from typing import List
from application.scan_application_service.scan_application_service import ScanApplicationService
from application.dtos.scan_dtos import Scan2DConfigDTO
from infrastructure.tests.mock_ports import MockMotionPort, MockAcquisitionPort
from domain.events.domain_event import DomainEvent
from domain.events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted

class TestScanApplicationService(unittest.TestCase):
    def setUp(self):
        print("[TEST] Setting up service and ports...")
        self.motion_port = MockMotionPort()
        self.acquisition_port = MockAcquisitionPort()
        self.service = ScanApplicationService(
            self.motion_port, self.acquisition_port
        )
        self.events: List[DomainEvent] = []
        self.service.subscribe(self.on_event)
        
    def on_event(self, event: DomainEvent):
        self.events.append(event)
        print(f"[TEST] Event received: {type(event).__name__}")
        
    def test_full_scan_execution(self):
        print("\n" + "="*60)
        print("🧪 [TEST] ScanApplicationService Execution")
        print("="*60)
        
        # Config
        print("[TEST] Configuring scan parameters...")
        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=2,
            y_min=0, y_max=1, y_nb_points=2,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=1,
            uncertainty_volts=1e-6
        )
        
        # Execute
        print("[TEST] Calling execute_scan...")
        
        success = self.service.execute_scan(scan_dto)
        
        # Verify Success
        print("[TEST] Verifying execution success...")
        self.assertTrue(success)
        print("✅ [TEST] Scan returned True")
        
        # Verify Events
        print(f"[TEST] Verifying events (Total: {len(self.events)})...")
        self.assertTrue(any(isinstance(e, ScanStarted) for e in self.events))
        self.assertTrue(any(isinstance(e, ScanCompleted) for e in self.events))
        
        points_acquired = [e for e in self.events if isinstance(e, ScanPointAcquired)]
        self.assertEqual(len(points_acquired), 4) # 2x2 grid
        print(f"✅ [TEST] Acquired {len(points_acquired)} points (Expected 4)")
        
        # Verify Ports
        print(f"[TEST] Verifying motion history (Total: {len(self.motion_port.move_history)})...")
        self.assertEqual(len(self.motion_port.move_history), 4)
        
        print("="*60 + "\n")

if __name__ == '__main__':
    unittest.main()
