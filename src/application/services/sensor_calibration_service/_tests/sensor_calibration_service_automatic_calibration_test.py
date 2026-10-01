"""
Automatic sensor calibration, end to end on the mock stack (no hardware):
the cube sensor is simulated mounted at known angles, the excitation mock is
mode-aware (X_DIR / Y_DIR), so the fitted angles must be the mounted ones.
"""

import threading
import time
import unittest
from uuid import uuid4

from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.sensor_calibration_service.ports.i_sensor_calibration_output_port import (
    ISensorCalibrationOutputPort,
)
from application.services.sensor_calibration_service.sensor_calibration_service import SensorCalibrationService
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.fake.fake_thread_pool_task_runner import FakeThreadPoolTaskRunner
from infrastructure.mocks._tests.point_charge_field_simulator_test import make_synthetic_config
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.cube_sensor_field_simulator import CubeSensorFieldSimulator
from infrastructure.persistence.calibration.fake.fake_sensor_calibration_repository import (
    FakeSensorCalibrationRepository,
)

IDEAL_ANGLES = SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.0)
MOUNTED_ANGLES = {"theta_x": 36.4, "theta_y": 43.1, "theta_z": 2.5}  # the "real" mounting, unknown to the service


class RecordingOutputPort(ISensorCalibrationOutputPort):
    def __init__(self):
        self.steps, self.succeeded, self.failed = [], [], []

    def present_automatic_calibration_step(self, message):
        self.steps.append(message)

    def present_automatic_calibration_succeeded(self, result):
        self.succeeded.append(result)

    def present_automatic_calibration_failed(self, reason):
        self.failed.append(reason)


class SilentAcquisitionService:
    """Acquisition that never delivers a sample (ADC unplugged)."""

    def __init__(self):
        self.running = False

    def start_acquisition(self, config):
        self.running = True

    def stop_acquisition(self):
        self.running = False

    def is_acquisition_running(self):
        return self.running


class BufferedAcquisitionService:
    """Back-to-back acquisition whose samples reach the event bus LAG samples
    late (serial/USB buffering): at each excitation change, several samples
    acquired under the previous excitation are still in transit."""

    LAG = 3

    def __init__(self, event_bus, acquisition_port):
        self._event_bus = event_bus
        self._port = acquisition_port
        self._stop = threading.Event()
        self._thread = None

    def start_acquisition(self, config):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        acquisition_id, buffer, index = uuid4(), [], 0
        while not self._stop.is_set():
            buffer.append(AefiVoltageSampleAcquired(acquisition_id=acquisition_id, sample_index=index, sample=self._port.acquire_sample()))
            index += 1
            if len(buffer) > self.LAG:
                self._event_bus.publish("aefivoltagesampleacquired", buffer.pop(0))
            time.sleep(0.002)

    def stop_acquisition(self):
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._thread = None

    def is_acquisition_running(self):
        return self._thread is not None


class TestAutomaticSensorCalibration(unittest.TestCase):
    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.excitation_port = MockExcitationPort()
        self.excitation_service = ExcitationConfigurationService(self.excitation_port, self.event_bus)
        config = make_synthetic_config()
        config["sensor"]["calibration"]["sources_to_sensor_rotation"] = MOUNTED_ANGLES
        acquisition_port = ExcitationAwareAcquisitionPort(
            RandomNoiseAcquisitionPort(noise_std=0.0, seed=1),
            self.excitation_port,
            field_simulator=CubeSensorFieldSimulator.from_config(config),
        )
        self.acquisition_port = acquisition_port
        self.acquisition_service = AefiAcquisitionService(MockAefiAcquisitionExecutor(self.event_bus), acquisition_port)
        self.output = RecordingOutputPort()

    def _make_service(self, acquisition_service=None, sample_timeout_s=10.0):
        service = SensorCalibrationService(
            calibration_repository=FakeSensorCalibrationRepository(),
            sensor_mounting_id=uuid4(),
            source_geometry_entry_id=uuid4(),
            default_angles=IDEAL_ANGLES,
            event_bus=self.event_bus,
            excitation_service=self.excitation_service,
            acquisition_service=acquisition_service or self.acquisition_service,
            task_runner=FakeThreadPoolTaskRunner(),
            settle_delay_s=0.0,
            samples_per_step=3,
            sample_timeout_s=sample_timeout_s,
        )
        service.set_output_port(self.output)
        return service

    def _operator_excitation(self, level=40.0, mode=ExcitationMode.CIRCULAR_PLUS):
        self.excitation_service.set_excitation(mode, level, level, 1000.0)

    def test_fits_the_mounted_angles_and_applies_them_as_trial(self):
        self._operator_excitation()
        service = self._make_service()

        service.start_automatic_calibration()

        self.assertEqual(self.output.failed, [])
        self.assertEqual(len(self.output.succeeded), 1)
        active = service.get_active_rotation()
        self.assertTrue(active.is_trial)
        self.assertAlmostEqual(active.theta_x_degrees, MOUNTED_ANGLES["theta_x"], places=1)
        self.assertAlmostEqual(active.theta_y_degrees, MOUNTED_ANGLES["theta_y"], places=1)
        self.assertAlmostEqual(active.theta_z_degrees, MOUNTED_ANGLES["theta_z"], places=1)
        self.assertLess(self.output.succeeded[0].misalignment_x_degrees, 0.1)
        self.assertIsNone(service.get_latest_calibration(), "a fit is a trial, never recorded on its own")

    def test_samples_buffered_across_an_excitation_change_are_not_averaged(self):
        """Several stale samples in transit at each change: only samples that
        started after the excitation settled may enter the mean, otherwise the
        baseline inherits the operator's (circular) excitation and the fit drifts."""
        self._operator_excitation()
        service = self._make_service(acquisition_service=BufferedAcquisitionService(self.event_bus, self.acquisition_port))

        service.start_automatic_calibration()

        self.assertEqual(self.output.failed, [])
        result = self.output.succeeded[0]
        self.assertLess(result.misalignment_x_degrees, 0.01)
        self.assertAlmostEqual(result.response_separation_degrees, 90.0, places=2)
        self.assertAlmostEqual(result.theta_z_degrees, MOUNTED_ANGLES["theta_z"], places=2)

    def test_restores_the_operator_excitation_and_stops_the_acquisition_it_started(self):
        self._operator_excitation(level=40.0, mode=ExcitationMode.CIRCULAR_PLUS)
        before = self.excitation_service.get_current_parameters()

        self._make_service().start_automatic_calibration()

        self.assertEqual(self.excitation_service.get_current_parameters(), before)
        self.assertEqual(self.excitation_port.last_parameters, before)
        self.assertFalse(self.acquisition_service.is_acquisition_running())

    def test_reports_the_three_measurement_steps(self):
        self._operator_excitation()
        self._make_service().start_automatic_calibration()
        self.assertEqual(len(self.output.steps), 3)

    def test_zero_excitation_level_is_refused_without_touching_the_excitation(self):
        self._operator_excitation(level=0.0)
        before = self.excitation_port.last_parameters

        self._make_service().start_automatic_calibration()

        self.assertEqual(len(self.output.failed), 1)
        self.assertIn("niveau d'excitation", self.output.failed[0])
        self.assertIs(self.excitation_port.last_parameters, before)

    def test_refused_while_a_scan_controls_the_excitation(self):
        self._operator_excitation()
        self.excitation_service.take_control("scan")
        before = self.excitation_port.last_parameters

        self._make_service().start_automatic_calibration()

        self.assertEqual(len(self.output.failed), 1)
        self.assertIn("scan", self.output.failed[0])
        self.assertIs(self.excitation_port.last_parameters, before)
        self.assertEqual(self.excitation_service.get_controller(), "scan")

    def test_excitation_is_controlled_during_the_run_and_released_after(self):
        self._operator_excitation()
        controllers = []
        self.event_bus.subscribe("excitationcontrolchanged", lambda e: controllers.append(e.controller))

        self._make_service().start_automatic_calibration()

        self.assertEqual(controllers, ["calibration automatique du capteur", None])
        self.assertIsNone(self.excitation_service.get_controller())

    def test_missing_samples_fail_and_still_restore_the_excitation(self):
        self._operator_excitation()
        before = self.excitation_service.get_current_parameters()
        silent = SilentAcquisitionService()

        self._make_service(acquisition_service=silent, sample_timeout_s=0.1).start_automatic_calibration()

        self.assertEqual(len(self.output.failed), 1)
        self.assertIn("échantillons", self.output.failed[0])
        self.assertEqual(self.excitation_service.get_current_parameters(), before)
        self.assertFalse(silent.is_acquisition_running())
        self.assertIsNone(self.excitation_service.get_controller())


if __name__ == "__main__":
    unittest.main()
