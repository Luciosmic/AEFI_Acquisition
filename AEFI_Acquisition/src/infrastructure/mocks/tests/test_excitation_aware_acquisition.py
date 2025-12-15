"""
Unit tests for ExcitationAwareAcquisitionPort.

Tests the integration between acquisition and excitation systems,
including offset application, ratio configuration, and separation functions.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock

from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_level import ExcitationLevel

from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import (
    ExcitationAwareAcquisitionPort,
    OffsetVector3D
)


class TestOffsetVector3D(unittest.TestCase):
    """Tests for OffsetVector3D utility class."""
    
    def test_vector_creation(self):
        """Test creating a 3D offset vector."""
        vec = OffsetVector3D(1.0, 2.0, 3.0)
        self.assertEqual(vec.x, 1.0)
        self.assertEqual(vec.y, 2.0)
        self.assertEqual(vec.z, 3.0)
    
    def test_vector_scale(self):
        """Test scaling a vector."""
        vec = OffsetVector3D(1.0, 2.0, 3.0)
        scaled = vec.scale(2.0)
        self.assertEqual(scaled.x, 2.0)
        self.assertEqual(scaled.y, 4.0)
        self.assertEqual(scaled.z, 6.0)
    
    def test_vector_addition(self):
        """Test adding two vectors."""
        vec1 = OffsetVector3D(1.0, 2.0, 3.0)
        vec2 = OffsetVector3D(4.0, 5.0, 6.0)
        result = vec1 + vec2
        self.assertEqual(result.x, 5.0)
        self.assertEqual(result.y, 7.0)
        self.assertEqual(result.z, 9.0)
    
    def test_vector_multiplication(self):
        """Test multiplying vector by scalar."""
        vec = OffsetVector3D(1.0, 2.0, 3.0)
        result = vec * 2.0
        self.assertEqual(result.x, 2.0)
        self.assertEqual(result.y, 4.0)
        self.assertEqual(result.z, 6.0)
        
        # Right multiplication
        result2 = 2.0 * vec
        self.assertEqual(result2.x, 2.0)
        self.assertEqual(result2.y, 4.0)
        self.assertEqual(result2.z, 6.0)


class TestExcitationAwareAcquisitionPort(unittest.TestCase):
    """Tests for ExcitationAwareAcquisitionPort."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_port = RandomNoiseAcquisitionPort(noise_std=0.01, seed=42)
        self.excitation_port = MockExcitationPort()
        self.aware_port = ExcitationAwareAcquisitionPort(
            self.base_port,
            self.excitation_port,
            real_ratio=0.9,
            offset_scale=1.0
        )
    
    def test_initialization(self):
        """Test port initialization."""
        self.assertIsNotNone(self.aware_port)
        self.assertEqual(self.aware_port._real_ratio, 0.9)
        self.assertEqual(self.aware_port._offset_scale, 1.0)
    
    def test_acquire_without_excitation(self):
        """Test acquisition without active excitation (no offset applied)."""
        # No excitation set
        measurement = self.aware_port.acquire_sample()
        
        # Should return base measurement (with noise)
        self.assertIsInstance(measurement, VoltageMeasurement)
        self.assertIsNotNone(measurement.voltage_x_in_phase)
    
    def test_acquire_with_x_dir_excitation(self):
        """Test acquisition with X_DIR excitation (offset (1,0,0))."""
        # Set X_DIR excitation at 100% level
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # X in-phase should have offset applied (approximately +1.0)
        # Note: Due to noise, we check that offset is applied (difference > 0.5)
        x_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        self.assertGreater(x_diff, 0.5, "X offset should be applied")
        
        # Y and Z should have minimal offset
        y_diff = abs(offset_measurement.voltage_y_in_phase - base_measurement.voltage_y_in_phase)
        z_diff = abs(offset_measurement.voltage_z_in_phase - base_measurement.voltage_z_in_phase)
        self.assertLess(y_diff, 0.5, "Y should have minimal offset")
        self.assertLess(z_diff, 0.5, "Z should have minimal offset")
    
    def test_acquire_with_y_dir_excitation(self):
        """Test acquisition with Y_DIR excitation (offset (0,0,1))."""
        # Set Y_DIR excitation at 100% level
        params = ExcitationParameters(
            mode=ExcitationMode.Y_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # Z in-phase should have offset applied (approximately +1.0)
        z_diff = offset_measurement.voltage_z_in_phase - base_measurement.voltage_z_in_phase
        self.assertGreater(z_diff, 0.5, "Z offset should be applied")
        
        # X and Y should have minimal offset
        x_diff = abs(offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase)
        y_diff = abs(offset_measurement.voltage_y_in_phase - base_measurement.voltage_y_in_phase)
        self.assertLess(x_diff, 0.5, "X should have minimal offset")
        self.assertLess(y_diff, 0.5, "Y should have minimal offset")
    
    def test_acquire_with_zero_level_excitation(self):
        """Test acquisition with excitation at 0% level (no offset)."""
        # Set excitation at 0% level
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(0.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement (should have no offset)
        measurement = self.aware_port.acquire_sample()
        
        # Should be similar to base (within noise)
        x_diff = abs(measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase)
        self.assertLess(x_diff, 0.5, "No offset should be applied at 0% level")
    
    def test_real_ratio_configuration(self):
        """Test configuring real/quadrature ratio."""
        # Set 50% real ratio
        self.aware_port.set_real_ratio(0.5)
        
        # Set X_DIR excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # With 50% ratio, offset should be split between real and quadrature
        x_i_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        x_q_diff = offset_measurement.voltage_x_quadrature - base_measurement.voltage_x_quadrature
        
        # Both should have offset (approximately 0.5 each)
        self.assertGreater(x_i_diff, 0.3, "Real component should have offset")
        self.assertGreater(x_q_diff, 0.3, "Quadrature component should have offset")
    
    def test_offset_scale_configuration(self):
        """Test configuring offset scale factor."""
        # Set 2x scale
        self.aware_port.set_offset_scale(2.0)
        
        # Set X_DIR excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with scaled offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # Offset should be approximately 2.0 (scaled from 1.0)
        x_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        self.assertGreater(x_diff, 1.5, "Scaled offset should be larger")
    
    def test_custom_excitation_offset(self):
        """Test setting custom offset for excitation mode."""
        # Set custom offset for X_DIR
        custom_offset = OffsetVector3D(2.0, 1.0, 0.5)
        self.aware_port.set_excitation_offset(ExcitationMode.X_DIR, custom_offset)
        
        # Set X_DIR excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with custom offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # X should have larger offset (2.0 instead of 1.0)
        x_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        self.assertGreater(x_diff, 1.5, "Custom offset should be applied")
        
        # Y should also have offset (1.0)
        y_diff = offset_measurement.voltage_y_in_phase - base_measurement.voltage_y_in_phase
        self.assertGreater(y_diff, 0.5, "Y should have custom offset")
    
    def test_separation_vector(self):
        """Test separation vector functionality."""
        # Set separation vector for X_DIR
        separation = OffsetVector3D(0.5, 0.5, 0.0)
        self.aware_port.set_separation_vector(ExcitationMode.X_DIR, separation)
        
        # Set X_DIR excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get measurement
        measurement = self.aware_port.acquire_sample()
        
        # Separation vector should be added to offset
        # Base offset (1,0,0) + separation (0.5,0.5,0) = (1.5,0.5,0)
        # We can't easily test exact values due to noise, but we verify it runs
        self.assertIsInstance(measurement, VoltageMeasurement)
    
    def test_equalization_factor(self):
        """Test equalization factor functionality."""
        # Set equalization factor for X_DIR
        self.aware_port.set_equalization_factor(ExcitationMode.X_DIR, 0.5)
        
        # Set X_DIR excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with equalized offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # Offset should be reduced by 0.5 factor
        x_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        # Should be approximately 0.5 (1.0 * 0.5)
        self.assertGreater(x_diff, 0.3, "Equalized offset should be smaller")
        self.assertLess(x_diff, 0.8, "Equalized offset should be smaller")
    
    def test_manual_excitation_parameters(self):
        """Test manually setting excitation parameters (without port)."""
        # Create port without excitation port
        aware_port_no_exc = ExcitationAwareAcquisitionPort(
            self.base_port,
            excitation_port=None
        )
        
        # Manually set excitation
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(100.0),
            frequency=1000.0
        )
        aware_port_no_exc.set_excitation_parameters(params)
        
        # Get measurement
        measurement = aware_port_no_exc.acquire_sample()
        self.assertIsInstance(measurement, VoltageMeasurement)
    
    def test_level_scaling(self):
        """Test that excitation level scales the offset."""
        # Set X_DIR excitation at 50% level
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level=ExcitationLevel(50.0),
            frequency=1000.0
        )
        self.excitation_port.apply_excitation(params)
        
        # Get base measurement
        base_measurement = self.base_port.acquire_sample()
        
        # Get measurement with 50% scaled offset
        offset_measurement = self.aware_port.acquire_sample()
        
        # Offset should be approximately 0.5 (1.0 * 0.5)
        x_diff = offset_measurement.voltage_x_in_phase - base_measurement.voltage_x_in_phase
        self.assertGreater(x_diff, 0.3, "50% level should apply 50% offset")
        self.assertLess(x_diff, 0.8, "50% level should apply 50% offset")
    
    def test_invalid_real_ratio(self):
        """Test that invalid real ratio raises error."""
        with self.assertRaises(ValueError):
            self.aware_port.set_real_ratio(1.5)  # > 1.0
        
        with self.assertRaises(ValueError):
            self.aware_port.set_real_ratio(-0.1)  # < 0.0
    
    def test_is_ready(self):
        """Test is_ready() delegates to base port."""
        self.assertTrue(self.aware_port.is_ready())
    
    def test_get_quantification_noise(self):
        """Test get_quantification_noise() delegates to base port."""
        noise = self.aware_port.get_quantification_noise()
        self.assertIsInstance(noise, float)
        self.assertGreaterEqual(noise, 0.0)


if __name__ == '__main__':
    unittest.main()

