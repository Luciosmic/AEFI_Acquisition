import unittest

from domain.step_scan.step_scan import StepScan
from domain.step_scan.value_objects.step_scan_config.step_scan_config import StepScanConfig
from domain.step_scan.value_objects.scan_zone.scan_zone import ScanZone
from domain.step_scan.value_objects.scan_pattern.scan_pattern import ScanPattern
from domain.step_scan.value_objects.scan_axis.scan_axis import ScanAxis
from domain.shared_kernel.value_objects.measurement_uncertainty.measurement_uncertainty import MeasurementUncertainty


def _config(**overrides):
    defaults = dict(
        scan_zone=ScanZone(x_min=0, x_max=1, y_min=0, y_max=1),
        x_nb_points=1,
        y_nb_points=1,
        scan_pattern=ScanPattern.RASTER,
        stabilization_delay_ms=0,
        averaging_per_position=1,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
    )
    defaults.update(overrides)
    return StepScanConfig(**defaults)


class TestStepScanLifecycleGuards(unittest.TestCase):
    """Locks in the domain-observability audit fixes: pause() on a final
    scan and repeat complete() must be observable to the caller (raise /
    return False), never a silent no-op."""

    def test_pause_on_completed_scan_raises(self):
        scan = StepScan()
        scan.start(_config())
        scan.complete()
        with self.assertRaises(ValueError):
            scan.pause()

    def test_pause_on_paused_scan_is_a_silent_noop(self):
        """The one case that IS legitimate idempotence."""
        scan = StepScan()
        scan.start(_config())
        scan.pause()
        scan.pause()  # must not raise

    def test_complete_returns_false_when_already_completed(self):
        scan = StepScan()
        scan.start(_config())
        self.assertTrue(scan.complete())
        self.assertFalse(scan.complete())


class TestStepScanConfigCombAxisGuard(unittest.TestCase):
    def test_comb_with_x_axis_raises(self):
        with self.assertRaises(ValueError):
            _config(scan_pattern=ScanPattern.COMB, scan_axis=ScanAxis.X)

    def test_comb_with_y_axis_is_allowed(self):
        _config(scan_pattern=ScanPattern.COMB, scan_axis=ScanAxis.Y)  # must not raise


class TestMeasurementUncertaintyWarnings(unittest.TestCase):
    def test_out_of_range_uncertainty_is_valid_but_carries_a_warning(self):
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=1e-2)  # > 1mV
        self.assertTrue(len(uncertainty.warnings) >= 1)

    def test_typical_uncertainty_has_no_warnings(self):
        uncertainty = MeasurementUncertainty(max_uncertainty_volts=1e-6)
        self.assertEqual(uncertainty.warnings, [])


if __name__ == "__main__":
    unittest.main()
