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
from application.services.sensor_calibration_service.sensor_calibration_service import (
    ACTIVE_SENSOR_ROTATION_CHANGED_TOPIC,
    SENSOR_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class SensorCalibrationPresenter(QObject):
    """
    Presenter for the "Sensor Calibration" panel.
    - Receives UI events and calls Service
    - Emits signals for UI updates
    """

    # dto (SensorCalibrationDTO) or None
    latest_calibration_updated = Signal(object)
    # ActiveSensorRotationDTO (never None: ideal angles as fallback)
    active_rotation_updated = Signal(object)
    status_message = Signal(str)

    def __init__(self, service: IApiSensorCalibrationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
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
