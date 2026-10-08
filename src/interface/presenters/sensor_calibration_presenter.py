"""
Sensor Calibration Presenter

Bridges between SensorCalibrationService and SensorCalibrationPanel.
Separate presenter (not folded into ElectricFieldProbePresenter or
SynchronousDetectionPresenter) because it adapts a distinct service 1:1,
following the same pattern used everywhere else in this codebase.
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from application.services.sensor_calibration_service.i_api_sensor_calibration_service import (
    IApiSensorCalibrationService,
)
from application.services.sensor_calibration_service.ports.i_sensor_calibration_output_port import (
    ISensorCalibrationOutputPort,
)
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
    SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from interface.qt_abc import QABCMeta

logger = logging.getLogger(__name__)


class SensorCalibrationPresenter(QObject, ISensorCalibrationOutputPort, metaclass=QABCMeta):
    """
    Presenter for the "Sensor Calibration" panel.
    - Receives UI events and calls Service
    - Emits signals for UI updates
    - Output port of the automatic calibration (called from its background
      task: only emits signals, queued to the GUI thread by Qt)
    """

    # dto (SensorCalibrationDTO) or None
    latest_calibration_updated = Signal(object)
    # ActiveSensorRotationDTO (never None: ideal angles as fallback)
    active_rotation_updated = Signal(object)
    status_message = Signal(str)
    # True while the automatic calibration runs (button disabled)
    automatic_calibration_running = Signal(bool)

    def __init__(self, service: IApiSensorCalibrationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        service.set_output_port(self)
        event_bus.subscribe(SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC, self._on_calibration_state_changed)
        # Also fires on a source geometry change (active rotation falls back
        # to the ideal angles), not only after a record from this panel.
        event_bus.subscribe(ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC, self._on_calibration_state_changed)

    def _on_calibration_state_changed(self, event) -> None:
        self.refresh_state()

    def refresh_state(self) -> None:
        """Push the latest recorded calibration (for the current sensor
        mounting + source geometry entry) to the UI."""
        self.latest_calibration_updated.emit(self._service.get_latest_calibration())
        self.active_rotation_updated.emit(self._service.get_active_rotation())

    @Slot(float, float, float)
    def on_trial_rotation_requested(self, theta_x: float, theta_y: float, theta_z: float) -> None:
        self._service.preview_rotation(theta_x, theta_y, theta_z)

    @Slot()
    def on_reset_to_default_requested(self) -> None:
        self._service.reset_to_default()

    @Slot()
    def on_automatic_calibration_requested(self) -> None:
        self.automatic_calibration_running.emit(True)
        self.status_message.emit("Calibration automatique lancée…")
        self._service.start_automatic_calibration()

    # -- ISensorCalibrationOutputPort (Service -> Presenter) ----------------------

    def present_automatic_calibration_step(self, message: str) -> None:
        self.status_message.emit(message)

    def present_automatic_calibration_succeeded(self, result) -> None:
        self.status_message.emit(
            f"Calibration automatique : θx={result.theta_x_degrees:.2f}°  θy={result.theta_y_degrees:.2f}°  "
            f"θz={result.theta_z_degrees:.2f}° appliqués en essai — désalignement résiduel "
            f"X {result.misalignment_x_degrees:.2f}°, Y {result.misalignment_y_degrees:.2f}° ; "
            f"angle entre réponses X/Y {result.response_separation_degrees:.1f}° (idéal 90°). "
            "Vérifier puis « Enregistrer calibration »."
        )
        self.automatic_calibration_running.emit(False)

    def present_automatic_calibration_failed(self, reason: str) -> None:
        self.status_message.emit(f"Erreur: calibration automatique — {reason}")
        self.automatic_calibration_running.emit(False)

    @Slot(float, float, float)
    def on_save_calibration_requested(
        self,
        theta_x_degrees: float,
        theta_y_degrees: float,
        theta_z_degrees: float,
    ) -> None:
        try:
            self._service.record_calibration(theta_x_degrees, theta_y_degrees, theta_z_degrees)
            message = "Calibration enregistrée"
            logger.info(message)
            self.status_message.emit(message)
        except Exception as e:
            message = f"Erreur: {e}"
            logger.error(message)
            self.status_message.emit(message)
