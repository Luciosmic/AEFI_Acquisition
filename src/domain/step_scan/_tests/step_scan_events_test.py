import unittest
from datetime import datetime

from domain.step_scan.step_scan import StepScan
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.step_scan.events.scan_started.scan_started import ScanStarted
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_failed.scan_failed import ScanFailed
from domain.step_scan.events.scan_cancelled.scan_cancelled import ScanCancelled

class TestStepScanEvents(unittest.TestCase):
    
    def setUp(self):
        self.config = StepScanConfig(
            scan_zone=ScanZone(x_min=0, x_max=10, y_min=0, y_max=10),
            x_nb_points=2,
            y_nb_points=2,
            scan_pattern=ScanPattern.RASTER,
            stabilization_delay_ms=100,
            averaging_per_position=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
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

    def test_start_with_line_config(self):
        from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
        line = LineScanConfig(center=Position2D(600.0, 600.0), length_mm=100.0, n_points=7, theta_deg=30.0)
        self.scan.start(line)
        events = self.scan.domain_events
        self.assertIsInstance(events[0], ScanStarted)
        self.assertEqual(events[0].config, line)

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
