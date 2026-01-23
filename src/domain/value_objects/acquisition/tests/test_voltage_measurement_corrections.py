"""
Tests for VoltageMeasurement correction methods.
Verifies invariants: amplitude preservation and sign preservation.
"""
import unittest
import math
from datetime import datetime
from domain.value_objects.acquisition.voltage_measurement import VoltageMeasurement


class TestVoltageMeasurementCorrections(unittest.TestCase):
    """Test correction methods preserve invariants."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
    
    def test_apply_noise_correction(self):
        """Test noise correction subtracts offsets correctly."""
        measurement = VoltageMeasurement(
            voltage_x_in_phase=5.0,
            voltage_x_quadrature=3.0,
            voltage_y_in_phase=10.0,
            voltage_y_quadrature=7.0,
            voltage_z_in_phase=2.0,
            voltage_z_quadrature=1.0,
            timestamp=self.timestamp
        )
        
        noise_offset = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=0.5,
            voltage_y_in_phase=2.0,
            voltage_y_quadrature=1.0,
            voltage_z_in_phase=0.5,
            voltage_z_quadrature=0.2,
            timestamp=self.timestamp
        )
        
        corrected = measurement.apply_noise_correction(noise_offset)
        
        self.assertAlmostEqual(corrected.voltage_x_in_phase, 4.0)
        self.assertAlmostEqual(corrected.voltage_x_quadrature, 2.5)
        self.assertAlmostEqual(corrected.voltage_y_in_phase, 8.0)
        self.assertAlmostEqual(corrected.voltage_y_quadrature, 6.0)
        self.assertAlmostEqual(corrected.voltage_z_in_phase, 1.5)
        self.assertAlmostEqual(corrected.voltage_z_quadrature, 0.8)
    
    def test_apply_phase_correction_preserves_amplitude(self):
        """Test that phase correction preserves amplitude."""
        # Test with different angles and amplitudes
        test_cases = [
            (1.0, 1.0, math.pi/4),  # 45 deg, amplitude = sqrt(2)
            (3.0, 4.0, math.atan2(4.0, 3.0)),  # amplitude = 5.0
            (10.0, 0.0, 0.0),  # Already aligned
            (0.0, 5.0, math.pi/2),  # 90 deg
        ]
        
        for i_val, q_val, theta in test_cases:
            with self.subTest(i=i_val, q=q_val, theta=theta):
                measurement = VoltageMeasurement(
                    voltage_x_in_phase=i_val,
                    voltage_x_quadrature=q_val,
                    voltage_y_in_phase=0.0,
                    voltage_y_quadrature=0.0,
                    voltage_z_in_phase=0.0,
                    voltage_z_quadrature=0.0,
                    timestamp=self.timestamp
                )
                
                # Amplitude before rotation
                mag_before = math.sqrt(i_val**2 + q_val**2)
                
                # Apply phase correction
                phase_angles = {'x': theta}
                corrected = measurement.apply_phase_correction(phase_angles)
                
                # Amplitude after rotation
                mag_after = math.sqrt(corrected.voltage_x_in_phase**2 + corrected.voltage_x_quadrature**2)
                
                # Verify amplitude preserved
                self.assertAlmostEqual(
                    mag_before, mag_after,
                    places=10,
                    msg=f"Amplitude not preserved: before={mag_before:.10f}, after={mag_after:.10f}"
                )
                
                # Verify quadrature is zero
                self.assertAlmostEqual(
                    corrected.voltage_x_quadrature, 0.0,
                    places=10,
                    msg=f"Quadrature should be zero: Q={corrected.voltage_x_quadrature:.10f}"
                )
    
    def test_apply_phase_correction_preserves_sign(self):
        """Test that phase correction preserves sign of in-phase component."""
        test_cases = [
            (3.0, 4.0),   # Positive -> I_rotated should be +5.0
            (-3.0, 4.0),  # Negative (quadrant 2) -> I_rotated should be -5.0
            (3.0, -4.0),  # Positive (quadrant 4) -> I_rotated should be +5.0
            (-3.0, -4.0), # Negative (quadrant 3) -> I_rotated should be -5.0
        ]
        
        for i_val, q_val in test_cases:
            with self.subTest(i=i_val, q=q_val):
                measurement = VoltageMeasurement(
                    voltage_x_in_phase=i_val,
                    voltage_x_quadrature=q_val,
                    voltage_y_in_phase=0.0,
                    voltage_y_quadrature=0.0,
                    voltage_z_in_phase=0.0,
                    voltage_z_quadrature=0.0,
                    timestamp=self.timestamp
                )
                
                # Calculate phase angle
                theta = math.atan2(q_val, i_val)
                phase_angles = {'x': theta}
                
                # Apply phase correction
                corrected = measurement.apply_phase_correction(phase_angles)
                
                # Amplitude (always positive)
                mag = math.sqrt(i_val**2 + q_val**2)
                
                # Verify sign preserved
                if abs(i_val) > 1e-10:
                    expected_sign = 1 if i_val >= 0 else -1
                    actual_sign = 1 if corrected.voltage_x_in_phase >= 0 else -1
                    self.assertEqual(
                        expected_sign, actual_sign,
                        msg=f"Sign not preserved: I_orig={i_val}, I_new={corrected.voltage_x_in_phase}, mag={mag}"
                    )
                    
                    # Verify |I_new| = magnitude
                    self.assertAlmostEqual(
                        abs(corrected.voltage_x_in_phase), mag,
                        places=10,
                        msg=f"|I_new| should equal magnitude: |{corrected.voltage_x_in_phase}| != {mag}"
                    )
    
    def test_apply_primary_field_correction(self):
        """Test primary field correction subtracts offsets correctly."""
        measurement = VoltageMeasurement(
            voltage_x_in_phase=10.0,
            voltage_x_quadrature=0.0,  # After phase correction, Q should be 0
            voltage_y_in_phase=15.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=5.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        primary_offset = VoltageMeasurement(
            voltage_x_in_phase=5.0,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=10.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=2.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        corrected = measurement.apply_primary_field_correction(primary_offset)
        
        self.assertAlmostEqual(corrected.voltage_x_in_phase, 5.0)
        self.assertAlmostEqual(corrected.voltage_x_quadrature, 0.0)
        self.assertAlmostEqual(corrected.voltage_y_in_phase, 5.0)
        self.assertAlmostEqual(corrected.voltage_y_quadrature, 0.0)
        self.assertAlmostEqual(corrected.voltage_z_in_phase, 3.0)
        self.assertAlmostEqual(corrected.voltage_z_quadrature, 0.0)
    
    def test_combined_corrections_invariants(self):
        """Test that combined corrections respect invariants."""
        # Signal initial: (3, 4) with amplitude 5.0
        i_initial = 3.0
        q_initial = 4.0
        mag_initial = math.sqrt(i_initial**2 + q_initial**2)
        
        measurement = VoltageMeasurement(
            voltage_x_in_phase=i_initial,
            voltage_x_quadrature=q_initial,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        # 1. Noise subtraction: (3, 4) - (1, 1) = (2, 3)
        noise_offset = VoltageMeasurement(
            voltage_x_in_phase=1.0,
            voltage_x_quadrature=1.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        after_noise = measurement.apply_noise_correction(noise_offset)
        mag_after_noise = math.sqrt(after_noise.voltage_x_in_phase**2 + after_noise.voltage_x_quadrature**2)
        
        # 2. Phase rotation: align (2, 3) on I
        theta = math.atan2(after_noise.voltage_x_quadrature, after_noise.voltage_x_in_phase)
        phase_angles = {'x': theta}
        after_phase = after_noise.apply_phase_correction(phase_angles)
        mag_after_phase = math.sqrt(after_phase.voltage_x_in_phase**2 + after_phase.voltage_x_quadrature**2)
        
        # Verify amplitude preserved by phase rotation
        self.assertAlmostEqual(mag_after_noise, mag_after_phase, places=10)
        
        # Verify quadrature is zero after phase correction
        self.assertAlmostEqual(after_phase.voltage_x_quadrature, 0.0, places=10)
        
        # 3. Primary subtraction: (I_phase, 0) - (I_primary, 0)
        primary_offset = VoltageMeasurement(
            voltage_x_in_phase=0.5,
            voltage_x_quadrature=0.0,
            voltage_y_in_phase=0.0,
            voltage_y_quadrature=0.0,
            voltage_z_in_phase=0.0,
            voltage_z_quadrature=0.0,
            timestamp=self.timestamp
        )
        
        after_primary = after_phase.apply_primary_field_correction(primary_offset)
        
        # After primary, quadrature should remain zero
        self.assertAlmostEqual(after_primary.voltage_x_quadrature, 0.0, places=10)


if __name__ == "__main__":
    unittest.main()
