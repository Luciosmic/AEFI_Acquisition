"""
Frequency Sweep Presenter

Bridges FrequencySweepService and the Frequency Sweep panel (see
frequency_sweep_presenter_intention.md). Output port of the sweep: called
from its background task, it only emits signals (queued to the GUI thread by Qt).
"""

import logging
import math
from dataclasses import dataclass
from typing import Tuple

from PySide6.QtCore import QObject, Signal, Slot

from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    ROLE_LABELS,
    FrequencyPointDTO,
    FrequencySweepRequestDTO,
    FrequencySweepResultDTO,
)
from application.services.frequency_sweep_service.i_api_frequency_sweep_service import IApiFrequencySweepService
from application.services.frequency_sweep_service.ports.i_frequency_sweep_output_port import IFrequencySweepOutputPort
from interface.qt_abc import QABCMeta

logger = logging.getLogger(__name__)

AXES = ("X", "Y", "Z")
_STATUS_LABELS = {"completed": "terminé", "cancelled": "arrêté avant la fin"}


@dataclass(frozen=True)
class FrequencyPointViewModel:
    """One frequency as plotted: amplitude √(I²+Q²) in V and phase atan2(Q, I)
    in degrees, per axis X, Y, Z."""

    frequency_hz: float
    amplitude_v: Tuple[float, float, float]
    phase_deg: Tuple[float, float, float]


def to_view_model(point: FrequencyPointDTO) -> FrequencyPointViewModel:
    in_phase, quadrature = point.mean_v[:3], point.mean_v[3:]
    return FrequencyPointViewModel(
        frequency_hz=point.frequency_hz,
        amplitude_v=tuple(math.hypot(i, q) for i, q in zip(in_phase, quadrature)),
        phase_deg=tuple(math.degrees(math.atan2(q, i)) for i, q in zip(in_phase, quadrature)),
    )


class FrequencySweepPresenter(QObject, IFrequencySweepOutputPort, metaclass=QABCMeta):
    running_changed = Signal(bool)  # True while the sweep runs
    request_defaults = Signal(object, object)  # FrequencySweepRequestDTO, role labels ((id, label), ...)
    status_message = Signal(str)
    point_measured = Signal(object)  # FrequencyPointViewModel

    def __init__(self, service: IApiFrequencySweepService):
        super().__init__()
        self._service = service
        service.set_output_port(self)

    def refresh_state(self) -> None:
        """Pre-fill the panel with the default request (one source: the DTO)."""
        self.request_defaults.emit(FrequencySweepRequestDTO(), ROLE_LABELS)

    @Slot(object)
    def on_start_requested(self, parameters: dict) -> None:
        """`parameters`: the panel's fields (role, start_hz, stop_hz,
        frequency_count, samples_per_frequency, table_height_mm, operator_name,
        operator_id)."""
        self.running_changed.emit(True)
        self.status_message.emit("Balayage lancé…")
        self._service.start_sweep(FrequencySweepRequestDTO(**parameters))

    @Slot()
    def on_stop_requested(self) -> None:
        self.status_message.emit("Arrêt demandé : fin après la fréquence en cours…")
        self._service.stop_sweep()

    # -- IFrequencySweepOutputPort (Service -> Presenter) -------------------------

    def present_frequency_sweep_step(self, message: str) -> None:
        self.status_message.emit(message)

    def present_frequency_point_measured(self, point: FrequencyPointDTO) -> None:
        self.point_measured.emit(to_view_model(point))

    def present_frequency_sweep_ended(self, result: FrequencySweepResultDTO) -> None:
        exported = f"exporté dans {result.export_path}" if result.export_path else "EXPORT ÉCHOUÉ (voir les logs)"
        status = _STATUS_LABELS.get(result.status, result.status)
        self.status_message.emit(f"Balayage {status} ({len(result.points)} fréquences) — {exported}")
        self.running_changed.emit(False)

    def present_frequency_sweep_failed(self, reason: str) -> None:
        self.status_message.emit(f"Erreur: balayage en fréquence — {reason}")
        self.running_changed.emit(False)
