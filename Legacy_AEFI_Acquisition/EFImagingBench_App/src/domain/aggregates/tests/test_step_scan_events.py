import unittest
from uuid import UUID
from datetime import datetime
from ...aggregates.step_scan import StepScan
from ...value_objects.scan.step_scan_config import StepScanConfig
from ...value_objects.scan.scan_zone import ScanZone
from ...value_objects.scan.scan_mode import ScanMode
from ...value_objects.measurement_uncertainty import MeasurementUncertainty
from ...value_objects.scan.scan_point_result import ScanPointResult
from ...value_objects.geometric.position_2d import Position2D
from ...value_objects.acquisition.voltage_measurement import VoltageMeasurement
from ...events.scan_events import ScanStarted, ScanPointAcquired, ScanCompleted, ScanFailed, ScanCancelled

class TestStepScanEvents(unittest.TestCase):
    
    def setUp(self):
        self.config = StepScanConfig(
            scan_zone=ScanZone(x_min=0, x_max=10, y_min=0, y_max=10),
            x_nb_points=2,
            y_nb_points=2,
            scan_mode=ScanMode.RASTER,
            stabilization_delay_ms=100,
            averaging_per_scan_point=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6)
        )
        self.scan = StepScan()

    def test_start_emits_event(self):
        print("\n=== Testing Start Event ===")
        self.scan.start(self.config)
        events = self.scan.domain_events
        print(f"Emitted {len(events)} events: {[type(e).__name__ for e in events]}")
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ScanStarted)
        self.assertEqual(events[0].scan_id, self.scan.id)
        self.assertEqual(events[0].config, self.config)

    def test_add_point_emits_event(self):
        print("\n=== Testing Add Point Event ===")
        self.scan.start(self.config)
        self.scan.domain_events # Clear start event
        
        result = ScanPointResult(
            position=Position2D(x=1.0, y=2.0),
            measurement=VoltageMeasurement(
                voltage_x_in_phase=0.123, voltage_x_quadrature=0.001,
                voltage_y_in_phase=0.456, voltage_y_quadrature=0.002,
                voltage_z_in_phase=0.789, voltage_z_quadrature=0.003,
                timestamp=datetime.now(), uncertainty_estimate_volts=1e-6
            ),
            point_index=0
        )
        
        print(f"Adding Point: Index={result.point_index}, Pos=({result.position.x}, {result.position.y})")
        print(f"              Meas X={result.measurement.voltage_x_in_phase}V, Y={result.measurement.voltage_y_in_phase}V")
        
        self.scan.add_point_result(result)
        events = self.scan.domain_events
        print(f"Emitted {len(events)} events: {[type(e).__name__ for e in events]}")
        
        if events and isinstance(events[0], ScanPointAcquired):
            e = events[0]
            print(f"  -> Event Details: ScanID={e.scan_id}")
            print(f"                    Index={e.point_index}")
            print(f"                    Position=({e.position.x}, {e.position.y})")
            print(f"                    Measurement X_InPhase={e.measurement.voltage_x_in_phase}V")
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ScanPointAcquired)
        self.assertEqual(events[0].scan_id, self.scan.id)
        self.assertEqual(events[0].point_index, 0)
        self.assertEqual(events[0].position.x, 1.0)

    def test_complete_emits_event(self):
        print("\n=== Testing Complete Event ===")
        self.scan.start(self.config)
        self.scan.complete()
        events = self.scan.domain_events
        print(f"Emitted {len(events)} events: {[type(e).__name__ for e in events]}")
        
        # Should have Start and Complete
        self.assertEqual(len(events), 2)
        self.assertIsInstance(events[1], ScanCompleted)
        self.assertEqual(events[1].scan_id, self.scan.id)

    def test_fail_emits_event(self):
        print("\n=== Testing Fail Event ===")
        self.scan.start(self.config)
        self.scan.fail("Error")
        events = self.scan.domain_events
        print(f"Emitted {len(events)} events: {[type(e).__name__ for e in events]}")
        
        self.assertIsInstance(events[1], ScanFailed)
        self.assertEqual(events[1].reason, "Error")

    def test_cancel_emits_event(self):
        print("\n=== Testing Cancel Event ===")
        self.scan.start(self.config)
        self.scan.cancel()
        events = self.scan.domain_events
        print(f"Emitted {len(events)} events: {[type(e).__name__ for e in events]}")
        
        self.assertIsInstance(events[1], ScanCancelled)

if __name__ == '__main__':
    unittest.main()
