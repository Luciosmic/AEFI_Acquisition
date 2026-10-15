"""
Bar Transmission Calibration Presenter

See bar_transmission_calibration_presenter_intention.md.
"""

import logging
import threading
from typing import Dict

from PySide6.QtCore import QObject, Signal, Slot

from application.services.bar_transmission_calibration_service.dtos.bar_transmission_calibration_dtos import (
    AxisBarTransmissionDTO,
    BarTransmissionMeanDTO,
    EdgeBracketDTO,
)
from application.services.bar_transmission_calibration_service.i_api_bar_transmission_calibration_service import (
    IApiBarTransmissionCalibrationService,
)
from application.services.bar_transmission_calibration_service.ports.i_bar_transmission_calibration_output_port import (
    IBarTransmissionCalibrationOutputPort,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from interface.qt_abc import QABCMeta

logger = logging.getLogger(__name__)

MOTOR_INCREMENTS_UPDATED_TOPIC = "motorincrementsupdated"


class BarTransmissionCalibrationPresenter(QObject, IBarTransmissionCalibrationOutputPort, metaclass=QABCMeta):
    """Presenter of the « Transmission (barre) » tab. Output port of the
    background measurement: only emits signals (queued to the GUI thread)."""

    increments_updated = Signal(int, int, bool)  # x, y (motor increments), is_moving
    running_changed = Signal(bool)
    progress_message = Signal(str)
    axis_result_updated = Signal(str, str)  # axis, formatted result
    mean_updated = Signal(str)  # formatted X/Y mean and deviation (empty: none yet)
    status_message = Signal(str)

    def __init__(self, service: IApiBarTransmissionCalibrationService, event_bus: IDomainEventBus) -> None:
        super().__init__()
        self._service = service
        self._lock = threading.Lock()
        self._measured: Dict[str, AxisBarTransmissionDTO] = {}
        service.set_output_port(self)
        event_bus.subscribe(MOTOR_INCREMENTS_UPDATED_TOPIC, self._on_motor_increments)

    # -- operator actions -----------------------------------------------------------

    @Slot(str, float)
    def on_measure_requested(self, axis: str, bar_length_mm: float) -> None:
        result = self._service.measure_axis(axis, bar_length_mm, 0.0, self._service.default_settings())
        if result.is_failure:
            self.status_message.emit(f"Mesure {axis} refusée : {result.error.message}")
            return
        self.running_changed.emit(True)
        self.status_message.emit(f"Mesure de l'axe {axis} lancée (L = {bar_length_mm:.3f} mm)…")

    @Slot()
    def on_cancel_requested(self) -> None:
        self._service.cancel_measurement()

    @Slot()
    def on_record_requested(self) -> None:
        with self._lock:
            x, y = self._measured.get("X"), self._measured.get("Y")
        if x is None or y is None:
            missing = " et ".join(axis for axis, m in (("X", x), ("Y", y)) if m is None)
            self.status_message.emit(f"Enregistrement impossible : mesurer d'abord l'axe {missing}")
            return
        result = self._service.record(x, y)
        if result.is_failure:
            self.status_message.emit(f"Enregistrement refusé : {result.error.message}")
            return
        self.mean_updated.emit(self._format_mean(result.value))
        self.status_message.emit(
            f"Transmission enregistrée : {result.value.travel_per_motor_revolution_mm:.5f} mm/tour "
            f"(entrée {result.value.entry_id}) — appliquée au banc"
        )

    # -- output port (called from the measurement thread) ---------------------------

    def present_measurement_progress(self, axis: str, message: str) -> None:
        self.progress_message.emit(f"[{axis}] {message}")

    def present_axis_measured(self, result: AxisBarTransmissionDTO) -> None:
        with self._lock:
            self._measured[result.axis] = result
            x, y = self._measured.get("X"), self._measured.get("Y")
        self.axis_result_updated.emit(result.axis, self._format_axis(result))
        self.running_changed.emit(False)
        self.status_message.emit(f"Axe {result.axis} mesuré.")
        if x is not None and y is not None:
            compared = self._service.compare(x, y)
            self.mean_updated.emit(
                self._format_mean(compared.value) if compared.is_success else f"Non combinables : {compared.error.message}"
            )
        else:
            other = "Y" if result.axis == "X" else "X"
            self.status_message.emit(
                f"Axe {result.axis} mesuré. Repositionner la barre le long de l'axe {other}, puis mesurer {other}."
            )

    def present_axis_failed(self, axis: str, error) -> None:
        self.running_changed.emit(False)
        self.status_message.emit(f"Mesure {axis} en échec : {error.message}")

    # -- events -----------------------------------------------------------------------

    def _on_motor_increments(self, event) -> None:
        self.increments_updated.emit(event.x_increments, event.y_increments, event.is_moving)

    # -- formatting (presentation only) ----------------------------------------------

    @staticmethod
    def _format_bracket(name: str, bracket: EdgeBracketDTO) -> str:
        limit = "bruit LIDAR" if bracket.limited_by_lidar_noise else "1 incrément"
        return (
            f"{name} : [{bracket.on_bar_increment} sur barre, {bracket.off_bar_increment} hors barre] "
            f"→ n = {bracket.center_increment:.1f} ± {bracket.half_width_increments:.1f} ({limit})"
        )

    @classmethod
    def _format_axis(cls, r: AxisBarTransmissionDTO) -> str:
        return "\n".join([
            cls._format_bracket("Front 1", r.first_front),
            cls._format_bracket("Front 2", r.second_front),
            f"N = {r.increments_between_fronts:.1f} ± {r.increments_uncertainty:.1f} incréments",
            f"travel_per_motor_revolution_mm = {r.travel_per_motor_revolution_mm:.5f} "
            f"± {r.travel_per_motor_revolution_uncertainty_mm:.5f} mm "
            f"({r.relative_uncertainty * 100:.3f} %) → {r.microns_per_pulse:.4f} µm/incrément",
            f"Plateaux : barre {r.on_bar_distance_mm:.1f} mm, sol {r.off_bar_distance_mm:.1f} mm, "
            f"seuil {r.threshold_mm:.1f} mm, bruit {r.plateau_noise_mm:.2f} mm "
            f"(L = {r.bar_length_mm:.3f} mm, {r.full_steps_per_revolution:.0f} pas × {r.microsteps} micro-pas)",
        ])

    @staticmethod
    def _format_mean(m: BarTransmissionMeanDTO) -> str:
        agree = "compatibles" if m.axes_agree else "ÉCART SUPÉRIEUR AUX INCERTITUDES"
        return (
            f"Moyenne X/Y : {m.travel_per_motor_revolution_mm:.5f} ± {m.travel_per_motor_revolution_uncertainty_mm:.5f} mm/tour\n"
            f"X {m.x_travel_per_motor_revolution_mm:.5f}, Y {m.y_travel_per_motor_revolution_mm:.5f} — "
            f"écart X−Y {m.deviation_mm:+.5f} mm ({m.relative_deviation * 100:+.3f} %), {agree}"
        )
