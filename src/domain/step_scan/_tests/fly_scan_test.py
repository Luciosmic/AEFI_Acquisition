import unittest
from datetime import datetime

from domain.step_scan.fly_scan import FlyScan
from domain.step_scan.services.scan_trajectory_factory.scan_trajectory_factory import ScanTrajectoryFactory
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.line_scan_config.line_scan_config import LineScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_point_result.scan_point_result import ScanPointResult
from domain.step_scan.value_objects.scan_status.scan_status import ScanStatus
from domain.step_scan.events.scan_point_acquired.scan_point_acquired import ScanPointAcquired
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from domain.step_scan.events.scan_paused.scan_paused import ScanPaused
from domain.step_scan.events.scan_resumed.scan_resumed import ScanResumed
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty


def _config(n=3) -> StepScanConfig:
    return StepScanConfig(
        scan_zone=ScanZone(x_min=0, x_max=1, y_min=0, y_max=1),
        x_nb_points=n,
        y_nb_points=n,
        scan_pattern=ScanPattern.RASTER,
        stabilization_delay_ms=0,
        averaging_per_position=1,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
    )


def _result(i: int, position: Position2D = Position2D(x=1.0, y=2.0)) -> ScanPointResult:
    return ScanPointResult(
        position=position,
        measurement=AefiVoltageMeasurement(
            voltage_x_in_phase=0.1 * i, voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.2 * i, voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0, voltage_z_quadrature=0.0,
            timestamp=datetime.now(), uncertainty_estimate_volts=None,
        ),
        point_index=i,
    )


class TestFlyScan(unittest.TestCase):
    def test_auto_completion_after_the_expected_points(self):
        config = _config(3)
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        scan = FlyScan()
        scan.start(config)
        self.assertEqual(scan.status, ScanStatus.RUNNING)
        self.assertEqual(scan.expected_points, 9)

        for i, position in enumerate(trajectory):
            scan.add_point_result(_result(i, position))
            expected = ScanStatus.RUNNING if i < len(trajectory) - 1 else ScanStatus.COMPLETED
            self.assertEqual(scan.status, expected)

        self.assertEqual(len(scan.points), 9)
        events = scan.domain_events
        self.assertIsInstance(events[-1], ScanCompleted)
        self.assertEqual(events[-1].total_points, 9)

    def test_add_point_emits_event(self):
        scan = FlyScan()
        scan.start(_config(2))
        scan.domain_events  # clear ScanStarted

        scan.add_point_result(_result(0))
        events = scan.domain_events

        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ScanPointAcquired)
        self.assertEqual(events[0].scan_id, scan.id)
        self.assertEqual(events[0].point_index, 0)
        self.assertEqual(events[0].position.x, 1.0)

    def test_add_point_refused_when_not_running(self):
        scan = FlyScan()
        with self.assertRaises(ValueError):
            scan.add_point_result(_result(0))

    def test_complete_reports_the_points_it_holds(self):
        scan = FlyScan()
        scan.start(_config(3))
        scan.add_point_result(_result(0))
        scan.add_point_result(_result(1))
        scan.domain_events

        self.assertTrue(scan.complete())

        self.assertEqual(scan.domain_events[-1].total_points, 2)

    def test_pause_and_resume_report_the_points_it_holds(self):
        scan = FlyScan()
        scan.start(_config(3))
        scan.add_point_result(_result(0))
        scan.domain_events

        scan.pause()
        scan.resume()
        paused, resumed = scan.domain_events

        self.assertIsInstance(paused, ScanPaused)
        self.assertEqual(paused.current_point_index, 1)
        self.assertIsInstance(resumed, ScanResumed)
        self.assertEqual(resumed.resume_from_point_index, 1)

    def test_start_with_line_config_expects_its_points(self):
        scan = FlyScan()
        scan.start(LineScanConfig(center=Position2D(600.0, 600.0), length_mm=100.0, n_points=7, theta_deg=30.0))
        self.assertEqual(scan.expected_points, 7)


if __name__ == "__main__":
    unittest.main()
