"""Tests for StepScanConfig value object."""
import pytest
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.scan.scan_mode import ScanMode
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty


def _make_config(scan_zone, **overrides):
    defaults = dict(
        x_nb_points=10,
        y_nb_points=20,
        scan_pattern=ScanMode.SERPENTINE,
        stabilization_delay_ms=100,
        averaging_per_position=5,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=1e-6),
    )
    defaults.update(overrides)
    return StepScanConfig(scan_zone=scan_zone, **defaults)


@pytest.fixture
def valid_scan_zone():
    return ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)


def test_step_scan_config_creation(valid_scan_zone):
    config = _make_config(valid_scan_zone)
    assert config.x_nb_points == 10
    assert config.y_nb_points == 20
    assert config.scan_pattern == ScanMode.SERPENTINE


def test_step_scan_config_immutable(valid_scan_zone):
    config = _make_config(valid_scan_zone)
    with pytest.raises(AttributeError):
        config.x_nb_points = 15


def test_step_scan_config_rejects_zero_x_points(valid_scan_zone):
    with pytest.raises(ValueError, match="x_nb_points must be >= 1"):
        _make_config(valid_scan_zone, x_nb_points=0)


def test_step_scan_config_rejects_zero_y_points(valid_scan_zone):
    with pytest.raises(ValueError, match="y_nb_points must be >= 1"):
        _make_config(valid_scan_zone, y_nb_points=0)


def test_step_scan_config_rejects_negative_stabilization(valid_scan_zone):
    with pytest.raises(ValueError, match="stabilization_delay_ms must be >= 0"):
        _make_config(valid_scan_zone, stabilization_delay_ms=-100)


def test_step_scan_config_rejects_zero_averaging(valid_scan_zone):
    with pytest.raises(ValueError, match="averaging_per_position must be >= 1"):
        _make_config(valid_scan_zone, averaging_per_position=0)


def test_step_scan_config_total_points(valid_scan_zone):
    config = _make_config(valid_scan_zone)
    assert config.total_points() == 200  # 10 * 20


def test_step_scan_config_estimated_duration(valid_scan_zone):
    config = _make_config(valid_scan_zone, stabilization_delay_ms=100, averaging_per_position=5)
    duration = config.estimated_duration_seconds()
    # 200 points * (0.1s stabilization + 5 * 0.1s acquisition) = 200 * 0.6 = 120s
    assert duration == pytest.approx(120.0, rel=0.01)


def test_step_scan_config_accepts_zero_stabilization(valid_scan_zone):
    config = _make_config(valid_scan_zone, stabilization_delay_ms=0)
    assert config.stabilization_delay_ms == 0
