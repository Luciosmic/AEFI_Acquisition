"""Tests for StepScanConfig value object."""
import pytest
from .step_scan_config import StepScanConfig
from .scan_zone import ScanZone
from .scan_mode import ScanMode
from ..acquisition.acquisition_parameters import AcquisitionParameters

@pytest.fixture
def valid_scan_zone():
    """Fixture providing a valid scan zone."""
    return ScanZone(x_min=10.0, x_max=50.0, y_min=20.0, y_max=60.0)

@pytest.fixture
def valid_acquisition_params():
    """Fixture providing valid acquisition parameters."""
    return AcquisitionParameters(
        averaging_adc=10,
        adc_gains={1: 0, 2: 1, 3: 2, 4: 3},
        sampling_rate=1000.0
    )

def test_step_scan_config_creation(valid_scan_zone, valid_acquisition_params):
    """Test creating a valid step scan configuration."""
    config = StepScanConfig(
        scan_zone=valid_scan_zone,
        x_nb_points=10,
        y_nb_points=20,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=100,
        averaging_per_scan_point=5,
        acquisition_params=valid_acquisition_params
    )
    
    assert config.x_nb_points == 10
    assert config.y_nb_points == 20
    assert config.scan_mode == ScanMode.SERPENTINE

def test_step_scan_config_immutable(valid_scan_zone, valid_acquisition_params):
    """Test that configuration is immutable."""
    config = StepScanConfig(
        scan_zone=valid_scan_zone,
        x_nb_points=10,
        y_nb_points=20,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=100,
        averaging_per_scan_point=5,
        acquisition_params=valid_acquisition_params
    )
    
    with pytest.raises(AttributeError):
        config.x_nb_points = 15

def test_step_scan_config_rejects_zero_x_points(valid_scan_zone, valid_acquisition_params):
    """Test that x_nb_points must be >= 1."""
    with pytest.raises(ValueError, match="x_nb_points must be >= 1"):
        StepScanConfig(
            scan_zone=valid_scan_zone,
            x_nb_points=0,
            y_nb_points=20,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=100,
            averaging_per_scan_point=5,
            acquisition_params=valid_acquisition_params
        )

def test_step_scan_config_rejects_zero_y_points(valid_scan_zone, valid_acquisition_params):
    """Test that y_nb_points must be >= 1."""
    with pytest.raises(ValueError, match="y_nb_points must be >= 1"):
        StepScanConfig(
            scan_zone=valid_scan_zone,
            x_nb_points=10,
            y_nb_points=0,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=100,
            averaging_per_scan_point=5,
            acquisition_params=valid_acquisition_params
        )

def test_step_scan_config_rejects_negative_stabilization(valid_scan_zone, valid_acquisition_params):
    """Test that stabilization_delay_ms must be >= 0."""
    with pytest.raises(ValueError, match="stabilization_delay_ms must be >= 0"):
        StepScanConfig(
            scan_zone=valid_scan_zone,
            x_nb_points=10,
            y_nb_points=20,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=-100,
            averaging_per_scan_point=5,
            acquisition_params=valid_acquisition_params
        )

def test_step_scan_config_rejects_zero_averaging(valid_scan_zone, valid_acquisition_params):
    """Test that averaging_per_scan_point must be >= 1."""
    with pytest.raises(ValueError, match="averaging_per_scan_point must be >= 1"):
        StepScanConfig(
            scan_zone=valid_scan_zone,
            x_nb_points=10,
            y_nb_points=20,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=100,
            averaging_per_scan_point=0,
            acquisition_params=valid_acquisition_params
        )

def test_step_scan_config_total_points(valid_scan_zone, valid_acquisition_params):
    """Test total_points() calculation."""
    config = StepScanConfig(
        scan_zone=valid_scan_zone,
        x_nb_points=10,
        y_nb_points=20,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=100,
        averaging_per_scan_point=5,
        acquisition_params=valid_acquisition_params
    )
    
    assert config.total_points() == 200  # 10 * 20

def test_step_scan_config_estimated_duration(valid_scan_zone, valid_acquisition_params):
    """Test estimated_duration_seconds() calculation."""
    config = StepScanConfig(
        scan_zone=valid_scan_zone,
        x_nb_points=10,
        y_nb_points=20,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=100,  # 0.1s per point
        averaging_per_scan_point=5,  # 5 measurements at 1000 Hz = 0.005s
        acquisition_params=valid_acquisition_params
    )
    
    duration = config.estimated_duration_seconds()
    
    # Expected: 200 points * (0.1 + 0.005) = 21 seconds
    assert duration == pytest.approx(21.0, rel=0.01)

def test_step_scan_config_accepts_zero_stabilization(valid_scan_zone, valid_acquisition_params):
    """Test that zero stabilization delay is accepted."""
    config = StepScanConfig(
        scan_zone=valid_scan_zone,
        x_nb_points=10,
        y_nb_points=20,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=0,
        averaging_per_scan_point=5,
        acquisition_params=valid_acquisition_params
    )
    
    assert config.stabilization_delay_ms == 0

