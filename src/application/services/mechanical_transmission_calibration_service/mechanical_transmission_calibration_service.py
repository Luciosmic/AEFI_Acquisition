import logging
from typing import Optional

from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_calibration_dto import (
    MechanicalTransmissionCalibrationDTO,
)
from application.services.mechanical_transmission_calibration_service.i_api_mechanical_transmission_calibration_service import (
    IApiMechanicalTransmissionCalibrationService,
)
from domain.calibration.calibration import Calibration
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.repositories.i_mechanical_transmission_calibration_repository import (
    IMechanicalTransmissionCalibrationRepository,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

MECHANICAL_TRANSMISSION_CALIBRATION_ENTRY_ADDED_TOPIC = "mechanicaltransmissioncalibrationentryadded"

logger = logging.getLogger(__name__)


class MechanicalTransmissionCalibrationService(IApiMechanicalTransmissionCalibrationService):
    """
    Application Service de la transmission mécanique du banc : réglage de la
    chaîne de mouvement (moteur et driver montés, micro-pas, courant, avance
    par tour) et distance par impulsion moteur qui en découle.
    """

    def __init__(
        self,
        calibration_repository: IMechanicalTransmissionCalibrationRepository,
        hardware_component_repository: IHardwareComponentRepository,
        event_bus: IDomainEventBus,
    ) -> None:
        self._calibration_repository = calibration_repository
        self._components = hardware_component_repository
        self._event_bus = event_bus

    # -- commands -----------------------------------------------------------------

    def record_calibration(
        self,
        microsteps: int,
        driver_current_a: float,
        driver_peak_current_a: float,
        travel_per_motor_revolution_mm: float,
    ) -> None:
        logger.info(
            "MechanicalTransmissionCalibrationService: Command record_calibration microsteps=%s "
            "driver_current_a=%s driver_peak_current_a=%s travel_per_motor_revolution_mm=%s",
            microsteps, driver_current_a, driver_peak_current_a, travel_per_motor_revolution_mm,
        )
        calibration = Calibration()
        entry = calibration.record_mechanical_transmission_calibration_entry(
            self._mounting_id(HardwareComponentKind.MOTORS),
            self._mounting_id(HardwareComponentKind.STEPPER_DRIVER),
            microsteps,
            driver_current_a,
            driver_peak_current_a,
            travel_per_motor_revolution_mm,
        )
        self._calibration_repository.add(entry)
        # ponytail: the motion controller gets its factor at startup only —
        # subscribe it to this event if live re-setting becomes needed.
        logger.info(
            "MechanicalTransmissionCalibrationService: transmission %s recorded — the motion controller applies "
            "the current transmission at startup",
            entry.entry_id,
        )
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)

    # -- queries ------------------------------------------------------------------

    def get_current_calibration(self) -> Optional[MechanicalTransmissionCalibrationDTO]:
        motor = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.MOTORS))
        driver = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.STEPPER_DRIVER))
        entry = Calibration.current_mechanical_transmission(
            self._calibration_repository.find_all(),
            motor.mounting_id if motor else None,
            driver.mounting_id if driver else None,
        )
        if entry is None:
            logger.warning(
                "MechanicalTransmissionCalibrationService: no transmission recorded for mounted motor=%s driver=%s",
                motor.component_name if motor else None,
                driver.component_name if driver else None,
            )
            return None

        motor_values = Calibration.current_characterization(
            self._components.find_all(HardwareComponentKind.MOTORS), motor.component_name
        ).characterization.values
        steps_per_revolution = motor_values.get("full_steps_per_revolution")
        if steps_per_revolution is None:
            logger.warning(
                "MechanicalTransmissionCalibrationService: motor '%s' steps per revolution NOT CHARACTERIZED — "
                "no distance per pulse",
                motor.component_name,
            )
            return None

        rated_current = motor_values.get("rated_current_a")
        warning = entry.driver_current_shortfall(rated_current) if rated_current is not None else None
        if warning:
            logger.warning("MechanicalTransmissionCalibrationService: %s", warning)
        if rated_current is None:
            logger.warning(
                "MechanicalTransmissionCalibrationService: motor '%s' rated current NOT CHARACTERIZED — "
                "driver current not checked",
                motor.component_name,
            )

        return MechanicalTransmissionCalibrationDTO(
            motor_name=motor.component_name,
            stepper_driver_name=driver.component_name,
            microsteps=entry.microsteps,
            driver_current_a=entry.driver_current_a,
            driver_peak_current_a=entry.driver_peak_current_a,
            travel_per_motor_revolution_mm=entry.travel_per_motor_revolution_mm,
            microns_per_pulse=entry.microns_per_pulse(steps_per_revolution),
            driver_current_warning=warning,
            recorded_at=entry.recorded_at,
        )

    def _mounting_id(self, kind: HardwareComponentKind):
        mounting = Calibration.current_mounting(self._components.find_selections(kind))
        return mounting.mounting_id if mounting else None
