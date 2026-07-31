"""
Integration test: differential measurement (baseline without excitation).

Proves — using the existing mock stack, no hardware — that
ExcitationConfigurationService.mute() actually eliminates the
excitation-dependent offset for the baseline window, and that unmute()
restores it for the normal (excited) window. This is the mechanism the
whole differential-measurement feature rests on; see
_system/ops/tasks.md ("Mesure différentielle").

Stack: RandomNoiseAcquisitionPort(noise_std=0.0) [deterministic] wrapped by
ExcitationAwareAcquisitionPort, driven by MockExcitationPort — the same
composition main.py uses for mock/mock hardware config (src/main.py:198-218).
"""
import threading
import unittest

from application.services.scan_application_service.scan_application_service import ScanApplicationService
from application.services.scan_application_service.dtos.scan_dtos import Scan2DConfigDTO
from application.services.aefi_acquisition_service.aefi_acquisition_service import AefiAcquisitionService
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.execution.thread_pool_task_runner import ThreadPoolTaskRunner
from infrastructure.execution.event_bus_motion_synchronizer import EventBusMotionSynchronizer
from infrastructure.mocks.adapter_mock_i_motion_port import MockMotionPort
from infrastructure.mocks.adapter_mock_i_aefi_acquisition_executor import MockAefiAcquisitionExecutor
from infrastructure.mocks.adapter_mock_i_acquisition_port import RandomNoiseAcquisitionPort
from infrastructure.mocks.adapter_mock_i_excitation_port import MockExcitationPort
from infrastructure.mocks.adapter_mock_excitation_aware_acquisition import ExcitationAwareAcquisitionPort
from infrastructure.mocks.cube_sensor_field_simulator import CubeSensorFieldSimulator
from infrastructure.mocks._tests.point_charge_field_simulator_test import make_synthetic_config


class TestScanDifferentialModeIntegration(unittest.TestCase):
    EXCITATION_LEVEL_PERCENT = 80.0

    def setUp(self):
        self.event_bus = InMemoryEventBus()
        self.motion_port = MockMotionPort(event_bus=self.event_bus, motion_delay_ms=1)

        self.mock_excitation_port = MockExcitationPort()
        self.excitation_service = ExcitationConfigurationService(
            excitation_port=self.mock_excitation_port, event_bus=self.event_bus
        )
        # Excitation ON before the scan starts, exactly as a real acquisition
        # would have it configured — the loop must mute it for the baseline
        # window and restore this exact state for the excited window.
        self.excitation_service.set_excitation(
            ExcitationMode.X_DIR,
            level_s1_s2_percent=self.EXCITATION_LEVEL_PERCENT,
            level_s3_s4_percent=self.EXCITATION_LEVEL_PERCENT,
            frequency=1000.0,
        )

        # Synthetic geometry (not the real hardware config, identity
        # rotation) so the expected offset below is deterministic.
        self.field_simulator = CubeSensorFieldSimulator.from_config(make_synthetic_config())

        base_acquisition_port = RandomNoiseAcquisitionPort(noise_std=0.0, seed=42)
        self.acquisition_port = ExcitationAwareAcquisitionPort(
            base_acquisition_port=base_acquisition_port,
            excitation_port=self.mock_excitation_port,
            field_simulator=self.field_simulator,
        )
        # No sensor rotation configured -> source frame == sensor frame,
        # offset vector applies unrotated.

        continuous_service = AefiAcquisitionService(
            MockAefiAcquisitionExecutor(self.event_bus), self.acquisition_port
        )
        self.service = ScanApplicationService(
            self.motion_port,
            continuous_service,
            self.event_bus,
            task_runner=ThreadPoolTaskRunner(),
            motion_sync=EventBusMotionSynchronizer(self.event_bus),
            excitation_service=self.excitation_service,
        )

    def _wait_for_completion(self, timeout: float = 10.0) -> bool:
        done = threading.Event()
        self.event_bus.subscribe("scancompleted", lambda e: done.set())
        return done.wait(timeout=timeout)

    def test_mute_eliminates_excitation_offset_for_baseline_window(self):
        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=5,
            uncertainty_volts=1e-6,
            differential_mode=True,
            differential_settle_delay_ms=20,
        )

        self.assertTrue(self.service.execute_scan(scan_dto))
        self.assertTrue(self._wait_for_completion(), "Scan did not complete within timeout")

        scan = self.service._current_scan
        self.assertEqual(len(scan.points), 1)
        point = scan.points[0]

        # Same levels on both DDS pairs -> the field's x component cancels by
        # symmetry, only y carries an offset (see PointChargeFieldSimulator/
        # CubeSensorFieldSimulator tests for the direction derivation); z
        # stays 0 (identity rotation, coplanar cube in this synthetic config).
        expected_ex, expected_ey, expected_ez = self.field_simulator.compute_axis_voltages(
            self.EXCITATION_LEVEL_PERCENT, self.EXCITATION_LEVEL_PERCENT
        )
        self.assertAlmostEqual(expected_ex, 0.0)
        self.assertNotAlmostEqual(expected_ey, 0.0)
        self.assertAlmostEqual(expected_ez, 0.0)

        # 1. Baseline was acquired with excitation muted -> raw signal, no offset.
        self.assertIsNotNone(point.baseline_measurement)
        self.assertAlmostEqual(point.baseline_measurement.voltage_x_in_phase, 0.0)
        self.assertAlmostEqual(point.baseline_measurement.voltage_y_in_phase, 0.0)
        self.assertAlmostEqual(point.baseline_measurement.voltage_z_in_phase, 0.0)

        # 2. Excited measurement carries the expected excitation field offset.
        self.assertAlmostEqual(point.measurement.voltage_x_in_phase, expected_ex)
        self.assertAlmostEqual(point.measurement.voltage_y_in_phase, expected_ey)

        # 3. The delta reconstructs exactly the offset vector (noise_std=0.0).
        delta_x = point.measurement.voltage_x_in_phase - point.baseline_measurement.voltage_x_in_phase
        delta_y = point.measurement.voltage_y_in_phase - point.baseline_measurement.voltage_y_in_phase
        self.assertAlmostEqual(delta_x, expected_ex)
        self.assertAlmostEqual(delta_y, expected_ey)

        # 4. Excitation is restored to its pre-scan state after the point (no
        # lingering mute) — mute()/unmute() must be balanced.
        self.assertAlmostEqual(self.mock_excitation_port.last_parameters.level_s1_s2.value, self.EXCITATION_LEVEL_PERCENT)

    def test_baseline_is_forwarded_to_output_port_as_its_own_channel(self):
        """The live plot only showed the excited sample — mute/unmute is too
        fast to see on hardware (~0.4s), so the baseline needs to be visible
        on screen too, not just recorded for export. Guards the
        `baseline_<axis>_<component>` keys scan_application_service.py adds
        to the ScanPointAcquired progress payload."""
        received = []
        self.service.set_output_port(_RecordingOutputPort(received))

        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=5,
            uncertainty_volts=1e-6,
            differential_mode=True,
            differential_settle_delay_ms=20,
        )

        self.assertTrue(self.service.execute_scan(scan_dto))
        self.assertTrue(self._wait_for_completion(), "Scan did not complete within timeout")

        self.assertEqual(len(received), 1)
        _, _, data = received[0]
        point = self.service._current_scan.points[0]
        self.assertEqual(data["value"]["baseline_x_in_phase"], point.baseline_measurement.voltage_x_in_phase)
        self.assertEqual(data["value"]["baseline_y_in_phase"], point.baseline_measurement.voltage_y_in_phase)
        self.assertEqual(data["value"]["x_in_phase"], point.measurement.voltage_x_in_phase)

    def test_non_differential_scan_has_no_baseline(self):
        scan_dto = Scan2DConfigDTO(
            x_min=0, x_max=1, x_nb_points=1,
            y_min=0, y_max=1, y_nb_points=1,
            scan_pattern="RASTER",
            stabilization_delay_ms=0,
            averaging_per_position=3,
            uncertainty_volts=1e-6,
            differential_mode=False,
        )

        self.assertTrue(self.service.execute_scan(scan_dto))
        self.assertTrue(self._wait_for_completion(), "Scan did not complete within timeout")

        point = self.service._current_scan.points[0]
        self.assertIsNone(point.baseline_measurement)


class _RecordingOutputPort:
    """Minimal IScanOutputPort fake — records present_scan_progress calls only."""

    def __init__(self, sink: list):
        self._sink = sink

    def present_scan_progress(self, current_point_index, total_points, point_data):
        self._sink.append((current_point_index, total_points, point_data))

    def __getattr__(self, name):
        return lambda *a, **k: None


if __name__ == "__main__":
    unittest.main()
