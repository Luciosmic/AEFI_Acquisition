import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Tuple

from application.services.sensor_calibration_service.dtos.sensor_calibration_dto import (
    ActiveSensorRotationDTO,
    SensorCalibrationDTO,
)
from application.services.sensor_calibration_service.i_api_sensor_calibration_service import (
    IApiSensorCalibrationService,
)
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

logger = logging.getLogger(__name__)


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
    ) -> None:
        """`sensor_mounting_id`: the current mounting of the sensor (None if
        no sensor mounted yet). `default_angles` are the ideal mounting
        angles, applied when no calibration exists for the current mounting
        and source geometry."""
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
