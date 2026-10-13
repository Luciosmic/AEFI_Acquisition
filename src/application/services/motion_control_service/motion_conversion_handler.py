import logging
from typing import Optional

from application.services.mechanical_transmission_calibration_service.i_api_mechanical_transmission_calibration_service import (
    IApiMechanicalTransmissionCalibrationService,
)
from application.services.motion_control_service.dtos.motion_conversion_status_dto import MotionConversionStatusDTO
from application.services.motion_control_service.ports.i_motion_conversion_status_port import (
    IMotionConversionStatusPort,
)
from application.services.motion_control_service.ports.i_motion_port import IMotionPort
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.motion_conversion_became_available.motion_conversion_became_available import (
    MotionConversionBecameAvailable,
)
from domain.shared_kernel.events.motion_conversion_found_missing.motion_conversion_found_missing import (
    MotionConversionFoundMissing,
)

logger = logging.getLogger(__name__)

# Facts that can complete the transmission: the motor/driver characterization,
# their mounting and the transmission setting itself.
RE_EVALUATION_TOPICS = (
    "hardwarecomponentcharacterized",
    "hardwarecomponentmounted",
    "mechanicaltransmissioncalibrationentryadded",
)


class MotionConversionHandler(IMotionConversionStatusPort):
    """Applique la transmission mécanique au port de mouvement et publie l'état
    « non calibré » / « calibré » (voir motion_conversion_handler_intention.md)."""

    def __init__(
        self,
        motion_port: IMotionPort,
        transmission_service: IApiMechanicalTransmissionCalibrationService,
        event_bus: IDomainEventBus,
    ) -> None:
        self._motion_port = motion_port
        self._transmission_service = transmission_service
        self._event_bus = event_bus
        self._status: MotionConversionStatusDTO = MotionConversionStatusDTO(
            is_available=motion_port.is_conversion_available()
        )
        for topic in RE_EVALUATION_TOPICS:
            event_bus.subscribe(topic, self._on_transmission_input_changed)

    # -- command ------------------------------------------------------------------

    def apply_current_transmission(self) -> MotionConversionStatusDTO:
        """Give the motion port its mm/pulse conversion from the current
        transmission, or record what is missing. Never raises on a missing
        conversion: the application must start so it can be calibrated."""
        logger.info("MotionConversionHandler: Command apply current transmission")
        if self._motion_port.is_conversion_available():
            logger.info("MotionConversionHandler: conversion already applied. Doing nothing.")
            return self._status

        calibration = self._transmission_service.get_current_calibration()
        if calibration is not None:
            self._motion_port.set_microns_per_pulse(calibration.microns_per_pulse)
            self._status = MotionConversionStatusDTO(
                is_available=True, microns_per_pulse=calibration.microns_per_pulse, motor_name=calibration.motor_name
            )
            logger.info(
                "MotionConversionHandler: motion set to %.4f µm/pulse (motor=%s, driver=%s, microsteps=1/%d)",
                calibration.microns_per_pulse, calibration.motor_name, calibration.stepper_driver_name,
                calibration.microsteps,
            )
            self._event_bus.publish(
                "motionconversionbecameavailable",
                MotionConversionBecameAvailable(
                    microns_per_pulse=calibration.microns_per_pulse,
                    motor_name=calibration.motor_name,
                    stepper_driver_name=calibration.stepper_driver_name,
                ),
            )
            return self._status

        gap = self._transmission_service.get_current_gap()
        status = MotionConversionStatusDTO(
            is_available=False,
            motor_name=gap.motor_name if gap else None,
            missing_quantity=gap.missing_quantity if gap else "conversion mm/impulsion",
            where_to_enter=gap.where_to_enter if gap else None,
        )
        if status == self._status:
            logger.info("MotionConversionHandler: conversion still missing (%s). Doing nothing.", status.missing_quantity)
            return self._status
        self._status = status
        logger.warning(
            "MotionConversionHandler: no mm/pulse conversion — motion and scan are refused until it is calibrated "
            "(motor=%s, missing=%s, where=%s)",
            status.motor_name, status.missing_quantity, status.where_to_enter,
        )
        self._event_bus.publish(
            "motionconversionfoundmissing",
            MotionConversionFoundMissing(
                motor_name=status.motor_name,
                missing_quantity=status.missing_quantity,
                where_to_enter=status.where_to_enter or "",
            ),
        )
        return self._status

    # -- query --------------------------------------------------------------------

    def get_status(self) -> MotionConversionStatusDTO:
        return self._status

    # -- events -------------------------------------------------------------------

    def _on_transmission_input_changed(self, event: Optional[object] = None) -> None:
        # ponytail: only the uncalibrated -> calibrated transition is applied live.
        # A conversion already applied is never changed under a running session
        # (the controller's pulse positions would be reinterpreted): restart.
        if self._motion_port.is_conversion_available():
            logger.info(
                "MotionConversionHandler: %s received, conversion already applied — a changed transmission "
                "takes effect at the next startup",
                type(event).__name__,
            )
            return
        self.apply_current_transmission()
