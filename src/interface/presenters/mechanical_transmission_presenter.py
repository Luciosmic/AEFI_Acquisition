"""
Mechanical Transmission Presenter

See mechanical_transmission_presenter_intention.md.
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.mechanical_transmission_calibration_service.i_api_mechanical_transmission_calibration_service import (
    IApiMechanicalTransmissionCalibrationService,
)
from application.services.mechanical_transmission_calibration_service.mechanical_transmission_calibration_service import (
    MECHANICAL_TRANSMISSION_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from interface.presentation.mechanical_transmission_view_model import MechanicalTransmissionViewModel

logger = logging.getLogger(__name__)

_SCAN_STARTED = "scanstarted"
_SCAN_ENDED = ("scancompleted", "scanfailed", "scancancelled")


def _french(value: float) -> str:
    return f"{value:g}".replace(".", ",")


class MechanicalTransmissionPresenter(QObject):
    """Bridges MechanicalTransmissionCalibrationService and the Transmission tab."""

    transmission_changed = Signal(object)  # MechanicalTransmissionViewModel
    status_message = Signal(str)
    scan_running_changed = Signal(bool)

    def __init__(self, service: IApiMechanicalTransmissionCalibrationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self._scan_running = False
        event_bus.subscribe(MECHANICAL_TRANSMISSION_CALIBRATION_ENTRY_ADDED_TOPIC, self._on_entry_added)
        event_bus.subscribe(_SCAN_STARTED, self._on_scan_started)
        for topic in _SCAN_ENDED:
            event_bus.subscribe(topic, self._on_scan_ended)

    def refresh_state(self) -> None:
        current = self._service.get_current_calibration()
        if current is not None:
            view_model = MechanicalTransmissionViewModel.recorded(
                motor_name=current.motor_name,
                stepper_driver_name=current.stepper_driver_name,
                microsteps=current.microsteps,
                driver_current_a=current.driver_current_a,
                driver_peak_current_a=current.driver_peak_current_a,
                microns_per_pulse=current.microns_per_pulse,
                recorded_at_text=current.recorded_at.astimezone().strftime("%d/%m/%Y à %H:%M"),
                driver_current_warning=current.driver_current_warning,
            )
        else:
            gap = self._service.get_current_gap()
            view_model = MechanicalTransmissionViewModel.missing(
                gap.missing_quantity if gap else "transmission mécanique", gap.where_to_enter if gap else ""
            )
        self.transmission_changed.emit(view_model)

    def _on_entry_added(self, _event) -> None:
        self.refresh_state()

    def _on_scan_started(self, _event) -> None:
        self._scan_running = True
        self.scan_running_changed.emit(True)

    def _on_scan_ended(self, _event) -> None:
        self._scan_running = False
        self.scan_running_changed.emit(False)

    @Slot(int, float, float, float)
    def on_save_requested(
        self, microsteps: int, driver_current_a: float, driver_peak_current_a: float, microns_per_pulse: float
    ) -> None:
        if self._scan_running:
            self.status_message.emit("Enregistrement refusé : un scan est en cours (deux échelles dans ses positions).")
            return
        try:
            self._service.record_calibration(microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse)
        except Exception as e:
            logger.warning("Mechanical transmission not recorded: %s", e)
            self.status_message.emit(f"Erreur: {e}")
            return
        message = f"Transmission enregistrée : {_french(microns_per_pulse)} µm par incrément."
        logger.info(message)
        self.status_message.emit(message)
