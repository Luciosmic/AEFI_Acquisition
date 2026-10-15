"""
Bar Transmission Calibration Service

See bar_transmission_calibration_service_intention.md.
"""

import logging
import math
import threading
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
    BarCalibrationSettingsDTO,
    BarTransmissionMeanDTO,
    EdgeBracketDTO,
)
from application.services.bar_transmission_calibration_service.errors.bar_transmission_calibration_error import (
    BarNotFound,
    BarTransmissionCalibrationError,
    BenchMotionFailed,
    EdgeNotBracketed,
    InternalCalibrationError,
    InvalidMeasurementRequest,
    LidarStreamBusy,
    LidarUnavailable,
    MeasurementAlreadyRunning,
    MeasurementCancelled,
    MeasurementsNotComparable,
    MotionChainIncomplete,
    PositiveLimitNotReached,
    ScanRunning,
)
from application.services.bar_transmission_calibration_service.i_api_bar_transmission_calibration_service import (
    IApiBarTransmissionCalibrationService,
)
from application.services.bar_transmission_calibration_service.ports.i_bar_transmission_calibration_output_port import (
    IBarTransmissionCalibrationOutputPort,
)
from application.services.bar_transmission_calibration_service.ports.i_lidar_distance_port import (
    ILidarDistancePort,
)
from application.services.bar_transmission_calibration_service.ports.i_raw_increment_motion_port import (
    IRawIncrementMotionPort,
)
from application.services.bar_transmission_calibration_service.ports.lidar_stream_error import (
    LidarStreamBusyError,
    LidarUnavailableError,
)
from application.services.bar_transmission_calibration_service.ports.raw_increment_motion_error import (
    RawIncrementMotionError,
)
from application.shared.exclusive_control.exclusive_control import ExclusiveControl
from application.shared.ports.i_async_task_runner import IAsyncTaskRunner
from domain.calibration.calibration import Calibration
from domain.calibration.errors.bar_profile_unusable_error import BarProfileUnusableError
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.repositories.i_mechanical_transmission_calibration_repository import (
    IMechanicalTransmissionCalibrationRepository,
)
from domain.calibration.services.bar_profile_analysis.bar_profile_analysis import (
    locate_bar,
    pair_by_reception_time,
)
from domain.calibration.value_objects.axis_bar_transmission_measurement.axis_bar_transmission_measurement import (
    AXES,
    AxisBarTransmissionMeasurement,
)
from domain.calibration.value_objects.bar_coarse_localization.bar_coarse_localization import (
    BarCoarseLocalization,
)
from domain.calibration.value_objects.bar_point_reading.bar_point_reading import (
    BarPointClassification,
    BarPointReading,
)
from domain.calibration.value_objects.bar_transmission_mean.bar_transmission_mean import BarTransmissionMean
from domain.calibration.value_objects.edge_bracket.edge_bracket import EdgeBracket
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

# Owner name of the LIDAR stream while a measurement runs.
LIDAR_STREAM_CONTROLLER = "calibration de la transmission (barre)"
SCAN_STARTED_TOPIC = "scanstarted"
SCAN_ENDED_TOPICS = ("scancompleted", "scanfailed", "scancancelled")

# Repositioning between probes: the "fast" preset (HS 3000 Hz).
TRAVEL_SPEED_INCREMENTS_PER_S = 3000
# Fly scan time budget: the bench travel (1270 mm at 21.8 µm/increment ≈ 58 257
# increments) rounded up, twice, plus a fixed margin.
NOMINAL_TRAVEL_INCREMENTS = 60_000
FLY_SCAN_EXTRA_TIMEOUT_S = 30.0
MOVE_TIMEOUT_S = 60.0
LIDAR_READ_TIMEOUT_S = 0.25
# No LIDAR distance for this long: the stream is dead (the board streams at ~25 Hz).
LIDAR_SILENCE_S = 3.0
# Coarse bracket that does not check out at rest: widened by one margin, at most this often.
MAX_BRACKET_WIDENINGS = 3
# Plateau contrast below which the fly scan saw no bar.
MIN_CONTRAST_MM = 10.0

FIRST_FRONT, SECOND_FRONT = "front 1 (entrée sur la barre)", "front 2 (sortie de la barre)"


class _SystemClock:
    """perf_counter: the clock the LIDAR stream stamps its readings with."""

    now = staticmethod(time.perf_counter)
    sleep = staticmethod(time.sleep)


class _Abort(Exception):
    """Internal: an expected failure of the running measurement."""

    def __init__(self, error: BarTransmissionCalibrationError) -> None:
        super().__init__(error.message)
        self.error = error


class BarTransmissionCalibrationService(IApiBarTransmissionCalibrationService):
    """Measures travel_per_motor_revolution_mm with a bar of known length seen by the LIDAR."""

    def __init__(
        self,
        motion: IRawIncrementMotionPort,
        lidar: ILidarDistancePort,
        calibration_repository: IMechanicalTransmissionCalibrationRepository,
        hardware_component_repository: IHardwareComponentRepository,
        event_bus: IDomainEventBus,
        task_runner: IAsyncTaskRunner,
        lidar_stream_control: Optional[ExclusiveControl] = None,
        clock=None,
    ) -> None:
        """`lidar_stream_control`: shared owner of the LIDAR stream (the sensor
        panel is refused while it is held). `clock`: now()/sleep(), perf_counter by default."""
        self._motion = motion
        self._lidar = lidar
        self._calibration_repository = calibration_repository
        self._components = hardware_component_repository
        self._event_bus = event_bus
        self._task_runner = task_runner
        self._lidar_stream_control = lidar_stream_control
        self._clock = clock or _SystemClock()
        self._output_port: Optional[IBarTransmissionCalibrationOutputPort] = None
        self._lock = threading.Lock()
        self._running_axis: Optional[str] = None
        self._cancel = threading.Event()
        self._scan_running = False
        event_bus.subscribe(SCAN_STARTED_TOPIC, self._on_scan_started)
        for topic in SCAN_ENDED_TOPICS:
            event_bus.subscribe(topic, self._on_scan_ended)

    # -- commands -----------------------------------------------------------------

    def set_output_port(self, output_port: IBarTransmissionCalibrationOutputPort) -> None:
        self._output_port = output_port

    def measure_axis(
        self,
        axis: str,
        bar_length_mm: float,
        bar_length_uncertainty_mm: float,
        settings: BarCalibrationSettingsDTO,
    ) -> OperationResult[None, BarTransmissionCalibrationError]:
        logger.info(
            "BarTransmissionCalibrationService: Command measure_axis axis=%s bar_length_mm=%s ±%s settings=%s",
            axis, bar_length_mm, bar_length_uncertainty_mm, settings,
        )
        invalid = self._validate_request(axis, bar_length_mm, bar_length_uncertainty_mm, settings)
        if invalid is not None:
            return self._refuse(invalid)
        if self._scan_running:
            return self._refuse(ScanRunning())
        chain = self._resolve_chain()
        if chain.is_failure:
            return self._refuse(chain.error)
        full_steps_per_revolution, microsteps = chain.value
        with self._lock:
            if self._running_axis is not None:
                return self._refuse(MeasurementAlreadyRunning(self._running_axis))
            if self._lidar.is_streamed_elsewhere():
                return self._refuse(LidarStreamBusy("le panneau du capteur inertiel"))
            if self._lidar_stream_control is not None:
                taken = self._lidar_stream_control.take(LIDAR_STREAM_CONTROLLER)
                if taken.is_failure:
                    return self._refuse(LidarStreamBusy(taken.error))
            self._running_axis = axis
            self._cancel.clear()
        measurement_id = uuid4()
        self._task_runner.submit(
            lambda: self._run(
                measurement_id, axis, bar_length_mm, bar_length_uncertainty_mm, settings,
                full_steps_per_revolution, microsteps,
            )
        )
        return OperationResult.ok(None)

    def cancel_measurement(self) -> None:
        logger.info("BarTransmissionCalibrationService: Command cancel_measurement axis=%s", self._running_axis)
        if self._running_axis is None:
            logger.info("BarTransmissionCalibrationService: no measurement running. Doing nothing.")
            return
        self._cancel.set()

    def record(
        self, x: AxisBarTransmissionDTO, y: AxisBarTransmissionDTO
    ) -> OperationResult[BarTransmissionMeanDTO, BarTransmissionCalibrationError]:
        logger.info(
            "BarTransmissionCalibrationService: Command record X=%.5f mm/rev Y=%.5f mm/rev",
            x.travel_per_motor_revolution_mm, y.travel_per_motor_revolution_mm,
        )
        combined = self._combine(x, y)
        if combined.is_failure:
            return self._refuse(combined.error)
        mean: BarTransmissionMean = combined.value
        motor = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.MOTORS))
        driver = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.STEPPER_DRIVER))
        current = Calibration.current_mechanical_transmission(
            self._calibration_repository.find_all(),
            motor.mounting_id if motor else None,
            driver.mounting_id if driver else None,
        )
        if current is None:
            return self._refuse(MotionChainIncomplete(
                "aucun réglage de transmission pour le moteur et le driver montés (micro-pas, courants à reprendre)"
            ))
        if current.microsteps != mean.x.microsteps:
            return self._refuse(MeasurementsNotComparable(
                f"micro-pas changés depuis la mesure ({mean.x.microsteps} mesurés, {current.microsteps} réglés) : remesurer"
            ))
        calibration = Calibration()
        try:
            entry = calibration.record_mechanical_transmission_calibration_entry(
                current.motor_mounting_id,
                current.stepper_driver_mounting_id,
                current.microsteps,
                current.driver_current_a,
                current.driver_peak_current_a,
                mean.travel_per_motor_revolution_mm,
            )
        except ValueError as error:
            return self._refuse(MotionChainIncomplete(str(error)))
        self._calibration_repository.add(entry)
        logger.info(
            "BarTransmissionCalibrationService: transmission entry %s recorded travel_per_motor_revolution_mm=%.5f "
            "±%.5f (X %.5f, Y %.5f, deviation %.5f mm, axes_agree=%s)",
            entry.entry_id, mean.travel_per_motor_revolution_mm, mean.travel_per_motor_revolution_uncertainty_mm,
            mean.x.travel_per_motor_revolution_mm, mean.y.travel_per_motor_revolution_mm,
            mean.deviation_mm, mean.axes_agree,
        )
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)
        return OperationResult.ok(self._mean_dto(mean, entry.entry_id))

    # -- queries ------------------------------------------------------------------

    def default_settings(self) -> BarCalibrationSettingsDTO:
        return BarCalibrationSettingsDTO()

    def is_measuring(self) -> bool:
        return self._running_axis is not None

    def compare(
        self, x: AxisBarTransmissionDTO, y: AxisBarTransmissionDTO
    ) -> OperationResult[BarTransmissionMeanDTO, BarTransmissionCalibrationError]:
        combined = self._combine(x, y)
        if combined.is_failure:
            return OperationResult.fail(combined.error)
        return OperationResult.ok(self._mean_dto(combined.value, None))

    # -- background measurement ---------------------------------------------------

    def _run(
        self,
        measurement_id: UUID,
        axis: str,
        bar_length_mm: float,
        bar_length_uncertainty_mm: float,
        settings: BarCalibrationSettingsDTO,
        full_steps_per_revolution: float,
        microsteps: int,
    ) -> None:
        logger.info("BarTransmissionCalibrationService: measurement %s axis=%s started", measurement_id, axis)
        try:
            try:
                located, first, second = self._measure_fronts(measurement_id, axis, settings)
                measurement = AxisBarTransmissionMeasurement(
                    axis=axis,
                    bar_length_mm=bar_length_mm,
                    bar_length_uncertainty_mm=bar_length_uncertainty_mm,
                    first_front=first,
                    second_front=second,
                    full_steps_per_revolution=full_steps_per_revolution,
                    microsteps=microsteps,
                )
                self._park(axis)
            except _Abort as aborted:
                self._fail(measurement_id, axis, aborted.error)
                return
            except RawIncrementMotionError as error:
                self._fail(measurement_id, axis, BenchMotionFailed(axis, str(error)))
                return
            except LidarStreamBusyError:
                self._fail(measurement_id, axis, LidarStreamBusy("le panneau du capteur inertiel"))
                return
            except LidarUnavailableError as error:
                self._fail(measurement_id, axis, LidarUnavailable(str(error)))
                return
            except ValueError as error:  # domain invariant (fronts not separated)
                self._fail(measurement_id, axis, BarNotFound(axis, str(error)))
                return
            except Exception as error:
                logger.exception("BarTransmissionCalibrationService: measurement %s axis=%s crashed", measurement_id, axis)
                self._fail(measurement_id, axis, InternalCalibrationError(f"{type(error).__name__}: {error}"))
                raise
            result = self._axis_dto(measurement, located)
            logger.info(
                "BarTransmissionCalibrationService: measurement %s axis=%s N=%.1f ±%.1f increments "
                "travel_per_motor_revolution_mm=%.5f ±%.5f (%.2e relative)",
                measurement_id, axis, measurement.increments_between_fronts, measurement.increments_uncertainty,
                measurement.travel_per_motor_revolution_mm, measurement.travel_per_motor_revolution_uncertainty_mm,
                measurement.relative_uncertainty,
            )
            if self._output_port is not None:
                self._output_port.present_axis_measured(result)
        finally:
            try:
                self._lidar.close()
            except Exception as error:
                logger.error("BarTransmissionCalibrationService: LIDAR close failed measurement=%s error=%s",
                             measurement_id, error)
            if self._lidar_stream_control is not None:
                self._lidar_stream_control.release(LIDAR_STREAM_CONTROLLER)
            with self._lock:
                self._running_axis = None
            logger.info("BarTransmissionCalibrationService: measurement %s axis=%s ended", measurement_id, axis)

    def _measure_fronts(
        self, measurement_id: UUID, axis: str, settings: BarCalibrationSettingsDTO
    ) -> Tuple[BarCoarseLocalization, EdgeBracket, EdgeBracket]:
        self._progress(axis, "Ouverture du flux LIDAR…")
        self._lidar.open()
        self._progress(axis, f"Homing de l'axe {axis}…")
        self._motion.home(axis)
        located, limit = self._fly_scan(measurement_id, axis, settings)
        self._motion.set_speed(axis, TRAVEL_SPEED_INCREMENTS_PER_S)
        margin = max(1, math.ceil(settings.fly_speed_increments_per_s * settings.coarse_margin_s))
        brackets = []
        for name, front, direction in (
            (FIRST_FRONT, located.first_front_increment, +1),
            (SECOND_FRONT, located.second_front_increment, -1),
        ):
            bracket = self._verified_bracket(axis, name, front, direction, margin, limit, located, settings)
            brackets.append(self._refine(measurement_id, axis, name, bracket, located, settings))
        return located, brackets[0], brackets[1]

    def _fly_scan(
        self, measurement_id: UUID, axis: str, settings: BarCalibrationSettingsDTO
    ) -> Tuple[BarCoarseLocalization, int]:
        speed = settings.fly_speed_increments_per_s
        self._progress(axis, f"Fly scan de butée à butée à {speed} incréments/s…")
        self._motion.set_speed(axis, speed)
        self._drain_lidar()
        positions: List[Tuple[float, float]] = [(self._clock.now(), self._motion.get_position(axis))]
        samples: List[Tuple[float, float]] = []
        self._motion.run_to_positive_limit(axis)
        started = last_sample = self._clock.now()
        deadline = started + 2 * NOMINAL_TRAVEL_INCREMENTS / speed + FLY_SCAN_EXTRA_TIMEOUT_S
        while True:
            self._abort_if_cancelled(axis)
            reading = self._lidar.read_distance(LIDAR_READ_TIMEOUT_S)
            now = self._clock.now()
            if reading is not None:
                samples.append((reading.timestamp_s, reading.distance_mm))
                last_sample = now
            elif now - last_sample > LIDAR_SILENCE_S:
                self._motion.stop(axis)
                raise _Abort(LidarUnavailable(f"aucune distance depuis {LIDAR_SILENCE_S:.0f} s pendant le fly scan"))
            positions.append((self._clock.now(), self._motion.get_position(axis)))
            if not self._motion.is_moving(axis):
                break
            if now > deadline:
                self._motion.stop(axis)
                raise _Abort(BenchMotionFailed(axis, f"fly scan non terminé après {deadline - started:.0f} s"))
        limit = self._motion.get_position(axis)
        if not self._motion.is_at_positive_limit(axis):
            raise _Abort(PositiveLimitNotReached(axis, limit))
        profile = pair_by_reception_time(positions, samples)
        logger.info(
            "BarTransmissionCalibrationService: measurement %s axis=%s fly scan done limit=%d increments "
            "duration_s=%.1f lidar_samples=%d positions=%d profile_points=%d",
            measurement_id, axis, limit, self._clock.now() - started, len(samples), len(positions), len(profile),
        )
        try:
            located = locate_bar(profile, MIN_CONTRAST_MM)
        except BarProfileUnusableError as error:
            raise _Abort(BarNotFound(axis, str(error))) from error
        logger.info(
            "BarTransmissionCalibrationService: measurement %s axis=%s plateaus on_bar=%.1f mm off_bar=%.1f mm "
            "threshold=%.1f mm noise=%.2f mm coarse fronts %.0f / %.0f",
            measurement_id, axis, located.on_bar_distance_mm, located.off_bar_distance_mm, located.threshold_mm,
            located.plateau_noise_mm, located.first_front_increment, located.second_front_increment,
        )
        self._progress(
            axis,
            f"Barre repérée : plateaux {located.on_bar_distance_mm:.1f} / {located.off_bar_distance_mm:.1f} mm, "
            f"seuil {located.threshold_mm:.1f} mm, fronts ≈ {located.first_front_increment:.0f} et "
            f"{located.second_front_increment:.0f} incréments",
        )
        return located, limit

    def _verified_bracket(
        self,
        axis: str,
        name: str,
        front: float,
        direction: int,
        margin: int,
        limit: int,
        located: BarCoarseLocalization,
        settings: BarCalibrationSettingsDTO,
    ) -> EdgeBracket:
        """Coarse bracket checked at rest: bar side on the bar, floor side off it;
        widened by one margin when it does not check out."""
        bracket = EdgeBracket.around(front, direction, margin)
        for attempt in range(MAX_BRACKET_WIDENINGS + 1):
            clamped = [min(max(side, 0), limit) for side in (bracket.on_bar_increment, bracket.off_bar_increment)]
            if clamped[0] == clamped[1]:
                break
            bracket = bracket.with_sides(*clamped)
            on_side = self._classify(axis, bracket.on_bar_increment, located, settings)
            off_side = self._classify(axis, bracket.off_bar_increment, located, settings)
            if on_side is BarPointClassification.ON_BAR and off_side is BarPointClassification.OFF_BAR:
                self._progress(axis, f"{name} encadré : [{bracket.on_bar_increment}, {bracket.off_bar_increment}]")
                return bracket
            logger.info(
                "BarTransmissionCalibrationService: axis=%s %s bracket [%d, %d] not confirmed "
                "(bar side %s, floor side %s), attempt %d/%d",
                axis, name, bracket.on_bar_increment, bracket.off_bar_increment, on_side.value, off_side.value,
                attempt + 1, MAX_BRACKET_WIDENINGS + 1,
            )
            if attempt < MAX_BRACKET_WIDENINGS:
                bracket = bracket.widened(margin)
        raise _Abort(EdgeNotBracketed(
            axis, name,
            f"pas de point sur la barre et de point hors barre de part et d'autre autour de {front:.0f} incréments "
            f"après {MAX_BRACKET_WIDENINGS} élargissements de {margin} incréments",
        ))

    def _refine(
        self,
        measurement_id: UUID,
        axis: str,
        name: str,
        bracket: EdgeBracket,
        located: BarCoarseLocalization,
        settings: BarCalibrationSettingsDTO,
    ) -> EdgeBracket:
        while not bracket.is_resolved:
            probe = bracket.next_probe()
            classification = self._classify(axis, probe, located, settings)
            bracket = bracket.narrowed(probe, classification)
            self._progress(
                axis,
                f"{name} : {classification.value} à {probe} → [{bracket.on_bar_increment}, {bracket.off_bar_increment}]",
            )
        reason = "point indécidable (bruit LIDAR)" if bracket.stopped_undecidable else "1 incrément (moteur)"
        logger.info(
            "BarTransmissionCalibrationService: measurement %s axis=%s %s resolved [%d, %d] n=%.1f δ=%.1f — %s",
            measurement_id, axis, name, bracket.on_bar_increment, bracket.off_bar_increment,
            bracket.center_increment, bracket.half_width_increments, reason,
        )
        return bracket

    def _classify(
        self, axis: str, increment: int, located: BarCoarseLocalization, settings: BarCalibrationSettingsDTO
    ) -> BarPointClassification:
        reading = self._read_point(axis, increment, settings)
        classification = reading.classify(located.threshold_mm, settings.k_sigma)
        logger.debug(
            "BarTransmissionCalibrationService: axis=%s point %d mean=%.2f mm std=%.2f mm k=%d -> %s",
            axis, increment, reading.mean_distance_mm, reading.std_distance_mm, reading.sample_count,
            classification.value,
        )
        return classification

    def _read_point(self, axis: str, increment: int, settings: BarCalibrationSettingsDTO) -> BarPointReading:
        """k distances read at rest at `increment`, all received after the settling time."""
        self._abort_if_cancelled(axis)
        self._motion.move_to(axis, increment)
        self._motion.wait_until_stopped(axis, MOVE_TIMEOUT_S)
        reached = self._motion.get_position(axis)
        if reached != increment:
            raise _Abort(BenchMotionFailed(axis, f"arrêté à {reached} au lieu de {increment} incréments"))
        self._clock.sleep(settings.settle_time_s)
        settled_at = self._clock.now()
        distances: List[float] = []
        last_sample = settled_at
        while len(distances) < settings.samples_per_point:
            reading = self._lidar.read_distance(LIDAR_READ_TIMEOUT_S)
            now = self._clock.now()
            if reading is None:
                if now - last_sample > LIDAR_SILENCE_S:
                    raise _Abort(LidarUnavailable(f"aucune distance depuis {LIDAR_SILENCE_S:.0f} s à l'arrêt"))
                continue
            last_sample = now
            if reading.timestamp_s >= settled_at:
                distances.append(reading.distance_mm)
        return BarPointReading.from_samples(distances)

    def _park(self, axis: str) -> None:
        """Measured axis back to its origin: the bench is left where homing would leave it."""
        self._progress(axis, f"Retour de l'axe {axis} à l'origine…")
        self._motion.move_to(axis, 0)
        self._motion.wait_until_stopped(axis, MOVE_TIMEOUT_S)

    def _drain_lidar(self) -> None:
        """Drop the distances buffered before the fly scan (e.g. during homing)."""
        dropped = 0
        while self._lidar.read_distance(0.0) is not None:
            dropped += 1
        logger.debug("BarTransmissionCalibrationService: %d buffered LIDAR distance(s) dropped", dropped)

    def _abort_if_cancelled(self, axis: str) -> None:
        if self._cancel.is_set():
            self._motion.stop(axis)
            raise _Abort(MeasurementCancelled(axis))

    def _fail(self, measurement_id: UUID, axis: str, error: BarTransmissionCalibrationError) -> None:
        logger.warning(
            "BarTransmissionCalibrationService: measurement %s axis=%s failed (%s): %s",
            measurement_id, axis, type(error).__name__, error.message,
        )
        try:
            self._motion.stop(axis)
        except RawIncrementMotionError as stop_error:
            logger.error("BarTransmissionCalibrationService: stop after failure failed axis=%s error=%s", axis, stop_error)
        if self._output_port is not None:
            self._output_port.present_axis_failed(axis, error)

    def _progress(self, axis: str, message: str) -> None:
        logger.info("BarTransmissionCalibrationService: axis=%s %s", axis, message)
        if self._output_port is not None:
            self._output_port.present_measurement_progress(axis, message)

    # -- helpers ------------------------------------------------------------------

    def _refuse(self, error: BarTransmissionCalibrationError) -> OperationResult:
        logger.warning("BarTransmissionCalibrationService: refused (%s): %s", type(error).__name__, error.message)
        return OperationResult.fail(error)

    @staticmethod
    def _validate_request(
        axis: str, bar_length_mm: float, bar_length_uncertainty_mm: float, settings: BarCalibrationSettingsDTO
    ) -> Optional[BarTransmissionCalibrationError]:
        problems = []
        if axis not in AXES:
            problems.append(f"axe {axis!r} inconnu (X ou Y)")
        if not (isinstance(bar_length_mm, (int, float)) and math.isfinite(bar_length_mm) and bar_length_mm > 0):
            problems.append("longueur de barre L > 0 requise")
        if not (math.isfinite(bar_length_uncertainty_mm) and bar_length_uncertainty_mm >= 0):
            problems.append("incertitude sur L ≥ 0 requise")
        if settings.samples_per_point < 2:
            problems.append("au moins 2 échantillons par point (k ≥ 2)")
        if settings.settle_time_s < 0:
            problems.append("temps de stabilisation ≥ 0")
        if settings.k_sigma < 0:
            problems.append("k_σ ≥ 0")
        if settings.fly_speed_increments_per_s <= 0:
            problems.append("vitesse du fly scan > 0")
        if settings.coarse_margin_s <= 0:
            problems.append("marge > 0")
        return InvalidMeasurementRequest(" ; ".join(problems)) if problems else None

    def _resolve_chain(self) -> OperationResult[Tuple[float, int], BarTransmissionCalibrationError]:
        """(full_steps_per_revolution, microsteps) of the mounted chain: both are
        needed to turn N into a travel per revolution."""
        motor = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.MOTORS))
        driver = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.STEPPER_DRIVER))
        if motor is None or driver is None:
            return OperationResult.fail(MotionChainIncomplete(
                "moteur ou driver non monté (panneau Calibration, onglets « Moteurs » et « Driver pas à pas »)"
            ))
        entry = Calibration.current_mechanical_transmission(
            self._calibration_repository.find_all(), motor.mounting_id, driver.mounting_id
        )
        if entry is None:
            return OperationResult.fail(MotionChainIncomplete(
                "aucun réglage de transmission (micro-pas) pour le moteur et le driver montés"
            ))
        characterization = Calibration.current_characterization(
            self._components.find_all(HardwareComponentKind.MOTORS), motor.component_name
        )
        steps = characterization.characterization.values.get("full_steps_per_revolution") if characterization else None
        if steps is None:
            return OperationResult.fail(MotionChainIncomplete(
                f"pas par tour du moteur « {motor.component_name} » non caractérisé (onglet « Moteurs »)"
            ))
        return OperationResult.ok((float(steps), entry.microsteps))

    def _combine(
        self, x: AxisBarTransmissionDTO, y: AxisBarTransmissionDTO
    ) -> OperationResult[BarTransmissionMean, BarTransmissionCalibrationError]:
        try:
            return OperationResult.ok(BarTransmissionMean(self._to_measurement(x), self._to_measurement(y)))
        except ValueError as error:
            return OperationResult.fail(MeasurementsNotComparable(str(error)))

    @staticmethod
    def _to_measurement(dto: AxisBarTransmissionDTO) -> AxisBarTransmissionMeasurement:
        def bracket(b: EdgeBracketDTO) -> EdgeBracket:
            return EdgeBracket(b.on_bar_increment, b.off_bar_increment, b.stopped_undecidable)

        return AxisBarTransmissionMeasurement(
            axis=dto.axis,
            bar_length_mm=dto.bar_length_mm,
            bar_length_uncertainty_mm=dto.bar_length_uncertainty_mm,
            first_front=bracket(dto.first_front),
            second_front=bracket(dto.second_front),
            full_steps_per_revolution=dto.full_steps_per_revolution,
            microsteps=dto.microsteps,
        )

    @staticmethod
    def _axis_dto(m: AxisBarTransmissionMeasurement, located: BarCoarseLocalization) -> AxisBarTransmissionDTO:
        def bracket(b: EdgeBracket) -> EdgeBracketDTO:
            return EdgeBracketDTO(
                on_bar_increment=b.on_bar_increment,
                off_bar_increment=b.off_bar_increment,
                stopped_undecidable=b.stopped_undecidable,
                center_increment=b.center_increment,
                half_width_increments=b.half_width_increments,
            )

        return AxisBarTransmissionDTO(
            axis=m.axis,
            bar_length_mm=m.bar_length_mm,
            bar_length_uncertainty_mm=m.bar_length_uncertainty_mm,
            first_front=bracket(m.first_front),
            second_front=bracket(m.second_front),
            full_steps_per_revolution=m.full_steps_per_revolution,
            microsteps=m.microsteps,
            increments_between_fronts=m.increments_between_fronts,
            increments_uncertainty=m.increments_uncertainty,
            travel_per_motor_revolution_mm=m.travel_per_motor_revolution_mm,
            travel_per_motor_revolution_uncertainty_mm=m.travel_per_motor_revolution_uncertainty_mm,
            relative_uncertainty=m.relative_uncertainty,
            microns_per_pulse=m.microns_per_pulse,
            on_bar_distance_mm=located.on_bar_distance_mm,
            off_bar_distance_mm=located.off_bar_distance_mm,
            threshold_mm=located.threshold_mm,
            plateau_noise_mm=located.plateau_noise_mm,
            measured_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _mean_dto(mean: BarTransmissionMean, entry_id: Optional[UUID]) -> BarTransmissionMeanDTO:
        return BarTransmissionMeanDTO(
            x_travel_per_motor_revolution_mm=mean.x.travel_per_motor_revolution_mm,
            y_travel_per_motor_revolution_mm=mean.y.travel_per_motor_revolution_mm,
            travel_per_motor_revolution_mm=mean.travel_per_motor_revolution_mm,
            travel_per_motor_revolution_uncertainty_mm=mean.travel_per_motor_revolution_uncertainty_mm,
            deviation_mm=mean.deviation_mm,
            relative_deviation=mean.relative_deviation,
            axes_agree=mean.axes_agree,
            entry_id=entry_id,
        )

    # -- events -------------------------------------------------------------------

    def _on_scan_started(self, event=None) -> None:
        self._scan_running = True

    def _on_scan_ended(self, event=None) -> None:
        self._scan_running = False
