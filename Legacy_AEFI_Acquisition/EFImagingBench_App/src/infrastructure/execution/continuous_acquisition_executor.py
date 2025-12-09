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

from application.ports.i_continuous_acquisition_executor import (
    IContinuousAcquisitionExecutor,
    ContinuousAcquisitionConfig,
)
from application.ports.i_acquisition_port import IAcquisitionPort

from domain.events.i_domain_event_bus import IDomainEventBus
from domain.events.continuous_acquisition_events import (
    ContinuousAcquisitionSampleAcquired,
)


class ContinuousAcquisitionExecutor(IContinuousAcquisitionExecutor):
    def __init__(self, acquisition_port: IAcquisitionPort, event_bus: IDomainEventBus) -> None:
        self._acquisition = acquisition_port
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: UUID | None = None

    def start(self, config: ContinuousAcquisitionConfig) -> None:
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
            args=(self._current_acquisition_id, config),
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
    ) -> None:
        """Background acquisition loop."""
        if config.sample_rate_hz <= 0:
            return

        dt = 1.0 / config.sample_rate_hz
        t0 = time.time()
        index = 0

        while not self._stop_flag.is_set():
            if config.max_duration_s is not None and (time.time() - t0) > config.max_duration_s:
                break

            sample = self._acquisition.acquire_sample()

            event = ContinuousAcquisitionSampleAcquired(
                acquisition_id=acquisition_id,
                sample_index=index,
                sample=sample,
            )
            self._event_bus.publish("continuousacquisitionsampleacquired", event)

            index += 1
            time.sleep(dt)


