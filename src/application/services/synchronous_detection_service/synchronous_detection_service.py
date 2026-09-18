import logging
from typing import Optional

from application.services.synchronous_detection_service.ports.i_synchronous_detection_hardware_port import (
    ISynchronousDetectionHardwarePort,
)
from application.services.synchronous_detection_service.dtos.sphere_phases_dto import SpherePhasesDTO
from application.services.synchronous_detection_service.i_api_synchronous_detection_service import (
    IApiSynchronousDetectionService,
)
from application.services.excitation_configuration_service.excitation_configuration_service import (
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
)
from domain.calibration.calibration import Calibration
from domain.calibration.repositories.i_synchronous_detection_phase_calibration_repository import (
    ISynchronousDetectionPhaseCalibrationRepository,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.excitation.value_objects.phase_angle import PhaseAngle
from domain.shared_kernel.excitation.value_objects.sphere_id import SphereId

SYNCHRONOUS_DETECTION_PHASE_CALIBRATION_ENTRY_ADDED_TOPIC = "synchronousdetectionphasecalibrationentryadded"
SYNCHRONOUS_DETECTION_COMPENSATION_ENABLED_CHANGED_TOPIC = "synchronousdetectioncompensationenabledchanged"

logger = logging.getLogger(__name__)


class SynchronousDetectionService(IApiSynchronousDetectionService):
    """
    Application Service pour la calibration de phase de détection synchrone
    (ch3/ch4, référence de démodulation) relative à l'excitation (ch1/ch2).
    """

    def __init__(
        self,
        hardware_port: ISynchronousDetectionHardwarePort,
        calibration_repository: ISynchronousDetectionPhaseCalibrationRepository,
        hardware_signature: HardwareSignature,
        event_bus: IDomainEventBus,
    ) -> None:
        self._hardware_port = hardware_port
        self._calibration_repository = calibration_repository
        self._hardware_signature = hardware_signature
        self._event_bus = event_bus
        self._calibration = Calibration.reconstitute(
            calibration_repository.load_compensation_enabled()
        )
        self._current_frequency_hz: float = 0.0
        self._event_bus.subscribe(EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_frequency_changed)

    def _on_frequency_changed(self, event) -> None:
        self._current_frequency_hz = event.frequency_hz
        if self._calibration.synchronous_detection_compensation_enabled:
            self._apply_current_correction()

    def get_sphere_phases(self) -> SpherePhasesDTO:
        registers = self._hardware_port.get_all_channel_phase_registers()
        dds1_phase = PhaseAngle.from_register(registers[1])
        dds2_phase = PhaseAngle.from_register(registers[2])
        dds4_phase = PhaseAngle.from_register(registers[4])

        # Live delta (ch4 - ch1), the "Lock-in Detection Phase Offset" — ch4
        # is the lock-in demodulation reference that must align with the
        # excitation (ch1) phase. Not the static calibration-table lookup:
        # this is what lets a user manually tune ch3 (which ch4 rigidly
        # follows at -90°, see _enforce_dds3_dds4_quadrature) via Hardware
        # Advanced Config and see immediate feedback.
        current_delta_phi_degrees = dds4_phase.difference_from(dds1_phase)

        return SpherePhasesDTO(
            s1_degrees=SphereId.S1.derive_phase(dds1_phase, dds2_phase).degrees,
            s2_degrees=SphereId.S2.derive_phase(dds1_phase, dds2_phase).degrees,
            s3_degrees=SphereId.S3.derive_phase(dds1_phase, dds2_phase).degrees,
            s4_degrees=SphereId.S4.derive_phase(dds1_phase, dds2_phase).degrees,
            delta_phi_corrige_degrees=current_delta_phi_degrees,
            quadrature_enforced=self._hardware_port.is_quadrature_enforcement_enabled(),
            lock_in_gain_below_default=(
                self._hardware_port.get_lock_in_gain() < self._hardware_port.get_default_lock_in_gain()
            ),
        )

    def enable_lock_in_detection(self) -> None:
        """Force ch3/ch4's gain back to the recommended default — the
        Excitation panel's "Enable Lock-In Detection" toggle."""
        logger.info("SynchronousDetectionService: Command enable_lock_in_detection")
        self._hardware_port.reset_lock_in_gain_to_default()

    def save_calibration_point(self) -> None:
        logger.info(
            "SynchronousDetectionService: Command save_calibration_point frequency_hz=%s",
            self._current_frequency_hz,
        )
        if self._current_frequency_hz <= 0:
            raise ValueError(
                "Aucune fréquence d'excitation active — impossible d'enregistrer un point de calibration"
            )

        registers = self._hardware_port.get_all_channel_phase_registers()
        ch1_phase = PhaseAngle.from_register(registers[1])
        ch4_phase = PhaseAngle.from_register(registers[4])
        raw_delta_phi = ch4_phase.difference_from(ch1_phase)

        point = SynchronousDetectionPhaseCalibrationPoint(
            frequency_hz=self._current_frequency_hz, delta_phi_degrees=raw_delta_phi
        )
        entry = self._calibration.record_synchronous_detection_phase_entry(
            self._hardware_signature, point
        )
        self._calibration_repository.add(entry)
        self._publish_domain_events()

    def is_compensation_enabled(self) -> bool:
        return self._calibration.synchronous_detection_compensation_enabled

    def set_compensation_enabled(self, enabled: bool) -> None:
        logger.info(
            "SynchronousDetectionService: Command set_compensation_enabled enabled=%s",
            enabled,
        )
        self._calibration.set_synchronous_detection_compensation_enabled(enabled)
        self._calibration_repository.save_compensation_enabled(enabled)
        self._publish_domain_events()
        if enabled:
            self._apply_current_correction()
        else:
            # Compensation's writes never persist to ad9106_last_config.json
            # (see ISynchronousDetectionHardwarePort.set_ch3_phase_register) —
            # reloading it here restores whatever the user last manually set.
            logger.debug(
                "SynchronousDetectionService: restoring manual ch3 configuration (compensation disabled)"
            )
            self._hardware_port.restore_manual_configuration()

    def _lookup_current_correction(self) -> Optional[float]:
        """
        Nearest-neighbor par fréquence parmi tous les points de toutes les
        entrées enregistrées pour la signature matérielle courante.
        Tie-break : à écart de fréquence égal, l'entrée la plus récemment
        enregistrée gagne.
        """
        entries = self._calibration_repository.find_by_hardware_signature(self._hardware_signature)
        candidates = [
            (point, entry.recorded_at) for entry in entries for point in entry.points
        ]
        if not candidates:
            return None

        best_point, _ = min(
            candidates,
            key=lambda candidate: (
                abs(candidate[0].frequency_hz - self._current_frequency_hz),
                -candidate[1].timestamp(),
            ),
        )
        return best_point.delta_phi_degrees

    def _apply_current_correction(self) -> None:
        delta_phi = self._lookup_current_correction()
        if delta_phi is None:
            logger.debug(
                "SynchronousDetectionService: no calibration data yet for hardware signature, skipping correction"
            )
            return  # pas encore de donnée de calibration pour cette signature

        registers = self._hardware_port.get_all_channel_phase_registers()
        ch1_phase = PhaseAngle.from_register(registers[1])
        # Target: ch4 = ch1 + delta_phi. Ch4 isn't independently writable —
        # it rigidly follows ch3 at -90° (_enforce_dds3_dds4_quadrature) — so
        # solve for the ch3 register that makes that hold: ch3 - 90 = ch1 +
        # delta_phi  =>  ch3 = ch1 + delta_phi + 90.
        new_ch3_phase = PhaseAngle(ch1_phase.degrees + delta_phi + 90.0)
        self._hardware_port.set_ch3_phase_register(new_ch3_phase.to_register())

    def _publish_domain_events(self) -> None:
        for event in self._calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
