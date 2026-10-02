"""
Acquisition Throughput Characterization Presenter

Bridges AcquisitionThroughputCharacterizationService and the throughput
section of the 'Microcontrôleur' calibration tab. Output port of the sweep:
called from its background task, it only emits signals (queued to the GUI
thread by Qt).
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)
from application.services.acquisition_throughput_characterization_service.i_api_acquisition_throughput_characterization_service import (
    IApiAcquisitionThroughputCharacterizationService,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_output_port import (
    IAcquisitionThroughputOutputPort,
)
from interface.qt_abc import QABCMeta

logger = logging.getLogger(__name__)


class AcquisitionThroughputCharacterizationPresenter(QObject, IAcquisitionThroughputOutputPort, metaclass=QABCMeta):
    running_changed = Signal(bool)  # True while the sweep runs (button disabled)
    request_defaults = Signal(object, int)  # default n_avg values, samples per point
    status_message = Signal(str)
    point_measured = Signal(object)  # AcquisitionThroughputPointDTO
    characterization_succeeded = Signal(object)  # AcquisitionThroughputCharacterizationDTO
    # {quantity key: value} for the microcontroller characterization form
    component_values_measured = Signal(object)

    def __init__(self, service: IApiAcquisitionThroughputCharacterizationService):
        super().__init__()
        self._service = service
        service.set_output_port(self)

    def refresh_state(self) -> None:
        """Pre-fill the form with the default request (one source: the DTO)."""
        defaults = AcquisitionThroughputRequestDTO()
        self.request_defaults.emit(defaults.n_avg_values, defaults.samples_per_point)

    @Slot(object, int)
    def on_start_requested(self, n_avg_values, samples_per_point: int) -> None:
        self.running_changed.emit(True)
        self.status_message.emit("Caractérisation lancée…")
        self._service.start_characterization(
            AcquisitionThroughputRequestDTO(n_avg_values=tuple(n_avg_values), samples_per_point=samples_per_point)
        )

    # -- IAcquisitionThroughputOutputPort (Service -> Presenter) ------------------

    def present_throughput_characterization_step(self, message: str) -> None:
        self.status_message.emit(message)

    def present_throughput_point_measured(self, point) -> None:
        self.point_measured.emit(point)

    def present_throughput_characterization_succeeded(self, result) -> None:
        self.characterization_succeeded.emit(result)
        self.component_values_measured.emit(result.component_values)
        exported = f"exporté dans {result.export_path}" if result.export_path else "EXPORT ÉCHOUÉ (voir les logs)"
        self.status_message.emit(f"Caractérisation terminée — {exported}")
        self.running_changed.emit(False)

    def present_throughput_characterization_failed(self, reason: str) -> None:
        self.status_message.emit(f"Erreur: caractérisation du débit — {reason}")
        self.running_changed.emit(False)
