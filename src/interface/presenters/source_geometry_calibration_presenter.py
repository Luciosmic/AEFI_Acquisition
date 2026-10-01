"""
Source Geometry Calibration Presenter

Bridges between SourceGeometryCalibrationService and
SourceGeometryCalibrationPanel (a tab of CalibrationPanel). Separate
presenter (not folded into SensorCalibrationPresenter) because it
adapts a distinct service 1:1, following the same pattern used everywhere
else in this codebase.
"""

import logging
from typing import List

from PySide6.QtCore import QObject, Signal, Slot

from application.services.source_geometry_calibration_service.i_api_source_geometry_calibration_service import (
    IApiSourceGeometryCalibrationService,
)
from application.services.source_geometry_calibration_service.source_geometry_calibration_service import (
    SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus

logger = logging.getLogger(__name__)


class SourceGeometryCalibrationPresenter(QObject):
    """
    Presenter for the "Source Geometry Calibration" tab.
    - Receives UI events and calls Service
    - Emits signals for UI updates
    """

    # dto (SourceGeometryCalibrationDTO) or None
    latest_calibration_updated = Signal(object)
    status_message = Signal(str)

    def __init__(self, service: IApiSourceGeometryCalibrationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        event_bus.subscribe(SOURCE_GEOMETRY_CALIBRATION_ENTRY_ADDED_TOPIC, self._on_entry_added)

    def _on_entry_added(self, event) -> None:
        self.refresh_state()

    def refresh_state(self) -> None:
        """Push the latest recorded source geometry calibration to the UI."""
        self.latest_calibration_updated.emit(self._service.get_latest_calibration())

    @Slot(list, list)
    def on_save_calibration_requested(
        self, sphere_diameters_m: List[float], pairwise_distances_ext_m: List[float]
    ) -> None:
        try:
            self._service.record_calibration(sphere_diameters_m, pairwise_distances_ext_m)
            message = "Calibration enregistrée"
            logger.info(message)
            self.status_message.emit(message)
        except Exception as e:
            message = f"Erreur: {e}"
            logger.error(message)
            self.status_message.emit(message)
