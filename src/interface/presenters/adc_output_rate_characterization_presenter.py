"""
ADC Output Rate Characterization Presenter

Bridges AdcOutputRateCharacterizationService and the ODR section of the 'ADC'
calibration tab. Output port of the measurement: called from its background
task, it only emits signals (queued to the GUI thread by Qt).
"""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateRequestDTO,
)
from application.services.adc_output_rate_characterization_service.i_api_adc_output_rate_characterization_service import (
    IApiAdcOutputRateCharacterizationService,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_output_port import (
    IAdcOutputRateOutputPort,
)
from interface.qt_abc import QABCMeta

logger = logging.getLogger(__name__)


class AdcOutputRateCharacterizationPresenter(QObject, IAdcOutputRateOutputPort, metaclass=QABCMeta):
    running_changed = Signal(bool)
    request_defaults = Signal(object)  # OSR values accepted by the ADC
    status_message = Signal(str)
    point_measured = Signal(object)  # AdcOutputRatePointDTO
    characterization_succeeded = Signal(object)  # AdcOutputRateCharacterizationDTO
    component_values_measured = Signal(object)  # {quantity key: value} for the ADC characterization form

    def __init__(self, service: IApiAdcOutputRateCharacterizationService):
        super().__init__()
        self._service = service
        service.set_output_port(self)

    def refresh_state(self) -> None:
        self.request_defaults.emit(self._service.get_allowed_oversampling_ratios())

    @Slot(object, int, float, int)
    def on_start_requested(self, osr_values, channel: int, probe_ratio: float, periods: int) -> None:
        self.running_changed.emit(True)
        self.status_message.emit("Mesure de l'ODR lancée…")
        self._service.start_characterization(AdcOutputRateRequestDTO(
            scope_channel=channel, probe_ratio=probe_ratio, oversampling_ratios=tuple(osr_values),
            periods_per_capture=periods,
        ))

    # -- IAdcOutputRateOutputPort (Service -> Presenter) --------------------------

    def present_output_rate_step(self, message: str) -> None:
        self.status_message.emit(message)

    def present_output_rate_point_measured(self, point) -> None:
        self.point_measured.emit(point)

    def present_output_rate_characterization_succeeded(self, result) -> None:
        self.characterization_succeeded.emit(result)
        self.component_values_measured.emit(result.component_values)
        exported = f"exporté dans {result.export_path}" if result.export_path else "EXPORT ÉCHOUÉ (voir les logs)"
        self.status_message.emit(f"Mesure de l'ODR terminée — {exported}")
        self.running_changed.emit(False)

    def present_output_rate_characterization_failed(self, reason: str) -> None:
        self.status_message.emit(f"Erreur: mesure de l'ODR — {reason}")
        self.running_changed.emit(False)
