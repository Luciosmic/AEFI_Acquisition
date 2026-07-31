"""
AefiAcquisitionExecutor

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

from application.services.aefi_acquisition_service.ports.i_aefi_acquisition_executor import (
    IAefiAcquisitionExecutor,
    AefiAcquisitionConfig,
)
from application.services.scan_application_service.ports.i_acquisition_port import IAcquisitionPort

from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.aefi_voltage_sample_acquired.aefi_voltage_sample_acquired import (
    AefiVoltageSampleAcquired,
)
from domain.shared_kernel.events.aefi_voltage_reading_started.aefi_voltage_reading_started import (
    AefiVoltageReadingStarted,
)
from domain.shared_kernel.events.aefi_voltage_reading_failed.aefi_voltage_reading_failed import (
    AefiVoltageReadingFailed,
)
from domain.shared_kernel.events.aefi_voltage_reading_stopped.aefi_voltage_reading_stopped import (
    AefiVoltageReadingStopped,
)


class AefiAcquisitionExecutor(IAefiAcquisitionExecutor):
    # ponytail: events renamed Acquisition->Reading (AefiVoltageReadingStarted/
    # Stopped/Failed) but this class/its port (IAefiAcquisitionExecutor) and
    # the application-layer AefiAcquisitionService/AefiAcquisitionConfig still
    # say "Acquisition" — cascade deliberately scoped out. Upgrade: rename
    # those too if the vocabulary mismatch causes real confusion.
    def __init__(self, event_bus: IDomainEventBus, acquisition_port: IAcquisitionPort | None = None) -> None:
        self._event_bus = event_bus
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self._current_acquisition_id: UUID | None = None

    def start(self, config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
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

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------ #
    # Internal worker
    # ------------------------------------------------------------------ #

    def _worker(
        self,
        acquisition_id: UUID,
        config: AefiAcquisitionConfig,
        acquisition_port: IAcquisitionPort,
    ) -> None:
        """Background acquisition loop. Best-effort: no software pacing."""
        started_event = AefiVoltageReadingStarted(acquisition_id=acquisition_id)
        self._event_bus.publish("aefivoltagereadingstarted", started_event)

        t0 = time.time()
        index = 0

        try:
            while not self._stop_flag.is_set():
                if config.max_duration_s is not None and (time.time() - t0) > config.max_duration_s:
                    break

                sample = acquisition_port.acquire_sample()

                event = AefiVoltageSampleAcquired(
                    acquisition_id=acquisition_id,
                    sample_index=index,
                    sample=sample,
                )
                self._event_bus.publish("aefivoltagesampleacquired", event)

                index += 1
        except Exception as e:
            error_event = AefiVoltageReadingFailed(
                acquisition_id=acquisition_id,
                reason=str(e)
            )
            self._event_bus.publish("aefivoltagereadingfailed", error_event)
        finally:
            stop_event = AefiVoltageReadingStopped(acquisition_id=acquisition_id)
            self._event_bus.publish("aefivoltagereadingstopped", stop_event)


