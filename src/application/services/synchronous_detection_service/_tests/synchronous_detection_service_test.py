import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from application.services.synchronous_detection_service.synchronous_detection_service import (
    SynchronousDetectionService,
    SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC,
    SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC,
)
from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
)
from domain.shared_kernel.excitation.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)
from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.mocks.adapter_mock_i_synchronous_detection_hardware_port import (
    MockSynchronousDetectionHardwarePort,
)
from infrastructure.persistence.calibration.fake.fake_synchronous_detection_phase_calibration_repository import (
    FakeSynchronousDetectionPhaseCalibrationRepository,
)
from tool.diagram_friendly_test import DiagramFriendlyTest


def make_hardware_signature(**overrides) -> HardwareSignature:
    defaults = dict(
        excitation_board_version="rev-b",
        conditioning_board_version="rev-a",
        sensor_version="v2",
        sensor_serial_number="SN-001",
    )
    defaults.update(overrides)
    return HardwareSignature(**defaults)


class TestSynchronousDetectionService(DiagramFriendlyTest):

    def setUp(self):
        super().setUp()
        self.hardware_signature = make_hardware_signature()
        self.port = MockSynchronousDetectionHardwarePort()
        self.repository = FakeSynchronousDetectionPhaseCalibrationRepository()
        self.event_bus = InMemoryEventBus()
        self.service = SynchronousDetectionService(
            hardware_port=self.port,
            calibration_repository=self.repository,
            hardware_signature=self.hardware_signature,
            event_bus=self.event_bus,
        )

    def _publish_frequency(self, frequency_hz: float) -> None:
        self.event_bus.publish(
            EXCITATION_FREQUENCY_CHANGED_TOPIC, ExcitationFrequencyChanged(frequency_hz=frequency_hz)
        )

    def _spy_on_set_ch3(self) -> MagicMock:
        spy = MagicMock(side_effect=self.port.set_ch3_phase_register)
        self.port.set_ch3_phase_register = spy
        return spy

    # -- sphere-phase derivation ------------------------------------------------

    def test_get_sphere_phases_derives_all_four_spheres_from_ch1_ch2_registers(self):
        # dds1 (ch1) = 0deg, dds2 (ch2) = 180deg
        self.port.registers[1] = 0
        self.port.registers[2] = 32768

        dto = self.service.get_sphere_phases()

        self.assertAlmostEqual(dto.s1_degrees, 0.0)  # dds2 + 180 (complementary)
        self.assertAlmostEqual(dto.s2_degrees, 180.0)  # dds2 direct
        self.assertAlmostEqual(dto.s3_degrees, 180.0)  # dds1 + 180 (complementary)
        self.assertAlmostEqual(dto.s4_degrees, 0.0)  # dds1 direct

    def test_get_sphere_phases_reports_quadrature_enforcement_from_port(self):
        self.port.quadrature_enforced = False

        dto = self.service.get_sphere_phases()

        self.assertFalse(dto.quadrature_enforced)

    # -- delta_phi ("Lock-in Detection Phase Offset") is the LIVE ch4-ch1 delta,
    # not a calibration lookup — ch4 is the lock-in demodulation reference,
    # ch3 is only the register physically written (ch4 rigidly follows it
    # at -90°, see _enforce_dds3_dds4_quadrature) ------------------------------

    def test_delta_phi_reflects_live_ch4_minus_ch1_even_without_any_calibration_data(self):
        # No calibration entries exist at all — delta_phi must still reflect
        # the actual current hardware state (this is what lets a user tune
        # ch3 manually via Hardware Advanced Config — which ch4 follows — and
        # see live feedback).
        self.port.registers[1] = 0  # ch1 = 0deg
        self.port.registers[4] = 16384  # ch4 = 90deg

        dto = self.service.get_sphere_phases()

        self.assertAlmostEqual(dto.delta_phi_corrige_degrees, 90.0)

    def test_delta_phi_updates_immediately_when_ch4_is_manually_changed(self):
        self.port.registers[1] = 0
        self.port.registers[4] = 16384  # 90deg
        self.assertAlmostEqual(self.service.get_sphere_phases().delta_phi_corrige_degrees, 90.0)

        self.port.registers[4] = 0  # e.g. ch3 edited via Hardware Advanced Config, ch4 follows

        self.assertAlmostEqual(self.service.get_sphere_phases().delta_phi_corrige_degrees, 0.0)

    # -- save_calibration_point ---------------------------------------------------

    def test_save_calibration_point_raises_clear_error_when_no_active_frequency(self):
        with self.assertRaises(ValueError):
            self.service.save_calibration_point()

    def test_save_calibration_point_persists_entry_with_injected_signature_and_signed_delta(self):
        self.port.registers[1] = 0  # ch1 = 0deg
        self.port.registers[4] = 16384  # ch4 = 90deg
        self._publish_frequency(5000.0)

        self.service.save_calibration_point()

        entries = self.repository.find_by_hardware_signature(self.hardware_signature)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.hardware_signature, self.hardware_signature)
        self.assertEqual(len(entry.points), 1)
        point = entry.points[0]
        self.assertAlmostEqual(point.frequency_hz, 5000.0)
        self.assertAlmostEqual(point.delta_phi_degrees, 90.0)

    def test_save_calibration_point_publishes_entry_added_event(self):
        received = []
        self.event_bus.subscribe(
            SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC, lambda e: received.append(e)
        )
        self._publish_frequency(1000.0)

        self.service.save_calibration_point()

        self.assertEqual(len(received), 1)

    # -- compensation toggle --------------------------------------------------------

    def test_set_compensation_enabled_true_immediately_writes_corrected_ch3_when_data_exists(self):
        self.repository.add(
            SynchronousDetectionPhaseCalibrationEntry.single(
                self.hardware_signature,
                SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=15.0),
            )
        )
        self.port.registers[1] = 0  # ch1 = 0deg
        self._publish_frequency(1000.0)
        spy = self._spy_on_set_ch3()

        self.service.set_compensation_enabled(True)

        # Target ch4 = ch1 + 15.0; ch4 isn't independently writable (rigidly
        # follows ch3 at -90°), so the service writes ch3 = ch1 + 15.0 + 90.
        spy.assert_called_once_with(PhaseAngle(105.0).to_register())
        self.assertEqual(self.port.registers[3], PhaseAngle(105.0).to_register())

    def test_set_compensation_enabled_false_does_not_write_any_register(self):
        self.repository.add(
            SynchronousDetectionPhaseCalibrationEntry.single(
                self.hardware_signature,
                SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=15.0),
            )
        )
        self._publish_frequency(1000.0)
        spy = self._spy_on_set_ch3()

        self.service.set_compensation_enabled(False)

        spy.assert_not_called()

    def test_set_compensation_enabled_false_restores_manual_configuration(self):
        self.service.set_compensation_enabled(False)

        self.assertEqual(self.port.restore_manual_configuration_calls, 1)

    def test_set_compensation_enabled_true_does_not_restore_manual_configuration(self):
        self.service.set_compensation_enabled(True)

        self.assertEqual(self.port.restore_manual_configuration_calls, 0)

    def test_set_compensation_enabled_publishes_changed_event(self):
        received = []
        self.event_bus.subscribe(
            SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC, lambda e: received.append(e)
        )

        self.service.set_compensation_enabled(True)

        self.assertEqual(len(received), 1)
        self.assertTrue(received[0].enabled)

    # -- reactive re-application on frequency change --------------------------------

    def test_frequency_changed_event_reapplies_correction_only_when_compensation_enabled(self):
        self.repository.add(
            SynchronousDetectionPhaseCalibrationEntry.single(
                self.hardware_signature,
                SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1000.0, delta_phi_degrees=10.0),
            )
        )
        self.repository.add(
            SynchronousDetectionPhaseCalibrationEntry.single(
                self.hardware_signature,
                SynchronousDetectionPhaseCalibrationPoint(frequency_hz=9000.0, delta_phi_degrees=20.0),
            )
        )
        self.port.registers[1] = 0
        self._publish_frequency(1000.0)
        self.service.set_compensation_enabled(True)  # applies once for freq=1000 (delta=10)
        spy = self._spy_on_set_ch3()

        # compensation enabled: a new frequency, nearer the second point, re-applies
        # (target ch4 = ch1 + 20.0 -> writes ch3 = ch1 + 20.0 + 90)
        self._publish_frequency(9000.0)
        spy.assert_called_once_with(PhaseAngle(110.0).to_register())

        # compensation disabled: no further writes on frequency change
        self.service.set_compensation_enabled(False)
        spy.reset_mock()
        self._publish_frequency(1000.0)
        spy.assert_not_called()

    # -- nearest-neighbor tie-break ---------------------------------------------------

    def test_lookup_tie_break_prefers_most_recently_recorded_entry(self):
        # The nearest-neighbor calibration lookup (used internally by
        # _apply_current_correction, not by get_sphere_phases anymore — see
        # the delta_phi tests above) must prefer the most recently recorded
        # entry on an exact frequency-distance tie. Exercised indirectly via
        # set_compensation_enabled(True), which writes the looked-up value.
        older_entry = SynchronousDetectionPhaseCalibrationEntry(
            entry_id=uuid4(),
            hardware_signature=self.hardware_signature,
            points=(SynchronousDetectionPhaseCalibrationPoint(frequency_hz=900.0, delta_phi_degrees=1.0),),
            recorded_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        newer_entry = SynchronousDetectionPhaseCalibrationEntry(
            entry_id=uuid4(),
            hardware_signature=self.hardware_signature,
            points=(SynchronousDetectionPhaseCalibrationPoint(frequency_hz=1100.0, delta_phi_degrees=2.0),),
            recorded_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )
        self.repository.add(older_entry)
        self.repository.add(newer_entry)
        self.port.registers[1] = 0  # ch1 = 0deg
        # current frequency = 1000 -> both points are 100Hz away (tie)
        self._publish_frequency(1000.0)
        spy = self._spy_on_set_ch3()

        self.service.set_compensation_enabled(True)

        # target ch4 = ch1 + 2.0 -> writes ch3 = ch1 + 2.0 + 90
        spy.assert_called_once_with(PhaseAngle(92.0).to_register())


if __name__ == "__main__":
    unittest.main()
