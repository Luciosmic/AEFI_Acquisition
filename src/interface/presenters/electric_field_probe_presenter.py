"""
Electric Field Probe Presenter - Interface V2

Bridges between ElectricFieldProbeService and ElectricFieldProbePanel.
No phase calibration, no rotation — the probe has no in-phase/quadrature
separation and doesn't move on the bench (cf. plan Context).
"""

from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal, Slot

from application.services.electric_field_probe_service.electric_field_probe_service import (
    ElectricFieldProbeService,
)
from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.electric_field_probe.events.field_sample_acquired.field_sample_acquired import (
    FieldSampleAcquired,
)
from domain.electric_field_probe.events.electric_field_probe_connection_changed.electric_field_probe_connection_changed import (
    ElectricFieldProbeConnectionChanged,
)
from domain.shared_kernel.events.continuous_acquisition_failed.continuous_acquisition_failed import (
    ContinuousAcquisitionFailed,
)
from domain.shared_kernel.events.continuous_acquisition_stopped.continuous_acquisition_stopped import (
    ContinuousAcquisitionStopped,
)

SAMPLE_ACQUIRED_TOPIC = "fieldsampleacquired"
CONNECTION_CHANGED_TOPIC = "electricfieldprobeconnectionchanged"
ACQUISITION_FAILED_TOPIC = "electricfieldprobeacquisitionfailed"
ACQUISITION_STOPPED_TOPIC = "electricfieldprobeacquisitionstopped"


class ElectricFieldProbePresenter(QObject):
    """
    Presenter for the Electric Field Probe panel.
    - Translates UI interactions to service calls.
    - Subscribes to domain events and emits Qt signals.
    - Applies an optional ambient-noise offset (tare), no phase/rotation.
    """

    probe_connection_changed = Signal(bool, str)  # connected, label (identity or error)
    probe_axes_defined = Signal(tuple)  # axis_labels, emitted once connected
    acquisition_started = Signal(str)  # acquisition_id
    acquisition_stopped = Signal(str)  # acquisition_id
    acquisition_failed = Signal(str)  # reason
    sample_acquired = Signal(
        dict
    )  # {axis_label: value, ..., "Norm": ..., "timestamp": ...}
    noise_state_updated = Signal(bool, str)  # enabled, offset_str

    def __init__(self, service: ElectricFieldProbeService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        self._event_bus = event_bus
        self._current_acquisition_id: Optional[str] = None

        self._last_raw_sample: Dict[str, float] = {}
        self._noise_offset: Optional[Dict[str, float]] = None
        self._noise_enabled = False
        self._axis_labels: tuple = ()

        self._event_bus.subscribe(SAMPLE_ACQUIRED_TOPIC, self._on_sample_event)
        self._event_bus.subscribe(
            CONNECTION_CHANGED_TOPIC, self._on_connection_changed_event
        )
        self._event_bus.subscribe(ACQUISITION_FAILED_TOPIC, self._on_failed_event)
        self._event_bus.subscribe(ACQUISITION_STOPPED_TOPIC, self._on_stopped_event)

    def shutdown(self):
        self._event_bus.unsubscribe(SAMPLE_ACQUIRED_TOPIC, self._on_sample_event)
        self._event_bus.unsubscribe(
            CONNECTION_CHANGED_TOPIC, self._on_connection_changed_event
        )
        self._event_bus.unsubscribe(ACQUISITION_FAILED_TOPIC, self._on_failed_event)
        self._event_bus.unsubscribe(ACQUISITION_STOPPED_TOPIC, self._on_stopped_event)

    # ------------------------------------------------------------------ #
    # UI Commands (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot()
    def on_connect_requested(self):
        self._service.connect_probe()

    @Slot()
    def on_disconnect_requested(self):
        self._service.disconnect_probe()

    @Slot(dict)
    def on_acquisition_start_requested(self, params: Dict[str, Any]):
        config = ElectricFieldProbeAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
        )
        self._service.start_acquisition(config)

    @Slot()
    def on_acquisition_stop_requested(self):
        self._service.stop_acquisition()
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(self._current_acquisition_id)
            self._current_acquisition_id = None

    @Slot(dict)
    def on_parameters_updated(self, params: Dict[str, Any]):
        config = ElectricFieldProbeAcquisitionConfig(
            sample_rate_hz=float(params.get("sample_rate_hz", 20.0)),
            max_duration_s=params.get("max_duration_s", None),
        )
        self._service.update_acquisition_parameters(config)

    @Slot()
    def calibrate_noise(self):
        """Use last received sample as the ambient-noise baseline (tare)."""
        if self._last_raw_sample:
            self._noise_offset = dict(self._last_raw_sample)
            self._noise_enabled = True
            self._emit_noise_state()

    @Slot()
    def reset_calibration(self):
        self._noise_offset = None
        self._noise_enabled = False
        self._emit_noise_state()

    @Slot(bool)
    def on_noise_toggled(self, enabled: bool):
        self._noise_enabled = enabled
        self._emit_noise_state()

    def _emit_noise_state(self):
        if self._noise_offset:
            offset_str = "  ".join(
                f"{k}={v * 1000:.2f}mV/m" for k, v in self._noise_offset.items()
            )
        else:
            offset_str = "—"
        self.noise_state_updated.emit(self._noise_enabled, offset_str)

    # ------------------------------------------------------------------ #
    # Domain events
    # ------------------------------------------------------------------ #

    def _on_connection_changed_event(self, event: ElectricFieldProbeConnectionChanged):
        if event.connected and event.probe is not None:
            p = event.probe
            label = f"{p.brand} {p.model} (SN {p.serial_number})"
            if p.battery_percentage is not None:
                label += (
                    f" — batt {p.battery_percentage:.0f}%"
                    f" (~{p.battery_remaining_hours:.0f}h, {p.battery_voltage_v:.2f}V)"
                )
            self._axis_labels = p.axis_labels
            self.probe_connection_changed.emit(True, label)
            self.probe_axes_defined.emit(p.axis_labels)
        else:
            label = event.error or "Disconnected"
            self.probe_connection_changed.emit(False, label)
            self._last_raw_sample = {}

    def _on_failed_event(self, event: ContinuousAcquisitionFailed):
        self.acquisition_failed.emit(str(event.reason))

    def _on_stopped_event(self, event: ContinuousAcquisitionStopped):
        if self._current_acquisition_id is not None:
            self.acquisition_stopped.emit(str(event.acquisition_id))
            self._current_acquisition_id = None

    def _on_sample_event(self, event: FieldSampleAcquired):
        acquisition_id_str = str(event.acquisition_id)

        if self._current_acquisition_id is None:
            self._current_acquisition_id = acquisition_id_str
            self.acquisition_started.emit(acquisition_id_str)

        m = event.sample
        labels = self._axis_labels or tuple(
            f"axis_{i}" for i in range(len(m.components))
        )
        raw = dict(zip(labels, m.components))
        self._last_raw_sample = raw

        offset = (
            self._noise_offset if self._noise_enabled and self._noise_offset else None
        )
        displayed = {k: (v - offset[k] if offset else v) for k, v in raw.items()}

        data: Dict[str, Any] = dict(displayed)
        data["Norm"] = sum(v**2 for v in displayed.values()) ** 0.5
        data["acquisition_id"] = acquisition_id_str
        data["index"] = event.sample_index
        data["timestamp"] = m.timestamp.isoformat()

        self.sample_acquired.emit(data)
