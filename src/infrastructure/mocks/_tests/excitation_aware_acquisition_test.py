"""
Unit tests for ExcitationAwareAcquisitionPort.
"""

import unittest

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_level import ExcitationLevel

from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.cube_sensor_field_simulator import CubeSensorFieldSimulator
from infrastructure.mocks._tests.point_charge_field_simulator_test import make_synthetic_config


def make_aware_port(excitation_port=None) -> ExcitationAwareAcquisitionPort:
    base_port = RandomNoiseAcquisitionPort(noise_std=0.0, seed=42)  # deterministic: no noise
    simulator = CubeSensorFieldSimulator.from_config(make_synthetic_config())
    return ExcitationAwareAcquisitionPort(base_port, excitation_port, field_simulator=simulator)


class TestExcitationAwareAcquisitionPort(unittest.TestCase):
    def test_acquire_without_excitation(self):
        port = make_aware_port()
        measurement = port.acquire_sample()
        self.assertIsInstance(measurement, AefiVoltageMeasurement)

    def test_acquire_with_zero_level_excitation_has_no_offset(self):
        excitation_port = MockExcitationPort()
        port = make_aware_port(excitation_port)
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(0.0),
            level_s3_s4=ExcitationLevel(0.0),
            frequency=1000.0,
        )
        excitation_port.apply_excitation(params)

        base = RandomNoiseAcquisitionPort(noise_std=0.0, seed=42).acquire_sample()
        measurement = port.acquire_sample()
        self.assertAlmostEqual(measurement.voltage_x_in_phase, base.voltage_x_in_phase)
        self.assertAlmostEqual(measurement.voltage_y_in_phase, base.voltage_y_in_phase)

    def test_mode_has_no_effect_on_the_simulated_field(self):
        """No object-under-test is modeled — only the two DDS levels matter."""
        excitation_port = MockExcitationPort()
        port = make_aware_port(excitation_port)

        results = {}
        for mode in (ExcitationMode.X_DIR, ExcitationMode.Y_DIR, ExcitationMode.CIRCULAR_PLUS):
            params = ExcitationParameters(
                mode=mode,
                level_s1_s2=ExcitationLevel(100.0),
                level_s3_s4=ExcitationLevel(0.0),
                frequency=1000.0,
            )
            excitation_port.apply_excitation(params)
            m = port.acquire_sample()
            results[mode] = (m.voltage_x_in_phase, m.voltage_y_in_phase)

        values = list(results.values())
        self.assertTrue(all(v == values[0] for v in values))

    def test_quadrature_untouched_by_excitation(self):
        excitation_port = MockExcitationPort()
        port = make_aware_port(excitation_port)
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(100.0),
            level_s3_s4=ExcitationLevel(0.0),
            frequency=1000.0,
        )
        excitation_port.apply_excitation(params)

        base = RandomNoiseAcquisitionPort(noise_std=0.0, seed=42).acquire_sample()
        measurement = port.acquire_sample()
        self.assertAlmostEqual(measurement.voltage_x_quadrature, base.voltage_x_quadrature)
        self.assertAlmostEqual(measurement.voltage_y_quadrature, base.voltage_y_quadrature)
        self.assertAlmostEqual(measurement.voltage_z_quadrature, base.voltage_z_quadrature)

    def test_manual_excitation_parameters(self):
        port = make_aware_port(excitation_port=None)
        params = ExcitationParameters(
            mode=ExcitationMode.X_DIR,
            level_s1_s2=ExcitationLevel(100.0),
            level_s3_s4=ExcitationLevel(0.0),
            frequency=1000.0,
        )
        port.set_excitation_parameters(params)

        measurement = port.acquire_sample()
        self.assertIsInstance(measurement, AefiVoltageMeasurement)

    def test_is_ready(self):
        self.assertTrue(make_aware_port().is_ready())

    def test_get_quantification_noise(self):
        noise = make_aware_port().get_quantification_noise()
        self.assertIsInstance(noise, float)
        self.assertGreaterEqual(noise, 0.0)


if __name__ == '__main__':
    unittest.main()
