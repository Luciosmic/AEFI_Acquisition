import logging
import queue
import time
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np

from application.services.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.services.aefi_acquisition_service.i_api_aefi_acquisition_service import (
    IApiAefiAcquisitionService,
)
# ponytail: direct Application-Service-to-Application-Service dependency,
# same precedent as ScanApplicationService (mute/unmute) — no event exists
# for "excitation control requested".
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
)
from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import (
    ActiveSensorRotationDTO,
    AutomaticSensorCalibrationDTO,
    SensorCalibrationDTO,
)
from application.services.sensor_calibration_service.i_api_sensor_calibration_service import (
    IApiSensorCalibrationService,
)
from application.services.sensor_calibration_service.ports.i_sensor_calibration_output_port import (
    ISensorCalibrationOutputPort,
)
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from domain.calibration.errors.sensor_response_degenerate_error import SensorResponseDegenerateError
from domain.calibration.services.sensor_mounting_solver.sensor_mounting_solver import solve_mounting_angles
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from application.services.source_geometry_calibration_service.source_geometry_calibration_service import (
    SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from application.services.hardware_component_service.hardware_component_service import (
    HARDWARE_COMPONENT_MOUNTED_TOPIC,
)
from domain.calibration.calibration import Calibration
from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.events.active_sensor_rotation_changed.active_sensor_rotation_changed import (
    ActiveSensorRotationChanged,
)
from domain.calibration.repositories.i_sensor_calibration_repository import (
    ISensorCalibrationRepository,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC = "sensorcalibrationentryadded"
ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC = "activesensorrotationchanged"
AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC = "aefivoltagesampleacquired"
EXCITATION_CONTROLLER = "calibration automatique du capteur"

logger = logging.getLogger(__name__)


class _AutomaticCalibrationAborted(Exception):
    """Internal: an expected failure of the automatic calibration (reason for the operator)."""


class SensorCalibrationService(IApiSensorCalibrationService):
    """
    Application Service pour la calibration capteur : angles de montage P du
    capteur monté (amène le capteur du repère sources au montage actuel ;
    mesure E_sensor = Pᵀ·E_sources ; correction E_sources = P·E_sensor),
    procédure décrite dans le vault de thèse. Définition des repères et de P :
    domain/calibration/value_objects/rotation_convention/rotation_convention_intention.md.

    L'identité et le gain du capteur relèvent du catalogue des composants
    (onglet « Capteur ») ; ici, seuls les angles, mesurés sur UN montage du
    capteur : chaque calibration référence ce montage (`sensor_mounting_id`)
    et l'entrée de géométrie source courante. La rotation active : angles
    d'essai en cours de réglage (non persistés), sinon dernière calibration
    pour ce montage et cette géométrie, sinon les angles idéaux par défaut.
    """

    def __init__(
        self,
        calibration_repository: ISensorCalibrationRepository,
        sensor_mounting_id: Optional[UUID],
        source_geometry_entry_id: UUID,
        default_angles: SensorRotationAngles,
        event_bus: IDomainEventBus,
        excitation_service: Optional[ExcitationConfigurationService] = None,
        acquisition_service: Optional[IApiAefiAcquisitionService] = None,
        task_runner: Optional[IAsyncTaskRunner] = None,
        settle_delay_s: float = 1.0,
        samples_per_step: int = 20,
        sample_timeout_s: float = 30.0,
    ) -> None:
        """`sensor_mounting_id`: the current mounting of the sensor (None if
        no sensor mounted yet). `default_angles` are the ideal mounting
        angles, applied when no calibration exists for the current mounting
        and source geometry. `excitation_service`, `acquisition_service` and
        `task_runner` enable the automatic calibration; `settle_delay_s`
        (after each excitation change), `samples_per_step` (averaged per
        excitation state) and `sample_timeout_s` are its bench knobs."""
        self._excitation_service = excitation_service
        self._acquisition_service = acquisition_service
        self._task_runner = task_runner
        self._settle_delay_s = settle_delay_s
        self._samples_per_step = samples_per_step
        self._sample_timeout_s = sample_timeout_s
        self._output_port: Optional[ISensorCalibrationOutputPort] = None
        self._automatic_calibration_running = False
        self._calibration_repository = calibration_repository
        self._sensor_mounting_id = sensor_mounting_id
        self._source_geometry_entry_id = source_geometry_entry_id
        self._default_angles = default_angles
        # Trial angles being tuned (trial-and-error), not persisted.
        self._trial_angles: Optional[SensorRotationAngles] = None
        self._event_bus = event_bus
        if sensor_mounting_id is None:
            logger.warning(
                "SensorCalibrationService: no sensor mounted — mounting angles cannot be calibrated, "
                "ideal angles applied. Mount the sensor in the 'Capteur' tab."
            )
        event_bus.subscribe(SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC, self._on_source_geometry_recorded)
        event_bus.subscribe(HARDWARE_COMPONENT_MOUNTED_TOPIC, self._on_component_mounted)

    # -- commands -----------------------------------------------------------------

    def record_calibration(
        self,
        theta_x_degrees: float,
        theta_y_degrees: float,
        theta_z_degrees: float,
    ) -> None:
        logger.info(
            "SensorCalibrationService: Command record_calibration theta_x=%s theta_y=%s theta_z=%s "
            "sensor_mounting=%s source_geometry_entry=%s",
            theta_x_degrees,
            theta_y_degrees,
            theta_z_degrees,
            self._sensor_mounting_id,
            self._source_geometry_entry_id,
        )
        angles = SensorRotationAngles(
            theta_x_degrees=theta_x_degrees,
            theta_y_degrees=theta_y_degrees,
            theta_z_degrees=theta_z_degrees,
        )
        calibration = Calibration()
        entry = calibration.record_sensor_calibration_entry(
            self._sensor_mounting_id, self._source_geometry_entry_id, angles
        )
        self._calibration_repository.add(entry)
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
        self._trial_angles = None
        self._publish_active_rotation()

    def preview_rotation(
        self,
        theta_x_degrees: float,
        theta_y_degrees: float,
        theta_z_degrees: float,
    ) -> None:
        logger.info(
            "SensorCalibrationService: Command preview_rotation theta_x=%s theta_y=%s theta_z=%s",
            theta_x_degrees,
            theta_y_degrees,
            theta_z_degrees,
        )
        self._trial_angles = SensorRotationAngles(
            theta_x_degrees=theta_x_degrees,
            theta_y_degrees=theta_y_degrees,
            theta_z_degrees=theta_z_degrees,
        )
        self._publish_active_rotation()

    def reset_to_default(self) -> None:
        logger.info("SensorCalibrationService: Command reset_to_default (ideal angles as trial)")
        self._trial_angles = self._default_angles
        self._publish_active_rotation()

    def set_output_port(self, output_port: ISensorCalibrationOutputPort) -> None:
        self._output_port = output_port

    def start_automatic_calibration(self) -> None:
        logger.info(
            "SensorCalibrationService: Command start_automatic_calibration sensor_mounting=%s source_geometry_entry=%s",
            self._sensor_mounting_id,
            self._source_geometry_entry_id,
        )
        if self._automatic_calibration_running:
            logger.info("SensorCalibrationService: automatic calibration already running. Doing nothing.")
            return
        if self._excitation_service is None or self._acquisition_service is None or self._task_runner is None:
            self._fail_automatic_calibration("calibration automatique non disponible (excitation/acquisition non câblées)")
            return
        params = self._excitation_service.get_current_parameters()
        # The operator chooses the level (up to ~100 V RMS on the spheres): never picked here.
        if params.level_s1_s2.value <= 0.0 or params.level_s3_s4.value <= 0.0:
            self._fail_automatic_calibration(
                "régler un niveau d'excitation non nul (S1-S2 et S3-S4) avant la calibration automatique"
            )
            return
        # Single owner: refused during a scan; locks the Excitation panel until released.
        control = self._excitation_service.take_control(EXCITATION_CONTROLLER)
        if control.is_failure:
            self._fail_automatic_calibration(control.error)
            return
        self._automatic_calibration_running = True
        self._task_runner.submit(self._run_automatic_calibration)

    def _run_automatic_calibration(self) -> None:
        try:
            try:
                response_x, response_y = self._measure_responses()
                fit = solve_mounting_angles(response_x, response_y)
            except (_AutomaticCalibrationAborted, SensorResponseDegenerateError) as error:
                self._fail_automatic_calibration(str(error))
                return
            logger.info(
                "SensorCalibrationService: automatic calibration fit %s misalignment_x=%.3f° misalignment_y=%.3f° "
                "response_separation=%.3f° sensor_mounting=%s",
                fit.angles,
                fit.misalignment_x_degrees,
                fit.misalignment_y_degrees,
                fit.response_separation_degrees,
                self._sensor_mounting_id,
            )
            # Applied as a trial only: the operator checks it, then records it.
            self.preview_rotation(
                fit.angles.theta_x_degrees, fit.angles.theta_y_degrees, fit.angles.theta_z_degrees
            )
            if self._output_port is not None:
                self._output_port.present_automatic_calibration_succeeded(
                    AutomaticSensorCalibrationDTO(
                        theta_x_degrees=fit.angles.theta_x_degrees,
                        theta_y_degrees=fit.angles.theta_y_degrees,
                        theta_z_degrees=fit.angles.theta_z_degrees,
                        misalignment_x_degrees=fit.misalignment_x_degrees,
                        misalignment_y_degrees=fit.misalignment_y_degrees,
                        response_separation_degrees=fit.response_separation_degrees,
                    )
                )
        finally:
            self._excitation_service.release_control(EXCITATION_CONTROLLER)
            self._automatic_calibration_running = False

    def _measure_responses(self) -> Tuple[np.ndarray, np.ndarray]:
        """Sensor responses (sensor frame, in-phase) to X and Y excitation at
        the operator's levels, baseline (excitation off) subtracted. The
        operator's excitation is restored afterwards, whatever happens.
        ponytail: in-phase only — assumes the synchronous detection phase is
        calibrated (quadrature is logged)."""
        previous = self._excitation_service.get_current_parameters()
        samples: "queue.Queue" = queue.Queue()  # AefiVoltageSampleAcquired events

        def _on_sample(event) -> None:
            samples.put(event)

        self._event_bus.subscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
        started_here = not self._acquisition_service.is_acquisition_running()
        if started_here:
            self._acquisition_service.start_acquisition(AefiAcquisitionConfig())
        levels = (previous.level_s1_s2.value, previous.level_s3_s4.value)
        try:
            baseline = self._measure_step(samples, "baseline (excitation coupée)", ExcitationMode.Y_DIR, (0.0, 0.0), previous.frequency)
            excited_x = self._measure_step(samples, "excitation X", ExcitationMode.X_DIR, levels, previous.frequency)
            excited_y = self._measure_step(samples, "excitation Y", ExcitationMode.Y_DIR, levels, previous.frequency)
        finally:
            self._event_bus.unsubscribe(AEFI_VOLTAGE_SAMPLE_ACQUIRED_TOPIC, _on_sample)
            if started_here:
                self._acquisition_service.stop_acquisition()
            logger.info("SensorCalibrationService: restoring the operator's excitation %s", previous)
            if previous.mode == ExcitationMode.CUSTOM:
                logger.warning(
                    "SensorCalibrationService: excitation was CUSTOM — levels and frequency restored, "
                    "custom DDS phases are not (the hardware keeps the last calibration mode's phases)"
                )
            self._excitation_service.set_excitation(
                previous.mode, *levels, previous.frequency, controller=EXCITATION_CONTROLLER
            )
        return excited_x - baseline, excited_y - baseline

    def _measure_step(
        self, samples: "queue.Queue", label: str, mode: ExcitationMode, levels: Tuple[float, float], frequency: float
    ) -> np.ndarray:
        """Mean in-phase sensor vector over `samples_per_step` samples acquired
        entirely after the excitation was applied and had `settle_delay_s` to settle.

        A sample's timestamp marks the END of its acquisition window (taken
        when the MCU answers), and the stream acquires back-to-back: sample i
        starts after sample i-1 ends. So sample i is clean iff its predecessor
        (same stream, index i-1) ended after the settle instant — whatever the
        number of samples buffered or in flight between ADC and event bus."""
        if self._output_port is not None:
            self._output_port.present_automatic_calibration_step(f"Mesure {label}…")
        applied = self._excitation_service.set_excitation(
            mode, levels[0], levels[1], frequency, controller=EXCITATION_CONTROLLER
        )
        if applied.is_failure:  # programmer error: we hold the control
            raise RuntimeError(f"excitation refused during automatic calibration: {applied.error}")
        settled_at = datetime.now() + timedelta(seconds=self._settle_delay_s)

        collected: List = []
        rejected = 0
        predecessor = None
        deadline = time.monotonic() + self._settle_delay_s + self._sample_timeout_s
        while len(collected) < self._samples_per_step:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                event = samples.get(timeout=remaining)
            except queue.Empty:
                break
            if (
                predecessor is not None
                and event.acquisition_id == predecessor.acquisition_id
                and event.sample_index == predecessor.sample_index + 1
                and predecessor.sample.timestamp > settled_at
            ):
                collected.append(event.sample)
            else:
                rejected += 1
            predecessor = event
        logger.info(
            "SensorCalibrationService: step '%s' rejected %d sample(s) started before the excitation settled",
            label, rejected,
        )
        if len(collected) < self._samples_per_step:
            raise _AutomaticCalibrationAborted(
                f"acquisition : {len(collected)}/{self._samples_per_step} échantillons reçus "
                f"en {self._sample_timeout_s:.0f} s pendant la mesure {label}"
            )
        in_phase = np.mean(
            [[s.voltage_x_in_phase, s.voltage_y_in_phase, s.voltage_z_in_phase] for s in collected], axis=0
        )
        quadrature = np.mean(
            [[s.voltage_x_quadrature, s.voltage_y_quadrature, s.voltage_z_quadrature] for s in collected], axis=0
        )
        logger.info(
            "SensorCalibrationService: automatic calibration step '%s' mode=%s samples=%d in_phase=%s quadrature=%s",
            label, mode.name, len(collected), in_phase.tolist(), quadrature.tolist(),
        )
        return in_phase

    def _fail_automatic_calibration(self, reason: str) -> None:
        logger.warning("SensorCalibrationService: automatic calibration failed: %s", reason)
        if self._output_port is not None:
            self._output_port.present_automatic_calibration_failed(reason)

    def _on_source_geometry_recorded(self, event) -> None:
        geometry_entry_id = event.entry.entry_id
        if geometry_entry_id == self._source_geometry_entry_id:
            logger.info(
                "SensorCalibrationService: source geometry entry %s already current. Active rotation kept.",
                geometry_entry_id,
            )
            return
        logger.info(
            "SensorCalibrationService: source geometry entry changed (%s -> %s), re-evaluating active rotation",
            self._source_geometry_entry_id,
            geometry_entry_id,
        )
        self._source_geometry_entry_id = geometry_entry_id
        if self._trial_angles is not None:
            logger.info("SensorCalibrationService: source geometry changed, trial discarded")
            self._trial_angles = None
        self._publish_active_rotation()

    def _on_component_mounted(self, event) -> None:
        if event.kind != HardwareComponentKind.SENSOR:
            return
        logger.info(
            "SensorCalibrationService: sensor '%s' mounted (mounting %s -> %s), re-evaluating active rotation",
            event.component_name,
            self._sensor_mounting_id,
            event.mounting_id,
        )
        self._sensor_mounting_id = event.mounting_id
        if self._trial_angles is not None:
            logger.info("SensorCalibrationService: sensor remounted, trial discarded")
            self._trial_angles = None
        self._publish_active_rotation()

    def _resolve_active_rotation(
        self,
    ) -> Tuple[SensorRotationAngles, bool, Optional[datetime], bool]:
        """(angles, is_calibrated, recorded_at, is_trial): trial angles first,
        else the latest matching calibration, else the ideal default angles."""
        if self._trial_angles is not None:
            return self._trial_angles, False, None, True
        latest = self._find_latest_matching_entry()
        if latest is not None:
            return latest.angles, True, latest.recorded_at, False
        return self._default_angles, False, None, False

    def _publish_active_rotation(self) -> None:
        angles, is_calibrated, recorded_at, is_trial = self._resolve_active_rotation()
        event = ActiveSensorRotationChanged(
            angles=angles,
            is_calibrated=is_calibrated,
            recorded_at=recorded_at,
            is_trial=is_trial,
        )
        logger.info(
            "SensorCalibrationService: active rotation %s (is_calibrated=%s, is_trial=%s)",
            event.angles,
            event.is_calibrated,
            event.is_trial,
        )
        self._event_bus.publish(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, event)

    # -- queries ------------------------------------------------------------------

    def get_latest_calibration(self) -> Optional[SensorCalibrationDTO]:
        latest = self._find_latest_matching_entry()
        if latest is None:
            return None
        return SensorCalibrationDTO(
            theta_x_degrees=latest.angles.theta_x_degrees,
            theta_y_degrees=latest.angles.theta_y_degrees,
            theta_z_degrees=latest.angles.theta_z_degrees,
            recorded_at=latest.recorded_at,
        )

    def get_active_rotation(self) -> ActiveSensorRotationDTO:
        angles, is_calibrated, recorded_at, is_trial = self._resolve_active_rotation()
        return ActiveSensorRotationDTO(
            theta_x_degrees=angles.theta_x_degrees,
            theta_y_degrees=angles.theta_y_degrees,
            theta_z_degrees=angles.theta_z_degrees,
            is_calibrated=is_calibrated,
            is_trial=is_trial,
            recorded_at=recorded_at,
            mounting_matrix=tuple(tuple(row) for row in angles.mounting_matrix().tolist()),
        )

    def _find_latest_matching_entry(self) -> Optional[SensorCalibrationEntry]:
        matching = [
            entry
            for entry in self._calibration_repository.find_all()
            if entry.sensor_mounting_id == self._sensor_mounting_id
            and entry.source_geometry_entry_id == self._source_geometry_entry_id
        ]
        if not matching:
            logger.debug(
                "SensorCalibrationService: no calibration yet for sensor mounting %s and source geometry entry %s",
                self._sensor_mounting_id,
                self._source_geometry_entry_id,
            )
            return None
        return max(matching, key=lambda entry: entry.recorded_at)
