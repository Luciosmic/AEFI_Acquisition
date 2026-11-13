"""
Inertial Probe Presenter

Bridges InertialProbeService and InertialProbePanel.

- Operator actions (@Slot) forward to the service; no domain logic here.
- Domain events arrive from a worker thread at the stream rate (25 Hz): the
  handler only keeps the latest sample; a QTimer of the Qt thread emits a
  ready-to-display view model at ~10 Hz.
- The measured rate comes from the samples' reception timestamps (sliding
  window), never from the display instants.
"""

import logging
import threading
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from application.services.inertial_probe_service.inertial_probe_service import InertialProbeService
from domain.detection_devices.inertial_probe.events.inertial_probe_connection_changed.inertial_probe_connection_changed import (
    InertialProbeConnectionChanged,
)
from domain.detection_devices.inertial_probe.events.inertial_probe_sample_acquired.inertial_probe_sample_acquired import (
    InertialProbeSampleAcquired,
)
from domain.detection_devices.inertial_probe.events.inertial_probe_stream_failed.inertial_probe_stream_failed import (
    InertialProbeStreamFailed,
)
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from interface.presentation.inertial_probe_view_model import build_reading_view_model
from interface.presentation.sample_rate_meter import SampleRateMeter

SAMPLE_ACQUIRED_TOPIC = "inertialprobesampleacquired"
CONNECTION_CHANGED_TOPIC = "inertialprobeconnectionchanged"
STREAM_FAILED_TOPIC = "inertialprobestreamfailed"

DISPLAY_INTERVAL_MS = 100  # ~10 Hz display for a 25 Hz stream
RATE_WINDOW_SAMPLES = 50  # ~2 s at 25 Hz

logger = logging.getLogger(__name__)


# ponytail: the lidar channel is displayed by this presenter only because it
# travels in the same stream (same board, same serial link). Ceiling: one
# presenter carries both. Upgrade: a separate lidar presenter with its own port.
class InertialProbePresenter(QObject):
    connection_changed = Signal(bool, str)  # connected, label
    acquisition_started = Signal()
    acquisition_stopped = Signal()
    acquisition_failed = Signal(str)  # reason
    reading_updated = Signal(object)  # InertialProbeReadingViewModel
    _acquisition_ended = Signal()  # internal: marshals worker-thread events to the Qt thread

    def __init__(self, service: InertialProbeService, event_bus: IDomainEventBus) -> None:
        super().__init__()
        self._service = service
        self._event_bus = event_bus

        self._lock = threading.Lock()
        self._latest: Optional[InertialProbeSampleAcquired] = None
        self._sample_count = 0
        self._displayed_count = 0
        self._meter = SampleRateMeter(RATE_WINDOW_SAMPLES)
        self._acquiring = False

        self._timer = QTimer(self)
        self._timer.setInterval(DISPLAY_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh_display)
        self._acquisition_ended.connect(self._finish_acquisition)

        # Registered in __init__, not lazily.
        self._event_bus.subscribe(SAMPLE_ACQUIRED_TOPIC, self._on_sample_event)
        self._event_bus.subscribe(CONNECTION_CHANGED_TOPIC, self._on_connection_changed_event)
        self._event_bus.subscribe(STREAM_FAILED_TOPIC, self._on_failed_event)

    def shutdown(self) -> None:
        self._event_bus.unsubscribe(SAMPLE_ACQUIRED_TOPIC, self._on_sample_event)
        self._event_bus.unsubscribe(CONNECTION_CHANGED_TOPIC, self._on_connection_changed_event)
        self._event_bus.unsubscribe(STREAM_FAILED_TOPIC, self._on_failed_event)
        self._timer.stop()

    @property
    def is_display_timer_active(self) -> bool:
        return self._timer.isActive()

    # ------------------------------------------------------------------ #
    # Operator actions (from panel signals)
    # ------------------------------------------------------------------ #

    @Slot()
    def on_connect_requested(self) -> None:
        self._service.connect_sensor()

    @Slot()
    def on_disconnect_requested(self) -> None:
        self._service.disconnect_sensor()
        self._finish_acquisition()

    @Slot()
    def on_start_requested(self) -> None:
        with self._lock:
            self._latest = None
            self._sample_count = 0
            self._displayed_count = 0
            self._meter.reset()
        self._service.start_acquisition()
        if self._service.is_acquisition_running():
            self._acquiring = True
            self._timer.start()
            self.acquisition_started.emit()

    @Slot()
    def on_stop_requested(self) -> None:
        self._service.stop_acquisition()
        self._finish_acquisition()

    # ------------------------------------------------------------------ #
    # Display refresh (Qt thread, ~10 Hz while acquiring)
    # ------------------------------------------------------------------ #

    @Slot()
    def refresh_display(self) -> None:
        with self._lock:
            latest = self._latest
            count = self._sample_count
            rate_hz = self._meter.rate_hz
        if latest is None or count == self._displayed_count:
            return
        self._displayed_count = count
        self.reading_updated.emit(
            build_reading_view_model(
                acceleration_g=latest.acceleration_g,
                angular_rate_dps=latest.angular_rate_dps,
                magnetic_field_ut=latest.magnetic_field_ut,
                lidar_streamed=latest.lidar_distance is not None,
                lidar_distance_mm=latest.lidar_distance.distance_mm if latest.lidar_distance else None,
                measured_rate_hz=rate_hz,
                sample_count=count,
            )
        )

    @Slot()
    def _finish_acquisition(self) -> None:
        if not self._acquiring:
            return
        self._acquiring = False
        self._timer.stop()
        self.acquisition_stopped.emit()

    # ------------------------------------------------------------------ #
    # Domain events (may run in the worker thread)
    # ------------------------------------------------------------------ #

    def _on_sample_event(self, event: InertialProbeSampleAcquired) -> None:
        with self._lock:
            self._latest = event
            self._sample_count += 1
            self._meter.add(event.timestamp_s)

    def _on_connection_changed_event(self, event: InertialProbeConnectionChanged) -> None:
        if event.connected:
            label = "Connecté"
        else:
            label = event.error or "Déconnecté"
            self._acquisition_ended.emit()
        self.connection_changed.emit(event.connected, label)

    def _on_failed_event(self, event: InertialProbeStreamFailed) -> None:
        logger.warning(
            "InertialProbePresenter: stream failed acquisition_id=%s reason=%s",
            event.acquisition_id,
            event.reason,
        )
        self.acquisition_failed.emit(str(event.reason))
        self._acquisition_ended.emit()
