"""
Unit tests for AutomaticStepScanService

Tests the domain service in isolation using mock ports.
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from domain.services.automatic_step_scan_service import AutomaticStepScanService
from domain.ports.i_motion_port import IMotionPort
from domain.ports.i_acquisition_port import IAcquisitionPort
from domain.value_objects.geometric.position_2d import Position2D
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.scan.step_scan_config import StepScanConfig
from domain.value_objects.scan.scan_zone import ScanZone
from domain.value_objects.scan.scan_mode import ScanMode
from domain.value_objects.scan.scan_status import ScanStatus
from domain.value_objects.measurement_uncertainty import MeasurementUncertainty


@pytest.fixture
def mock_motion_port():
    """Create a mock motion port."""
    port = Mock(spec=IMotionPort)
    port.move_to = Mock()
    port.get_current_position = Mock(return_value=Position2D(x=0.0, y=0.0))
    port.is_moving = Mock(return_value=False)
    port.wait_until_stopped = Mock()
    return port


@pytest.fixture
def mock_acquisition_port():
    """Create a mock acquisition port."""
    port = Mock(spec=IAcquisitionPort)
    port.configure_for_uncertainty = Mock()
    port.is_ready = Mock(return_value=True)
    
    # Mock acquire_sample to return realistic voltage measurements
    def mock_acquire():
        return VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=0.5,
            voltage_y_in_phase=0.8,
            voltage_y_quadrature=0.3,
            voltage_z_in_phase=1.2,
            voltage_z_quadrature=0.6,
            timestamp=datetime.now(),
            uncertainty_estimate_volts=10e-6
        )
    
    port.acquire_sample = Mock(side_effect=mock_acquire)
    return port


@pytest.fixture
def service(mock_motion_port, mock_acquisition_port):
    """Create service with mock ports."""
    return AutomaticStepScanService(mock_motion_port, mock_acquisition_port)


@pytest.fixture
def simple_scan_config():
    """Create a simple scan configuration for testing."""
    return StepScanConfig(
        scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
        x_nb_points=3,
        y_nb_points=3,
        scan_mode=ScanMode.SERPENTINE,
        stabilization_delay_ms=10,
        averaging_per_scan_point=2,
        measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
    )


class TestTrajectoryGeneration:
    """Test trajectory generation algorithms."""
    
    def test_serpentine_trajectory_3x3(self, service, simple_scan_config):
        """Test serpentine trajectory generation for 3x3 grid."""
        trajectory = service._generate_scan_trajectory(simple_scan_config)
        
        # Should have 9 points
        assert len(trajectory) == 9
        
        # First row: left to right (y=0)
        assert trajectory[0] == Position2D(x=0.0, y=0.0)
        assert trajectory[1] == Position2D(x=5.0, y=0.0)
        assert trajectory[2] == Position2D(x=10.0, y=0.0)
        
        # Second row: right to left (y=5)
        assert trajectory[3] == Position2D(x=10.0, y=5.0)
        assert trajectory[4] == Position2D(x=5.0, y=5.0)
        assert trajectory[5] == Position2D(x=0.0, y=5.0)
        
        # Third row: left to right (y=10)
        assert trajectory[6] == Position2D(x=0.0, y=10.0)
        assert trajectory[7] == Position2D(x=5.0, y=10.0)
        assert trajectory[8] == Position2D(x=10.0, y=10.0)
    
    def test_raster_trajectory_3x3(self, service):
        """Test raster trajectory generation for 3x3 grid."""
        config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_mode=ScanMode.RASTER,
            stabilization_delay_ms=10,
            averaging_per_scan_point=2,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
        )
        
        trajectory = service._generate_scan_trajectory(config)
        
        # Should have 9 points
        assert len(trajectory) == 9
        
        # All rows: left to right
        assert trajectory[0] == Position2D(x=0.0, y=0.0)
        assert trajectory[1] == Position2D(x=5.0, y=0.0)
        assert trajectory[2] == Position2D(x=10.0, y=0.0)
        
        assert trajectory[3] == Position2D(x=0.0, y=5.0)
        assert trajectory[4] == Position2D(x=5.0, y=5.0)
        assert trajectory[5] == Position2D(x=10.0, y=5.0)
    
    def test_comb_trajectory_2x2(self, service):
        """Test comb trajectory generation for 2x2 grid."""
        config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=2,
            y_nb_points=2,
            scan_mode=ScanMode.COMB,
            stabilization_delay_ms=10,
            averaging_per_scan_point=2,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
        )
        
        trajectory = service._generate_scan_trajectory(config)
        
        # Should have 4 points
        assert len(trajectory) == 4
        
        # First column (x=0)
        assert trajectory[0] == Position2D(x=0.0, y=0.0)
        assert trajectory[1] == Position2D(x=0.0, y=10.0)
        
        # Second column (x=10)
        assert trajectory[2] == Position2D(x=10.0, y=0.0)
        assert trajectory[3] == Position2D(x=10.0, y=10.0)


class TestMeasurementAveraging:
    """Test measurement averaging logic."""
    
    def test_average_measurements(self, service):
        """Test averaging of voltage measurements."""
        measurements = [
            VoltageMeasurement(
                voltage_x_in_phase=1.0,
                voltage_x_quadrature=0.5,
                voltage_y_in_phase=0.8,
                voltage_y_quadrature=0.3,
                voltage_z_in_phase=1.2,
                voltage_z_quadrature=0.6,
                timestamp=datetime.now(),
                uncertainty_estimate_volts=10e-6
            ),
            VoltageMeasurement(
                voltage_x_in_phase=1.2,
                voltage_x_quadrature=0.7,
                voltage_y_in_phase=1.0,
                voltage_y_quadrature=0.5,
                voltage_z_in_phase=1.4,
                voltage_z_quadrature=0.8,
                timestamp=datetime.now(),
                uncertainty_estimate_volts=10e-6
            ),
        ]
        
        averaged = service._average_measurements(measurements)
        
        # Check averages
        assert averaged.voltage_x_in_phase == pytest.approx(1.1)
        assert averaged.voltage_x_quadrature == pytest.approx(0.6)
        assert averaged.voltage_y_in_phase == pytest.approx(0.9)
        assert averaged.voltage_y_quadrature == pytest.approx(0.4)
        assert averaged.voltage_z_in_phase == pytest.approx(1.3)
        assert averaged.voltage_z_quadrature == pytest.approx(0.7)
    
    def test_average_empty_list_raises_error(self, service):
        """Test that averaging empty list raises ValueError."""
        with pytest.raises(ValueError, match="Cannot average empty list"):
            service._average_measurements([])


class TestScanExecution:
    """Test scan execution workflow."""
    
    def test_execute_simple_scan(self, service, mock_motion_port, mock_acquisition_port, simple_scan_config):
        """Test executing a simple 3x3 scan."""
        scan = service.execute_step_scan(simple_scan_config)
        
        # Check scan completed successfully
        assert scan.status == ScanStatus.COMPLETED
        assert scan.start_time is not None
        assert scan.end_time is not None
        
        # Should have 9 results (3x3 grid)
        assert len(scan.results) == 9
        
        # Check acquisition was configured
        mock_acquisition_port.configure_for_uncertainty.assert_called_once_with(
            simple_scan_config.measurement_uncertainty
        )
        
        # Check motion port was called 9 times (once per point)
        assert mock_motion_port.move_to.call_count == 9
        assert mock_motion_port.wait_until_stopped.call_count == 9
        
        # Check acquisition port was called 18 times (9 points × 2 averaging)
        assert mock_acquisition_port.acquire_sample.call_count == 18
    
    def test_scan_results_structure(self, service, simple_scan_config):
        """Test that scan results have correct structure."""
        scan = service.execute_step_scan(simple_scan_config)
        
        # Check first result structure
        result = scan.results[0]
        assert 'position' in result
        assert 'timestamp' in result
        assert 'voltage' in result
        assert 'point_index' in result
        assert 'uncertainty_estimate_volts' in result
        
        # Check position structure
        assert 'x' in result['position']
        assert 'y' in result['position']
        
        # Check voltage structure
        voltage = result['voltage']
        assert 'x_in_phase' in voltage
        assert 'x_quadrature' in voltage
        assert 'y_in_phase' in voltage
        assert 'y_quadrature' in voltage
        assert 'z_in_phase' in voltage
        assert 'z_quadrature' in voltage


class TestScanLifecycle:
    """Test scan lifecycle management."""
    
    def test_pause_and_resume(self, service, mock_acquisition_port, simple_scan_config):
        """Test pause and resume functionality."""
        # This is a simplified test - in reality, pause happens between points
        # For a real test, we'd need to pause during execution
        
        service.pause_scan()
        assert service._paused is True
        
        service.resume_scan()
        assert service._paused is False
    
    def test_cancel_scan(self, service, mock_motion_port, mock_acquisition_port):
        """Test scan cancellation."""
        config = StepScanConfig(
            scan_zone=ScanZone(x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0),
            x_nb_points=10,  # Larger scan
            y_nb_points=10,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=0,
            averaging_per_scan_point=1,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
        )
        
        # Cancel immediately
        service._cancelled = True
        
        scan = service.execute_step_scan(config)
        
        # Scan should be cancelled
        assert scan.status == ScanStatus.CANCELLED
        
        # Should have stopped early (not all 100 points)
        assert len(scan.results) < 100
    
    def test_scan_status_tracking(self, service, simple_scan_config):
        """Test that scan status is tracked correctly."""
        # Before scan
        assert service.get_scan_status() is None
        
        # During scan (we can't easily test this without threading)
        # After scan
        scan = service.execute_step_scan(simple_scan_config)
        
        # After completion, current_scan is None
        assert service.get_scan_status() is None


class TestValidation:
    """Test configuration validation."""
    
    def test_invalid_config_raises_error(self, service):
        """Test that invalid configuration raises ValueError."""
        # Create invalid config (x_min > x_max)
        invalid_config = StepScanConfig(
            scan_zone=ScanZone(x_min=10.0, x_max=0.0, y_min=0.0, y_max=10.0),
            x_nb_points=3,
            y_nb_points=3,
            scan_mode=ScanMode.SERPENTINE,
            stabilization_delay_ms=10,
            averaging_per_scan_point=2,
            measurement_uncertainty=MeasurementUncertainty(max_uncertainty_volts=10e-6)
        )
        
        with pytest.raises(ValueError, match="Invalid scan configuration"):
            service.execute_step_scan(invalid_config)


class TestMotionIntegration:
    """Test motion port integration."""
    
    def test_move_to_each_position(self, service, mock_motion_port, simple_scan_config):
        """Test that service moves to each position in trajectory."""
        service.execute_step_scan(simple_scan_config)
        
        # Get all move_to calls
        move_calls = mock_motion_port.move_to.call_args_list
        
        # Should have 9 calls for 3x3 grid
        assert len(move_calls) == 9
        
        # Check first few positions (serpentine pattern)
        assert move_calls[0][0][0] == Position2D(x=0.0, y=0.0)
        assert move_calls[1][0][0] == Position2D(x=5.0, y=0.0)
        assert move_calls[2][0][0] == Position2D(x=10.0, y=0.0)
    
    def test_wait_for_stabilization(self, service, mock_motion_port, simple_scan_config):
        """Test that service waits for motion to stop."""
        service.execute_step_scan(simple_scan_config)
        
        # Should wait after each move
        assert mock_motion_port.wait_until_stopped.call_count == 9
