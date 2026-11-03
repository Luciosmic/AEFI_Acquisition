import logging
from typing import Optional, Tuple

from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_calibration_dto import (
    MechanicalTransmissionCalibrationDTO,
)
from application.services.mechanical_transmission_calibration_service.dtos.mechanical_transmission_gap_dto import (
    MechanicalTransmissionGapDTO,
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
        # ponytail: a factor already applied is NOT re-set live (the controller's
        # pulse positions would be reinterpreted mid-session) — restart to apply a
        # changed transmission. The uncalibrated -> calibrated transition IS applied
        # live (MotionConversionHandler): nothing could have moved before.
        logger.info("MechanicalTransmissionCalibrationService: transmission %s recorded", entry.entry_id)
        for event in calibration.domain_events:
            self._event_bus.publish(type(event).__name__.lower(), event)

    # -- queries ------------------------------------------------------------------

    def get_current_calibration(self) -> Optional[MechanicalTransmissionCalibrationDTO]:
        return self._resolve(log_gap=True)[0]

    def get_current_gap(self) -> Optional[MechanicalTransmissionGapDTO]:
        """What blocks the mm/pulse conversion; None when it can be derived."""
        return self._resolve(log_gap=False)[1]

    def _resolve(
        self, log_gap: bool
    ) -> Tuple[Optional[MechanicalTransmissionCalibrationDTO], Optional[MechanicalTransmissionGapDTO]]:
        def gap(motor_name: Optional[str], missing_quantity: str, where_to_enter: str, log_message: str):
            if log_gap:
                logger.warning("MechanicalTransmissionCalibrationService: %s", log_message)
            return None, MechanicalTransmissionGapDTO(motor_name, missing_quantity, where_to_enter)

        motor = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.MOTORS))
        driver = Calibration.current_mounting(self._components.find_selections(HardwareComponentKind.STEPPER_DRIVER))
        motor_name = motor.component_name if motor else None
        entry = Calibration.current_mechanical_transmission(
            self._calibration_repository.find_all(),
            motor.mounting_id if motor else None,
            driver.mounting_id if driver else None,
        )
        if motor is None or driver is None or entry is None:
            return gap(
                motor_name,
                "réglage de la transmission mécanique (moteur et driver montés, micro-pas, courant, avance par tour)",
                "panneau Calibration, onglets « Moteurs » et « Driver pas à pas » pour monter le moteur et le driver ; "
                "l'enregistrement du réglage n'a pas d'écran dédié",
                f"no transmission recorded for mounted motor={motor_name} "
                f"driver={driver.component_name if driver else None}",
            )

        motor_entry = Calibration.current_characterization(
            self._components.find_all(HardwareComponentKind.MOTORS), motor.component_name
        )
        motor_values = motor_entry.characterization.values if motor_entry else {}
        steps_per_revolution = motor_values.get("full_steps_per_revolution")
        if steps_per_revolution is None:
            label = next(
                q.label for q in HardwareComponentKind.MOTORS.quantities if q.key == "full_steps_per_revolution"
            )
            return gap(
                motor.component_name,
                label,
                "panneau Calibration, onglet « Moteurs »",
                f"motor '{motor.component_name}' steps per revolution NOT CHARACTERIZED — no distance per pulse",
            )

        rated_current = motor_values.get("rated_current_a")
        warning = entry.driver_current_shortfall(rated_current) if rated_current is not None else None
        if log_gap and warning:
            logger.warning("MechanicalTransmissionCalibrationService: %s", warning)
        if log_gap and rated_current is None:
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
        ), None

    def _mounting_id(self, kind: HardwareComponentKind):
        mounting = Calibration.current_mounting(self._components.find_selections(kind))
        return mounting.mounting_id if mounting else None
