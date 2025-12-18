"""
ContinuousAcquisitionExecutor

Responsibility:
- Run a continuous acquisition loop in a background worker thread
  using the IAcquisitionPort and publish domain events for each sample.

Design:
- Non‑blocking `start(config)`; loop runs in a daemon thread.
- `stop()` uses an Event flag and join with timeout.
"""

from __future__ import annotations

import threading
import time
from uuid import uuid4, UUID

from application.services.continuous_acquisition_service.i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)
from src.application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort

from domain.shared.events.i_domain_event_bus import IDomainEventBus
from domain.models.aefi_device.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
    ContinuousAcquisitionFailed,
    ContinuousAcquisitionStopped,
)


class ContinuousAcquisitionExecutor(IContinuousAcquisitionExecutor):
    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: UUID | None = None

    def start(self, config: ContinuousAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Start a new continuous acquisition in the background.

        If an acquisition is already running, this call is ignored for now.
        """
        if self._thread and self._thread.is_alive():
            return

        self._stop_flag.clear()
        self._current_acquisition_id = uuid4()
        self._thread = threading.Thread(
            target=self._worker,
            args=(self._current_acquisition_id, config, acquisition_port),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Request graceful stop of the running acquisition."""
        self._stop_flag.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        acquisition_id: UUID,
        config: ContinuousAcquisitionConfig,
        acquisition_port: IAcquisitionPort,
    ) -> None:
        """Background acquisition loop."""
        if config.sample_rate_hz <= 0:
            return

        dt = 1.0 / config.sample_rate_hz
        t0 = time.time()
        index = 0

        try:
            while not self._stop_flag.is_set():
                if config.max_duration_s is not None and (time.time() - t0) > config.max_duration_s:
                    break

                sample = acquisition_port.acquire_sample()

                event = ContinuousAcquisitionSampleAcquired(
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish("continuousacquisitionsampleacquired", event)

                index += 1
                time.sleep(dt)
        except Exception as e:
            error_event = ContinuousAcquisitionFailed(
                acquisition_id=acquisition_id,
                reason=str(e)
            )
            self._event_bus.publish("continuousacquisitionfailed", error_event)
        finally:
            stop_event = ContinuousAcquisitionStopped(acquisition_id=acquisition_id)
            self._event_bus.publish("continuousacquisitionstopped", stop_event)


