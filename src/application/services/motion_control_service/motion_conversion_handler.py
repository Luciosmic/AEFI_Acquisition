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
from domain.shared_kernel.motion.events.motion_conversion_became_available.motion_conversion_became_available import (
    MotionConversionBecameAvailable,
)
from domain.shared_kernel.motion.events.motion_conversion_changed.motion_conversion_changed import (
    MotionConversionChanged,
)
from domain.shared_kernel.motion.events.motion_conversion_found_missing.motion_conversion_found_missing import (
    MotionConversionFoundMissing,
)

logger = logging.getLogger(__name__)

# Facts that can complete or change the transmission: the motor/driver
# characterization, their mounting and the transmission setting itself.
RE_EVALUATION_TOPICS = (
    "hardwarecomponentcharacterized",
    "hardwarecomponentmounted",
    "mechanicaltransmissioncalibrationentryadded",
)
SCAN_STARTED_TOPIC = "scanstarted"
SCAN_ENDED_TOPICS = ("scancompleted", "scanfailed", "scancancelled")


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
        self._scan_running = False
        for topic in RE_EVALUATION_TOPICS:
            event_bus.subscribe(topic, self._on_transmission_input_changed)
        event_bus.subscribe(SCAN_STARTED_TOPIC, self._on_scan_started)
        for topic in SCAN_ENDED_TOPICS:
            event_bus.subscribe(topic, self._on_scan_ended)

    # -- command ------------------------------------------------------------------

    def apply_current_transmission(self) -> MotionConversionStatusDTO:
        """Give the motion port its mm/pulse conversion from the current
        transmission (first time or recalibration), or record what is missing.
        Never during a scan (abnormal: whoever drives the motors is refused during
        a scan): logged, nothing applied, no deferral — the operator re-applies.
        Never raises on a missing conversion: the application must start so it
        can be calibrated."""
        logger.info("MotionConversionHandler: Command apply current transmission")
        if self._scan_running:
            logger.warning(
                "MotionConversionHandler: transmission change NOT applied — a scan is running "
                "(its positions would mix two scales). Nothing deferred: record the transmission again after the scan"
            )
            return self._status

        calibration = self._transmission_service.get_current_calibration()
        if calibration is not None:
            return self._apply(calibration)

        if self._motion_port.is_conversion_available():
            # ponytail: no "unset" on the motion port — a transmission that becomes
            # incomplete after being applied keeps the applied conversion.
            logger.warning(
                "MotionConversionHandler: current transmission no longer complete; conversion kept at "
                "%s µm/pulse (motion stays allowed)",
                self._status.microns_per_pulse,
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

    def _apply(self, calibration) -> MotionConversionStatusDTO:
        was_available = self._motion_port.is_conversion_available()
        previous = self._status.microns_per_pulse
        if was_available and previous == calibration.microns_per_pulse:
            logger.info(
                "MotionConversionHandler: %.4f µm/pulse already applied. Doing nothing.", calibration.microns_per_pulse
            )
            return self._status
        self._motion_port.set_microns_per_pulse(calibration.microns_per_pulse)
        self._status = MotionConversionStatusDTO(
            is_available=True, microns_per_pulse=calibration.microns_per_pulse, motor_name=calibration.motor_name
        )
        if was_available:
            logger.info(
                "MotionConversionHandler: conversion CHANGED %s -> %.4f µm/pulse without restart "
                "(motor=%s, driver=%s, microsteps=1/%d) — the same pulse positions now read in the new scale",
                previous, calibration.microns_per_pulse, calibration.motor_name, calibration.stepper_driver_name,
                calibration.microsteps,
            )
            self._event_bus.publish(
                "motionconversionchanged",
                MotionConversionChanged(
                    previous_microns_per_pulse=previous,
                    microns_per_pulse=calibration.microns_per_pulse,
                    motor_name=calibration.motor_name,
                    stepper_driver_name=calibration.stepper_driver_name,
                ),
            )
            return self._status
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

    # -- query --------------------------------------------------------------------

    def get_status(self) -> MotionConversionStatusDTO:
        return self._status

    # -- events -------------------------------------------------------------------

    def _on_transmission_input_changed(self, event: Optional[object] = None) -> None:
        logger.info("MotionConversionHandler: %s received, re-evaluating the transmission", type(event).__name__)
        self.apply_current_transmission()

    def _on_scan_started(self, event: Optional[object] = None) -> None:
        self._scan_running = True

    def _on_scan_ended(self, event: Optional[object] = None) -> None:
        self._scan_running = False
